from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
import requests
import time

app = FastAPI(
    title="🔞 Premium Adult Site",
    description="Adult content site with BlockVerify age verification",
    version="1.0.0"
)

@app.get("/", response_class=HTMLResponse)
async def home():
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🔞 PremiumAdultSite.com</title>
    <style>
        /* CRITICAL: Hide content by default - BlockVerify will show it when verified */
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
            color: white; 
            margin: 0; 
            padding: 0;
            /* Don't hide body - let JavaScript control visibility */
        }}
        
        .container {{ 
            max-width: 1200px; 
            margin: 0 auto; 
            padding: 2rem; 
            display: none; /* Hide main content initially */
        }}
        
        .site-header {{ 
            background: linear-gradient(135deg, #ff6b6b 0%, #ff8e8e 100%);
            padding: 2rem; 
            margin-bottom: 2rem; 
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 8px 32px rgba(255, 107, 107, 0.3);
        }}
        
        .content-grid {{ 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); 
            gap: 1.5rem; 
            margin: 2rem 0;
        }}
        
        .content-card {{ 
            background: linear-gradient(135deg, #2a2a2a 0%, #3a3a3a 100%);
            border-radius: 12px; 
            padding: 1.5rem; 
            border: 2px solid #ff6b6b;
            transition: transform 0.3s, box-shadow 0.3s;
        }}
        
        .content-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(255, 107, 107, 0.2);
        }}
        
        .btn {{ 
            background: linear-gradient(135deg, #ff6b6b 0%, #ff5252 100%);
            color: white; 
            border: none; 
            padding: 0.75rem 1.5rem; 
            border-radius: 8px; 
            cursor: pointer;
            font-size: 1rem;
            font-weight: bold;
            transition: background 0.3s;
        }}
        
        .btn:hover {{ 
            background: linear-gradient(135deg, #ff5252 0%, #ff4444 100%);
        }}
        
        .privacy-info {{
            background: #2a2a2a; 
            border-radius: 12px; 
            padding: 2rem; 
            margin-top: 2rem;
            border: 2px solid #4CAF50;
        }}
        
        .privacy-info ul {{
            list-style: none;
            padding: 0;
        }}
        
        .privacy-info li {{
            margin: 0.5rem 0;
            padding: 0.5rem;
            background: #333;
            border-radius: 6px;
            border-left: 3px solid #4CAF50;
        }}
        
        .loading-screen {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-direction: column;
            z-index: 9999;
        }}
        
        .spinner {{
            border: 4px solid #333;
            border-top: 4px solid #ff6b6b;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
            margin-bottom: 2rem;
        }}
        
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
    </style>
</head>
<body>
    <!-- Loading screen shown while verifying age -->
    <div class="loading-screen" id="loadingScreen">
        <div class="spinner"></div>
        <h2>🔐 Checking Age Verification...</h2>
        <p>Please wait while we verify your access</p>
    </div>

    <!-- Main Content (hidden until age verified) -->
    <div class="container">
        <header class="site-header">
            <h1>🔞 PremiumAdultSite.com</h1>
            <p>Welcome to our exclusive adult content platform</p>
        </header>

        <div class="content-grid">
            <div class="content-card">
                <h3>🎬 Premium Videos</h3>
                <p>Access our exclusive collection of adult content with crystal-clear HD quality.</p>
                <button class="btn">Watch Now</button>
            </div>
            
            <div class="content-card">
                <h3>📸 Photo Galleries</h3>
                <p>Browse thousands of high-resolution photos from professional photographers.</p>
                <button class="btn">View Gallery</button>
            </div>
            
            <div class="content-card">
                <h3>💬 Live Chat</h3>
                <p>Connect with performers in real-time through our interactive chat platform.</p>
                <button class="btn">Start Chat</button>
            </div>
            
            <div class="content-card">
                <h3>⭐ VIP Content</h3>
                <p>Unlock exclusive VIP content available only to verified members.</p>
                <button class="btn">Go VIP</button>
            </div>
        </div>

        <div class="privacy-info">
            <h3>🔐 Privacy & Security</h3>
            <p>Your privacy is our priority. This site uses BlockVerify for secure age verification.</p>
            <ul>
                <li>✅ Zero personal data shared with this site</li>
                <li>✅ Device-bound security tokens</li>
                <li>✅ One-time verification across all participating sites</li>
                <li>✅ Full regulatory compliance</li>
            </ul>
        </div>
    </div>

    <!-- BlockVerify Integration - PRODUCTION MODE -->
    <script src="http://localhost:8000/static/at-simple.js"></script>
</body>
</html>
"""

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test connection to BlockVerify API
        response = requests.get("http://localhost:8000/health", timeout=5)
        api_status = "healthy" if response.status_code == 200 else "unhealthy"
    except:
        api_status = "unreachable"
    
    return JSONResponse({
        "status": "healthy",
        "service": "demo-adult-site",
        "blockverify_api": api_status,
        "timestamp": int(time.time())
    })

if __name__ == "__main__":
    import uvicorn
    print("🔞 Starting Demo Adult Site on http://localhost:3000")
    print("🔐 This site demonstrates BlockVerify integration")
    uvicorn.run(app, host="0.0.0.0", port=3000) 