import os, json, base64
from pathlib import Path
from web3 import Web3
from eth_account import Account
from hashlib import sha256
from jwcrypto import jwk
from .settings import settings

w3  = Web3(Web3.HTTPProvider(settings.CHAIN_RPC_URL))

# Only load account if private key is available
private_key = os.getenv("PRIVATE_KEY")
if private_key:
    acct = Account.from_key(private_key)
else:
    acct = None

# Load contract ABI from artifacts
abi_path = Path(__file__).parent.parent.parent / "infra/contracts/artifacts/contracts/AgeTokenBulletin.sol/AgeTokenBulletin.json"
try:
    with open(abi_path) as fh:
        contract_data = json.load(fh)
        bulletin = w3.eth.contract(
            address=settings.BULLETIN_ADDRESS,
            abi=contract_data["abi"],
        )
except FileNotFoundError:
    # Fallback to a minimal ABI if artifacts not found
    minimal_abi = [
        {"inputs": [], "name": "thumbprint", "outputs": [{"type": "bytes32"}], "stateMutability": "view", "type": "function"},
        {"inputs": [{"name": "_thumbprint", "type": "bytes32"}], "name": "setThumbprint", "outputs": [], "stateMutability": "nonpayable", "type": "function"}
    ]
    bulletin = w3.eth.contract(
        address=settings.BULLETIN_ADDRESS,
        abi=minimal_abi,
    )

def current_thumbprint() -> bytes:
    # Load issuer key from project root
    key_path = Path(settings.ISSUER_KEY_FILE)
    if not key_path.is_absolute():
        key_path = Path(__file__).parent.parent.parent / key_path
    
    key = jwk.JWK.from_json(open(key_path).read())
    return sha256(key.export_public().encode()).digest()

def push_thumbprint():
    if not acct:
        raise ValueError("Private key not configured")
        
    tx = bulletin.functions.setThumbprint(current_thumbprint()).build_transaction({
        "from": acct.address,
        "nonce": w3.eth.get_transaction_count(acct.address),
        "gas": 80_000,
        "maxFeePerGas": w3.to_wei("80", "gwei"),
        "maxPriorityFeePerGas": w3.to_wei("30", "gwei"),
    })
    signed = acct.sign_transaction(tx)
    return w3.eth.send_raw_transaction(signed.raw_transaction).hex()
