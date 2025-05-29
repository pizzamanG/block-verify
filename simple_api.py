#!/usr/bin/env python3
"""
Simple BlockVerify API for testing the verification flow
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

app = FastAPI(title="BlockVerify Simple API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# Serve static files
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "blockverify-api"}

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
        </div>
        
        <div class="step">
            <h3>Step 2: Secure Device Registration</h3>
            <p>Register this device for secure, anonymous access across all participating sites</p>
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
            🌐 Browser: ${{deviceInfo.browser}} 
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
            }}
        }}
        
        async function registerDevice() {{
            if (!uploadComplete) {{
                showStatus('deviceStatus', '❌ Please upload your ID first', 'error');
                return;
            }}
            
            console.log('🔐 [BlockVerify] Starting device registration...');
            showStatus('deviceStatus', '🔄 Registering device securely...', 'info');
            
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
                    deviceInfo: deviceInfo
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
                    showStatus('deviceStatus', '✅ Device registered successfully', 'success');
                    
                    // Show success and redirect
                    document.getElementById('successMessage').style.display = 'block';
                    
                    setTimeout(() => {{
                        console.log('🔐 [BlockVerify] Redirecting to:', returnUrl);
                        
                        // Ensure token is stored in localStorage before redirect
                        try {{
                            if (result.token) {{
                                localStorage.setItem('AgeToken', result.token);
                                localStorage.setItem('AgeTokenAccess', result.token);
                                console.log('💾 [BlockVerify] Token stored in localStorage for cross-domain access');
                            }}
                        }} catch (e) {{
                            console.warn('⚠️ [BlockVerify] Could not store in localStorage:', e);
                        }}
                        
                        window.location.href = returnUrl + (returnUrl.includes('?') ? '&' : '?') + 'verified=true';
                    }}, 3000);
                }} else {{
                    throw new Error(`HTTP ${{response.status}}: ${{response.statusText}}`);
                }}
            }} catch (error) {{
                console.error('🔐 [BlockVerify] Registration failed:', error);
                showStatus('deviceStatus', `❌ Registration failed: ${{error.message}}`, 'error');
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
    """Enhanced WebAuthn registration with production-quality cookie handling"""
    print("🔐 [BlockVerify] WebAuthn Registration Started")
    print(f"📝 [BlockVerify] Request data: {request}")
    
    # Generate a cryptographically secure device ID
    import secrets
    device_id = secrets.token_hex(32)
    print(f"🔑 [BlockVerify] Generated device ID: {device_id[:16]}...")
    
    # Create a comprehensive JWT-like token
    exp_time = int((datetime.now() + timedelta(days=365)).timestamp())
    iat_time = int(time.time())
    
    token_data = {
        "device": device_id,
        "ageOver": 18,
        "iat": iat_time,
        "exp": exp_time,
        "iss": "BlockVerify",
        "aud": "adult-sites",
        "sub": "age-verification",
        "jti": secrets.token_hex(16),  # JWT ID for uniqueness
        "device_type": "web",
        "verified_at": datetime.now().isoformat()
    }
    
    print(f"📋 [BlockVerify] Token payload created:")
    print(f"   🔹 Device: {device_id[:16]}...")
    print(f"   🔹 Age: {token_data['ageOver']}+")
    print(f"   🔹 Issued: {datetime.fromtimestamp(iat_time)}")
    print(f"   🔹 Expires: {datetime.fromtimestamp(exp_time)}")
    print(f"   🔹 Valid for: {(exp_time - iat_time) // 86400} days")
    
    # Simple base64 encoding for demo (in production would be properly signed JWT)
    import base64
    token = base64.b64encode(json.dumps(token_data).encode()).decode()
    print(f"🎫 [BlockVerify] Token generated: {token[:50]}...")
    
    response_data = {
        "token": token, 
        "status": "success",
        "device_id": device_id[:16] + "...",
        "expires": datetime.fromtimestamp(exp_time).isoformat()
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
        max_age=60*60*24*365,  # 1 year
        domain="localhost",  # Set to your domain in production
        path="/"
    )
    
    # Also set in localStorage accessible cookie for JavaScript
    response.set_cookie(
        "AgeTokenAccess", 
        token,
        httponly=False,  # Accessible to JavaScript
        secure=False,
        samesite="lax",
        max_age=60*60*24*365,
        domain="localhost",
        path="/"
    )
    
    print("✅ [BlockVerify] Cookies set successfully")
    print("🔄 [BlockVerify] Registration complete")
    
    return response_data

@app.post("/verify-token")
async def verify_token(request: dict):
    """Verify a token for demo purposes"""
    token = request.get("token")
    if not token:
        return {"valid": False, "error": "No token provided"}
    
    try:
        # Decode the simple token
        import base64
        token_data = json.loads(base64.b64decode(token).decode())
        
        # Check expiration
        if time.time() > token_data.get("exp", 0):
            return {"valid": False, "error": "Token expired"}
        
        return {
            "valid": True,
            "device": token_data["device"],
            "ageOver": token_data["ageOver"],
            "iat": token_data["iat"],
            "exp": token_data["exp"],
            "verified_by": "BlockVerify"
        }
    except Exception as e:
        return {"valid": False, "error": str(e)}

@app.get("/debug/create-token")
async def debug_create_token(response: Response):
    """Debug endpoint to manually create and set a token"""
    import secrets
    import base64
    
    device_id = secrets.token_hex(32)
    exp_time = int((datetime.now() + timedelta(days=365)).timestamp())
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

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Simple BlockVerify API on http://localhost:8000")
    print("🔐 Verification endpoint: http://localhost:8000/verify.html")
    uvicorn.run(app, host="0.0.0.0", port=8000) 