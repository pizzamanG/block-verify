#!/usr/bin/env python3
"""
BlockVerify Deployment Script
Handles smart contract deployment and thumbprint management
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from hashlib import sha256
from jwcrypto import jwk
from web3 import Web3
from eth_account import Account

def load_config():
    """Load configuration from environment or .env file"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    
    config = {
        'rpc_url': os.getenv('CHAIN_RPC_URL'),
        'private_key': os.getenv('PRIVATE_KEY'),
        'bulletin_address': os.getenv('BULLETIN_ADDRESS'),
        'issuer_key_file': os.getenv('ISSUER_KEY_FILE', 'issuer_ed25519.jwk')
    }
    
    missing = [k for k, v in config.items() if not v]
    if missing:
        print(f"❌ Missing required environment variables: {', '.join(missing)}")
        sys.exit(1)
    
    return config

def generate_issuer_key(key_file):
    """Generate a new Ed25519 issuer key if it doesn't exist"""
    if os.path.exists(key_file):
        print(f"✅ Using existing issuer key: {key_file}")
        return jwk.JWK.from_json(open(key_file).read())
    
    print(f"🔑 Generating new Ed25519 issuer key: {key_file}")
    key = jwk.JWK.generate(kty='OKP', crv='Ed25519')
    with open(key_file, 'w') as f:
        f.write(key.export())
    
    print(f"✅ Issuer key generated and saved to {key_file}")
    return key

def calculate_thumbprint(key):
    """Calculate SHA-256 thumbprint of the public key"""
    public_key_json = key.export_public()
    return sha256(public_key_json.encode()).digest()

def deploy_contract(config):
    """Deploy the AgeTokenBulletin contract"""
    print("🚀 Deploying AgeTokenBulletin contract...")
    
    # Change to contracts directory
    contracts_dir = Path("infra/contracts")
    if not contracts_dir.exists():
        print("❌ Contracts directory not found")
        sys.exit(1)
    
    os.chdir(contracts_dir)
    
    # Compile and deploy
    try:
        result = subprocess.run([
            "npx", "hardhat", "run", "scripts/deploy.js", 
            "--network", "amoy"
        ], capture_output=True, text=True, check=True)
        
        # Extract contract address from output
        output_lines = result.stdout.strip().split('\n')
        for line in output_lines:
            if "deployed to:" in line:
                address = line.split("deployed to:")[-1].strip()
                print(f"✅ Contract deployed to: {address}")
                return address
        
        print("❌ Could not find contract address in deployment output")
        sys.exit(1)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Deployment failed: {e.stderr}")
        sys.exit(1)
    finally:
        os.chdir("../..")

def push_thumbprint(config, thumbprint):
    """Push the issuer thumbprint to the smart contract"""
    print("📤 Pushing thumbprint to blockchain...")
    
    w3 = Web3(Web3.HTTPProvider(config['rpc_url']))
    if not w3.is_connected():
        print("❌ Failed to connect to blockchain")
        sys.exit(1)
    
    account = Account.from_key(config['private_key'])
    
    # Load contract ABI
    abi_file = Path("infra/contracts/artifacts/contracts/AgeTokenBulletin.sol/AgeTokenBulletin.json")
    if not abi_file.exists():
        print("❌ Contract ABI not found. Run deployment first.")
        sys.exit(1)
    
    with open(abi_file) as f:
        contract_data = json.load(f)
    
    contract = w3.eth.contract(
        address=config['bulletin_address'],
        abi=contract_data['abi']
    )
    
    # Build and send transaction
    try:
        tx = contract.functions.setThumbprint(thumbprint).build_transaction({
            "from": account.address,
            "nonce": w3.eth.get_transaction_count(account.address),
            "gas": 80_000,
            "maxFeePerGas": w3.to_wei("80", "gwei"),
            "maxPriorityFeePerGas": w3.to_wei("30", "gwei"),
        })
        
        signed = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        
        print(f"✅ Thumbprint pushed! Transaction: {tx_hash.hex()}")
        
        # Wait for confirmation
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"✅ Transaction confirmed in block {receipt.blockNumber}")
        
    except Exception as e:
        print(f"❌ Failed to push thumbprint: {e}")
        sys.exit(1)

def setup_database():
    """Initialize the database schema"""
    print("🗄️  Setting up database...")
    
    try:
        from backend.app.db import engine
        from backend.app.models import SQLModel
        
        SQLModel.metadata.create_all(engine)
        print("✅ Database schema created")
        return True
        
    except Exception as e:
        print(f"⚠️  Database setup skipped (not running in production): {e}")
        print("   Database will be initialized when you start the API server")
        return False

def main():
    print("🔐 BlockVerify Deployment Script")
    print("=" * 40)
    
    config = load_config()
    
    # Generate or load issuer key
    issuer_key = generate_issuer_key(config['issuer_key_file'])
    thumbprint = calculate_thumbprint(issuer_key)
    
    print(f"🔍 Issuer thumbprint: {thumbprint.hex()}")
    
    # Deploy contract if address not provided
    if not config['bulletin_address']:
        contract_address = deploy_contract(config)
        config['bulletin_address'] = contract_address
        print(f"💡 Add this to your .env file: BULLETIN_ADDRESS={contract_address}")
    
    # Push thumbprint to contract
    push_thumbprint(config, thumbprint)
    
    # Setup database
    setup_database()
    
    print("\n🎉 Deployment completed successfully!")
    print("\nNext steps:")
    print("1. Update your .env file with the contract address")
    print("2. Start the FastAPI server: uvicorn backend.app.main:app --reload")
    print("3. Register your first verifier at /verifiers/register")
    print("4. Test the integration with the dashboard at /dashboard.html")

if __name__ == "__main__":
    main() 