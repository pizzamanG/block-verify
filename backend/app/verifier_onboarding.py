from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session
from pydantic import BaseModel, EmailStr
import secrets
import hashlib
from .db import get_session
from .models import Verifier

router = APIRouter()

class VerifierRegistration(BaseModel):
    business_name: str
    contact_email: EmailStr
    website_url: str
    use_case_description: str

class VerifierResponse(BaseModel):
    verifier_id: str
    api_key: str
    business_name: str
    status: str

@router.post("/register", response_model=VerifierResponse)
async def register_verifier(
    registration: VerifierRegistration,
    session: Session = Depends(get_session)
):
    """Register a new business verifier and issue API key"""
    
    # Check if business already registered
    existing = session.query(Verifier).filter(
        Verifier.contact_email == registration.contact_email
    ).first()
    
    if existing:
        raise HTTPException(400, "Business already registered with this email")
    
    # Generate secure API key
    api_key = secrets.token_urlsafe(32)
    api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    
    # Create verifier record
    verifier = Verifier(
        business_name=registration.business_name,
        contact_email=registration.contact_email,
        website_url=registration.website_url,
        use_case_description=registration.use_case_description,
        api_key=api_key_hash,  # Store hash, not plaintext
        status="active"
    )
    
    session.add(verifier)
    session.commit()
    session.refresh(verifier)
    
    return VerifierResponse(
        verifier_id=verifier.id,
        api_key=api_key,  # Return plaintext only once
        business_name=verifier.business_name,
        status=verifier.status
    )

@router.get("/integration-guide")
async def get_integration_guide():
    """Return integration documentation for verifiers"""
    return {
        "jwks_endpoint": "/issuer_jwks.json",
        "verification_endpoint": "/verify-token",
        "client_library": "/static/at.js",
        "example_integration": {
            "html": '<script src="https://your-domain.com/static/at.js"></script>',
            "api_call": {
                "url": "/verify-token",
                "method": "POST",
                "headers": {"X-API-Key": "your-api-key"},
                "body": {"token": "user-age-token"}
            }
        }
    } 