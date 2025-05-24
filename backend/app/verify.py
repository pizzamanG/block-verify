from fastapi import APIRouter, Header, HTTPException
from jwcrypto import jwk, jwt
from hashlib import sha256
from .db import DBSession
from .models import Device
from .verifier import Verifier
import json, time

router = APIRouter()

def get_public_key():
    return jwk.JWK.from_json(open("issuer_ed25519.jwk").read())

@router.post("/verify-token", summary="Validate JWT for age + device, API-key protected")
async def verify_token(token: str, x_api_key: str = Header(...)):
    with DBSession() as s:
        verifier = s.query(Verifier).filter(Verifier.api_key == x_api_key).first()
        if not verifier:
            raise HTTPException(403, "Invalid API key")

    key = get_public_key()
    try:
        j = jwt.JWT(key=key, jwt=token)
        claims = json.loads(j.claims)
    except Exception:
        raise HTTPException(400, "Invalid token")

    if time.time() > claims.get("exp", 0):
        raise HTTPException(400, "Expired token")

    return {
        "valid": True,
        "device": claims["device"],
        "ageOver": claims["ageOver"],
        "iat": claims["iat"],
        "exp": claims["exp"]
    }