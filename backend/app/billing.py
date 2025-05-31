"""
BlockVerify Billing and Monetization System
Handles client management, usage tracking, API key generation, and billing
"""

import os
import uuid
import secrets
import hashlib
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any
from enum import Enum

import stripe
from sqlalchemy import Column, String, Integer, DateTime, Decimal as SQLDecimal, Boolean, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, relationship
from sqlalchemy.dialects.postgresql import UUID
from pydantic import BaseModel, EmailStr
from fastapi import HTTPException

# Initialize Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

Base = declarative_base()

class PlanType(str, Enum):
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"

class UsageType(str, Enum):
    VERIFICATION = "verification"
    TOKEN_CHECK = "token_check"
    API_CALL = "api_call"

# Database Models
class Client(Base):
    __tablename__ = "clients"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_name = Column(String(255), nullable=False)
    contact_email = Column(String(255), nullable=False, unique=True)
    website_url = Column(String(500))
    plan_type = Column(String(50), default=PlanType.FREE)
    
    # Billing info
    stripe_customer_id = Column(String(255))
    stripe_subscription_id = Column(String(255))
    billing_email = Column(String(255))
    
    # Usage limits
    monthly_limit = Column(Integer, default=1000)  # Free tier limit
    current_usage = Column(Integer, default=0)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    api_keys = relationship("APIKey", back_populates="client")
    usage_records = relationship("UsageRecord", back_populates="client")
    invoices = relationship("Invoice", back_populates="client")

class APIKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Key details
    key_prefix = Column(String(20), nullable=False)  # bv_prod_, bv_test_
    key_hash = Column(String(64), nullable=False, unique=True)  # SHA-256 of full key
    
    # Permissions and limits
    name = Column(String(255))  # Human-readable name
    permissions = Column(Text)  # JSON string of permissions
    rate_limit_per_minute = Column(Integer, default=100)
    rate_limit_per_hour = Column(Integer, default=5000)
    
    # Status
    is_active = Column(Boolean, default=True)
    last_used_at = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)  # Optional expiration
    
    # Relationships
    client = relationship("Client", back_populates="api_keys")
    usage_records = relationship("UsageRecord", back_populates="api_key")
    
    # Index for fast lookups
    __table_args__ = (
        Index('idx_api_key_hash', 'key_hash'),
        Index('idx_api_key_client', 'client_id'),
    )

class UsageRecord(Base):
    __tablename__ = "usage_records"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    api_key_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Usage details
    usage_type = Column(String(50), nullable=False)  # verification, token_check, etc.
    quantity = Column(Integer, default=1)
    
    # Request details
    endpoint = Column(String(255))
    method = Column(String(10))
    status_code = Column(Integer)
    response_time_ms = Column(Integer)
    
    # Billing
    cost_cents = Column(Integer, default=0)
    
    # Metadata
    user_agent = Column(String(500))
    ip_address = Column(String(45))
    metadata = Column(Text)  # JSON for additional data
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    client = relationship("Client", back_populates="usage_records")
    api_key = relationship("APIKey", back_populates="usage_records")
    
    # Indexes for analytics
    __table_args__ = (
        Index('idx_usage_client_date', 'client_id', 'created_at'),
        Index('idx_usage_type_date', 'usage_type', 'created_at'),
    )

class Invoice(Base):
    __tablename__ = "invoices"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Invoice details
    invoice_number = Column(String(50), unique=True, nullable=False)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    # Amounts in cents
    subtotal_cents = Column(Integer, nullable=False)
    tax_cents = Column(Integer, default=0)
    total_cents = Column(Integer, nullable=False)
    
    # Stripe integration
    stripe_invoice_id = Column(String(255))
    stripe_payment_intent_id = Column(String(255))
    
    # Status
    status = Column(String(50), default="draft")  # draft, sent, paid, failed
    paid_at = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    client = relationship("Client", back_populates="invoices")

# Pydantic Models
class ClientCreate(BaseModel):
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
    monthly_limit: int
    current_usage: int
    is_active: bool
    created_at: datetime

class APIKeyCreate(BaseModel):
    name: str
    permissions: Optional[List[str]] = ["verify"]
    rate_limit_per_minute: int = 100
    expires_in_days: Optional[int] = None

class APIKeyResponse(BaseModel):
    id: str
    name: str
    key_prefix: str
    permissions: List[str]
    rate_limit_per_minute: int
    is_active: bool
    created_at: datetime
    last_used_at: Optional[datetime]

class UsageStats(BaseModel):
    total_verifications: int
    total_api_calls: int
    current_month_usage: int
    monthly_limit: int
    usage_percentage: float
    cost_this_month_cents: int

# Plan Configurations
PLAN_CONFIGS = {
    PlanType.FREE: {
        "monthly_limit": 1000,
        "cost_per_verification_cents": 0,  # Free for first 1000
        "features": ["basic_verification", "webhook_support"],
        "rate_limit_per_minute": 10,
    },
    PlanType.STARTER: {
        "monthly_limit": 10000,
        "cost_per_verification_cents": 3,  # $0.03 per verification
        "features": ["basic_verification", "webhook_support", "analytics", "priority_support"],
        "rate_limit_per_minute": 100,
        "stripe_price_id": "price_starter_monthly",
    },
    PlanType.PROFESSIONAL: {
        "monthly_limit": 100000,
        "cost_per_verification_cents": 2,  # $0.02 per verification
        "features": ["all_features", "custom_integration", "dedicated_support"],
        "rate_limit_per_minute": 500,
        "stripe_price_id": "price_professional_monthly",
    },
    PlanType.ENTERPRISE: {
        "monthly_limit": 1000000,
        "cost_per_verification_cents": 1,  # $0.01 per verification
        "features": ["all_features", "custom_integration", "dedicated_support", "sla"],
        "rate_limit_per_minute": 2000,
        "stripe_price_id": "price_enterprise_monthly",
    }
}

class BillingService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_client(self, client_data: ClientCreate) -> Client:
        """Create a new client with free tier"""
        # Check if email already exists
        existing = self.db.query(Client).filter(Client.contact_email == client_data.contact_email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create Stripe customer
        stripe_customer = stripe.Customer.create(
            email=client_data.contact_email,
            name=client_data.business_name,
            metadata={
                "business_name": client_data.business_name,
                "website_url": client_data.website_url or "",
            }
        )
        
        client = Client(
            business_name=client_data.business_name,
            contact_email=client_data.contact_email,
            website_url=client_data.website_url,
            plan_type=client_data.plan_type,
            stripe_customer_id=stripe_customer.id,
            monthly_limit=PLAN_CONFIGS[client_data.plan_type]["monthly_limit"]
        )
        
        self.db.add(client)
        self.db.commit()
        self.db.refresh(client)
        
        # Create initial API key
        self.create_api_key(client.id, APIKeyCreate(name="Default API Key"))
        
        return client
    
    def create_api_key(self, client_id: str, key_data: APIKeyCreate) -> tuple[APIKey, str]:
        """Generate a new API key for a client"""
        client = self.db.query(Client).filter(Client.id == client_id).first()
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Generate API key
        key_secret = secrets.token_urlsafe(32)
        key_prefix = "bv_prod_" if client.plan_type != PlanType.FREE else "bv_test_"
        full_key = f"{key_prefix}{key_secret}"
        key_hash = hashlib.sha256(full_key.encode()).hexdigest()
        
        # Set expiration
        expires_at = None
        if key_data.expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=key_data.expires_in_days)
        
        api_key = APIKey(
            client_id=client_id,
            key_prefix=key_prefix,
            key_hash=key_hash,
            name=key_data.name,
            permissions=",".join(key_data.permissions or ["verify"]),
            rate_limit_per_minute=key_data.rate_limit_per_minute,
            expires_at=expires_at
        )
        
        self.db.add(api_key)
        self.db.commit()
        self.db.refresh(api_key)
        
        return api_key, full_key
    
    def validate_api_key(self, api_key: str) -> Optional[APIKey]:
        """Validate an API key and return the APIKey object"""
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        api_key_obj = self.db.query(APIKey).filter(
            APIKey.key_hash == key_hash,
            APIKey.is_active == True
        ).first()
        
        if not api_key_obj:
            return None
        
        # Check expiration
        if api_key_obj.expires_at and api_key_obj.expires_at < datetime.utcnow():
            return None
        
        # Update last used
        api_key_obj.last_used_at = datetime.utcnow()
        self.db.commit()
        
        return api_key_obj
    
    def record_usage(self, client_id: str, api_key_id: str, usage_type: UsageType, 
                    endpoint: str = None, **metadata) -> UsageRecord:
        """Record API usage for billing"""
        client = self.db.query(Client).filter(Client.id == client_id).first()
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Calculate cost
        plan_config = PLAN_CONFIGS[client.plan_type]
        cost_cents = 0
        
        if usage_type == UsageType.VERIFICATION:
            if client.current_usage >= client.monthly_limit:
                # Over limit, charge per verification
                cost_cents = plan_config["cost_per_verification_cents"]
            
            # Increment usage counter
            client.current_usage += 1
        
        usage_record = UsageRecord(
            client_id=client_id,
            api_key_id=api_key_id,
            usage_type=usage_type.value,
            endpoint=endpoint,
            cost_cents=cost_cents,
            metadata=str(metadata) if metadata else None
        )
        
        self.db.add(usage_record)
        self.db.commit()
        
        return usage_record
    
    def get_usage_stats(self, client_id: str) -> UsageStats:
        """Get usage statistics for a client"""
        client = self.db.query(Client).filter(Client.id == client_id).first()
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Current month usage
        start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        monthly_usage = self.db.query(UsageRecord).filter(
            UsageRecord.client_id == client_id,
            UsageRecord.created_at >= start_of_month,
            UsageRecord.usage_type == UsageType.VERIFICATION.value
        ).count()
        
        monthly_cost = self.db.query(UsageRecord).filter(
            UsageRecord.client_id == client_id,
            UsageRecord.created_at >= start_of_month
        ).with_entities(UsageRecord.cost_cents).all()
        
        total_cost = sum(record.cost_cents for record in monthly_cost)
        
        total_verifications = self.db.query(UsageRecord).filter(
            UsageRecord.client_id == client_id,
            UsageRecord.usage_type == UsageType.VERIFICATION.value
        ).count()
        
        total_api_calls = self.db.query(UsageRecord).filter(
            UsageRecord.client_id == client_id
        ).count()
        
        usage_percentage = (monthly_usage / client.monthly_limit) * 100 if client.monthly_limit > 0 else 0
        
        return UsageStats(
            total_verifications=total_verifications,
            total_api_calls=total_api_calls,
            current_month_usage=monthly_usage,
            monthly_limit=client.monthly_limit,
            usage_percentage=min(usage_percentage, 100),
            cost_this_month_cents=total_cost
        )
    
    def upgrade_plan(self, client_id: str, new_plan: PlanType) -> Client:
        """Upgrade a client's plan"""
        client = self.db.query(Client).filter(Client.id == client_id).first()
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        if new_plan == PlanType.FREE:
            raise HTTPException(status_code=400, detail="Cannot downgrade to free plan")
        
        # Create Stripe subscription
        plan_config = PLAN_CONFIGS[new_plan]
        
        if "stripe_price_id" in plan_config:
            subscription = stripe.Subscription.create(
                customer=client.stripe_customer_id,
                items=[{"price": plan_config["stripe_price_id"]}],
                metadata={"client_id": str(client_id)}
            )
            client.stripe_subscription_id = subscription.id
        
        # Update plan
        client.plan_type = new_plan
        client.monthly_limit = plan_config["monthly_limit"]
        
        self.db.commit()
        return client
    
    def check_rate_limit(self, api_key_obj: APIKey) -> bool:
        """Check if API key is within rate limits"""
        now = datetime.utcnow()
        minute_ago = now - timedelta(minutes=1)
        
        recent_calls = self.db.query(UsageRecord).filter(
            UsageRecord.api_key_id == api_key_obj.id,
            UsageRecord.created_at >= minute_ago
        ).count()
        
        return recent_calls < api_key_obj.rate_limit_per_minute
    
    def generate_invoice(self, client_id: str, period_start: datetime, period_end: datetime) -> Invoice:
        """Generate monthly invoice for a client"""
        client = self.db.query(Client).filter(Client.id == client_id).first()
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Calculate usage costs
        usage_records = self.db.query(UsageRecord).filter(
            UsageRecord.client_id == client_id,
            UsageRecord.created_at >= period_start,
            UsageRecord.created_at < period_end
        ).all()
        
        subtotal_cents = sum(record.cost_cents for record in usage_records)
        tax_cents = int(subtotal_cents * 0.08)  # 8% tax rate
        total_cents = subtotal_cents + tax_cents
        
        # Generate invoice number
        invoice_number = f"BV-{datetime.now().strftime('%Y%m')}-{client_id[:8].upper()}"
        
        invoice = Invoice(
            client_id=client_id,
            invoice_number=invoice_number,
            period_start=period_start,
            period_end=period_end,
            subtotal_cents=subtotal_cents,
            tax_cents=tax_cents,
            total_cents=total_cents
        )
        
        self.db.add(invoice)
        self.db.commit()
        
        # Create Stripe invoice if there are charges
        if total_cents > 0:
            stripe_invoice = stripe.Invoice.create(
                customer=client.stripe_customer_id,
                collection_method="send_invoice",
                days_until_due=30,
                metadata={
                    "invoice_id": str(invoice.id),
                    "period_start": period_start.isoformat(),
                    "period_end": period_end.isoformat()
                }
            )
            
            # Add line item for usage
            stripe.InvoiceItem.create(
                customer=client.stripe_customer_id,
                invoice=stripe_invoice.id,
                amount=total_cents,
                currency="usd",
                description=f"BlockVerify API usage ({period_start.strftime('%B %Y')})"
            )
            
            invoice.stripe_invoice_id = stripe_invoice.id
            self.db.commit()
        
        return invoice 