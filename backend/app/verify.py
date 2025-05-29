from fastapi import APIRouter, Header, HTTPException, Depends
from jwcrypto import jwk, jwt
from hashlib import sha256
from sqlmodel import Session
from .db import get_session
from .models import Device, Verifier
from .chain import bulletin, current_thumbprint
import json, time
from datetime import datetime
from pathlib import Path
from .settings import settings

router = APIRouter()

def get_public_key():
    # Load issuer key from project root or settings path
    key_path = Path(settings.ISSUER_KEY_FILE)
    if not key_path.is_absolute():
        # If relative path, make it relative to project root
        key_path = Path(__file__).parent.parent.parent / key_path
    
    return jwk.JWK.from_json(open(key_path).read())

def verify_thumbprint_integrity():
    """Verify that our current public key matches the on-chain thumbprint"""
    try:
        on_chain_thumbprint = bulletin.functions.thumbprint().call()
        local_thumbprint = current_thumbprint()
        return on_chain_thumbprint == local_thumbprint
    except Exception:
        return False

@router.post("/verify-token", summary="Validate JWT for age + device, API-key protected")
async def verify_token(
    token: str, 
    x_api_key: str = Header(...),
    session: Session = Depends(get_session)
):
    # Find and validate verifier
    verifier = session.query(Verifier).filter(
        Verifier.api_key == sha256(x_api_key.encode()).hexdigest()
    ).first()
    
    if not verifier or verifier.status != "active":
        raise HTTPException(403, "Invalid or inactive API key")

    # Verify thumbprint integrity against blockchain
    if not verify_thumbprint_integrity():
        raise HTTPException(500, "Key integrity check failed - contact issuer")

    # Validate JWT
    key = get_public_key()
    try:
        j = jwt.JWT(key=key, jwt=token)
        claims = json.loads(j.claims)
    except Exception:
        raise HTTPException(400, "Invalid token")

    if time.time() > claims.get("exp", 0):
        raise HTTPException(400, "Expired token")

    # Update verifier usage stats
    verifier.last_used = datetime.utcnow()
    verifier.request_count += 1
    session.add(verifier)
    session.commit()

    return {
        "valid": True,
        "device": claims["device"],
        "ageOver": claims["ageOver"],
        "iat": claims["iat"],
        "exp": claims["exp"],
        "verified_by": "BlockVerify"
    }