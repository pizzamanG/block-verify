#!/usr/bin/env bash
set -e

# -------- utility ----------
mk () { mkdir -p "$(dirname "$1")"; }

# -------- backend ----------
mk backend/app

cat > backend/requirements.txt <<'REQ'
fastapi
uvicorn[standard]
sqlmodel
jwcrypto
py_webauthn
python-jose[cryptography]
web3
python-dotenv
REQ

cat > backend/app/__init__.py <<'PY'
# package init
PY

cat > backend/app/settings.py <<'PY'
from pydantic import BaseSettings, Field
class Settings(BaseSettings):
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    ISSUER_KEY_FILE: str = "issuer_ed25519.jwk"
    CHAIN_RPC_URL: str = Field(..., env="CHAIN_RPC_URL")
    BULLETIN_ADDRESS: str = Field(..., env="BULLETIN_ADDRESS")
settings = Settings()
PY

cat > backend/app/db.py <<'PY'
from sqlmodel import SQLModel, create_engine, Session
from .settings import settings
engine = create_engine(settings.DATABASE_URL, echo=False, pool_pre_ping=True)
class DBSession:
    def __enter__(self): self.session = Session(engine); return self.session
    def __exit__(self, *_): self.session.close()
PY

cat > backend/app/models.py <<'PY'
from sqlmodel import SQLModel, Field
from datetime import datetime
class Device(SQLModel, table=True):
    id: str = Field(primary_key=True)   # SHA-256(pubkey)
    token_hash: str
    exp: datetime
PY

cat > backend/app/token.py <<'PY'
from jwcrypto import jwk, jwt
from datetime import datetime, timedelta
from hashlib import sha256
import os, json
from .settings import settings
if os.path.exists(settings.ISSUER_KEY_FILE):
    _key = jwk.JWK.from_json(open(settings.ISSUER_KEY_FILE).read())
else:
    _key = jwk.JWK.generate(kty='OKP', crv='Ed25519')
    open(settings.ISSUER_KEY_FILE,'w').write(_key.export())
_kid = _key.thumbprint().decode()
def mint(device_hash: str) -> str:
    exp = datetime.utcnow() + timedelta(days=365)
    claims = {"ageOver":18,"device":device_hash,
              "iat":int(datetime.utcnow().timestamp()),
              "exp":int(exp.timestamp())}
    t = jwt.JWT(header={"alg":"EdDSA","kid":_kid},claims=claims)
    t.make_signed_token(_key)
    return t.serialize()
PY

cat > backend/app/webauthn.py <<'PY'
from py_webauthn import generate_registration_options, verify_registration_response
def registration_challenge(session_id:str):
    return generate_registration_options(rp_id="age-token.io",
                                         user_id=session_id.encode(),
                                         user_name="anon")
def verify_attestation(resp:dict):
    return verify_registration_response(resp, expected_rp_id="age-token.io")
PY

cat > backend/app/kyc.py <<'PY'
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
PY

cat > backend/app/main.py <<'PY'
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
PY

cat > backend/Dockerfile <<'DOCKER'
FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/app app
EXPOSE 8000
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000"]
DOCKER

# -------- infra ----------
mk infra
cat > infra/docker-compose.yml <<'YAML'
version: "3.9"
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: dev
      POSTGRES_PASSWORD: dev
      POSTGRES_DB: age_token
    volumes: [ "pgdata:/var/lib/postgresql/data" ]
  api:
    build: ../backend
    environment:
      DATABASE_URL: postgresql+psycopg2://dev:dev@db/age_token
    ports: [ "8000:8000" ]
    depends_on: [ db ]
volumes: { pgdata: {} }
YAML

# -------- frontend ----------
mk frontend
cat > frontend/at.js <<'JS'
(async ()=>{
  const token=localStorage.AgeToken||(document.cookie.match(/AgeToken=([^;]+)/)||[,''])[1];
  if(!token){location.href='/verify.html';return;}
  const [,p]=token.split('.');const d=JSON.parse(atob(p));
  if(Date.now()/1000>d.exp)return location.href='/verify.html';
  const chall=crypto.getRandomValues(new Uint8Array(32));
  try{
    await navigator.credentials.get({publicKey:{challenge:chall,timeout:15000,
      allowCredentials:[{type:'public-key',id:new TextEncoder().encode(d.device)}]}});
    document.body.style.display='block';
  }catch{location.href='/verify.html';}
})();
JS

# -------- misc ----------
echo "DATABASE_URL=postgresql+psycopg2://dev:dev@localhost/age_token" > .env.example

echo "Scaffold ready.
1) create .env from .env.example and set vars
2) docker compose -f infra/docker-compose.yml up --build
3) open http://localhost:8000/docs"
