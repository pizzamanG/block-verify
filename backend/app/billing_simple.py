"""
BlockVerify Simple Billing System
Works without Stripe - can be upgraded later
Handles client management, API keys, and usage tracking
"""

import os
import uuid
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from enum import Enum

from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, Index, create_engine, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker, relationship
from pydantic import BaseModel, EmailStr

# Use the main database URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/blockverify")

# Handle SQLite for local development
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL, echo=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class PlanType(str, Enum):
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"

# Plan limits and pricing
PLAN_LIMITS = {
    PlanType.FREE: {
        "monthly_verifications": 1000,
        "rate_limit_per_minute": 10,
        "price_cents": 0
    },
    PlanType.STARTER: {
        "monthly_verifications": 10000,
        "rate_limit_per_minute": 60,
        "price_cents": 2900  # $29
    },
    PlanType.PROFESSIONAL: {
        "monthly_verifications": 100000,
        "rate_limit_per_minute": 300,
        "price_cents": 9900  # $99
    },
    PlanType.ENTERPRISE: {
        "monthly_verifications": 1000000,
        "rate_limit_per_minute": 1000,
        "price_cents": 29900  # $299+
    }
}

# Database Models
class SimpleClient(Base):
    __tablename__ = "simple_clients"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    business_name = Column(String(255), nullable=False)
    contact_email = Column(String(255), nullable=False, unique=True)
    website_url = Column(String(500))
    plan_type = Column(String(50), default=PlanType.FREE)
    
    # Usage tracking
    monthly_usage = Column(Integer, default=0)
    usage_reset_date = Column(DateTime, default=lambda: datetime.utcnow().replace(day=1))
    
    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=True)  # Auto-verify for now
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    api_keys = relationship("SimpleAPIKey", back_populates="client", cascade="all, delete-orphan")
    usage_records = relationship("SimpleUsageRecord", back_populates="client", cascade="all, delete-orphan")

class SimpleAPIKey(Base):
    __tablename__ = "simple_api_keys"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = Column(String(36), ForeignKey("simple_clients.id"), nullable=False, index=True)
    
    # Key details
    key_prefix = Column(String(20), nullable=False, default="bv_prod_")
    key_hash = Column(String(64), nullable=False, unique=True, index=True)
    
    # Metadata
    name = Column(String(255), default="Default API Key")
    
    # Rate limiting
    rate_limit_per_minute = Column(Integer, default=60)
    
    # Status
    is_active = Column(Boolean, default=True)
    last_used_at = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    client = relationship("SimpleClient", back_populates="api_keys")
    usage_records = relationship("SimpleUsageRecord", back_populates="api_key")

class SimpleUsageRecord(Base):
    __tablename__ = "simple_usage_records"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = Column(String(36), ForeignKey("simple_clients.id"), nullable=False, index=True)
    api_key_id = Column(String(36), ForeignKey("simple_api_keys.id"), nullable=False, index=True)
    
    # Usage details
    endpoint = Column(String(255))
    method = Column(String(10))
    status_code = Column(Integer)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    client = relationship("SimpleClient", back_populates="usage_records")
    api_key = relationship("SimpleAPIKey", back_populates="usage_records")
    
    # Indexes
    __table_args__ = (
        Index('idx_usage_client_date', 'client_id', 'created_at'),
    )

# Pydantic Models
class ClientRegister(BaseModel):
    business_name: str
    contact_email: EmailStr
    website_url: Optional[str] = None
    plan_type: PlanType = PlanType.FREE

class ClientResponse(BaseModel):
    id: str
    business_name: str
    contact_email: str
    website_url: Optional[str]
    plan_type: str
    monthly_usage: int
    monthly_limit: int
    is_active: bool
    created_at: datetime

class APIKeyResponse(BaseModel):
    id: str
    name: str
    key_prefix: str
    masked_key: str  # Shows only first 8 chars
    rate_limit_per_minute: int
    is_active: bool
    created_at: datetime
    last_used_at: Optional[datetime]

# Simple Billing Service
class SimpleBillingService:
    def __init__(self, db: Session):
        self.db = db
    
    def register_client(self, data: ClientRegister) -> SimpleClient:
        """Register a new client"""
        # Check if email already exists
        existing = self.db.query(SimpleClient).filter(
            SimpleClient.contact_email == data.contact_email
        ).first()
        
        if existing:
            raise ValueError("Email already registered")
        
        client = SimpleClient(
            business_name=data.business_name,
            contact_email=data.contact_email,
            website_url=data.website_url,
            plan_type=data.plan_type
        )
        
        self.db.add(client)
        self.db.commit()
        self.db.refresh(client)
        
        # Auto-create first API key
        api_key, raw_key = self.create_api_key(client.id, "Primary Key")
        
        return client, raw_key
    
    def create_api_key(self, client_id: str, name: str = None) -> tuple[SimpleAPIKey, str]:
        """Create a new API key for a client"""
        # Generate secure random key
        raw_key = f"bv_prod_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        
        # Get client's rate limit based on plan
        client = self.db.query(SimpleClient).filter(SimpleClient.id == client_id).first()
        if not client:
            raise ValueError("Client not found")
        
        rate_limit = PLAN_LIMITS[client.plan_type]["rate_limit_per_minute"]
        
        api_key = SimpleAPIKey(
            client_id=client_id,
            name=name or "API Key",
            key_hash=key_hash,
            rate_limit_per_minute=rate_limit
        )
        
        self.db.add(api_key)
        self.db.commit()
        self.db.refresh(api_key)
        
        return api_key, raw_key
    
    def validate_api_key(self, raw_key: str) -> Optional[SimpleAPIKey]:
        """Validate an API key and return the key object"""
        if not raw_key or not raw_key.startswith("bv_"):
            return None
        
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        
        api_key = self.db.query(SimpleAPIKey).filter(
            SimpleAPIKey.key_hash == key_hash,
            SimpleAPIKey.is_active == True
        ).first()
        
        if api_key:
            # Update last used
            api_key.last_used_at = datetime.utcnow()
            self.db.commit()
        
        return api_key
    
    def check_usage_limit(self, client_id: str) -> tuple[bool, dict]:
        """Check if client is within their usage limits"""
        client = self.db.query(SimpleClient).filter(SimpleClient.id == client_id).first()
        if not client:
            return False, {"error": "Client not found"}
        
        # Reset monthly usage if needed
        now = datetime.utcnow()
        if now >= client.usage_reset_date + timedelta(days=30):
            client.monthly_usage = 0
            client.usage_reset_date = now.replace(day=1)
            self.db.commit()
        
        # Check limit
        limit = PLAN_LIMITS[client.plan_type]["monthly_verifications"]
        
        if client.monthly_usage >= limit:
            return False, {
                "error": "Monthly limit exceeded",
                "usage": client.monthly_usage,
                "limit": limit,
                "plan": client.plan_type
            }
        
        return True, {
            "usage": client.monthly_usage,
            "limit": limit,
            "remaining": limit - client.monthly_usage
        }
    
    def record_usage(self, client_id: str, api_key_id: str, endpoint: str, 
                    method: str = "POST", status_code: int = 200) -> SimpleUsageRecord:
        """Record API usage"""
        # Create usage record
        usage = SimpleUsageRecord(
            client_id=client_id,
            api_key_id=api_key_id,
            endpoint=endpoint,
            method=method,
            status_code=status_code
        )
        
        self.db.add(usage)
        
        # Increment monthly usage
        client = self.db.query(SimpleClient).filter(SimpleClient.id == client_id).first()
        if client:
            client.monthly_usage += 1
        
        self.db.commit()
        return usage
    
    def get_client_stats(self, client_id: str) -> dict:
        """Get client usage statistics"""
        client = self.db.query(SimpleClient).filter(SimpleClient.id == client_id).first()
        if not client:
            return None
        
        # Get current month usage
        month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        recent_usage = self.db.query(SimpleUsageRecord).filter(
            SimpleUsageRecord.client_id == client_id,
            SimpleUsageRecord.created_at >= month_start
        ).count()
        
        # Get API keys
        api_keys = self.db.query(SimpleAPIKey).filter(
            SimpleAPIKey.client_id == client_id
        ).all()
        
        limit = PLAN_LIMITS[client.plan_type]["monthly_verifications"]
        
        return {
            "client": {
                "id": str(client.id),
                "business_name": client.business_name,
                "plan": client.plan_type,
                "created_at": client.created_at.isoformat()
            },
            "usage": {
                "current_month": client.monthly_usage,
                "limit": limit,
                "percentage": round((client.monthly_usage / limit) * 100, 2) if limit > 0 else 0,
                "reset_date": client.usage_reset_date.isoformat()
            },
            "api_keys": len(api_keys),
            "active_keys": sum(1 for k in api_keys if k.is_active)
        }

# Create tables
Base.metadata.create_all(bind=engine) 