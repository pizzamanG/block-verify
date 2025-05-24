import os

# Redefine files to generate after kernel reset
backend_dir = "backend/app"
files_to_generate = {
    f"{backend_dir}/verifier.py": '''
from sqlmodel import SQLModel, Field
from datetime import datetime

class Verifier(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    api_key: str  # securely generated in production
    created: datetime = Field(default_factory=datetime.utcnow)
''',

    f"{backend_dir}/verify.py": '''
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
''',

    f"{backend_dir}/init_verifiers.py": '''
from .db import DBSession, engine, SQLModel
from .verifier import Verifier
from uuid import uuid4

SQLModel.metadata.create_all(engine)

with DBSession() as s:
    if not s.query(Verifier).first():
        key = uuid4().hex
        verifier = Verifier(name="DefaultDev", api_key=key)
        s.add(verifier)
        s.commit()
        print("API key:", key)
    else:
        print("Verifier already initialized.")
''',

    f"{backend_dir}/landing.html": '''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Age Token Service</title>
</head>
<body>
  <h1>AgeToken: Stateless Age Verification</h1>
  <p>Drop-in 18+ verification for adult sites. Fast, private, reusable.</p>
  <pre>
    &lt;script src="https://yourdomain.com/at.js"&gt;&lt;/script&gt;
  </pre>
  <p>Need an API key? Contact us.</p>
</body>
</html>
'''
}

# Write all files
for path, content in files_to_generate.items():
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write(content.strip())

"Verifier DB model, token verification API, API key bootstrap script, and landing page scaffold created."
