from webauthn import (
    generate_registration_options,
    verify_registration_response,
)
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    UserVerificationRequirement,
)
from dataclasses import asdict
import base64


def _b64url(data: bytes) -> str:
    """Base64-url encode without padding so JSON is UTF-8-safe."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _clean(obj):
    """Recursively convert any bytes values → base64-url strings."""
    if isinstance(obj, bytes):
        return _b64url(obj)
    if isinstance(obj, list):
        return [_clean(i) for i in obj]
    if isinstance(obj, dict):
        return {k: _clean(v) for k, v in obj.items()}
    return obj


def registration_challenge(session_id: str):
    """Return pure JSON-serialisable dict for FastAPI (webauthn-py 1.x)."""
    opts = generate_registration_options(
        rp_id="age-token.io",
        rp_name="Age Token",
        user_id=session_id.encode(),
        user_name="anon",
        user_display_name="anonymous",
        authenticator_selection=AuthenticatorSelectionCriteria(
            user_verification=UserVerificationRequirement.PREFERRED,
        ),
    )
    return _clean(asdict(opts))


def verify_attestation(resp: dict):
    return verify_registration_response(
        credential=resp,
        expected_rp_id="age-token.io",
        expected_origin="http://localhost:8080",
    )

