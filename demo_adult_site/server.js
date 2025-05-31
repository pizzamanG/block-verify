const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;
const BLOCKVERIFY_API_URL = process.env.BLOCKVERIFY_API_URL || 'http://localhost:8000';

// Security middleware
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: [
        "'self'", 
        "'unsafe-inline'", 
        "https://cdn.jsdelivr.net",
        "https://unpkg.com",
        BLOCKVERIFY_API_URL
      ],
      styleSrc: ["'self'", "'unsafe-inline'"],
      imgSrc: ["'self'", "data:", "https:"],
      connectSrc: ["'self'", BLOCKVERIFY_API_URL],
      frameSrc: ["'self'"],
      objectSrc: ["'none'"],
      upgradeInsecureRequests: []
    }
  }
}));

app.use(cors());
app.use(express.static('.'));

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'healthy', timestamp: new Date().toISOString() });
});

// Main demo page
app.get('/', (req, res) => {
  res.send(`
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🔞 Adult Demo Site - BlockVerify Protected</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 0;
                padding: 0;
                background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                color: white;
                min-height: 100vh;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
            }
            .container {
                max-width: 800px;
                padding: 40px;
                text-align: center;
                background: rgba(255,255,255,0.1);
                border-radius: 20px;
                backdrop-filter: blur(10px);
                box-shadow: 0 20px 40px rgba(0,0,0,0.3);
                margin: 20px;
            }
            h1 {
                font-size: 3rem;
                margin-bottom: 20px;
                background: linear-gradient(45deg, #ff6b6b, #ee5a24);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }
            .warning {
                background: rgba(255,107,107,0.2);
                border: 2px solid #ff6b6b;
                border-radius: 12px;
                padding: 20px;
                margin: 30px 0;
            }
            .protected-content {
                display: none;
                margin-top: 30px;
                padding: 30px;
                background: rgba(46,204,113,0.2);
                border-radius: 12px;
                border: 2px solid #2ecc71;
            }
            .btn {
                background: linear-gradient(45deg, #2ecc71, #27ae60);
                color: white;
                border: none;
                padding: 15px 30px;
                border-radius: 8px;
                font-size: 18px;
                cursor: pointer;
                margin: 10px;
                transition: transform 0.3s;
            }
            .btn:hover {
                transform: translateY(-2px);
            }
            .status {
                margin: 20px 0;
                padding: 15px;
                border-radius: 8px;
                font-weight: bold;
            }
            .status.success {
                background: rgba(46,204,113,0.2);
                color: #2ecc71;
            }
            .status.error {
                background: rgba(231,76,60,0.2);
                color: #e74c3c;
            }
            .demo-info {
                background: rgba(52,152,219,0.2);
                border: 2px solid #3498db;
                border-radius: 12px;
                padding: 20px;
                margin: 20px 0;
                text-align: left;
            }
            code {
                background: rgba(0,0,0,0.3);
                padding: 2px 6px;
                border-radius: 4px;
                font-family: Monaco, monospace;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔞 Adult Demo Site</h1>
            
            <div class="warning">
                <h3>⚠️ Age Verification Required</h3>
                <p>This is a demonstration adult content site protected by <strong>BlockVerify</strong>.</p>
                <p>You must be 18+ years old to access this content.</p>
            </div>

            <div class="demo-info">
                <h4>🛡️ How BlockVerify Works:</h4>
                <ul>
                    <li><strong>Privacy-First</strong>: No personal data stored on this site</li>
                    <li><strong>One-Time Setup</strong>: Verify once, access everywhere</li>
                    <li><strong>Device-Bound</strong>: Secure, non-transferable tokens</li>
                    <li><strong>Blockchain Verified</strong>: Cryptographically secure</li>
                </ul>
            </div>

            <div id="status" class="status" style="display: none;"></div>

            <button id="testBtn" class="btn" onclick="testVerification()">
                🧪 Test Age Verification
            </button>

            <div id="protectedContent" class="protected-content">
                <h3>✅ Age Verified Successfully!</h3>
                <p>🎉 Congratulations! You have successfully verified your age using BlockVerify.</p>
                <p>This is where age-restricted content would appear on a real adult site.</p>
                
                <div style="margin-top: 20px; text-align: left;">
                    <h4>🔧 For Developers:</h4>
                    <p>Integration was as simple as adding one script tag:</p>
                    <code>&lt;script src="https://cdn.jsdelivr.net/gh/yourusername/blockverify@main/client_sdk/blockverify.min.js"&gt;&lt;/script&gt;</code>
                    
                    <p style="margin-top: 15px;">Then initializing with:</p>
                    <code>BlockVerify.init({ apiKey: 'your_api_key' });</code>
                </div>
            </div>

            <div style="margin-top: 40px; opacity: 0.8;">
                <p>🏠 <strong>Demo Site Status</strong></p>
                <p>API Endpoint: <code>${BLOCKVERIFY_API_URL}</code></p>
                <p>Powered by <a href="https://blockverify.com" style="color: #3498db;">BlockVerify</a></p>
            </div>
        </div>

        <!-- BlockVerify SDK -->
        <script src="https://cdn.jsdelivr.net/gh/yourusername/blockverify@main/client_sdk/blockverify.min.js"></script>
        
        <script>
            // Initialize BlockVerify
            BlockVerify.init({
                apiKey: 'bv_demo_test_key_12345', // Demo API key
                apiUrl: '${BLOCKVERIFY_API_URL}',
                minAge: 18,
                debug: true,
                onSuccess: (result) => {
                    console.log('✅ Age verification successful:', result);
                    showStatus('✅ Age verified successfully! Welcome.', 'success');
                    document.getElementById('protectedContent').style.display = 'block';
                },
                onFailure: (error) => {
                    console.log('❌ Age verification failed:', error);
                    showStatus('❌ Age verification required to access this content.', 'error');
                },
                onCancel: () => {
                    showStatus('⚠️ Age verification was cancelled.', 'error');
                }
            });

            function showStatus(message, type) {
                const status = document.getElementById('status');
                status.textContent = message;
                status.className = 'status ' + type;
                status.style.display = 'block';
            }

            function testVerification() {
                showStatus('🔄 Testing age verification...', 'info');
                
                // Manually trigger verification check
                BlockVerify.checkAge().then(result => {
                    if (result.verified) {
                        showStatus('✅ Test successful! User is verified.', 'success');
                    } else {
                        showStatus('⚠️ Test complete. User needs verification.', 'error');
                    }
                }).catch(error => {
                    showStatus('❌ Test failed: ' + error.message, 'error');
                });
            }

            // Auto-check on page load
            window.addEventListener('load', () => {
                console.log('🚀 BlockVerify Demo Site loaded');
                console.log('📊 SDK Status:', BlockVerify.getStatus ? BlockVerify.getStatus() : 'SDK not ready');
            });
        </script>
    </body>
    </html>
  `);
});

// API routes for demo purposes
app.get('/api/demo-status', (req, res) => {
  res.json({
    status: 'Demo site running',
    blockverify_api: BLOCKVERIFY_API_URL,
    features: [
      'Age verification integration',
      'Privacy-preserving authentication',
      'Device-bound tokens',
      'Blockchain verification'
    ],
    demo_data: {
      total_verifications_today: Math.floor(Math.random() * 1000) + 100,
      success_rate: '98.5%',
      avg_verification_time: '2.3 seconds'
    }
  });
});

app.listen(PORT, () => {
  console.log(`🚀 Demo Adult Site running on port ${PORT}`);
  console.log(`🔗 BlockVerify API: ${BLOCKVERIFY_API_URL}`);
  console.log(`🌐 Demo URL: http://localhost:${PORT}`);
}); 