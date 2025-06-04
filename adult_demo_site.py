#!/usr/bin/env python3
"""
Standalone Adult Demo Site
For testing BlockVerify integration end-to-end
"""

import os
import requests
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="Adult Demo Site", version="1.0.0")

# Your real API key - in production, store this as an environment variable
BLOCKVERIFY_API_KEY = "bv_prod_wuz0o51nqHDGgMuhqf4ZbEXeEJmNlDX94qYSyOKOu48"
BLOCKVERIFY_API_URL = "https://blockverify-api-production.up.railway.app"

class TokenVerifyRequest(BaseModel):
    token: str

@app.get("/")
async def home():
    """Adult demo site homepage"""
    return {"message": "Adult Demo Site", "status": "running"}

@app.post("/api/verify-token")
async def verify_token(request: TokenVerifyRequest):
    """Server-side token verification using real BlockVerify API"""
    try:
        # Call BlockVerify API to verify the token
        response = requests.post(
            f"{BLOCKVERIFY_API_URL}/api/v1/verify-token",
            headers={
                "Authorization": f"Bearer {BLOCKVERIFY_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "token": request.token,
                "min_age": 18
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "valid": True,
                "verified": data.get("verified", False),
                "age_verified": data.get("age_verified", False),
                "details": data
            }
        else:
            return {
                "valid": False,
                "error": f"API returned {response.status_code}",
                "details": response.text[:200]
            }
            
    except requests.RequestException as e:
        return {
            "valid": False,
            "error": f"Request failed: {str(e)}",
            "details": None
        }

@app.get("/site", response_class=HTMLResponse)
async def adult_site(verified: str = Query(None)):
    """The actual adult demo site"""
    
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🔞 PremiumAdultSite.com - BlockVerify Protected</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 0;
                padding: 0;
                background: #1a1a1a;
                color: white;
                min-height: 100vh;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                padding: 40px 20px;
            }}
            .header {{
                text-align: center;
                margin-bottom: 40px;
                padding: 40px;
                background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
                border-radius: 12px;
            }}
            .content-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin: 40px 0;
            }}
            .content-card {{
                background: rgba(255,255,255,0.1);
                padding: 30px;
                border-radius: 12px;
                text-align: center;
                transition: transform 0.3s;
            }}
            .content-card:hover {{
                transform: translateY(-5px);
            }}
            .btn {{
                background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
                color: white;
                border: none;
                padding: 15px 30px;
                border-radius: 8px;
                cursor: pointer;
                font-size: 16px;
                font-weight: 500;
                transition: all 0.3s;
            }}
            .btn:hover {{
                background: linear-gradient(135deg, #ff5252 0%, #e55100 100%);
                transform: translateY(-2px);
            }}
            .privacy-info {{
                background: rgba(76,175,80,0.1);
                border: 2px solid #4CAF50;
                padding: 30px;
                border-radius: 12px;
                margin: 40px 0;
            }}
            .age-gate {{
                background: rgba(255,107,107,0.1);
                border: 2px solid #ff6b6b;
                padding: 60px;
                border-radius: 12px;
                text-align: center;
                margin: 40px 0;
            }}
            .loading {{
                display: none;
                text-align: center;
                padding: 40px;
                background: rgba(33,150,243,0.1);
                border-radius: 12px;
                margin: 20px 0;
            }}
            .spinner {{
                border: 4px solid #f3f3f3;
                border-top: 4px solid #2196F3;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 0 auto 20px;
            }}
            @keyframes spin {{
                0% {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
            }}
            .verification-status {{
                position: fixed;
                bottom: 20px;
                right: 20px;
                padding: 15px 20px;
                border-radius: 8px;
                color: white;
                font-weight: 500;
                z-index: 1000;
            }}
            .status-verified {{
                background: #4CAF50;
            }}
            .status-pending {{
                background: #ff9800;
            }}
            .status-error {{
                background: #f44336;
            }}
            .dev-info {{
                background: rgba(33,150,243,0.1);
                border: 1px solid #2196F3;
                padding: 20px;
                border-radius: 8px;
                margin: 20px 0;
                font-family: monospace;
                font-size: 14px;
            }}
            .redirect-splash {{
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                display: none;
                align-items: center;
                justify-content: center;
                z-index: 10000;
                flex-direction: column;
            }}
            .splash-content {{
                text-align: center;
                padding: 60px 40px;
                background: rgba(255,255,255,0.1);
                border-radius: 20px;
                backdrop-filter: blur(10px);
            }}
            .countdown {{
                font-size: 48px;
                font-weight: bold;
                color: #fff;
                margin: 20px 0;
            }}
        </style>
    </head>
    <body>
        <!-- Redirect Splash Screen -->
        <div id="redirectSplash" class="redirect-splash">
            <div class="splash-content">
                <h1>🔐 Redirecting to BlockVerify</h1>
                <p style="font-size: 18px; opacity: 0.9;">You'll be redirected to verify your age securely</p>
                <div class="countdown" id="countdown">3</div>
                <p style="opacity: 0.7;">This ensures privacy - no personal info shared with this site</p>
                <button onclick="cancelRedirect()" style="background: rgba(255,255,255,0.2); color: white; border: 1px solid rgba(255,255,255,0.3); padding: 10px 20px; border-radius: 6px; cursor: pointer; margin-top: 20px;">
                    Cancel
                </button>
            </div>
        </div>

        <div class="container">
            <div class="header">
                <h1>🔞 PremiumAdultSite.com</h1>
                <p>The finest adult entertainment platform</p>
                <p><small>🔐 Protected by BlockVerify Age Verification</small></p>
            </div>

            <!-- Loading Screen -->
            <div id="loadingScreen" class="loading">
                <div class="spinner"></div>
                <h3>🔐 Verifying Age Token...</h3>
                <p>Please wait while we validate your credentials with BlockVerify...</p>
                <div class="dev-info" style="margin-top: 20px;">
                    <p><strong>🔧 Real API Integration:</strong> Using production BlockVerify API</p>
                    <p><strong>API Key:</strong> {BLOCKVERIFY_API_KEY[:20]}... (production)</p>
                    <p><strong>Endpoint:</strong> {BLOCKVERIFY_API_URL}/api/v1/verify-token</p>
                </div>
            </div>

            <!-- Age Gate -->
            <div id="ageGate" style="display: none;">
                <h2>⚠️ Age Verification Required</h2>
                <p style="font-size: 18px; margin: 20px 0;">
                    You must be 18+ years old to access this premium adult content
                </p>
                <p style="color: #ccc;">
                    This site uses BlockVerify for secure, privacy-preserving age verification
                </p>
                <button class="btn" onclick="startVerification()" style="font-size: 18px; padding: 20px 40px;">
                    🔐 Verify My Age (18+)
                </button>
                
                <div class="dev-info" style="margin-top: 40px;">
                    <h4>🔧 For Developers:</h4>
                    <p><strong>Integration Method:</strong> BlockVerify JavaScript SDK + Real API</p>
                    <p><strong>API Endpoint:</strong> {BLOCKVERIFY_API_URL}</p>
                    <p><strong>Verification Flow:</strong> User redirects → BlockVerify → Returns with token → Server validates</p>
                    <p><strong>API Key:</strong> {BLOCKVERIFY_API_KEY[:20]}... (production)</p>
                </div>
            </div>

            <!-- Premium Content (shown after verification) -->
            <div id="premiumContent" style="display: none;">
                <div class="privacy-info">
                    <h3>✅ Age Verified Successfully!</h3>
                    <p>🎉 Welcome! You have been verified as 18+ by BlockVerify.</p>
                    <p><strong>Privacy Note:</strong> No personal information was shared with this site during verification.</p>
                </div>

                <div class="content-grid">
                    <div class="content-card">
                        <h3>🎬 Premium Videos</h3>
                        <p>Access our exclusive collection of adult content with crystal-clear 4K quality.</p>
                        <button class="btn">Watch Now</button>
                    </div>
                    
                    <div class="content-card">
                        <h3>📸 Photo Galleries</h3>
                        <p>Browse thousands of high-resolution photos from professional photographers.</p>
                        <button class="btn">View Gallery</button>
                    </div>
                    
                    <div class="content-card">
                        <h3>💬 Live Chat</h3>
                        <p>Connect with performers in real-time through our interactive platform.</p>
                        <button class="btn">Start Chat</button>
                    </div>
                    
                    <div class="content-card">
                        <h3>⭐ VIP Content</h3>
                        <p>Unlock exclusive VIP content available only to verified premium members.</p>
                        <button class="btn">Go VIP</button>
                    </div>
                    
                    <div class="content-card">
                        <h3>🔞 Live Shows</h3>
                        <p>Experience live adult entertainment with interactive features.</p>
                        <button class="btn">Watch Live</button>
                    </div>
                    
                    <div class="content-card">
                        <h3>📱 Mobile App</h3>
                        <p>Download our mobile app for premium content on the go.</p>
                        <button class="btn">Download</button>
                    </div>
                </div>

                <div class="dev-info">
                    <h4>✅ Integration Success!</h4>
                    <p><strong>User Token:</strong> <span id="userToken">Loading...</span></p>
                    <p><strong>Verification Status:</strong> <span style="color: #4CAF50;" id="verificationStatus">VALID ADULT (18+)</span></p>
                    <p><strong>Last Verified:</strong> <span id="verificationTime"></span></p>
                    <p><strong>API Response:</strong> <span id="apiResponse" style="color: #4CAF50;">SUCCESS</span></p>
                    <button onclick="clearVerification()" style="background: #f44336; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; margin-top: 10px;">
                        🗑️ Clear Verification (Test Again)
                    </button>
                </div>
            </div>
        </div>

        <!-- BlockVerify SDK Integration -->
        <script>
            // Configuration with your real API key
            const BLOCKVERIFY_CONFIG = {{
                apiUrl: '{BLOCKVERIFY_API_URL}',
                verifyUrl: '{BLOCKVERIFY_API_URL}/verify',
                returnUrl: window.location.origin + '/site',
                localVerifyUrl: '/api/verify-token',
                debug: true
            }};

            // BlockVerify SDK with real API integration
            class BlockVerifySDK {{
                constructor(config) {{
                    this.config = config;
                    this.redirectTimer = null;
                    this.log('🔐 BlockVerify SDK initialized with real API');
                }}

                log(message, data = '') {{
                    if (this.config.debug) {{
                        console.log(`[BlockVerify] ${{message}}`, data);
                    }}
                }}

                // Check if user has a valid age verification token
                async checkAgeVerification() {{
                    this.log('🔍 Checking age verification...');
                    
                    // Check URL for verification callback
                    const urlParams = new URLSearchParams(window.location.search);
                    if (urlParams.get('verified') === 'true') {{
                        this.log('🔄 User returned from verification');
                        
                        // Get token from URL parameter if available
                        const urlToken = urlParams.get('token');
                        if (urlToken) {{
                            this.log('💾 Storing token from URL:', urlToken.substring(0, 20) + '...');
                            localStorage.setItem('AgeToken', urlToken);
                        }}
                        
                        // Small delay to allow token to be processed
                        setTimeout(() => this.validateToken(), 1000);
                        return;
                    }}

                    // Check for existing token
                    const token = this.getStoredToken();
                    if (token) {{
                        this.log('🎫 Found stored token, validating with API...');
                        await this.validateToken();
                    }} else {{
                        this.log('❌ No token found, showing age gate');
                        this.showAgeGate();
                    }}
                }}

                getStoredToken() {{
                    // Try multiple storage locations
                    return localStorage.getItem('AgeToken') ||
                           this.getCookie('AgeToken') ||
                           sessionStorage.getItem('AgeToken');
                }}

                getCookie(name) {{
                    const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
                    return match ? match[2] : null;
                }}

                async validateToken() {{
                    const token = this.getStoredToken();
                    if (!token) {{
                        this.showAgeGate();
                        return;
                    }}

                    this.log('🔍 Validating token with server API...');
                    
                    try {{
                        const response = await fetch(this.config.localVerifyUrl, {{
                            method: 'POST',
                            headers: {{
                                'Content-Type': 'application/json'
                            }},
                            body: JSON.stringify({{ token: token }})
                        }});

                        const result = await response.json();
                        this.log('📝 API Response:', result);

                        if (result.valid && result.verified) {{
                            this.log('✅ Token validation successful');
                            this.showPremiumContent(token, result);
                        }} else {{
                            this.log('❌ Token validation failed:', result.error);
                            this.showStatus(`Verification failed: ${{result.error || 'Invalid token'}}`, 'error');
                            this.showAgeGate();
                        }}
                    }} catch (error) {{
                        this.log('❌ API call failed:', error);
                        this.showStatus('API verification failed', 'error');
                        this.showAgeGate();
                    }}
                }}

                showLoadingScreen() {{
                    document.getElementById('loadingScreen').style.display = 'block';
                    document.getElementById('ageGate').style.display = 'none';
                    document.getElementById('premiumContent').style.display = 'none';
                }}

                showAgeGate() {{
                    document.getElementById('loadingScreen').style.display = 'none';
                    document.getElementById('ageGate').style.display = 'block';
                    document.getElementById('premiumContent').style.display = 'none';
                    
                    this.showStatus('Age verification required', 'pending');
                }}

                showPremiumContent(token, apiResult) {{
                    document.getElementById('loadingScreen').style.display = 'none';
                    document.getElementById('ageGate').style.display = 'none';
                    document.getElementById('premiumContent').style.display = 'block';
                    
                    // Update token display
                    document.getElementById('userToken').textContent = token.substring(0, 30) + '...';
                    document.getElementById('verificationTime').textContent = new Date().toLocaleString();
                    document.getElementById('verificationStatus').textContent = 
                        apiResult.age_verified ? 'VALID ADULT (18+)' : 'VERIFIED USER';
                    document.getElementById('apiResponse').textContent = 
                        `SUCCESS - Age: ${{apiResult.age_verified ? '18+' : 'Unknown'}}`;
                    
                    this.showStatus('Age verified (18+)', 'verified');
                    this.log('🎉 Premium content unlocked');
                }}

                showStatus(message, type) {{
                    // Remove existing status
                    const existing = document.querySelector('.verification-status');
                    if (existing) existing.remove();

                    // Add new status
                    const status = document.createElement('div');
                    status.className = `verification-status status-${{type}}`;
                    status.textContent = message;
                    document.body.appendChild(status);

                    // Auto-remove after 5 seconds
                    setTimeout(() => {{
                        if (status.parentNode) status.remove();
                    }}, 5000);
                }}

                showRedirectSplash() {{
                    const splash = document.getElementById('redirectSplash');
                    splash.style.display = 'flex';
                    
                    let countdown = 3;
                    const countdownEl = document.getElementById('countdown');
                    
                    this.redirectTimer = setInterval(() => {{
                        countdown--;
                        countdownEl.textContent = countdown;
                        
                        if (countdown <= 0) {{
                            this.executeRedirect();
                        }}
                    }}, 1000);
                }}

                executeRedirect() {{
                    const verifyUrl = `${{this.config.verifyUrl}}?return_url=${{encodeURIComponent(this.config.returnUrl)}}`;
                    this.log('🔄 Redirecting to:', verifyUrl);
                    window.location.href = verifyUrl;
                }}

                startVerification() {{
                    this.log('🚀 Starting verification process with splash screen...');
                    this.showRedirectSplash();
                }}

                clearVerification() {{
                    this.log('🗑️ Clearing verification data...');
                    localStorage.removeItem('AgeToken');
                    sessionStorage.removeItem('AgeToken');
                    document.cookie = 'AgeToken=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
                    
                    // Refresh page
                    window.location.href = this.config.returnUrl;
                }}
            }}

            // Initialize SDK when page loads
            document.addEventListener('DOMContentLoaded', function() {{
                window.blockVerify = new BlockVerifySDK(BLOCKVERIFY_CONFIG);
                
                // Show loading screen initially
                window.blockVerify.showLoadingScreen();
                
                // Start verification check after a brief delay
                setTimeout(() => {{
                    window.blockVerify.checkAgeVerification();
                }}, 1000);
            }});

            // Global functions for UI
            function startVerification() {{
                window.blockVerify.startVerification();
            }}

            function clearVerification() {{
                if (confirm('This will clear your verification and require you to verify again. Continue?')) {{
                    window.blockVerify.clearVerification();
                }}
            }}

            function cancelRedirect() {{
                if (window.blockVerify.redirectTimer) {{
                    clearInterval(window.blockVerify.redirectTimer);
                }}
                document.getElementById('redirectSplash').style.display = 'none';
            }}

            // URL parameter check for verification callback
            const urlParams = new URLSearchParams(window.location.search);
            if (urlParams.get('verified') === 'true') {{
                console.log('🔄 [BlockVerify] Verification callback detected');
            }}
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port) 