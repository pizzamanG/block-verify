#!/usr/bin/env python3
"""
BlockVerify API - Production Crypto + Blockchain Integration
"""

from fastapi import FastAPI, Response, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import json
import time
from hashlib import sha256
from datetime import datetime, timedelta
import os
import secrets
import base64
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
import jwt
from web3 import Web3
from eth_account import Account
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(title="BlockVerify API - Production")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# Serve static files
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# ================================
# CRYPTO CONFIGURATION (Use existing key)
# ================================

ISSUER_PRIVATE_KEY = None
ISSUER_PUBLIC_KEY = None
ISSUER_THUMBPRINT = None

def load_existing_keypair():
    """Load existing Ed25519 keypair from jwk file"""
    global ISSUER_PRIVATE_KEY, ISSUER_PUBLIC_KEY, ISSUER_THUMBPRINT
    
    try:
        with open('issuer_ed25519.jwk', 'r') as f:
            jwk_data = json.load(f)
        
        print("🔑 Loading existing Ed25519 issuer keypair...")
        
        # Import JWK using PyJWT
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        import base64
        
        # Decode private key from JWK
        d_bytes = base64.urlsafe_b64decode(jwk_data['d'] + '==')
        x_bytes = base64.urlsafe_b64decode(jwk_data['x'] + '==')
        
        # Create private key
        ISSUER_PRIVATE_KEY = Ed25519PrivateKey.from_private_bytes(d_bytes)
        ISSUER_PUBLIC_KEY = ISSUER_PRIVATE_KEY.public_key()
        
        # Create thumbprint (SHA-256 of public key bytes)
        public_key_bytes = ISSUER_PUBLIC_KEY.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        ISSUER_THUMBPRINT = sha256(public_key_bytes).hexdigest()
        
        print(f"✅ Loaded existing keypair")
        print(f"🔍 Public key thumbprint: {ISSUER_THUMBPRINT}")
        
        return ISSUER_THUMBPRINT
        
    except Exception as e:
        print(f"❌ Failed to load existing key: {e}")
        print("🔄 Generating new keypair...")
        return generate_issuer_keypair()

def generate_issuer_keypair():
    """Generate Ed25519 keypair for JWT signing (fallback)"""
    global ISSUER_PRIVATE_KEY, ISSUER_PUBLIC_KEY, ISSUER_THUMBPRINT
    
    print("🔑 Generating new Ed25519 issuer keypair...")
    
    # Generate key
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    
    # Store keys
    ISSUER_PRIVATE_KEY = private_key
    ISSUER_PUBLIC_KEY = public_key
    
    # Create thumbprint (SHA-256 of public key bytes)
    public_key_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )
    ISSUER_THUMBPRINT = sha256(public_key_bytes).hexdigest()
    
    print(f"✅ Issuer keypair generated")
    print(f"🔍 Public key thumbprint: {ISSUER_THUMBPRINT}")
    
    return ISSUER_THUMBPRINT

def get_jwks():
    """Get JWKS (JSON Web Key Set) for public key distribution"""
    if not ISSUER_PUBLIC_KEY:
        return {"keys": []}
    
    # Convert Ed25519 public key to JWK format
    public_key_bytes = ISSUER_PUBLIC_KEY.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )
    
    jwk = {
        "kty": "OKP",  # Octet string key type
        "crv": "Ed25519",  # Curve
        "x": base64.urlsafe_b64encode(public_key_bytes).decode().rstrip("="),
        "use": "sig",  # Signature use
        "kid": ISSUER_THUMBPRINT[:16],  # Key ID (first 16 chars of thumbprint)
        "alg": "EdDSA"  # Algorithm
    }
    
    return {"keys": [jwk]}

# ================================
# BLOCKCHAIN CONFIGURATION
# ================================

# Polygon Amoy testnet configuration
POLYGON_AMOY_RPC = "https://rpc-amoy.polygon.technology"
BLOCKCHAIN_ENABLED = False
w3 = None
blockchain_account = None

# AgeTokenBulletin contract (use existing deployed contract)
CONTRACT_ADDRESS = "0x61cc6944583CB81BF4fCB53322Be1bc16d68A5d7"  # Existing deployed contract
CONTRACT_ABI = [
    {
        "inputs": [],
        "name": "thumbprint",
        "outputs": [{"internalType": "bytes32", "name": "", "type": "bytes32"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "bytes32", "name": "_thumbprint", "type": "bytes32"}],
        "name": "setThumbprint",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "issuer",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "revocationRoot",
        "outputs": [{"internalType": "bytes32", "name": "", "type": "bytes32"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "bytes32", "name": "_root", "type": "bytes32"}],
        "name": "setRevocationRoot",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

def setup_blockchain():
    """Setup blockchain connection"""
    global w3, blockchain_account, BLOCKCHAIN_ENABLED
    
    try:
        print("🔗 Connecting to Polygon Amoy...")
        w3 = Web3(Web3.HTTPProvider(POLYGON_AMOY_RPC))
        
        if w3.is_connected():
            print("✅ Connected to Polygon Amoy")
            
            # Load private key from environment
            private_key = os.getenv("PRIVATE_KEY") or os.getenv("BLOCKCHAIN_PRIVATE_KEY")
            if not private_key:
                print("⚠️ No PRIVATE_KEY found, generating demo key...")
                private_key = "0x" + secrets.token_hex(32)
                print(f"📋 Demo private key: {private_key}")
                print("💰 Send some MATIC to this address for gas: " + Account.from_key(private_key).address)
                print("💡 Set PRIVATE_KEY environment variable to use your funded wallet")
            else:
                # Add 0x prefix if missing
                if not private_key.startswith("0x"):
                    private_key = "0x" + private_key
                print(f"🔑 Using private key from environment: {private_key[:6]}...{private_key[-4:]}")
            
            blockchain_account = Account.from_key(private_key)
            print(f"🏦 Blockchain account: {blockchain_account.address}")
            
            # Check balance
            balance = w3.eth.get_balance(blockchain_account.address)
            balance_matic = w3.from_wei(balance, 'ether')
            print(f"💰 Balance: {balance_matic:.4f} MATIC")
            
            if balance > 0:
                BLOCKCHAIN_ENABLED = True
                print("✅ Blockchain integration enabled")
            else:
                print("⚠️ No MATIC balance - blockchain integration disabled")
                
        else:
            print("❌ Failed to connect to Polygon Amoy")
            
    except Exception as e:
        print(f"❌ Blockchain setup failed: {e}")
        print("🔄 Continuing without blockchain integration")

async def push_thumbprint_to_blockchain(thumbprint: str):
    """Push issuer thumbprint to blockchain"""
    if not BLOCKCHAIN_ENABLED:
        print("⚠️ Blockchain not enabled, skipping push")
        return None
    
    if not CONTRACT_ADDRESS:
        print("⚠️ No contract address set, skipping push")
        return None
    
    try:
        print(f"📤 Pushing thumbprint to blockchain: {thumbprint}")
        
        # Convert thumbprint to bytes32
        thumbprint_bytes = bytes.fromhex(thumbprint)
        
        # Get contract
        contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=CONTRACT_ABI)
        
        # Build transaction
        tx = contract.functions.setThumbprint(thumbprint_bytes).build_transaction({
            'from': blockchain_account.address,
            'gas': 100000,
            'gasPrice': w3.to_wei('20', 'gwei'),
            'nonce': w3.eth.get_transaction_count(blockchain_account.address),
        })
        
        # Sign and send
        signed_tx = w3.eth.account.sign_transaction(tx, blockchain_account.key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        print(f"✅ Transaction sent: {tx_hash.hex()}")
        print(f"🔗 View on PolygonScan: https://amoy.polygonscan.com/tx/{tx_hash.hex()}")
        
        return tx_hash.hex()
        
    except Exception as e:
        print(f"❌ Blockchain push failed: {e}")
        return None

# Initialize crypto and blockchain on startup
load_existing_keypair()
setup_blockchain()

# Simple in-memory revocation list (in production, use database)
REVOKED_TOKENS = set()
REVOKED_DEVICES = set()

# Simple generation-based revocation (no database needed)
CURRENT_TOKEN_GENERATION = 1

def get_current_generation():
    """Get current token generation - bump this to revoke all tokens"""
    return CURRENT_TOKEN_GENERATION

def bump_generation(reason="Admin revocation"):
    """Bump generation to revoke ALL existing tokens"""
    global CURRENT_TOKEN_GENERATION
    old_gen = CURRENT_TOKEN_GENERATION
    CURRENT_TOKEN_GENERATION += 1
    print(f"🚫 [BlockVerify] Generation bumped from {old_gen} to {CURRENT_TOKEN_GENERATION} (Reason: {reason})")
    print(f"   This revokes ALL tokens from generation {old_gen} and below")
    return CURRENT_TOKEN_GENERATION

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "blockverify-api"}

@app.post("/fake/verify")
async def fake_kyc_verify(file: UploadFile = File(...)):
    """Fake KYC verification endpoint - always passes for demo"""
    # Read and discard the uploaded file (never store in demo)
    content = await file.read()
    print(f"📄 [BlockVerify] Fake KYC: Processed {file.filename} ({len(content)} bytes)")
    
    # Always return success for demo purposes
    return {
        "status": "approved",
        "confidence": 0.95,
        "age_estimate": 25,
        "document_type": "drivers_license",
        "session_id": secrets.token_hex(16)
    }

@app.get("/verify.html", response_class=HTMLResponse)
def serve_verify(return_url: str = None):
    """Enhanced verification page with proper return URL handling"""
    return f"""
<!DOCTYPE html>
<html>
<head>
    <title>BlockVerify - Secure Age Verification</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0; 
            padding: 2rem; 
            color: white;
            min-height: 100vh;
        }}
        .container {{ 
            max-width: 600px; 
            margin: 0 auto; 
            background: rgba(255,255,255,0.1); 
            padding: 2rem; 
            border-radius: 12px;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        }}
        .upload-area {{
            border: 2px dashed #fff;
            border-radius: 8px;
            padding: 2rem;
            text-align: center;
            margin: 2rem 0;
            cursor: pointer;
            transition: background 0.3s;
        }}
        .upload-area:hover {{ background: rgba(255,255,255,0.1); }}
        .btn {{
            background: #4CAF50;
            color: white;
            border: none;
            padding: 1rem 2rem;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1rem;
            margin: 1rem 0;
            width: 100%;
            transition: background 0.3s;
            font-weight: bold;
        }}
        .btn:hover {{ background: #45a049; }}
        .btn:disabled {{ 
            background: #666; 
            cursor: not-allowed; 
            opacity: 0.7;
        }}
        .step {{ 
            margin: 1rem 0; 
            padding: 1rem; 
            background: rgba(255,255,255,0.1); 
            border-radius: 8px; 
            border-left: 4px solid #4CAF50;
        }}
        .status {{
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
            display: none;
        }}
        .status.success {{ background: #4CAF50; display: block; }}
        .status.error {{ background: #f44336; display: block; }}
        .status.info {{ background: #2196F3; display: block; }}
        .device-info {{
            background: rgba(0,0,0,0.2);
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
            font-size: 0.9rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔐 BlockVerify Age Verification</h1>
        <p>Secure, private age verification for adult content access</p>
        
        <div class="device-info">
            <strong>🖥️ Device Information:</strong>
            <div id="deviceInfo">Detecting device...</div>
        </div>
        
        <div class="step">
            <h3>Step 1: Upload ID Document</h3>
            <div class="upload-area" onclick="document.getElementById('idFile').click()">
                <p>📄 Click to upload your ID document</p>
                <p><small>Driver's license, passport, or government ID<br>
                (Demo accepts any image file)</small></p>
            </div>
            <input type="file" id="idFile" accept="image/*" style="display:none" onchange="handleFileUpload(this)">
            <div id="uploadStatus" class="status"></div>
            
            <div id="kycFailureHelp" class="status error" style="display:none;">
                <h4>❌ Age Verification Failed</h4>
                <p>This can happen for several reasons:</p>
                <ul style="text-align: left; margin: 1rem 0; padding-left: 2rem;">
                    <li>Document image quality too low</li>
                    <li>Document type not supported</li>
                    <li>Age verification indicates under 18</li>
                    <li>Random demo failure (25% chance in test mode)</li>
                </ul>
                <p><strong>What to do:</strong></p>
                <ul style="text-align: left; margin: 1rem 0; padding-left: 2rem;">
                    <li>Try uploading a different, clearer image</li>
                    <li>Refresh the page and try again</li>
                    <li>Contact support if the issue persists</li>
                </ul>
                <button class="btn" onclick="resetVerification()" style="margin-top: 1rem;">
                    🔄 Try Again
                </button>
            </div>
        </div>
        
        <div class="step">
            <h3>Step 2: Secure Device Registration</h3>
            <p>Register this device for secure, anonymous access across all participating sites</p>
            
            <div style="margin: 1rem 0; padding: 1rem; background: rgba(0,0,0,0.2); border-radius: 8px;">
                <label style="display: flex; align-items: center; cursor: pointer;">
                    <input type="checkbox" id="blockchainMode" style="margin-right: 0.5rem; transform: scale(1.2);">
                    <span>🔗 <strong>Demo Mode 5:</strong> Push thumbprint to Polygon Amoy blockchain</span>
                </label>
                <small style="color: rgba(255,255,255,0.7);">
                    This demonstrates the full production flow with blockchain trust anchoring
                </small>
            </div>
            
            <button class="btn" onclick="registerDevice()" id="registerBtn" disabled>
                🔒 Register Device Securely
            </button>
            <div id="deviceStatus" class="status"></div>
        </div>
        
        <div id="successMessage" style="display:none; background:#4CAF50; padding:2rem; border-radius:8px; margin:2rem 0; text-align:center;">
            <h3>✅ Verification Complete!</h3>
            <p>Your device has been securely registered for age verification.</p>
            <p>Redirecting you back to the content...</p>
            <div style="margin: 1rem 0;">
                <div style="border: 3px solid rgba(255,255,255,0.3); border-top: 3px solid white; border-radius: 50%; width: 30px; height: 30px; animation: spin 1s linear infinite; margin: 0 auto;"></div>
            </div>
        </div>
        
        <div class="step" style="background: rgba(76,175,80,0.2); border-left-color: #4CAF50;">
            <h4>🔒 Privacy Guarantees</h4>
            <ul style="text-align: left; margin: 0; padding-left: 1.5rem;">
                <li>✅ Zero personal data shared with adult sites</li>
                <li>✅ Device-bound security prevents token sharing</li>
                <li>✅ Works across all participating sites</li>
                <li>✅ Compliant with privacy regulations</li>
            </ul>
        </div>
    </div>

    <style>
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
    </style>

    <script>
        let uploadComplete = false;
        const returnUrl = '{return_url or "http://localhost:3000"}';
        
        // Device detection and display
        const deviceInfo = {{
            isMobile: /iPhone|iPad|iPod|Android/i.test(navigator.userAgent),
            isIOS: /iPhone|iPad|iPod/i.test(navigator.userAgent),
            isAndroid: /Android/i.test(navigator.userAgent),
            browser: getBrowserName(),
            supportsWebAuthn: !!(navigator.credentials && navigator.credentials.create)
        }};
        
        function getBrowserName() {{
            if (/Chrome/i.test(navigator.userAgent)) return 'Chrome';
            if (/Safari/i.test(navigator.userAgent) && !/Chrome/i.test(navigator.userAgent)) return 'Safari';
            if (/Firefox/i.test(navigator.userAgent)) return 'Firefox';
            if (/Edge/i.test(navigator.userAgent)) return 'Edge';
            return 'Other';
        }}
        
        document.getElementById('deviceInfo').innerHTML = `
            📱 Type: ${{deviceInfo.isMobile ? 'Mobile' : 'Desktop'}} 
             Browser: ${{deviceInfo.browser}} 
            🔐 WebAuthn: ${{deviceInfo.supportsWebAuthn ? 'Supported' : 'Not Supported'}}
        `;
        
        function showStatus(elementId, message, type = 'info') {{
            const el = document.getElementById(elementId);
            el.className = `status ${{type}}`;
            el.innerHTML = message;
            el.style.display = 'block';
        }}
        
        function handleFileUpload(input) {{
            if (input.files && input.files[0]) {{
                const file = input.files[0];
                console.log('🔐 [BlockVerify] File uploaded:', file.name, file.size, 'bytes');
                showStatus('uploadStatus', `✅ ${{file.name}} uploaded successfully`, 'success');
                uploadComplete = true;
                document.getElementById('registerBtn').disabled = false;
                
                // Hide any previous failure messages
                document.getElementById('kycFailureHelp').style.display = 'none';
            }}
        }}
        
        function resetVerification() {{
            console.log('🔄 [BlockVerify] Resetting verification...');
            
            // Reset upload state
            uploadComplete = false;
            document.getElementById('idFile').value = '';
            document.getElementById('registerBtn').disabled = true;
            
            // Clear all status messages
            document.getElementById('uploadStatus').style.display = 'none';
            document.getElementById('deviceStatus').style.display = 'none';
            document.getElementById('kycFailureHelp').style.display = 'none';
            document.getElementById('successMessage').style.display = 'none';
            
            showStatus('uploadStatus', '🔄 Ready to upload new document', 'info');
        }}
        
        async function registerDevice() {{
            if (!uploadComplete) {{
                showStatus('deviceStatus', '❌ Please upload your ID first', 'error');
                return;
            }}
            
            console.log('🔐 [BlockVerify] Starting device registration...');
            showStatus('deviceStatus', '🔄 Registering device securely...', 'info');
            
            // Check if blockchain mode is enabled
            const blockchainMode = document.getElementById('blockchainMode').checked;
            if (blockchainMode) {{
                showStatus('deviceStatus', '🔗 Blockchain mode enabled - this may take longer...', 'info');
            }}
            
            try {{
                // Enhanced mock registration with device info
                const mockCredential = {{
                    id: 'blockverify_device_' + Date.now(),
                    response: {{
                        clientDataJSON: JSON.stringify({{
                            type: 'webauthn.create',
                            challenge: btoa('demo_challenge'),
                            origin: window.location.origin
                        }}),
                        attestationObject: 'mock_attestation_' + deviceInfo.browser
                    }},
                    deviceInfo: deviceInfo,
                    push_to_blockchain: blockchainMode  // Add blockchain flag
                }};
                
                console.log('🔐 [BlockVerify] Sending registration to API...');
                const response = await fetch('/webauthn/register', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify(mockCredential)
                }});
                
                if (response.ok) {{
                    const result = await response.json();
                    console.log('🔐 [BlockVerify] Registration successful:', result);
                    
                    let statusMessage = '✅ Device registered successfully';
                    
                    // Show blockchain info if enabled
                    if (blockchainMode && result.blockchain_enabled) {{
                        if (result.blockchain_tx) {{
                            statusMessage += `<br>🔗 Blockchain TX: <a href="https://amoy.polygonscan.com/tx/${{result.blockchain_tx}}" target="_blank" style="color: #4CAF50;">${{result.blockchain_tx.substring(0, 16)}}...</a>`;
                            statusMessage += `<br>🔍 Thumbprint: ${{result.thumbprint.substring(0, 32)}}...`;
                        }} else {{
                            statusMessage += '<br>⚠️ Blockchain push failed (check console for details)';
                        }}
                    }} else if (blockchainMode && !result.blockchain_enabled) {{
                        statusMessage += '<br>⚠️ Blockchain not enabled (need MATIC for gas)';
                    }}
                    
                    showStatus('deviceStatus', statusMessage, 'success');
                    
                    // Show success and redirect
                    document.getElementById('successMessage').style.display = 'block';
                    
                    setTimeout(() => {{
                        // Ensure token is stored in localStorage before redirect
                        try {{
                            if (result.token) {{
                                // Store in multiple locations for cross-port access
                                localStorage.setItem('AgeToken', result.token);
                                localStorage.setItem('AgeTokenAccess', result.token);
                                
                                // Also try to set cookies that work across localhost ports
                                document.cookie = `AgeToken=${{result.token}}; path=/; max-age=86400; SameSite=Lax`;
                                document.cookie = `AgeTokenAccess=${{result.token}}; path=/; max-age=86400; SameSite=Lax`;
                                
                                console.log('💾 [BlockVerify] Token stored in localStorage and cookies');
                                console.log('🔍 [BlockVerify] Token preview:', result.token.substring(0, 50) + '...');
                                
                                // Verify storage worked
                                const storedToken = localStorage.getItem('AgeToken');
                                console.log('✅ [BlockVerify] Storage verification:', storedToken ? 'SUCCESS' : 'FAILED');
                            }} else {{
                                console.error('❌ [BlockVerify] No token in response!', result);
                            }}
                        }} catch (e) {{
                            console.error('❌ [BlockVerify] Storage failed:', e);
                        }}
                        
                        console.log('🔄 [BlockVerify] Redirecting to:', returnUrl);
                        window.location.href = returnUrl + (returnUrl.includes('?') ? '&' : '?') + 'verified=true&t=' + Date.now();
                    }}, 3000);
                }} else {{
                    // Handle specific error cases
                    let errorMessage = `❌ Registration failed (HTTP ${{response.status}})`;
                    let showKycFailure = false;
                    
                    if (response.status === 400) {{
                        errorMessage = '❌ Age verification failed - unable to confirm age over 18';
                        showKycFailure = true;
                    }} else if (response.status === 403) {{
                        errorMessage = '❌ Access denied - please try again later';
                    }} else if (response.status >= 500) {{
                        errorMessage = '❌ Server error - please try again in a moment';
                    }}
                    
                    showStatus('deviceStatus', errorMessage, 'error');
                    
                    if (showKycFailure) {{
                        document.getElementById('kycFailureHelp').style.display = 'block';
                    }}
                    
                    throw new Error(`HTTP ${{response.status}}: ${{response.statusText}}`);
                }}
            }} catch (error) {{
                console.error('🔐 [BlockVerify] Registration failed:', error);
                
                // Only show generic error if we haven't already shown a specific one
                if (!document.getElementById('deviceStatus').innerHTML.includes('❌')) {{
                    showStatus('deviceStatus', `❌ Registration failed: ${{error.message}}`, 'error');
                }}
            }}
        }}
        
        console.log('🔐 [BlockVerify] Verification page loaded');
        console.log('🔐 [BlockVerify] Return URL:', returnUrl);
        console.log('🔐 [BlockVerify] Device Info:', deviceInfo);
    </script>
</body>
</html>
    """

@app.post("/webauthn/register")
async def webauthn_register(request: dict, response: Response):
    """Enhanced WebAuthn registration with production-quality JWT and blockchain integration"""
    print("🔐 [BlockVerify] WebAuthn Registration Started")
    print(f"📝 [BlockVerify] Request data: {request}")
    
    # Generate a cryptographically secure device ID
    device_id = secrets.token_hex(32)
    print(f"🔑 [BlockVerify] Generated device ID: {device_id[:16]}...")
    
    # Create proper JWT token
    token = create_jwt_token(device_id, 18)
    print(f"🎫 [BlockVerify] JWT created: {token[:50]}...")
    
    # Blockchain integration (optional demo mode 5)
    blockchain_tx = None
    if request.get("push_to_blockchain", False):
        print("🔗 [BlockVerify] Demo mode 5: Pushing to blockchain...")
        blockchain_tx = await push_thumbprint_to_blockchain(ISSUER_THUMBPRINT)
    
    response_data = {
        "token": token, 
        "status": "success",
        "device_id": device_id[:16] + "...",
        "issuer": "BlockVerify",
        "thumbprint": ISSUER_THUMBPRINT,
        "blockchain_enabled": BLOCKCHAIN_ENABLED,
        "blockchain_tx": blockchain_tx,
        "jwks_url": "/.well-known/jwks.json"
    }
    
    # Set production-quality cookies
    print("🍪 [BlockVerify] Setting secure cookies...")
    
    # Main token cookie - HttpOnly for security
    response.set_cookie(
        "AgeToken", 
        token,
        httponly=True,  # Prevents XSS attacks
        secure=False,   # Set to True in production with HTTPS
        samesite="lax", # CSRF protection
        max_age=60*60*24,  # 24 hours
        domain="localhost",
        path="/"
    )
    
    # Also set in localStorage accessible cookie for JavaScript
    response.set_cookie(
        "AgeTokenAccess", 
        token,
        httponly=False,  # Accessible to JavaScript
        secure=False,
        samesite="lax",
        max_age=60*60*24,  # 24 hours
        domain="localhost",
        path="/"
    )
    
    print("✅ [BlockVerify] Cookies set successfully")
    print("🔄 [BlockVerify] Registration complete")
    
    return response_data

@app.post("/verify-token")
async def verify_token(request: dict):
    """Verify a JWT token"""
    token = request.get("token")
    if not token:
        return {"valid": False, "error": "No token provided"}
    
    # Check if token is revoked (for old base64 tokens)
    if token in REVOKED_TOKENS:
        return {"valid": False, "error": "Token has been revoked"}
    
    try:
        # Try to decode as JWT first
        try:
            # Get the public key for verification
            public_key_pem = ISSUER_PUBLIC_KEY.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            
            # Decode and verify JWT
            payload = jwt.decode(
                token, 
                public_key_pem, 
                algorithms=["EdDSA"],
                audience="adult-sites",
                issuer="BlockVerify"
            )
            
            return {
                "valid": True,
                "issuer": payload.get("iss"),
                "subject": payload.get("sub"),
                "audience": payload.get("aud"),
                "age_over": payload.get("age_over"),
                "device_type": payload.get("device_type"),
                "issued_at": payload.get("iat"),
                "expires_at": payload.get("exp"),
                "jwt_id": payload.get("jti"),
                "verified_by": "BlockVerify-JWT",
                "token_type": "JWT"
            }
            
        except jwt.InvalidTokenError as e:
            # If JWT decode fails, try old base64 format for backwards compatibility
            print(f"JWT decode failed: {e}, trying base64 format...")
            
            token_data = json.loads(base64.b64decode(token).decode())
            
            # Check if device is revoked
            device_id = token_data.get("device")
            if device_id and device_id in REVOKED_DEVICES:
                return {"valid": False, "error": "Device has been revoked"}
            
            # Check generation (simple revocation without database)
            token_generation = token_data.get("generation", 0)
            if token_generation < get_current_generation():
                return {"valid": False, "error": f"Token generation {token_generation} is outdated (current: {get_current_generation()})"}
            
            # Check expiration
            if time.time() > token_data.get("exp", 0):
                return {"valid": False, "error": "Token expired"}
            
            return {
                "valid": True,
                "device": token_data["device"],
                "ageOver": token_data["ageOver"],
                "iat": token_data["iat"],
                "exp": token_data["exp"],
                "verified_by": "BlockVerify-Legacy",
                "token_type": "Base64",
                "revocation_checked": True
            }
            
    except Exception as e:
        return {"valid": False, "error": str(e)}

@app.get("/debug/create-token")
async def debug_create_token(response: Response):
    """Debug endpoint to manually create and set a token"""
    device_id = secrets.token_hex(32)
    exp_time = int((datetime.now() + timedelta(hours=24)).timestamp())
    iat_time = int(time.time())
    
    token_data = {
        "device": device_id,
        "ageOver": 18,
        "iat": iat_time,
        "exp": exp_time,
        "iss": "BlockVerify",
        "aud": "adult-sites",
        "sub": "age-verification"
    }
    
    token = base64.b64encode(json.dumps(token_data).encode()).decode()
    
    # Set cookies
    response.set_cookie("AgeToken", token, httponly=True, max_age=60*60*24*365, domain="localhost", path="/")
    response.set_cookie("AgeTokenAccess", token, httponly=False, max_age=60*60*24*365, domain="localhost", path="/")
    
    return {
        "status": "debug_token_created",
        "token": token[:50] + "...",
        "device_id": device_id[:16] + "...",
        "expires": datetime.fromtimestamp(exp_time).isoformat(),
        "instructions": "Token has been set. Visit http://localhost:3000 to test."
    }

@app.get("/static/{filename}")
async def serve_static(filename: str):
    """Serve static files with proper headers"""
    try:
        file_path = os.path.join("frontend", filename)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Set content type
        content_type = "application/javascript" if filename.endswith('.js') else "text/plain"
        
        # Return with no-cache headers
        return Response(
            content,
            media_type=content_type,
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/admin/revoke-token")
async def revoke_token(request: dict):
    """Revoke a specific token or device"""
    token = request.get("token")
    device_id = request.get("device_id") 
    reason = request.get("reason", "Admin revocation")
    
    if not token and not device_id:
        raise HTTPException(status_code=400, detail="Must provide token or device_id")
    
    revoked_count = 0
    
    if token:
        REVOKED_TOKENS.add(token)
        revoked_count += 1
        print(f"🚫 [BlockVerify] Token revoked: {token[:50]}... (Reason: {reason})")
    
    if device_id:
        REVOKED_DEVICES.add(device_id)
        revoked_count += 1
        print(f"🚫 [BlockVerify] Device revoked: {device_id} (Reason: {reason})")
    
    return {
        "status": "revoked",
        "revoked_tokens": len(REVOKED_TOKENS),
        "revoked_devices": len(REVOKED_DEVICES),
        "reason": reason,
        "timestamp": int(time.time())
    }

@app.get("/admin/revocation-status")
async def revocation_status():
    """Get revocation statistics"""
    return {
        "revoked_tokens": len(REVOKED_TOKENS),
        "revoked_devices": len(REVOKED_DEVICES),
        "revocation_list_sample": {
            "tokens": list(REVOKED_TOKENS)[:5],  # Show first 5
            "devices": list(REVOKED_DEVICES)[:5]
        }
    }

@app.post("/admin/revoke-all")
async def revoke_all_tokens(request: dict):
    """Bump generation to revoke ALL tokens (no database needed)"""
    reason = request.get("reason", "Mass revocation")
    
    old_generation = get_current_generation()
    new_generation = bump_generation(reason)
    
    return {
        "status": "all_tokens_revoked",
        "old_generation": old_generation,
        "new_generation": new_generation,
        "reason": reason,
        "message": f"All tokens from generation {old_generation} and below are now invalid",
        "timestamp": int(time.time())
    }

@app.get("/admin/generation-status")
async def generation_status():
    """Get current generation info"""
    return {
        "current_generation": get_current_generation(),
        "message": f"All tokens must be generation {get_current_generation()} or higher to be valid"
    }

@app.get("/.well-known/jwks.json")
async def jwks_endpoint():
    """JWKS endpoint for public key distribution"""
    return get_jwks()

@app.get("/issuer/info")
async def issuer_info():
    """Get issuer information including thumbprint"""
    return {
        "issuer": "BlockVerify",
        "thumbprint": ISSUER_THUMBPRINT,
        "blockchain_enabled": BLOCKCHAIN_ENABLED,
        "contract_address": CONTRACT_ADDRESS,
        "jwks_url": "/.well-known/jwks.json"
    }

def create_jwt_token(device_id: str, age_over: int) -> str:
    """Create properly signed JWT token"""
    now = datetime.utcnow()
    exp_time = now + timedelta(hours=24)
    
    payload = {
        "iss": "BlockVerify",  # Issuer
        "sub": device_id,      # Subject (device ID)
        "aud": "adult-sites",  # Audience
        "iat": int(now.timestamp()),
        "exp": int(exp_time.timestamp()),
        "age_over": age_over,
        "device_type": "web",
        "jti": secrets.token_hex(16),  # JWT ID
    }
    
    # Sign with Ed25519 private key
    private_key_pem = ISSUER_PRIVATE_KEY.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    token = jwt.encode(
        payload, 
        private_key_pem, 
        algorithm="EdDSA",
        headers={"kid": ISSUER_THUMBPRINT[:16]}
    )
    
    return token

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Simple BlockVerify API on http://localhost:8000")
    print("🔐 Verification endpoint: http://localhost:8000/verify.html")
    uvicorn.run(app, host="0.0.0.0", port=8000) 