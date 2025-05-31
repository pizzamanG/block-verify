"""
BlockVerify Client API
Handles client registration, API key management, and usage tracking
"""

from fastapi import APIRouter, Depends, HTTPException, Header, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional, List
import hashlib

from .db import get_session
from .billing_simple import (
    SimpleBillingService, ClientRegister, ClientResponse, 
    APIKeyResponse, SimpleClient, SimpleAPIKey, PlanType, PLAN_LIMITS
)

router = APIRouter(prefix="/api/v1/clients", tags=["clients"])
security = HTTPBearer()

def get_api_key(authorization: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Extract API key from Bearer token"""
    return authorization.credentials

def get_api_key_from_header(x_api_key: Optional[str] = Header(None)) -> Optional[str]:
    """Get API key from X-API-Key header"""
    return x_api_key

async def validate_client_api_key(
    bearer_key: Optional[str] = Depends(get_api_key),
    header_key: Optional[str] = Depends(get_api_key_from_header),
    db: Session = Depends(get_session)
) -> SimpleAPIKey:
    """Validate API key from either Bearer token or X-API-Key header"""
    api_key = bearer_key or header_key
    
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="API key required. Use Bearer token or X-API-Key header"
        )
    
    billing_service = SimpleBillingService(db)
    api_key_obj = billing_service.validate_api_key(api_key)
    
    if not api_key_obj:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    
    # Check if client is active
    if not api_key_obj.client.is_active:
        raise HTTPException(
            status_code=403,
            detail="Client account is suspended"
        )
    
    return api_key_obj

@router.post("/register", response_model=dict)
async def register_client(
    data: ClientRegister,
    db: Session = Depends(get_session)
):
    """
    Register a new client and get an API key
    
    Returns the client info and their first API key (SAVE THIS KEY!)
    """
    try:
        billing_service = SimpleBillingService(db)
        client, api_key = billing_service.register_client(data)
        
        return {
            "message": "Registration successful",
            "client": {
                "id": str(client.id),
                "business_name": client.business_name,
                "contact_email": client.contact_email,
                "plan": client.plan_type,
                "monthly_limit": PLAN_LIMITS[client.plan_type]["monthly_verifications"]
            },
            "api_key": {
                "key": api_key,  # This is the only time you'll see the full key!
                "instructions": "Save this API key securely. You won't be able to see it again."
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/me", response_model=ClientResponse)
async def get_client_info(
    api_key: SimpleAPIKey = Depends(validate_client_api_key),
    db: Session = Depends(get_session)
):
    """Get current client information"""
    client = api_key.client
    limit = PLAN_LIMITS[client.plan_type]["monthly_verifications"]
    
    return ClientResponse(
        id=str(client.id),
        business_name=client.business_name,
        contact_email=client.contact_email,
        website_url=client.website_url,
        plan_type=client.plan_type,
        monthly_usage=client.monthly_usage,
        monthly_limit=limit,
        is_active=client.is_active,
        created_at=client.created_at
    )

@router.get("/usage", response_model=dict)
async def get_usage_stats(
    api_key: SimpleAPIKey = Depends(validate_client_api_key),
    db: Session = Depends(get_session)
):
    """Get detailed usage statistics"""
    billing_service = SimpleBillingService(db)
    stats = billing_service.get_client_stats(str(api_key.client.id))
    
    if stats is None:
        # Return empty stats if none found
        return {
            "client": {
                "id": str(api_key.client.id),
                "business_name": api_key.client.business_name,
                "plan": api_key.client.plan_type,
                "created_at": api_key.client.created_at.isoformat()
            },
            "usage": {
                "current_month": 0,
                "limit": PLAN_LIMITS[api_key.client.plan_type]["monthly_verifications"],
                "percentage": 0.0,
                "reset_date": api_key.client.created_at.replace(day=1).isoformat()
            },
            "api_keys": 1,
            "active_keys": 1
        }
    
    return stats

@router.get("/api-keys", response_model=List[APIKeyResponse])
async def list_api_keys(
    api_key: SimpleAPIKey = Depends(validate_client_api_key),
    db: Session = Depends(get_session)
):
    """List all API keys for the client"""
    from .billing_simple import SimpleAPIKey as APIKeyModel
    
    keys = db.query(APIKeyModel).filter(
        APIKeyModel.client_id == api_key.client.id
    ).all()
    
    return [
        APIKeyResponse(
            id=str(k.id),
            name=k.name,
            key_prefix=k.key_prefix,
            masked_key=k.key_prefix + "****",  # Never show full key
            rate_limit_per_minute=k.rate_limit_per_minute,
            is_active=k.is_active,
            created_at=k.created_at,
            last_used_at=k.last_used_at
        )
        for k in keys
    ]

@router.post("/api-keys", response_model=dict)
async def create_api_key(
    name: str = "New API Key",
    api_key: SimpleAPIKey = Depends(validate_client_api_key),
    db: Session = Depends(get_session)
):
    """Create a new API key"""
    billing_service = SimpleBillingService(db)
    
    # Check key limit (max 5 keys per client)
    existing_keys = db.query(SimpleAPIKey).filter(
        SimpleAPIKey.client_id == api_key.client.id,
        SimpleAPIKey.is_active == True
    ).count()
    
    if existing_keys >= 5:
        raise HTTPException(
            status_code=400,
            detail="Maximum API keys limit reached (5 keys per client)"
        )
    
    new_key, raw_key = billing_service.create_api_key(str(api_key.client.id), name)
    
    return {
        "message": "API key created successfully",
        "api_key": {
            "id": str(new_key.id),
            "name": new_key.name,
            "key": raw_key,  # Only time you'll see this!
            "instructions": "Save this API key securely. You won't be able to see it again."
        }
    }

@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    key_id: str,
    api_key: SimpleAPIKey = Depends(validate_client_api_key),
    db: Session = Depends(get_session)
):
    """Revoke an API key"""
    # Find the key
    target_key = db.query(SimpleAPIKey).filter(
        SimpleAPIKey.id == key_id,
        SimpleAPIKey.client_id == api_key.client.id
    ).first()
    
    if not target_key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    # Don't allow revoking the last active key
    active_keys = db.query(SimpleAPIKey).filter(
        SimpleAPIKey.client_id == api_key.client.id,
        SimpleAPIKey.is_active == True
    ).count()
    
    if active_keys <= 1:
        raise HTTPException(
            status_code=400,
            detail="Cannot revoke the last active API key"
        )
    
    target_key.is_active = False
    db.commit()
    
    return {"message": "API key revoked successfully"}

@router.post("/upgrade-plan")
async def upgrade_plan(
    new_plan: PlanType,
    api_key: SimpleAPIKey = Depends(validate_client_api_key),
    db: Session = Depends(get_session)
):
    """Upgrade to a higher plan"""
    client = api_key.client
    
    # Check if it's actually an upgrade
    current_plan_index = list(PlanType).index(client.plan_type)
    new_plan_index = list(PlanType).index(new_plan)
    
    if new_plan_index <= current_plan_index:
        raise HTTPException(
            status_code=400,
            detail="Can only upgrade to a higher plan"
        )
    
    # Update plan
    client.plan_type = new_plan
    
    # Update rate limits for all API keys
    for key in client.api_keys:
        key.rate_limit_per_minute = PLAN_LIMITS[new_plan]["rate_limit_per_minute"]
    
    db.commit()
    
    return {
        "message": f"Successfully upgraded to {new_plan} plan",
        "new_limits": PLAN_LIMITS[new_plan]
    }

# Public endpoints (no auth required)
@router.get("/plans", response_model=dict)
async def get_available_plans():
    """Get available pricing plans"""
    return {
        "plans": [
            {
                "name": plan,
                "monthly_verifications": limits["monthly_verifications"],
                "rate_limit_per_minute": limits["rate_limit_per_minute"],
                "price_monthly": f"${limits['price_cents'] / 100:.2f}" if limits['price_cents'] > 0 else "Free"
            }
            for plan, limits in PLAN_LIMITS.items()
        ]
    } 