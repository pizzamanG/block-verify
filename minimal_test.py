#!/usr/bin/env python3
"""
Minimal test app for Railway deployment debugging
"""

from fastapi import FastAPI
from datetime import datetime
import os
import sys

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
        "python_version": sys.version,
        "environment_vars": {
            "PORT": os.getenv("PORT"),
            "PYTHONPATH": os.getenv("PYTHONPATH"),
            "RAILWAY_ENVIRONMENT": os.getenv("RAILWAY_ENVIRONMENT"),
        }
    }

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "port": os.getenv("PORT", "8000"),
        "message": "Railway health check working!"
    }

@app.get("/debug")
def debug():
    """Debug endpoint to see what's happening"""
    return {
        "all_env_vars": dict(os.environ),
        "sys_path": sys.path,
        "working_dir": os.getcwd(),
        "files_in_dir": os.listdir(".") if os.path.exists(".") else "no_dir"
    }

if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment with fallback
    port_str = os.getenv("PORT", "8000")
    try:
        port = int(port_str)
    except ValueError:
        print(f"❌ Invalid PORT value: {port_str}, using 8000")
        port = 8000
    
    print(f"🚀 Starting minimal test app")
    print(f"📍 Port: {port} (from PORT env: {os.getenv('PORT')})")
    print(f"📁 Working directory: {os.getcwd()}")
    print(f"🐍 Python: {sys.version}")
    
    # Start the server
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port,
        log_level="info"
    ) 