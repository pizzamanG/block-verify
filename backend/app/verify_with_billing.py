"""
BlockVerify Token Verification with Billing
Integrates age verification with API key authentication and usage tracking
"""

from fastapi import APIRouter, Depends, HTTPException, Header, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
import hashlib

from .db import get_session
from .models import Device
from .token import verify as verify_jwt_token
from .billing_simple import SimpleBillingService, SimpleAPIKey
from .api_clients import validate_client_api_key

router = APIRouter(prefix="/api/v1", tags=["verification"])

class VerifyTokenRequest(BaseModel):
    token: str
    min_age: int = 18
    user_agent: Optional[str] = None

class VerifyTokenResponse(BaseModel):
    valid: bool
    message: str
    metadata: Optional[dict] = None

@router.post("/verify-token", response_model=VerifyTokenResponse)
async def verify_token_with_billing(
    request: VerifyTokenRequest,
    api_key: SimpleAPIKey = Depends(validate_client_api_key),
    db: Session = Depends(get_session),
    user_agent: Optional[str] = Header(None)
):
    """
    Verify an age token with API key authentication and usage tracking
    
    This endpoint:
    1. Validates your API key
    2. Checks your usage limits
    3. Verifies the age token
    4. Records usage for billing
    
    **Authentication**: Requires API key via Bearer token or X-API-Key header
    """
    
    billing_service = SimpleBillingService(db)
    
    # Check usage limits
    within_limit, usage_info = billing_service.check_usage_limit(str(api_key.client.id))
    
    if not within_limit:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Monthly usage limit exceeded",
                "usage": usage_info["usage"],
                "limit": usage_info["limit"],
                "plan": usage_info["plan"],
                "upgrade_url": "/api/v1/clients/plans"
            }
        )
    
    # Record the API call (even if verification fails)
    try:
        # Verify the JWT token
        result = verify_jwt_token(request.token)
        
        if not result["valid"]:
            # Token is invalid - still record usage
            billing_service.record_usage(
                client_id=str(api_key.client.id),
                api_key_id=str(api_key.id),
                endpoint="/verify-token",
                method="POST",
                status_code=400
            )
            
            return VerifyTokenResponse(
                valid=False,
                message="Invalid or expired token",
                metadata={"reason": result.get("error", "verification_failed")}
            )
        
        # Check if token is in our database
        token_data = result["payload"]
        device_id = token_data.get("device_id")
        
        if device_id:
            # Verify device exists and token matches
            device = db.query(Device).filter(Device.id == device_id).first()
            
            if not device:
                billing_service.record_usage(
                    client_id=str(api_key.client.id),
                    api_key_id=str(api_key.id),
                    endpoint="/verify-token",
                    method="POST",
                    status_code=404
                )
                
                return VerifyTokenResponse(
                    valid=False,
                    message="Device not found",
                    metadata={"reason": "device_not_registered"}
                )
            
            # Check token hash matches
            token_hash = hashlib.sha256(request.token.encode()).hexdigest()
            if device.token_hash != token_hash:
                billing_service.record_usage(
                    client_id=str(api_key.client.id),
                    api_key_id=str(api_key.id),
                    endpoint="/verify-token",
                    method="POST",
                    status_code=401
                )
                
                return VerifyTokenResponse(
                    valid=False,
                    message="Token mismatch",
                    metadata={"reason": "token_mismatch"}
                )
        
        # Check age requirement
        user_age = token_data.get("age", 0)
        if user_age < request.min_age:
            billing_service.record_usage(
                client_id=str(api_key.client.id),
                api_key_id=str(api_key.id),
                endpoint="/verify-token",
                method="POST",
                status_code=403
            )
            
            return VerifyTokenResponse(
                valid=False,
                message=f"User does not meet minimum age requirement ({request.min_age})",
                metadata={
                    "user_age": user_age,
                    "required_age": request.min_age,
                    "reason": "age_requirement_not_met"
                }
            )
        
        # Success! Record usage
        billing_service.record_usage(
            client_id=str(api_key.client.id),
            api_key_id=str(api_key.id),
            endpoint="/verify-token",
            method="POST",
            status_code=200
        )
        
        return VerifyTokenResponse(
            valid=True,
            message="Token verified successfully",
            metadata={
                "age_verified": True,
                "verification_timestamp": datetime.utcnow().isoformat(),
                "usage_remaining": usage_info["remaining"] - 1
            }
        )
        
    except Exception as e:
        # Record failed attempt
        billing_service.record_usage(
            client_id=str(api_key.client.id),
            api_key_id=str(api_key.id),
            endpoint="/verify-token",
            method="POST",
            status_code=500
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"Verification error: {str(e)}"
        )

@router.get("/health")
async def health_check():
    """Public health check endpoint"""
    return {
        "status": "healthy",
        "service": "BlockVerify API",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    } 