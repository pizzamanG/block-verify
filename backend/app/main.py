from fastapi import FastAPI, Response
from datetime import datetime
from hashlib import sha256
import json
from sqlmodel import SQLModel
from .db import DBSession, engine
from .models import Device
from .kyc import router as kyc_router
from .webauthn import verify_attestation
from .token import mint
app = FastAPI(title="Age-Token API")
app.include_router(kyc_router, prefix="/kyc", tags=["kyc"])
SQLModel.metadata.create_all(engine)
@app.post("/webauthn/register")
async def webauthn_register(resp: dict):
    res = verify_attestation(resp)
    dev_hash = sha256(res.credential_public_key).hexdigest()
    tok = mint(dev_hash)
    with DBSession() as s:
        s.add(Device(id=dev_hash,
                     token_hash=sha256(tok.encode()).hexdigest(),
                     exp=datetime.utcnow()))
        s.commit()
    r = Response(content=json.dumps({"token": tok}),
                 media_type="application/json")
    r.set_cookie("AgeToken", tok,
                 httponly=True, secure=True, samesite="Lax",
                 max_age=60*60*24*365)
    return r
@app.get("/issuer_jwks.json")
async def jwks():
    from jwcrypto import jwk; key = jwk.JWK.from_json(open('issuer_ed25519.jwk').read())
    return {"keys":[json.loads(key.export_public())]}
