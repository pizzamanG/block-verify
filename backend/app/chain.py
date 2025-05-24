import os, json, base64
from web3 import Web3
from eth_account import Account
from hashlib import sha256
from jwcrypto import jwk

w3  = Web3(Web3.HTTPProvider(os.environ["CHAIN_RPC_URL"]))
acct = Account.from_key(os.environ["PRIVATE_KEY"])

with open(os.path.join(os.path.dirname(__file__),
                       "../../contracts/AgeTokenBulletin_abi.json")) as fh:
    bulletin = w3.eth.contract(
        address=os.environ["BULLETIN_ADDRESS"],
        abi=json.load(fh),
    )

def current_thumbprint() -> bytes:
    key = jwk.JWK.from_json(open("issuer_ed25519.jwk").read())
    return sha256(key.export_public().encode()).digest()

def push_thumbprint():
    tx = bulletin.functions.setThumbprint(current_thumbprint()).build_transaction({
        "from": acct.address,
        "nonce": w3.eth.get_transaction_count(acct.address),
        "gas": 80_000,
        "maxFeePerGas": w3.to_wei("40", "gwei"),
        "maxPriorityFeePerGas": w3.to_wei("2", "gwei"),
    })
    signed = acct.sign_transaction(tx)
    return w3.eth.send_raw_transaction(signed.rawTransaction).hex()
