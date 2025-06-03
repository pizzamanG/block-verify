from fastapi import FastAPI, Response
from datetime import datetime
from hashlib import sha256
import json
from sqlmodel import SQLModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from pathlib import Path

# Try to import database components with error handling
try:
    from .db import DBSession, engine
    from .models import Device, Verifier
    DB_AVAILABLE = True
except Exception as e:
    print(f"⚠️  Database not available: {e}")
    DB_AVAILABLE = False

# routers
from .kyc import router as kyc_router            # real vendor webhook (placeholder)
from .kyc_stub import router as stub_router      # local‑dev 75 / 25 fake KYC
from .verifier_onboarding import router as verifier_router
from .revocation import router as revocation_router
from .admin import router as admin_router
from .api_clients import router as clients_router
from .verify_with_billing import router as verify_billing_router

# Import billing router with error handling
try:
    from .api_billing import router as billing_router
    BILLING_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Stripe billing not available: {e}")
    billing_router = None
    BILLING_AVAILABLE = False

from .webauthn import verify_attestation
from .token import mint
from .verify import router as verify_router

app = FastAPI(
    title="BlockVerify API", 
    version="1.0.0",
    description="Privacy-preserving age verification platform"
)

# Simple health check endpoint for Railway (no database dependency)
@app.get("/health")
async def health_check():
    """Health check endpoint for Railway deployment"""
    health_status = {
        "status": "healthy",
        "service": "blockverify-api",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "components": {}
    }
    
    # Test database if available
    if DB_AVAILABLE:
        try:
            with DBSession() as session:
                session.execute("SELECT 1")
            health_status["components"]["database"] = "healthy"
        except Exception as e:
            health_status["components"]["database"] = f"unhealthy: {str(e)}"
            health_status["status"] = "degraded"
    else:
        health_status["components"]["database"] = "not_configured"
    
    return health_status

# Include routers
app.include_router(verify_router, tags=["verify"])  # Legacy verification endpoints
app.include_router(verify_billing_router, tags=["verification"])  # New billing-integrated endpoints
app.include_router(clients_router, tags=["clients"])  # Client management
app.include_router(verifier_router, prefix="/verifiers", tags=["verifiers"])
app.include_router(revocation_router, prefix="/revocation", tags=["revocation"])
app.include_router(admin_router, tags=["admin"])

# Only include Stripe billing routes if available
if BILLING_AVAILABLE and billing_router:
    app.include_router(billing_router, prefix="/billing", tags=["billing"])
    print("✅ Stripe billing system enabled")
else:
    print("📦 Running with simple billing (no Stripe required)")

# Serve static files (only if frontend directory exists)
frontend_dir = Path("frontend")
if frontend_dir.exists() and frontend_dir.is_dir():
    try:
        app.mount("/static", StaticFiles(directory="frontend"), name="static")
        print("✅ Static files mounted from frontend/")
    except Exception as e:
        print(f"⚠️  Could not mount static files: {e}")
else:
    print("⚠️  Frontend directory not found - static files disabled")

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

# Initialize database tables if available
if DB_AVAILABLE:
    try:
        SQLModel.metadata.create_all(engine)
        print("✅ Database tables created")
        
        # Also create simple billing tables
        try:
            from .billing_simple import Base as BillingBase, engine as billing_engine, create_tables
            create_tables()
            print("✅ Billing tables created")
        except Exception as e:
            print(f"⚠️  Billing tables creation failed: {e}")
    except Exception as e:
        print(f"⚠️  Database table creation failed: {e}")

@app.on_event("startup")
async def startup_event():
    """Initialize the application"""
    print("🚀 BlockVerify API starting up...")
    
    if not DB_AVAILABLE:
        print("⚠️  Database not available - skipping demo data creation")
        print("✅ BlockVerify API ready! (Limited functionality)")
        return
    
    try:
        # Create demo verifier for testing
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
    except Exception as e:
        print(f"⚠️  Demo verifier creation failed: {e}")
    
    try:
        # Create demo client for simple billing
        from .billing_simple import SessionLocal, SimpleClient, SimpleBillingService
        with SessionLocal() as session:
            existing = session.query(SimpleClient).filter(
                SimpleClient.contact_email == "demo@blockverify.com"
            ).first()
            
            if not existing:
                from .billing_simple import ClientRegister
                billing_service = SimpleBillingService(session)
                demo_data = ClientRegister(
                    business_name="BlockVerify Demo",
                    contact_email="demo@blockverify.com",
                    website_url="https://demo.blockverify.com"
                )
                try:
                    client, api_key = billing_service.register_client(demo_data)
                    print(f"✅ Created demo client with API key: {api_key}")
                    print("   Save this key for testing!")
                except Exception as e:
                    print(f"Demo client creation skipped: {e}")
    except Exception as e:
        print(f"⚠️  Demo billing client creation failed: {e}")
    
    print("✅ BlockVerify API ready!")

@app.post("/webauthn/register")
async def webauthn_register(resp: dict):
    """Receive the WebAuthn attestation, hash the pub‑key, mint a signed age token."""
    if not DB_AVAILABLE:
        return {"error": "Database not available"}
        
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
    try:
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
    except Exception as e:
        return {"error": f"JWKS endpoint failed: {str(e)}"}

@app.get("/dashboard.html", include_in_schema=False)
def serve_dashboard():
    """Serve dashboard if available"""
    dashboard_path = Path("frontend/dashboard.html")
    if dashboard_path.exists():
        return FileResponse("frontend/dashboard.html")
    else:
        return {"error": "Dashboard not available", "message": "Frontend files not found"}

@app.get("/verify.html", include_in_schema=False)  
def serve_verify():
    """Serve verify page if available"""
    verify_path = Path("frontend/verify.html")
    if verify_path.exists():
        return FileResponse("frontend/verify.html")
    else:
        return {"error": "Verify page not available", "message": "Frontend files not found"}

@app.get("/", include_in_schema=False)
def serve_landing():
    """Serve landing page"""
    landing_path = Path("backend/app/landing.html")
    if landing_path.exists():
        return FileResponse("backend/app/landing.html")
    else:
        return {
            "service": "BlockVerify API",
            "version": "1.0.0",
            "status": "running",
            "message": "BlockVerify Age Verification API",
            "endpoints": {
                "health": "/health",
                "docs": "/docs",
                "jwks": "/issuer_jwks.json"
            }
        }
