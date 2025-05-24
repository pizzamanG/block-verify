from fastapi import FastAPI, Response
from datetime import datetime
from hashlib import sha256
import json
from sqlmodel import SQLModel
from fastapi.middleware.cors import CORSMiddleware
from .db import DBSession, engine
from .models import Device

# routers
from .kyc import router as kyc_router            # real vendor webhook (placeholder)
from .kyc_stub import router as stub_router      # local‑dev 75 / 25 fake KYC

from .webauthn import verify_attestation
from .token import mint
from .verify import router as verify_router

app = FastAPI(title="Age‑Token API")
app.include_router(verify_router, tags=["verify"])
from fastapi.responses import FileResponse

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# expose both flows so front‑end can switch at will
app.include_router(kyc_router,  prefix="/kyc",  tags=["vendor"])
app.include_router(stub_router, prefix="/fake", tags=["stub"])

# ensure schema
SQLModel.metadata.create_all(engine)


@app.post("/webauthn/register")
async def webauthn_register(resp: dict):
    """Receive the WebAuthn attestation, hash the pub‑key, mint a signed age token."""
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
    """Public JWKS endpoint for verifiers—pulled by at.js."""
    from jwcrypto import jwk
    key = jwk.JWK.from_json(open('issuer_ed25519.jwk').read())
    return {"keys": [json.loads(key.export_public())]}

from .db import engine, SQLModel
SQLModel.metadata.create_all(engine)


@app.get("/", include_in_schema=False)
def serve_landing():
    return FileResponse("app/landing.html")
