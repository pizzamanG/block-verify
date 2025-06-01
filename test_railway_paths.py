#!/usr/bin/env python3
"""
Test script to verify all paths are correct for Railway deployment
"""

import os
import sys
from pathlib import Path

def check_file(filepath, description):
    """Check if a file exists and report"""
    if Path(filepath).exists():
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description}: {filepath} - NOT FOUND!")
        return False

def main():
    print("🔍 Checking Railway Deployment Files...\n")
    
    all_good = True
    
    # Check critical files
    files_to_check = [
        ("Dockerfile", "Dockerfile in root"),
        ("backend/requirements.txt", "Backend requirements"),
        ("backend/app/main.py", "Main application file"),
        ("backend/app/landing.html", "Landing page"),
        ("issuer_ed25519.jwk", "Issuer key file"),
        ("frontend/", "Frontend directory"),
        ("client_sdk/", "Client SDK directory"),
    ]
    
    for filepath, desc in files_to_check:
        if not check_file(filepath, desc):
            all_good = False
    
    print("\n🔍 Checking Python imports...")
    
    # Test importing the main app
    sys.path.insert(0, ".")
    try:
        import backend.app.main
        print("✅ Can import backend.app.main")
    except Exception as e:
        print(f"❌ Cannot import backend.app.main: {e}")
        all_good = False
    
    print("\n🔍 Checking environment setup...")
    
    # Check what happens with environment variables
    os.environ["PORT"] = "3000"
    port = os.environ.get("PORT", "8000")
    print(f"✅ PORT environment variable test: {port}")
    
    # Test the command that will run
    cmd = f"uvicorn backend.app.main:app --host 0.0.0.0 --port {port}"
    print(f"✅ Command that will run: {cmd}")
    
    print("\n" + "="*50)
    if all_good:
        print("✅ All checks passed! Ready for Railway deployment.")
    else:
        print("❌ Some issues found. Fix them before deploying.")
    
    return all_good

if __name__ == "__main__":
    sys.exit(0 if main() else 1) 