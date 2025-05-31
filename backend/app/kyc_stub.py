from fastapi import APIRouter, UploadFile, HTTPException
from random import random
from uuid import uuid4
from .webauthn import registration_challenge

router = APIRouter()

@router.post("/verify", summary="Fake KYC – Always pass for demo")
async def fake_kyc(file: UploadFile):
    # swallow the upload – we **never** persist user images in dev mode
    _ = await file.read()
    
    # REMOVED: Random failure for better demo experience
    # if random() > 0.75:
    #     raise HTTPException(400, "KYC failed – under 18 (stub)")
    
    session_id = str(uuid4())
    return registration_challenge(session_id)