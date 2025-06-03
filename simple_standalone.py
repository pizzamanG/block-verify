#!/usr/bin/env python3
"""
Simple BlockVerify API - No Database Required
Works immediately on Railway
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any
import jwt
import json
import base64
import os
import logging

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "your-super-secret-jwt-key")
JWT_ALGORITHM = "HS256"

app = FastAPI(
    title="BlockVerify Simple API",
    description="Age Verification Token Service",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class TokenVerifyRequest(BaseModel):
    token: str
    min_age: Optional[int] = 18

class TokenVerifyResponse(BaseModel):
    valid: bool
    age_over: Optional[int] = None
    verified_by: str
    expires_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

def verify_jwt_token(token: str) -> Optional[dict]:
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

@app.get("/")
async def root():
    """API information"""
    return {
        "service": "BlockVerify Simple API", 
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "verify_token": "/verify-token",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "service": "blockverify-simple-api",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/verify-token", response_model=TokenVerifyResponse)
async def verify_age_token(request: TokenVerifyRequest):
    """Verify an age verification token (no auth required for testing)"""
    
    token = request.token
    min_age = request.min_age or 18
    
    logger.info(f"🔍 Token verification request for min_age: {min_age}")
    
    # Try JWT format first
    try:
        payload = verify_jwt_token(token)
        
        if payload and payload.get("age_over", 0) >= min_age:
            response = TokenVerifyResponse(
                valid=True,
                age_over=payload.get("age_over"),
                verified_by="BlockVerify-JWT",
                expires_at=datetime.fromtimestamp(payload.get("exp", 0)),
                metadata={
                    "issuer": payload.get("iss"),
                    "jti": payload.get("jti")
                }
            )
            logger.info("✅ JWT token verified successfully")
            return response
        else:
            return TokenVerifyResponse(
                valid=False,
                verified_by="BlockVerify-JWT",
                metadata={"reason": "age_requirement_not_met"}
            )
            
    except Exception as jwt_error:
        logger.warning(f"JWT verification failed: {jwt_error}")
        
        # Try legacy base64 format
        try:
            decoded = json.loads(base64.b64decode(token))
            
            if decoded.get("ageOver", 0) >= min_age:
                # Check expiration
                exp = decoded.get("exp", 0)
                if exp and datetime.fromtimestamp(exp) < datetime.utcnow():
                    return TokenVerifyResponse(
                        valid=False,
                        verified_by="BlockVerify-Legacy",
                        metadata={"reason": "token_expired"}
                    )
                else:
                    return TokenVerifyResponse(
                        valid=True,
                        age_over=decoded.get("ageOver"),
                        verified_by="BlockVerify-Legacy",
                        expires_at=datetime.fromtimestamp(exp) if exp else None
                    )
            else:
                return TokenVerifyResponse(
                    valid=False,
                    verified_by="BlockVerify-Legacy",
                    metadata={"reason": "age_requirement_not_met"}
                )
                
        except Exception as legacy_error:
            logger.error(f"Legacy token verification failed: {legacy_error}")
            return TokenVerifyResponse(
                valid=False,
                verified_by="BlockVerify",
                metadata={"reason": "invalid_token_format"}
            )

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    
    print("🚀 Starting BlockVerify Simple API...")
    print(f"🌐 Will run on port {port}")
    
    uvicorn.run(app, host="0.0.0.0", port=port) 