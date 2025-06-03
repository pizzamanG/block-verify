#!/usr/bin/env python3
"""
BlockVerify Production API
Enterprise-grade age verification service with billing integration
"""

from fastapi import FastAPI, HTTPException, Depends, Request, Header, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Float, Boolean, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import secrets
import hashlib
import hmac
import jwt
import asyncio
import logging
import redis
import json
import time
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import geoip2.database
import user_agents
from usage_tracker import UsageTracker
from email_service import create_notification_service

load_dotenv()

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Redis setup for caching and rate limiting
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    password=os.getenv("REDIS_PASSWORD"),
    decode_responses=True
)

# Rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=f"redis://{os.getenv('REDIS_HOST', 'localhost')}:{os.getenv('REDIS_PORT', 6379)}"
)

# Database setup (same as B2B portal)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./blockverify_b2b.db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Import models from B2B portal
from b2b_portal.app import Company, APIKey, APIUsage, BillingEvent

# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "your-super-secret-jwt-key")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# GeoIP database for analytics
try:
    geoip_reader = geoip2.database.Reader('GeoLite2-Country.mmdb')
except:
    geoip_reader = None
    logger.warning("GeoIP database not found - country analytics disabled")

# Pydantic models
class TokenVerifyRequest(BaseModel):
    token: str
    min_age: Optional[int] = 18
    user_agent: Optional[str] = None

class TokenVerifyResponse(BaseModel):
    valid: bool
    age_over: Optional[int] = None
    verified_by: str
    expires_at: Optional[datetime] = None
    device_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class RateLimitInfo(BaseModel):
    requests_remaining: int
    reset_time: int
    plan: str

# FastAPI app
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting BlockVerify Production API...")
    logger.info(f"🔗 Redis: {redis_client.ping()}")
    logger.info(f"💾 Database: {DATABASE_URL}")
    yield
    logger.info("🛑 Shutting down Production API...")

app = FastAPI(
    title="BlockVerify Production API",
    description="Enterprise Age Verification Service",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs" if os.getenv("ENVIRONMENT") != "production" else None,  # Hide docs in prod
    redoc_url="/redoc" if os.getenv("ENVIRONMENT") != "production" else None
)

# Add middleware
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# CORS - restrictive in production
if os.getenv("ENVIRONMENT") == "production":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "https://*.blockverify.com",
            "https://api.blockverify.com"
        ],
        allow_credentials=True,
        allow_methods=["POST", "GET"],
        allow_headers=["Authorization", "Content-Type"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Trusted hosts in production
if os.getenv("ENVIRONMENT") == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["api.blockverify.com", "*.blockverify.com"]
    )

# Dependencies
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

security = HTTPBearer()

async def verify_api_key_and_rate_limit(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Verify API key, check rate limits, and track usage"""
    start_time = time.time()
    
    # Extract API key
    api_key_token = credentials.credentials
    
    # Check cache first for performance
    cache_key = f"api_key:{hashlib.sha256(api_key_token.encode()).hexdigest()[:16]}"
    cached = redis_client.get(cache_key)
    
    if cached:
        auth_data = json.loads(cached)
        api_key_id = auth_data["api_key_id"]
        company_id = auth_data["company_id"]
        rate_limit = auth_data["rate_limit"]
        company_name = auth_data["company_name"]
    else:
        # Hash the provided token
        key_hash = hashlib.sha256(api_key_token.encode()).hexdigest()
        
        # Look up in database
        api_key = db.query(APIKey).filter(
            APIKey.key_hash == key_hash, 
            APIKey.is_active == True
        ).first()
        
        if not api_key:
            raise HTTPException(status_code=401, detail="Invalid API key")
        
        # Get company
        company = db.query(Company).filter(Company.id == api_key.company_id).first()
        if not company:
            raise HTTPException(status_code=401, detail="Company not found")
        
        if company.subscription_status in ["suspended", "cancelled"]:
            raise HTTPException(status_code=402, detail="Subscription suspended - please update billing")
        
        # Cache for 5 minutes
        auth_data = {
            "api_key_id": api_key.id,
            "company_id": company.id,
            "rate_limit": api_key.rate_limit,
            "company_name": company.name
        }
        redis_client.setex(cache_key, 300, json.dumps(auth_data))
        
        api_key_id = api_key.id
        company_id = company.id
        rate_limit = api_key.rate_limit
        company_name = company.name
        
        # Update last used (async)
        api_key.last_used = datetime.utcnow()
        db.commit()
    
    # Rate limiting per API key
    rate_key = f"rate_limit:{api_key_id}"
    current_requests = redis_client.get(rate_key)
    
    if current_requests is None:
        redis_client.setex(rate_key, 3600, 1)  # 1 hour window
        current_requests = 1
    else:
        current_requests = int(current_requests)
        if current_requests >= rate_limit:
            raise HTTPException(
                status_code=429, 
                detail=f"Rate limit exceeded. {rate_limit} requests per hour allowed.",
                headers={"Retry-After": "3600"}
            )
        redis_client.incr(rate_key)
        current_requests += 1
    
    # Add quota check
    quota_key = f"quota:{company_id}"
    monthly_usage = redis_client.get(quota_key)
    if monthly_usage and int(monthly_usage) >= 50000:  # 50k monthly limit for trial
        raise HTTPException(
            status_code=402,
            detail="Monthly quota exceeded. Please upgrade your plan."
        )
    
    return {
        "api_key_id": api_key_id,
        "company_id": company_id,
        "company_name": company_name,
        "rate_limit": rate_limit,
        "requests_used": current_requests,
        "start_time": start_time
    }

def get_country_from_ip(ip_address: str) -> Optional[str]:
    """Get country code from IP address"""
    if not geoip_reader:
        return None
    
    try:
        response = geoip_reader.country(ip_address)
        return response.country.iso_code
    except:
        return None

async def track_api_usage(
    company_id: str,
    api_key_id: str,
    endpoint: str,
    response_code: int,
    start_time: float,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session
):
    """Track API usage for billing and analytics with smart notifications"""
    
    def _track_usage():
        try:
            # Calculate response time
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            
            # Parse user agent
            ua_string = request.headers.get("user-agent", "")
            ua = user_agents.parse(ua_string)
            
            # Get country
            ip = request.client.host
            country = get_country_from_ip(ip)
            
            # Create usage record
            usage = APIUsage(
                id=secrets.token_urlsafe(16),
                company_id=company_id,
                api_key_id=api_key_id,
                endpoint=endpoint,
                timestamp=datetime.utcnow(),
                response_code=response_code,
                response_time_ms=response_time,
                user_agent=ua_string[:500],  # Truncate
                ip_address=ip,
                country=country
            )
            
            db.add(usage)
            
            # Update company usage counter
            company = db.query(Company).filter(Company.id == company_id).first()
            if company:
                company.current_usage += 1
                
                # Check for notification triggers
                usage_tracker = UsageTracker(db)
                usage_tracker._check_usage_alerts(company)
            
            db.commit()
            
            # Update Redis counters for real-time analytics
            date_key = datetime.utcnow().strftime("%Y-%m")
            redis_client.incr(f"usage:{company_id}:{date_key}")
            redis_client.incr(f"quota:{company_id}")
            redis_client.expire(f"quota:{company_id}", 2592000)  # 30 days
            
            logger.info(f"📊 API call tracked: {company_id} -> {endpoint} ({response_code}) in {response_time:.1f}ms")
            
        except Exception as e:
            logger.error(f"❌ Failed to track usage: {e}")
    
    # Track in background to not slow down response
    background_tasks.add_task(_track_usage)

# Routes

@app.get("/")
async def root():
    """API information"""
    return {
        "service": "BlockVerify Production API",
        "version": "2.0.0",
        "status": "operational",
        "endpoints": {
            "verify_token": "/v1/verify-token",
            "health": "/health",
            "docs": "/docs" if os.getenv("ENVIRONMENT") != "production" else "disabled"
        },
        "support": "support@blockverify.com"
    }

@app.get("/health")
async def health_check():
    """Comprehensive health check"""
    try:
        # Test Redis
        redis_status = redis_client.ping()
        
        # Test Database
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        
        return {
            "status": "healthy",
            "service": "blockverify-production-api",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                "redis": "healthy" if redis_status else "unhealthy",
                "database": "healthy",
                "geoip": "healthy" if geoip_reader else "disabled"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

@app.post("/v1/verify-token", response_model=TokenVerifyResponse)
@limiter.limit("100/minute")  # Global rate limit
async def verify_age_token(
    request: Request,
    verify_request: TokenVerifyRequest,
    background_tasks: BackgroundTasks,
    auth_data: dict = Depends(verify_api_key_and_rate_limit),
    db: Session = Depends(get_db)
):
    """
    Verify an age verification token
    
    This is the main production endpoint that companies integrate with.
    """
    
    start_time = auth_data["start_time"]
    
    try:
        token = verify_request.token
        min_age = verify_request.min_age or 18
        
        logger.info(f"🔍 Token verification request from {auth_data['company_name']}")
        
        # Try to verify as JWT first (production format)
        try:
            # Import JWT functions from main API
            from simple_api import verify_jwt_token
            
            # Verify JWT token
            payload = verify_jwt_token(token)
            
            if payload and payload.get("age_over", 0) >= min_age:
                response = TokenVerifyResponse(
                    valid=True,
                    age_over=payload.get("age_over"),
                    verified_by="BlockVerify-JWT",
                    expires_at=datetime.fromtimestamp(payload.get("exp", 0)),
                    device_type=payload.get("device_type", "web"),
                    metadata={
                        "issuer": payload.get("iss"),
                        "audience": payload.get("aud"),
                        "jti": payload.get("jti")
                    }
                )
                
                # Track successful verification
                await track_api_usage(
                    auth_data["company_id"],
                    auth_data["api_key_id"],
                    "/v1/verify-token",
                    200,
                    start_time,
                    request,
                    background_tasks,
                    db
                )
                
                logger.info(f"✅ JWT token verified successfully for {auth_data['company_name']}")
                return response
            else:
                # Valid JWT but age requirement not met
                response = TokenVerifyResponse(
                    valid=False,
                    verified_by="BlockVerify-JWT",
                    metadata={"reason": "age_requirement_not_met"}
                )
                
                await track_api_usage(
                    auth_data["company_id"],
                    auth_data["api_key_id"],
                    "/v1/verify-token",
                    200,
                    start_time,
                    request,
                    background_tasks,
                    db
                )
                
                return response
                
        except Exception as jwt_error:
            logger.warning(f"JWT verification failed: {jwt_error}")
            
            # Fallback to legacy base64 format for backward compatibility
            try:
                import base64
                decoded = json.loads(base64.b64decode(token))
                
                if decoded.get("ageOver", 0) >= min_age:
                    # Check expiration
                    exp = decoded.get("exp", 0)
                    if exp and datetime.fromtimestamp(exp) < datetime.utcnow():
                        response = TokenVerifyResponse(
                            valid=False,
                            verified_by="BlockVerify-Legacy",
                            metadata={"reason": "token_expired"}
                        )
                    else:
                        response = TokenVerifyResponse(
                            valid=True,
                            age_over=decoded.get("ageOver"),
                            verified_by="BlockVerify-Legacy",
                            expires_at=datetime.fromtimestamp(exp) if exp else None,
                            device_type="web"
                        )
                else:
                    response = TokenVerifyResponse(
                        valid=False,
                        verified_by="BlockVerify-Legacy",
                        metadata={"reason": "age_requirement_not_met"}
                    )
                
                await track_api_usage(
                    auth_data["company_id"],
                    auth_data["api_key_id"],
                    "/v1/verify-token",
                    200,
                    start_time,
                    request,
                    background_tasks,
                    db
                )
                
                return response
                
            except Exception as legacy_error:
                logger.error(f"Legacy token verification failed: {legacy_error}")
                
                # Invalid token format
                response = TokenVerifyResponse(
                    valid=False,
                    verified_by="BlockVerify",
                    metadata={"reason": "invalid_token_format"}
                )
                
                await track_api_usage(
                    auth_data["company_id"],
                    auth_data["api_key_id"],
                    "/v1/verify-token",
                    400,
                    start_time,
                    request,
                    background_tasks,
                    db
                )
                
                return response
    
    except Exception as e:
        logger.error(f"❌ Token verification error: {e}")
        
        await track_api_usage(
            auth_data["company_id"],
            auth_data["api_key_id"],
            "/v1/verify-token",
            500,
            start_time,
            request,
            background_tasks,
            db
        )
        
        raise HTTPException(status_code=500, detail="Internal verification error")

@app.get("/v1/rate-limit-info")
async def get_rate_limit_info(
    auth_data: dict = Depends(verify_api_key_and_rate_limit)
) -> RateLimitInfo:
    """Get current rate limit status for the API key"""
    
    rate_key = f"rate_limit:{auth_data['api_key_id']}"
    current_requests = redis_client.get(rate_key) or 0
    ttl = redis_client.ttl(rate_key)
    
    return RateLimitInfo(
        requests_remaining=max(0, auth_data["rate_limit"] - int(current_requests)),
        reset_time=int(time.time()) + ttl if ttl > 0 else int(time.time()) + 3600,
        plan="trial"  # TODO: Get from company subscription
    )

@app.get("/v1/usage-stats")
async def get_usage_stats(
    auth_data: dict = Depends(verify_api_key_and_rate_limit),
    db: Session = Depends(get_db)
):
    """Get usage statistics for the company"""
    
    company_id = auth_data["company_id"]
    
    # Get stats from database
    total_calls = db.query(APIUsage).filter(APIUsage.company_id == company_id).count()
    
    # Today's calls
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    calls_today = db.query(APIUsage).filter(
        APIUsage.company_id == company_id,
        APIUsage.timestamp >= today
    ).count()
    
    # This month
    month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    calls_this_month = db.query(APIUsage).filter(
        APIUsage.company_id == company_id,
        APIUsage.timestamp >= month_start
    ).count()
    
    return {
        "total_calls": total_calls,
        "calls_today": calls_today,
        "calls_this_month": calls_this_month,
        "current_plan": "trial",
        "monthly_quota": 10000,
        "quota_used": calls_this_month
    }

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom error responses"""
    
    if exc.status_code == 401:
        return JSONResponse(
            status_code=401,
            content={
                "error": "unauthorized",
                "message": exc.detail,
                "documentation": "https://docs.blockverify.com/authentication"
            }
        )
    elif exc.status_code == 429:
        return JSONResponse(
            status_code=429,
            content={
                "error": "rate_limit_exceeded",
                "message": exc.detail,
                "documentation": "https://docs.blockverify.com/rate-limits"
            }
        )
    elif exc.status_code == 402:
        return JSONResponse(
            status_code=402,
            content={
                "error": "quota_exceeded",
                "message": exc.detail,
                "upgrade_url": "https://portal.blockverify.com/billing"
            }
        )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "api_error", "message": exc.detail}
    )

if __name__ == "__main__":
    import uvicorn
    
    # Production configuration
    if os.getenv("ENVIRONMENT") == "production":
        print("🚀 Starting BlockVerify Production API...")
        print("🔒 Production mode: Enhanced security enabled")
        uvicorn.run(
            "production_api:app",
            host="0.0.0.0",
            port=8080,
            workers=4,
            access_log=True,
            log_level="info"
        )
    else:
        print("🧪 Starting BlockVerify Production API (Development Mode)")
        print("🔓 Development mode: Relaxed security for testing")
        uvicorn.run(app, host="0.0.0.0", port=8080, reload=True) 