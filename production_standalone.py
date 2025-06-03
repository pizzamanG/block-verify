#!/usr/bin/env python3
"""
BlockVerify Standalone Production API
Simplified version for Railway deployment
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any
import json
import os
import jwt
import base64
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "your-super-secret-jwt-key")
JWT_ALGORITHM = "HS256"

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

# FastAPI app
app = FastAPI(
    title="BlockVerify Production API",
    description="Enterprise Age Verification Service",
    version="2.0.0",
    docs_url="/docs" if os.getenv("ENVIRONMENT") != "production" else None,
    redoc_url="/redoc" if os.getenv("ENVIRONMENT") != "production" else None
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if os.getenv("ENVIRONMENT") != "production" else [
        "https://*.blockverify.com",
        "https://api.blockverify.com"
    ],
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["Authorization", "Content-Type"],
)

def verify_jwt_token(token: str) -> Optional[Dict]:
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        return None

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
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "blockverify-production-api",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0"
    }

@app.post("/v1/verify-token", response_model=TokenVerifyResponse)
async def verify_age_token(
    request: Request,
    verify_request: TokenVerifyRequest
):
    """
    Verify an age verification token
    Simplified version without API key authentication for testing
    """
    
    token = verify_request.token
    min_age = verify_request.min_age or 18
    
    logger.info(f"🔍 Token verification request for min_age: {min_age}")
    
    # Try to verify as JWT first
    try:
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
            
            logger.info(f"✅ JWT token verified successfully")
            return response
        else:
            # Valid JWT but age requirement not met
            response = TokenVerifyResponse(
                valid=False,
                verified_by="BlockVerify-JWT",
                metadata={"reason": "age_requirement_not_met"}
            )
            return response
            
    except Exception as jwt_error:
        logger.warning(f"JWT verification failed: {jwt_error}")
        
        # Fallback to legacy base64 format
        try:
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
            
            logger.info(f"✅ Legacy token processed")
            return response
            
        except Exception as legacy_error:
            logger.error(f"Legacy token verification failed: {legacy_error}")
            
            # Invalid token format
            response = TokenVerifyResponse(
                valid=False,
                verified_by="BlockVerify",
                metadata={"reason": "invalid_token_format"}
            )
            return response

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom error responses"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "api_error", "message": exc.detail}
    )

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    
    print("🚀 Starting BlockVerify Standalone Production API...")
    print(f"📍 Port: {port}")
    print(f"🌍 Environment: {os.getenv('ENVIRONMENT', 'development')}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    ) 