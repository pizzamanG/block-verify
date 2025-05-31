"""
FastAPI endpoints for BlockVerify billing and client management
"""

from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from .billing import (
    BillingService, Client, APIKey, UsageRecord, Invoice,
    ClientCreate, ClientResponse, APIKeyCreate, APIKeyResponse, UsageStats,
    PlanType, UsageType, PLAN_CONFIGS
)
from .database import get_db

router = APIRouter(prefix="/billing", tags=["billing"])
security = HTTPBearer()

def get_billing_service(db: Session = Depends(get_db)) -> BillingService:
    return BillingService(db)

def get_client_from_api_key(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    billing_service: BillingService = Depends(get_billing_service)
) -> tuple[Client, APIKey]:
    """Extract client and API key from Authorization header"""
    api_key = credentials.credentials
    
    api_key_obj = billing_service.validate_api_key(api_key)
    if not api_key_obj:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    client = billing_service.db.query(Client).filter(Client.id == api_key_obj.client_id).first()
    if not client or not client.is_active:
        raise HTTPException(status_code=401, detail="Client not found or inactive")
    
    return client, api_key_obj

# Public endpoints (no auth required)
@router.post("/clients/register", response_model=dict)
async def register_client(
    client_data: ClientCreate,
    billing_service: BillingService = Depends(get_billing_service)
):
    """Register a new client and get API key"""
    try:
        client = billing_service.create_client(client_data)
        
        # Get the default API key
        api_key_obj = billing_service.db.query(APIKey).filter(
            APIKey.client_id == client.id
        ).first()
        
        # For security, regenerate the key and return it once
        new_api_key, full_key = billing_service.create_api_key(
            str(client.id), 
            APIKeyCreate(name="Initial API Key")
        )
        
        # Delete the old default key
        billing_service.db.delete(api_key_obj)
        billing_service.db.commit()
        
        return {
            "message": "Client registered successfully",
            "client_id": str(client.id),
            "api_key": full_key,  # Only shown once!
            "plan": client.plan_type,
            "monthly_limit": client.monthly_limit,
            "next_steps": [
                "Save your API key securely - it won't be shown again",
                "Integrate the BlockVerify SDK into your website",
                "Test with our demo at https://demo.blockverify.com"
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/plans")
async def get_plans():
    """Get available pricing plans"""
    plans = {}
    for plan_type, config in PLAN_CONFIGS.items():
        price_per_month = 0
        if "stripe_price_id" in config:
            if plan_type == PlanType.STARTER:
                price_per_month = 29
            elif plan_type == PlanType.PROFESSIONAL:
                price_per_month = 99
            elif plan_type == PlanType.ENTERPRISE:
                price_per_month = 299
        
        plans[plan_type.value] = {
            "name": plan_type.value.title(),
            "monthly_limit": config["monthly_limit"],
            "cost_per_verification_cents": config["cost_per_verification_cents"],
            "rate_limit_per_minute": config["rate_limit_per_minute"],
            "features": config["features"],
            "price_per_month_usd": price_per_month,
            "recommended": plan_type == PlanType.STARTER
        }
    
    return {"plans": plans}

# Protected endpoints (require API key)
@router.get("/me", response_model=ClientResponse)
async def get_my_info(
    client_and_key: tuple[Client, APIKey] = Depends(get_client_from_api_key)
):
    """Get current client information"""
    client, _ = client_and_key
    
    return ClientResponse(
        id=str(client.id),
        business_name=client.business_name,
        contact_email=client.contact_email,
        website_url=client.website_url,
        plan_type=client.plan_type,
        monthly_limit=client.monthly_limit,
        current_usage=client.current_usage,
        is_active=client.is_active,
        created_at=client.created_at
    )

@router.get("/usage", response_model=UsageStats)
async def get_usage_stats(
    client_and_key: tuple[Client, APIKey] = Depends(get_client_from_api_key),
    billing_service: BillingService = Depends(get_billing_service)
):
    """Get usage statistics for current client"""
    client, _ = client_and_key
    return billing_service.get_usage_stats(str(client.id))

@router.get("/api-keys", response_model=List[APIKeyResponse])
async def list_api_keys(
    client_and_key: tuple[Client, APIKey] = Depends(get_client_from_api_key),
    billing_service: BillingService = Depends(get_billing_service)
):
    """List all API keys for current client"""
    client, _ = client_and_key
    
    api_keys = billing_service.db.query(APIKey).filter(
        APIKey.client_id == client.id
    ).all()
    
    return [
        APIKeyResponse(
            id=str(key.id),
            name=key.name,
            key_prefix=key.key_prefix + "..." + key.key_hash[-4:],  # Show prefix + last 4 chars
            permissions=key.permissions.split(",") if key.permissions else [],
            rate_limit_per_minute=key.rate_limit_per_minute,
            is_active=key.is_active,
            created_at=key.created_at,
            last_used_at=key.last_used_at
        )
        for key in api_keys
    ]

@router.post("/api-keys", response_model=dict)
async def create_api_key(
    key_data: APIKeyCreate,
    client_and_key: tuple[Client, APIKey] = Depends(get_client_from_api_key),
    billing_service: BillingService = Depends(get_billing_service)
):
    """Create a new API key"""
    client, _ = client_and_key
    
    api_key_obj, full_key = billing_service.create_api_key(str(client.id), key_data)
    
    return {
        "message": "API key created successfully",
        "api_key": full_key,  # Only shown once!
        "key_id": str(api_key_obj.id),
        "name": api_key_obj.name,
        "warning": "Save this key securely - it won't be shown again"
    }

@router.delete("/api-keys/{key_id}")
async def delete_api_key(
    key_id: str,
    client_and_key: tuple[Client, APIKey] = Depends(get_client_from_api_key),
    billing_service: BillingService = Depends(get_billing_service)
):
    """Delete an API key"""
    client, current_key = client_and_key
    
    # Prevent deleting the current key
    if str(current_key.id) == key_id:
        raise HTTPException(status_code=400, detail="Cannot delete the currently used API key")
    
    api_key = billing_service.db.query(APIKey).filter(
        APIKey.id == key_id,
        APIKey.client_id == client.id
    ).first()
    
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    billing_service.db.delete(api_key)
    billing_service.db.commit()
    
    return {"message": "API key deleted successfully"}

@router.post("/upgrade")
async def upgrade_plan(
    new_plan: PlanType,
    client_and_key: tuple[Client, APIKey] = Depends(get_client_from_api_key),
    billing_service: BillingService = Depends(get_billing_service)
):
    """Upgrade client plan"""
    client, _ = client_and_key
    
    if client.plan_type == new_plan:
        raise HTTPException(status_code=400, detail="Already on this plan")
    
    updated_client = billing_service.upgrade_plan(str(client.id), new_plan)
    
    return {
        "message": f"Successfully upgraded to {new_plan.value} plan",
        "new_plan": updated_client.plan_type,
        "new_monthly_limit": updated_client.monthly_limit,
        "billing_info": "You will be billed monthly starting next billing cycle"
    }

@router.get("/invoices")
async def list_invoices(
    client_and_key: tuple[Client, APIKey] = Depends(get_client_from_api_key),
    billing_service: BillingService = Depends(get_billing_service),
    limit: int = 10
):
    """List client invoices"""
    client, _ = client_and_key
    
    invoices = billing_service.db.query(Invoice).filter(
        Invoice.client_id == client.id
    ).order_by(Invoice.created_at.desc()).limit(limit).all()
    
    return {
        "invoices": [
            {
                "id": str(invoice.id),
                "invoice_number": invoice.invoice_number,
                "period_start": invoice.period_start.isoformat(),
                "period_end": invoice.period_end.isoformat(),
                "total_usd": invoice.total_cents / 100,
                "status": invoice.status,
                "created_at": invoice.created_at.isoformat(),
                "stripe_invoice_url": f"https://dashboard.stripe.com/invoices/{invoice.stripe_invoice_id}" if invoice.stripe_invoice_id else None
            }
            for invoice in invoices
        ]
    }

@router.get("/usage/history")
async def get_usage_history(
    client_and_key: tuple[Client, APIKey] = Depends(get_client_from_api_key),
    billing_service: BillingService = Depends(get_billing_service),
    days: int = 30,
    limit: int = 100
):
    """Get detailed usage history"""
    client, _ = client_and_key
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    usage_records = billing_service.db.query(UsageRecord).filter(
        UsageRecord.client_id == client.id,
        UsageRecord.created_at >= start_date
    ).order_by(UsageRecord.created_at.desc()).limit(limit).all()
    
    return {
        "usage_records": [
            {
                "id": str(record.id),
                "usage_type": record.usage_type,
                "endpoint": record.endpoint,
                "cost_usd": record.cost_cents / 100 if record.cost_cents else 0,
                "created_at": record.created_at.isoformat()
            }
            for record in usage_records
        ],
        "summary": {
            "total_records": len(usage_records),
            "date_range": f"{start_date.date()} to {datetime.utcnow().date()}",
            "total_cost_usd": sum(r.cost_cents for r in usage_records) / 100
        }
    }

# Middleware function to track usage
async def track_api_usage(
    request: Request,
    endpoint: str,
    client: Client,
    api_key: APIKey,
    billing_service: BillingService,
    usage_type: UsageType = UsageType.API_CALL
):
    """Helper function to record API usage"""
    try:
        billing_service.record_usage(
            client_id=str(client.id),
            api_key_id=str(api_key.id),
            usage_type=usage_type,
            endpoint=endpoint,
            method=request.method,
            user_agent=request.headers.get("user-agent"),
            ip_address=request.client.host if request.client else None
        )
    except Exception as e:
        # Don't fail the request if usage tracking fails
        print(f"Failed to track usage: {e}")

# Rate limiting middleware
def check_rate_limit(
    client: Client,
    api_key: APIKey,
    billing_service: BillingService
):
    """Check if client is within rate limits"""
    if not billing_service.check_rate_limit(api_key):
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Rate limit exceeded",
                "limit": api_key.rate_limit_per_minute,
                "window": "per minute",
                "retry_after": 60
            }
        )

# Usage limit middleware
def check_usage_limit(client: Client):
    """Check if client is within usage limits"""
    if client.current_usage >= client.monthly_limit and client.plan_type == PlanType.FREE:
        raise HTTPException(
            status_code=402,  # Payment Required
            detail={
                "error": "Monthly usage limit exceeded",
                "current_usage": client.current_usage,
                "monthly_limit": client.monthly_limit,
                "upgrade_url": "/billing/upgrade",
                "message": "Upgrade your plan to continue using BlockVerify"
            }
        )

# Helper endpoint for testing
@router.get("/test")
async def test_endpoint(
    client_and_key: tuple[Client, APIKey] = Depends(get_client_from_api_key)
):
    """Test endpoint to verify authentication"""
    client, api_key = client_and_key
    
    return {
        "message": "Authentication successful",
        "client": client.business_name,
        "plan": client.plan_type,
        "usage": f"{client.current_usage}/{client.monthly_limit}"
    } 