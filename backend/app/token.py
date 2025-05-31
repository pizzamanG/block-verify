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
_kid = _key.thumbprint()
def mint(device_hash: str) -> str:
    exp = datetime.utcnow() + timedelta(days=365)
    claims = {"ageOver":18,"device":device_hash,
              "iat":int(datetime.utcnow().timestamp()),
              "exp":int(exp.timestamp())}
    t = jwt.JWT(header={"alg":"EdDSA","kid":_kid},claims=claims)
    t.make_signed_token(_key)
    return t.serialize()

def verify(token_string: str) -> dict:
    """Verify a JWT token and return its claims"""
    try:
        # Parse and verify the token
        t = jwt.JWT(key=_key, jwt=token_string)
        claims = json.loads(t.claims)
        
        # Check expiration
        if claims.get("exp", 0) < datetime.utcnow().timestamp():
            return {"valid": False, "error": "Token expired"}
        
        return {
            "valid": True,
            "payload": {
                "age": claims.get("ageOver", 0),
                "device_id": claims.get("device"),
                "issued_at": claims.get("iat"),
                "expires_at": claims.get("exp")
            }
        }
    except Exception as e:
        return {"valid": False, "error": str(e)}
