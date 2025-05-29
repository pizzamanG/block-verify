from fastapi import FastAPI, Response
from datetime import datetime
from hashlib import sha256
import json
from sqlmodel import SQLModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .db import DBSession, engine
from .models import Device, Verifier

# routers
from .kyc import router as kyc_router            # real vendor webhook (placeholder)
from .kyc_stub import router as stub_router      # local‑dev 75 / 25 fake KYC
from .verifier_onboarding import router as verifier_router
from .revocation import router as revocation_router

from .webauthn import verify_attestation
from .token import mint
from .verify import router as verify_router

app = FastAPI(title="Age‑Token API")
app.include_router(verify_router, tags=["verify"])
app.include_router(verifier_router, prefix="/verifiers", tags=["verifiers"])
app.include_router(revocation_router, prefix="/revocation", tags=["revocation"])

# Serve static files (client library, dashboard, etc.)
app.mount("/static", StaticFiles(directory="frontend"), name="static")

from fastapi.responses import FileResponse

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# expose both flows so front‑end can switch at will
app.include_router(kyc_router,  prefix="/kyc",  tags=["vendor"])
app.include_router(stub_router, prefix="/fake", tags=["stub"])

# ensure schema
SQLModel.metadata.create_all(engine)

@app.on_event("startup")
async def create_demo_verifier():
    """Create a demo verifier for testing"""
    with DBSession() as session:
        existing = session.query(Verifier).filter(
            Verifier.api_key == sha256("demo_key_for_testing".encode()).hexdigest()
        ).first()
        
        if not existing:
            demo_verifier = Verifier(
                business_name="Demo Test Site",
                contact_email="demo@test.com",
                website_url="http://localhost:3000",
                use_case_description="Testing BlockVerify integration",
                api_key=sha256("demo_key_for_testing".encode()).hexdigest(),
                status="active"
            )
            session.add(demo_verifier)
            session.commit()
            print("✅ Created demo verifier for testing")

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
    from pathlib import Path
    from .settings import settings
    
    # Load issuer key from project root or settings path
    key_path = Path(settings.ISSUER_KEY_FILE)
    if not key_path.is_absolute():
        # If relative path, make it relative to project root
        key_path = Path(__file__).parent.parent.parent / key_path
    
    try:
        key = jwk.JWK.from_json(open(key_path).read())
        return {"keys": [json.loads(key.export_public())]}
    except FileNotFoundError:
        return {"error": "Issuer key not found", "path": str(key_path)}
    except Exception as e:
        return {"error": str(e)}

from .db import engine, SQLModel
SQLModel.metadata.create_all(engine)

@app.get("/dashboard.html", include_in_schema=False)
def serve_dashboard():
    return FileResponse("frontend/dashboard.html")

@app.get("/verify.html", include_in_schema=False)  
def serve_verify():
    return FileResponse("frontend/verify.html")

@app.get("/", include_in_schema=False)
def serve_landing():
    return FileResponse("backend/app/landing.html")
