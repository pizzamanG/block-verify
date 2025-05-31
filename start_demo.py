#!/usr/bin/env python3
"""
Simple BlockVerify Demo Starter - No Browser Automation
"""

import subprocess
import time
import os
from dotenv import load_dotenv

def main():
    print("🔐" * 30)
    print("🔐 BLOCKVERIFY SIMPLE DEMO")
    print("🔐" * 30)
    print()
    
    # Load environment
    load_dotenv()
    
    # Kill existing processes
    print("🧹 Cleaning up...")
    os.system("lsof -ti:8000,3000 | xargs kill -9 2>/dev/null || true")
    time.sleep(2)
    
    # Start API
    print("🚀 Starting BlockVerify API...")
    api_process = subprocess.Popen(['python', 'simple_api.py'])
    time.sleep(3)
    
    # Start adult site
    print("🔞 Starting demo adult site...")
    site_process = subprocess.Popen(['python', 'app.py'], cwd='demo_adult_site')
    time.sleep(2)
    
    print("\n✅ Services started!")
    print("\n🌐 Open these URLs manually:")
    print("   🔐 BlockVerify API: http://localhost:8000")
    print("   🔞 Demo Adult Site: http://localhost:3000")
    print("   🔗 Direct Verification: http://localhost:8000/verify.html?return_url=http://localhost:3000")
    print("\n📋 Test Mode 5 (Blockchain):")
    print("   1. Go to: http://localhost:3000")
    print("   2. Click 'Verify My Age'")
    print("   3. Upload any image")
    print("   4. ✅ Check 'Demo Mode 5: Push thumbprint to Polygon Amoy'")
    print("   5. Click 'Register Device Securely'")
    print("   6. Watch for blockchain transaction!")
    print("\n🛑 Press Ctrl+C to stop all services")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping services...")
        api_process.terminate()
        site_process.terminate()
        print("✅ All services stopped")

if __name__ == "__main__":
    main() 