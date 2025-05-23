from py_webauthn import generate_registration_options, verify_registration_response
def registration_challenge(session_id:str):
    return generate_registration_options(rp_id="age-token.io",
                                         user_id=session_id.encode(),
                                         user_name="anon")
def verify_attestation(resp:dict):
    return verify_registration_response(resp, expected_rp_id="age-token.io")
