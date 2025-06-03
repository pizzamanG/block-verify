#!/usr/bin/env python3
"""
Minimal BlockVerify B2B Portal - Guaranteed to start
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import os

app = FastAPI(title="BlockVerify B2B Portal Minimal")

@app.get("/")
def home():
    return {"service": "BlockVerify B2B Portal", "status": "running", "version": "minimal"}

@app.get("/health")
def health():
    return {"status": "healthy", "service": "blockverify-b2b-portal"}

@app.get("/register", response_class=HTMLResponse)
def register():
    return """
    <html>
    <head><title>BlockVerify B2B - Register</title></head>
    <body>
        <h1>🔐 BlockVerify B2B Portal</h1>
        <h2>Coming Soon!</h2>
        <p>Full portal is being deployed...</p>
        <p>Health check: <a href="/health">/health</a></p>
    </body>
    </html>
    """

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    print(f"🚀 Starting minimal B2B portal on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port) 