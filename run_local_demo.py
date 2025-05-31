#!/usr/bin/env python3
"""
BlockVerify Local Demo
Run a complete demo locally with SQLite (no PostgreSQL required)
"""

import os
import sys
import uvicorn
import asyncio
import requests
import json
from pathlib import Path

# Set up environment for local demo
os.environ["DATABASE_URL"] = "sqlite:///blockverify_demo.db"
os.environ["ISSUER_KEY_FILE"] = "issuer_ed25519.jwk"
os.environ["ADMIN_USERNAME"] = "admin"
os.environ["ADMIN_PASSWORD"] = "demo123"

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

print("""
🚀 BlockVerify Local Demo
========================

This will start a local instance with:
- SQLite database (no PostgreSQL needed)
- Admin credentials: admin / demo123
- Demo API client created automatically

Starting server...
""")

def create_demo_data():
    """Create demo client after server starts"""
    import time
    time.sleep(3)  # Wait for server to start
    
    try:
        # Register a demo client
        response = requests.post(
            "http://localhost:8000/api/v1/clients/register",
            json={
                "business_name": "Local Demo Company",
                "contact_email": "demo@localhost.com",
                "website_url": "http://localhost:3000"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            api_key = data["api_key"]["key"]
            
            print("\n" + "="*60)
            print("✅ Demo client created successfully!")
            print("="*60)
            print(f"\n📋 DEMO API KEY: {api_key}")
            print("\nSave this key to test the API!")
            print("="*60)
            
            # Test the API
            print("\n🧪 Testing API...")
            test_response = requests.get(
                "http://localhost:8000/api/v1/clients/me",
                headers={"Authorization": f"Bearer {api_key}"}
            )
            
            if test_response.status_code == 200:
                print("✅ API key works! Client info:")
                print(json.dumps(test_response.json(), indent=2))
            
            print("\n📊 Available endpoints:")
            print("- Landing page: http://localhost:8000/")
            print("- Admin dashboard: http://localhost:8000/admin/dashboard")
            print("- API docs: http://localhost:8000/docs")
            print("- Health check: http://localhost:8000/api/v1/health")
            print("\n🔐 Admin login: admin / demo123")
            
    except Exception as e:
        print(f"Note: Demo client might already exist: {e}")

if __name__ == "__main__":
    # Fix imports for SQLite
    os.environ["SQLALCHEMY_SILENCE_UBER_WARNING"] = "1"
    
    # Start demo data creation in background
    from threading import Thread
    demo_thread = Thread(target=create_demo_data)
    demo_thread.daemon = True
    demo_thread.start()
    
    # Run the server
    from backend.app.main import app
    uvicorn.run(app, host="0.0.0.0", port=8000) 