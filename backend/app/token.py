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
