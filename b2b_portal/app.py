#!/usr/bin/env python3
"""
BlockVerify B2B Portal
Enterprise-grade customer management and billing system
"""

from fastapi import FastAPI, HTTPException, Depends, Request, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Float, Boolean, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import secrets
import hashlib
import hmac
import jwt
import stripe
import asyncio
import logging
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

load_dotenv()

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./blockverify_b2b.db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Stripe setup
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_...")

# Models
class Company(Base):
    __tablename__ = "companies"
    
    id = Column(String, primary_key=True)  # Company UUID
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    domain = Column(String, nullable=True)  # company.com
    industry = Column(String, nullable=True)  # adult-entertainment, gaming, etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    stripe_customer_id = Column(String, nullable=True)
    subscription_status = Column(String, default="trial")  # trial, active, suspended, cancelled
    monthly_quota = Column(Integer, default=10000)  # API calls per month
    current_usage = Column(Integer, default=0)
    billing_email = Column(String, nullable=True)
    contact_name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_email', 'email'),
        Index('idx_domain', 'domain'),
        Index('idx_subscription_status', 'subscription_status'),
    )

class APIKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(String, primary_key=True)  # API Key ID
    company_id = Column(String, nullable=False)  # Foreign key to companies
    key_hash = Column(String, nullable=False)  # SHA-256 hash of the actual key
    key_prefix = Column(String, nullable=False)  # First 8 chars for display (bv_prod_12345678...)
    name = Column(String, nullable=False)  # User-friendly name
    environment = Column(String, default="production")  # production, staging, development
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    allowed_domains = Column(Text, nullable=True)  # JSON array of allowed domains
    rate_limit = Column(Integer, default=1000)  # Requests per hour
    
    # Indexes
    __table_args__ = (
        Index('idx_company_id', 'company_id'),
        Index('idx_key_hash', 'key_hash'),
        Index('idx_key_prefix', 'key_prefix'),
    )

class APIUsage(Base):
    __tablename__ = "api_usage"
    
    id = Column(String, primary_key=True)
    company_id = Column(String, nullable=False)
    api_key_id = Column(String, nullable=False)
    endpoint = Column(String, nullable=False)  # /verify-token, /webauthn/register, etc.
    timestamp = Column(DateTime, default=datetime.utcnow)
    response_code = Column(Integer, nullable=False)  # 200, 400, 401, etc.
    response_time_ms = Column(Float, nullable=False)
    user_agent = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    country = Column(String, nullable=True)  # For analytics
    
    # Partitioning-ready indexes (unique names per table)
    __table_args__ = (
        Index('idx_usage_company_timestamp', 'company_id', 'timestamp'),
        Index('idx_usage_api_key_timestamp', 'api_key_id', 'timestamp'),
        Index('idx_usage_timestamp', 'timestamp'),  # For cleanup jobs
    )

class BillingEvent(Base):
    __tablename__ = "billing_events"
    
    id = Column(String, primary_key=True)
    company_id = Column(String, nullable=False)
    event_type = Column(String, nullable=False)  # invoice_created, payment_succeeded, etc.
    stripe_event_id = Column(String, nullable=True)
    amount_cents = Column(Integer, nullable=True)
    currency = Column(String, default="usd")
    timestamp = Column(DateTime, default=datetime.utcnow)
    event_data = Column(Text, nullable=True)  # JSON data (renamed from metadata)
    
    __table_args__ = (
        Index('idx_billing_company_timestamp', 'company_id', 'timestamp'),
        Index('idx_billing_stripe_event', 'stripe_event_id'),
    )

# Create tables
Base.metadata.create_all(bind=engine)

# Pydantic models
class CompanyCreate(BaseModel):
    name: str
    email: EmailStr
    domain: Optional[str] = None
    industry: Optional[str] = None
    contact_name: Optional[str] = None
    phone: Optional[str] = None

class APIKeyCreate(BaseModel):
    name: str
    environment: str = "production"
    allowed_domains: Optional[List[str]] = None
    rate_limit: int = 1000

class UsageStats(BaseModel):
    total_calls: int
    calls_today: int
    calls_this_month: int
    success_rate: float
    avg_response_time: float

# FastAPI app
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🏢 Starting BlockVerify B2B Portal...")
    yield
    logger.info("🏢 Shutting down B2B Portal...")

app = FastAPI(
    title="BlockVerify B2B Portal",
    description="Enterprise Age Verification API Management",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="b2b_portal/static"), name="static")

# Dependencies
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

security = HTTPBearer()

def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    """Verify API key for authenticated endpoints"""
    token = credentials.credentials
    
    # Hash the provided token
    key_hash = hashlib.sha256(token.encode()).hexdigest()
    
    # Look up in database
    api_key = db.query(APIKey).filter(APIKey.key_hash == key_hash, APIKey.is_active == True).first()
    if not api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # Update last used
    api_key.last_used = datetime.utcnow()
    db.commit()
    
    # Get company
    company = db.query(Company).filter(Company.id == api_key.company_id).first()
    if not company:
        raise HTTPException(status_code=401, detail="Company not found")
    
    return {"api_key": api_key, "company": company}

# Utility functions
def generate_api_key() -> tuple[str, str]:
    """Generate a new API key and return (full_key, prefix)"""
    # Format: bv_prod_32_random_chars
    key_id = secrets.token_urlsafe(32)
    full_key = f"bv_prod_{key_id}"
    prefix = full_key[:12] + "..."  # First 12 chars for display
    return full_key, prefix

def hash_api_key(api_key: str) -> str:
    """Hash an API key for storage"""
    return hashlib.sha256(api_key.encode()).hexdigest()

async def track_usage(company_id: str, api_key_id: str, endpoint: str, response_code: int, 
                     response_time_ms: float, request: Request, db: Session):
    """Track API usage for billing and analytics"""
    usage = APIUsage(
        id=secrets.token_urlsafe(16),
        company_id=company_id,
        api_key_id=api_key_id,
        endpoint=endpoint,
        response_code=response_code,
        response_time_ms=response_time_ms,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host,
    )
    
    db.add(usage)
    
    # Update company usage counter
    company = db.query(Company).filter(Company.id == company_id).first()
    if company:
        company.current_usage += 1
        
    db.commit()

# Routes

@app.get("/", response_class=HTMLResponse)
async def portal_home():
    """B2B Portal Landing Page"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>BlockVerify B2B Portal</title>
        <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    </head>
    <body class="bg-gray-50">
        <nav class="bg-blue-600 text-white p-4">
            <div class="container mx-auto flex justify-between items-center">
                <h1 class="text-2xl font-bold">🔐 BlockVerify B2B</h1>
                <div class="space-x-4">
                    <a href="/register" class="bg-white text-blue-600 px-4 py-2 rounded hover:bg-gray-100">Get Started</a>
                    <a href="/login" class="border border-white px-4 py-2 rounded hover:bg-blue-700">Login</a>
                </div>
            </div>
        </nav>
        
        <main class="container mx-auto py-12 px-4">
            <div class="text-center mb-12">
                <h1 class="text-5xl font-bold text-gray-800 mb-6">Enterprise Age Verification</h1>
                <p class="text-xl text-gray-600 mb-8">Privacy-preserving, blockchain-anchored identity verification for adult sites</p>
                <div class="flex justify-center space-x-4">
                    <a href="/register" class="bg-blue-600 text-white px-8 py-3 rounded-lg text-lg font-semibold hover:bg-blue-700">Start Free Trial</a>
                    <a href="/docs" class="border border-blue-600 text-blue-600 px-8 py-3 rounded-lg text-lg font-semibold hover:bg-blue-50">View Docs</a>
                </div>
            </div>
            
            <div class="grid md:grid-cols-3 gap-8 mb-12">
                <div class="bg-white p-6 rounded-lg shadow-md">
                    <div class="text-blue-600 text-3xl mb-4"><i class="fas fa-shield-alt"></i></div>
                    <h3 class="text-xl font-semibold mb-2">Privacy-First</h3>
                    <p class="text-gray-600">Zero-knowledge verification. No user data stored on your servers.</p>
                </div>
                <div class="bg-white p-6 rounded-lg shadow-md">
                    <div class="text-blue-600 text-3xl mb-4"><i class="fas fa-bolt"></i></div>
                    <h3 class="text-xl font-semibold mb-2">Lightning Fast</h3>
                    <p class="text-gray-600">Sub-100ms API responses. Built for scale with global CDN.</p>
                </div>
                <div class="bg-white p-6 rounded-lg shadow-md">
                    <div class="text-blue-600 text-3xl mb-4"><i class="fas fa-link"></i></div>
                    <h3 class="text-xl font-semibold mb-2">Blockchain Trust</h3>
                    <p class="text-gray-600">Cryptographically verified on Polygon. Tamper-proof audit trail.</p>
                </div>
            </div>
            
            <div class="bg-white p-8 rounded-lg shadow-md">
                <h2 class="text-2xl font-bold mb-6">Simple Integration</h2>
                <div class="bg-gray-100 p-4 rounded text-sm font-mono">
                    <span class="text-gray-500">// Add to your website</span><br>
                    &lt;script src="https://api.blockverify.com/v1/client.js"&gt;&lt;/script&gt;<br><br>
                    <span class="text-gray-500">// Verify age</span><br>
                    <span class="text-blue-600">const</span> verified = <span class="text-blue-600">await</span> BlockVerify.<span class="text-purple-600">checkAge</span>({<br>
                    &nbsp;&nbsp;apiKey: <span class="text-green-600">'bv_prod_your_key_here'</span>,<br>
                    &nbsp;&nbsp;minAge: <span class="text-orange-600">18</span><br>
                    });
                </div>
            </div>
        </main>
    </body>
    </html>
    """

@app.get("/register", response_class=HTMLResponse)
async def register_form():
    """Company Registration Form"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Register - BlockVerify B2B</title>
        <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    </head>
    <body class="bg-gray-50 min-h-screen flex items-center justify-center">
        <div class="max-w-md w-full bg-white p-8 rounded-lg shadow-md">
            <h2 class="text-2xl font-bold text-center mb-6">Start Your Free Trial</h2>
            <form action="/api/companies" method="post" class="space-y-4">
                <div>
                    <label class="block text-sm font-medium text-gray-700">Company Name</label>
                    <input type="text" name="name" required class="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500">
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700">Business Email</label>
                    <input type="email" name="email" required class="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500">
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700">Website Domain</label>
                    <input type="text" name="domain" placeholder="yoursite.com" class="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500">
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700">Industry</label>
                    <select name="industry" class="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500">
                        <option value="adult-entertainment">Adult Entertainment</option>
                        <option value="gaming">Gaming</option>
                        <option value="social-media">Social Media</option>
                        <option value="e-commerce">E-commerce</option>
                        <option value="other">Other</option>
                    </select>
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700">Contact Name</label>
                    <input type="text" name="contact_name" class="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500">
                </div>
                <button type="submit" class="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500">
                    Create Account
                </button>
            </form>
            <p class="text-center text-sm text-gray-600 mt-4">
                Already have an account? <a href="/login" class="text-blue-600 hover:underline">Sign in</a>
            </p>
        </div>
    </body>
    </html>
    """

@app.post("/api/companies")
async def create_company(
    name: str = Form(...),
    email: str = Form(...),
    domain: str = Form(None),
    industry: str = Form(None),
    contact_name: str = Form(None),
    db: Session = Depends(get_db)
):
    """Create a new company account"""
    
    # Check if email already exists
    existing = db.query(Company).filter(Company.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create company
    company_id = secrets.token_urlsafe(16)
    company = Company(
        id=company_id,
        name=name,
        email=email,
        domain=domain,
        industry=industry,
        contact_name=contact_name,
        subscription_status="trial",
        monthly_quota=10000,  # 10k free API calls
        current_usage=0
    )
    
    db.add(company)
    db.commit()
    
    # Generate first API key
    api_key, key_prefix = generate_api_key()
    api_key_record = APIKey(
        id=secrets.token_urlsafe(16),
        company_id=company_id,
        key_hash=hash_api_key(api_key),
        key_prefix=key_prefix,
        name="Production Key",
        environment="production"
    )
    
    db.add(api_key_record)
    db.commit()
    
    logger.info(f"🏢 New company registered: {name} ({email})")
    
    # Redirect to dashboard with API key
    return RedirectResponse(f"/dashboard?company_id={company_id}&api_key={api_key}", status_code=302)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(company_id: str = Query(...), api_key: str = Query(None), db: Session = Depends(get_db)):
    """Company Dashboard"""
    
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Get API keys
    api_keys = db.query(APIKey).filter(APIKey.company_id == company_id, APIKey.is_active == True).all()
    
    # Calculate usage stats
    total_calls = db.query(APIUsage).filter(APIUsage.company_id == company_id).count()
    calls_today = db.query(APIUsage).filter(
        APIUsage.company_id == company_id,
        APIUsage.timestamp >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    ).count()
    
    quota_used_pct = (company.current_usage / company.monthly_quota * 100) if company.monthly_quota > 0 else 0
    
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Dashboard - BlockVerify B2B</title>
        <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    </head>
    <body class="bg-gray-50">
        <nav class="bg-blue-600 text-white p-4">
            <div class="container mx-auto flex justify-between items-center">
                <h1 class="text-2xl font-bold">🔐 BlockVerify B2B</h1>
                <div class="text-sm">Welcome, {company.name}</div>
            </div>
        </nav>
        
        <main class="container mx-auto py-8 px-4">
            <div class="grid md:grid-cols-4 gap-6 mb-8">
                <div class="bg-white p-6 rounded-lg shadow">
                    <div class="text-2xl font-bold text-blue-600">{total_calls:,}</div>
                    <div class="text-gray-600">Total API Calls</div>
                </div>
                <div class="bg-white p-6 rounded-lg shadow">
                    <div class="text-2xl font-bold text-green-600">{calls_today:,}</div>
                    <div class="text-gray-600">Today</div>
                </div>
                <div class="bg-white p-6 rounded-lg shadow">
                    <div class="text-2xl font-bold text-orange-600">{company.current_usage:,}</div>
                    <div class="text-gray-600">This Month</div>
                </div>
                <div class="bg-white p-6 rounded-lg shadow">
                    <div class="text-2xl font-bold text-purple-600">{quota_used_pct:.1f}%</div>
                    <div class="text-gray-600">Quota Used</div>
                </div>
            </div>
            
            {"<div class='bg-yellow-100 border border-yellow-400 text-yellow-700 px-4 py-3 rounded mb-6'><strong>🎉 Welcome!</strong> Your API key: <code class='bg-yellow-200 px-2 py-1 rounded'>" + api_key + "</code><br><small>Save this key safely - it won't be shown again!</small></div>" if api_key else ""}
            
            <div class="grid md:grid-cols-2 gap-8">
                <div class="bg-white p-6 rounded-lg shadow">
                    <h2 class="text-xl font-bold mb-4">API Keys</h2>
                    <div class="space-y-3">
                        {"".join([f'''
                        <div class="flex justify-between items-center p-3 bg-gray-50 rounded">
                            <div>
                                <div class="font-medium">{key.name}</div>
                                <div class="text-sm text-gray-600">{key.key_prefix}</div>
                                <div class="text-xs text-gray-500">{key.environment} • Last used: {key.last_used.strftime("%Y-%m-%d") if key.last_used else "Never"}</div>
                            </div>
                            <div class="text-green-600"><i class="fas fa-check-circle"></i></div>
                        </div>
                        ''' for key in api_keys])}
                    </div>
                    <button class="mt-4 bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">Generate New Key</button>
                </div>
                
                <div class="bg-white p-6 rounded-lg shadow">
                    <h2 class="text-xl font-bold mb-4">Quick Integration</h2>
                    <div class="text-sm">
                        <h3 class="font-medium mb-2">JavaScript SDK</h3>
                        <div class="bg-gray-100 p-3 rounded text-xs font-mono">
&lt;script src="https://api.blockverify.com/v1/client.js">&lt;/script><br>
&lt;script><br>
&nbsp;&nbsp;BlockVerify.init({{<br>
&nbsp;&nbsp;&nbsp;&nbsp;apiKey: 'your_api_key_here',<br>
&nbsp;&nbsp;&nbsp;&nbsp;minAge: 18<br>
&nbsp;&nbsp;}});<br>
&lt;/script>
                        </div>
                        
                        <h3 class="font-medium mb-2 mt-4">REST API</h3>
                        <div class="bg-gray-100 p-3 rounded text-xs font-mono">
curl -X POST https://api.blockverify.com/v1/verify-token \\<br>
&nbsp;&nbsp;-H "Authorization: Bearer your_api_key" \\<br>
&nbsp;&nbsp;-H "Content-Type: application/json" \\<br>
&nbsp;&nbsp;-d '{{"token": "user_age_token"}}'
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="mt-8 bg-white p-6 rounded-lg shadow">
                <h2 class="text-xl font-bold mb-4">Account Status</h2>
                <div class="grid md:grid-cols-2 gap-6">
                    <div>
                        <div class="text-sm text-gray-600">Subscription</div>
                        <div class="text-lg font-semibold text-green-600 capitalize">{company.subscription_status}</div>
                        {"<div class='text-sm text-blue-600 mt-1'><a href='/billing' class='hover:underline'>Upgrade to Pro →</a></div>" if company.subscription_status == "trial" else ""}
                    </div>
                    <div>
                        <div class="text-sm text-gray-600">Monthly Quota</div>
                        <div class="text-lg font-semibold">{company.current_usage:,} / {company.monthly_quota:,}</div>
                        <div class="w-full bg-gray-200 rounded-full h-2 mt-1">
                            <div class="bg-blue-600 h-2 rounded-full" style="width: {quota_used_pct:.1f}%"></div>
                        </div>
                    </div>
                </div>
            </div>
        </main>
    </body>
    </html>
    """

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "blockverify-b2b-portal"}

if __name__ == "__main__":
    import uvicorn
    print("🏢 Starting BlockVerify B2B Portal on http://localhost:4000")
    print("🎯 Companies can register and manage API keys here")
    uvicorn.run(app, host="0.0.0.0", port=4000) 