from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import requests
import os

app = FastAPI(title="Test Adult Site")

# Mock adult site content
@app.get("/", response_class=HTMLResponse)
async def home():
    return """
<!DOCTYPE html>
<html>
<head>
    <title>🔞 Adult Content Site (TEST)</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            background: #1a1a1a; 
            color: white; 
            margin: 0; 
            padding: 0;
        }
        .container { max-width: 1200px; margin: 0 auto; padding: 2rem; }
        .header { 
            background: #333; 
            padding: 1rem; 
            margin-bottom: 2rem; 
            border-radius: 8px;
        }
        .content-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); 
            gap: 1rem; 
        }
        .content-card { 
            background: #2a2a2a; 
            border-radius: 8px; 
            padding: 1rem; 
            border: 2px solid #ff6b6b;
        }
        .flow-explanation {
            background: #2a2a2a; 
            border-radius: 8px; 
            padding: 1.5rem; 
            margin-bottom: 2rem;
            border-left: 4px solid #4CAF50;
        }
        .step { 
            margin: 0.5rem 0; 
            padding: 0.5rem; 
            background: #333; 
            border-radius: 4px; 
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔞 Premium Adult Content Site</h1>
            <p>✅ Age verified via BlockVerify - Welcome!</p>
            <p><strong>Zero personal data shared</strong> | Device-bound token | Works across all sites</p>
        </div>

        <div class="flow-explanation">
            <h3>🎯 What Just Happened (The Magic!):</h3>
            <div class="step">1️⃣ You visited this adult site</div>
            <div class="step">2️⃣ BlockVerify checked for your age token</div>
            <div class="step">3️⃣ Either you had one (instant access) OR got redirected to verify</div>
            <div class="step">4️⃣ If redirected: you did KYC + WebAuthn ONCE</div>
            <div class="step">5️⃣ Now this token works on ALL participating adult sites!</div>
            <div class="step">🔐 Your device's secure enclave prevents token sharing</div>
        </div>
        
        <div class="content-grid">
            <div class="content-card">
                <h3>🎬 Premium Videos</h3>
                <p>Access to exclusive content</p>
                <button style="background: #ff6b6b; color: white; border: none; padding: 0.5rem 1rem; border-radius: 4px;" onclick="alert('🎉 You have access! (This is just a demo)')">
                    Watch Now
                </button>
            </div>
            <div class="content-card">
                <h3>📸 Photo Galleries</h3>
                <p>High-quality image collections</p>
                <button style="background: #ff6b6b; color: white; border: none; padding: 0.5rem 1rem; border-radius: 4px;" onclick="alert('🎉 You have access! (This is just a demo)')">
                    View Gallery
                </button>
            </div>
            <div class="content-card">
                <h3>💬 Adult Chat</h3>
                <p>Connect with verified adults</p>
                <button style="background: #ff6b6b; color: white; border: none; padding: 0.5rem 1rem; border-radius: 4px;" onclick="alert('🎉 You have access! (This is just a demo)')">
                    Join Chat
                </button>
            </div>
        </div>

        <div style="margin-top: 2rem; padding: 1rem; background: #2a2a2a; border-radius: 8px;">
            <h3>🔐 How BlockVerify Protected Your Privacy:</h3>
            <ul>
                <li>✅ No personal data was shared with this site</li>
                <li>✅ Your identity remains anonymous</li>
                <li>✅ Token is bound to your device's secure enclave</li>
                <li>✅ One verification works across all participating sites</li>
                <li>✅ This site pays BlockVerify per verification (not you!)</li>
            </ul>
            
            <h4>🧪 Test Features:</h4>
            <button onclick="testToken()" style="background: #4CAF50; color: white; border: none; padding: 0.5rem 1rem; border-radius: 4px; margin: 0.5rem;">
                Test Your Token
            </button>
            <button onclick="clearToken()" style="background: #f44336; color: white; border: none; padding: 0.5rem 1rem; border-radius: 4px; margin: 0.5rem;">
                Clear Token (Test Flow)
            </button>
            
            <p><small>Powered by BlockVerify - Privacy-preserving age verification</small></p>
        </div>
    </div>

    <!-- BlockVerify Simple Integration (literally just this script tag!) -->
    <script src="http://localhost:8000/static/at-simple.js"></script>
            
    <script>
        function testToken() {
            const token = window.BlockVerify.getToken();
            if (token) {
                const [,payload] = token.split('.');
                const data = JSON.parse(atob(payload));
                alert(`Token Info:\nAge Over: ${data.ageOver}\nDevice: ${data.device.substring(0,10)}...\nExpires: ${new Date(data.exp * 1000).toLocaleDateString()}`);
            } else {
                alert('No token found!');
            }
        }
        
        function clearToken() {
            localStorage.removeItem('AgeToken');
            document.cookie = 'AgeToken=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/';
            alert('Token cleared! Refresh the page to test the verification flow.');
        }
    </script>
</body>
</html>
    """

@app.get("/test-api-verification")
async def test_api_verification(token: str):
    """Test server-side token verification"""
    try:
        # Call your BlockVerify API
        response = requests.post(
            'http://localhost:8000/verify-token',
            headers={
                'X-API-Key': 'demo_key_for_testing',
                'Content-Type': 'application/json'
            },
            json={'token': token}
        )
        
        if response.status_code == 200:
            return {"status": "verified", "data": response.json()}
        else:
            return {"status": "failed", "error": response.text}
            
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000) 