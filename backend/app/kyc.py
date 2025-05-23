from fastapi import APIRouter, HTTPException
from datetime import datetime
from .webauthn import registration_challenge
router = APIRouter()
@router.post("/webhook")
async def kyc_webhook(payload: dict):
    if payload.get("decision")!="approved":
        raise HTTPException(400,"KYC failed")
    dob = datetime.fromisoformat(payload["dob"])
    if (datetime.utcnow()-dob).days < 18*365:
        raise HTTPException(400,"Under-age")
    return registration_challenge(payload["session_id"]).dict()
