#!/usr/bin/env python3
"""
Minimal test app for Railway deployment debugging
"""

from fastapi import FastAPI
from datetime import datetime
import os

app = FastAPI(
    title="BlockVerify Minimal Test",
    version="1.0.0"
)

@app.get("/")
def root():
    return {
        "service": "BlockVerify Minimal Test",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "port": os.getenv("PORT", "not_set"),
        "working_directory": os.getcwd(),
        "environment": dict(os.environ)
    }

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    print(f"🚀 Starting minimal test app on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port) 