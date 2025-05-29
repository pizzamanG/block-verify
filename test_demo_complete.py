#!/usr/bin/env python3
"""
BlockVerify Complete Demo - Simplified
Run different test scenarios for the age verification system
"""

import subprocess
import webbrowser
import time
import requests
import os
import signal

def kill_existing_processes():
    """Kill any existing processes on our ports"""
    print("🧹 Cleaning up existing processes...")
    try:
        # Kill processes on ports 8000 and 3000
        result = subprocess.run(['lsof', '-ti:8000,3000'], capture_output=True, text=True)
        if result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                try:
                    os.kill(int(pid), signal.SIGKILL)
                    print(f"   Killed process {pid}")
                except:
                    pass
    except:
        pass
    print("✅ Cleanup complete")

def start_api():
    """Start the BlockVerify API"""
    print("🚀 Starting BlockVerify API...")
    return subprocess.Popen(
        ['python', 'simple_api.py'],
        cwd='.',
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

def start_adult_site():
    """Start the demo adult site"""
    print("🔞 Starting demo adult site...")
    return subprocess.Popen(
        ['python', 'app.py'],
        cwd='demo_adult_site',
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

def wait_for_service(url, name, max_attempts=30):
    """Wait for a service to be ready"""
    print(f"⏳ Waiting for {name} to be ready...")
    for i in range(max_attempts):
        try:
            response = requests.get(f"{url}/health", timeout=2)
            if response.status_code == 200:
                print(f"✅ {name} is ready!")
                return True
        except:
            pass
        time.sleep(1)
        print(f"   Attempt {i+1}/{max_attempts}...")
    
    print(f"❌ {name} failed to start")
    return False

def clear_tokens_browser():
    """Open a page that clears all tokens"""
    clear_script = """
    // Clear everything
    localStorage.clear();
    sessionStorage.clear();
    
    // Clear specific tokens
    ['AgeToken', 'AgeTokenAccess'].forEach(key => {
        localStorage.removeItem(key);
        sessionStorage.removeItem(key);
        document.cookie = key + "=;expires=Thu, 01 Jan 1970 00:00:00 UTC;path=/;domain=localhost";
        document.cookie = key + "=;expires=Thu, 01 Jan 1970 00:00:00 UTC;path=/;";
        document.cookie = key + "=;expires=Thu, 01 Jan 1970 00:00:00 UTC;path=/;domain=.localhost";
    });
    
    console.log('✅ All tokens cleared!');
    alert('🗑️ Tokens cleared! You can now test fresh verification.');
    """
    
    data_url = f"data:text/html,<html><head><title>Clear Tokens</title></head><body><h1>🗑️ Clearing Tokens</h1><script>{clear_script}</script></body></html>"
    webbrowser.open(data_url)

def create_token():
    """Create a token directly via API"""
    print("🎫 Creating verification token...")
    try:
        response = requests.post('http://localhost:8000/verify-age', 
                               json={'age_over': 18}, 
                               timeout=10)
        if response.status_code == 200:
            token = response.json().get('token')
            print(f"✅ Token created: {token[:50]}...")
            return token
        else:
            print(f"❌ Failed to create token: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error creating token: {e}")
        return None

def main():
    print("🔐" * 20)
    print("🔐 BLOCKVERIFY DEMO")
    print("🔐" * 20)
    print()
    
    # Kill existing processes
    kill_existing_processes()
    
    # Start services
    api_process = start_api()
    adult_site_process = start_adult_site()
    
    # Wait for services to be ready
    if not wait_for_service("http://localhost:8000", "BlockVerify API"):
        print("❌ API failed to start")
        return
    
    if not wait_for_service("http://localhost:3000", "Demo Adult Site"):
        print("❌ Adult site failed to start")
        return
    
    print("\n✅ All services running!")
    print("\n🎯 Choose your testing scenario:")
    print("1️⃣  Quick Test - Create token directly and visit site")
    print("2️⃣  Full Flow - Complete verification process")
    print("3️⃣  Clear Tokens - Reset everything for fresh testing")
    print("4️⃣  Manual Test - Just open the site and test manually")
    
    choice = input("\nSelect option (1-4): ").strip()
    
    if choice == "1":
        print("\n🎯 QUICK TEST")
        print("=" * 50)
        token = create_token()
        if token:
            # Store token in browser and open site
            store_script = f"""
            localStorage.setItem('AgeToken', '{token}');
            document.cookie = 'AgeTokenAccess={token}; path=/; domain=localhost';
            console.log('✅ Token stored!');
            window.location.href = 'http://localhost:3000';
            """
            data_url = f"data:text/html,<html><head><title>Store Token</title></head><body><h1>📝 Storing Token</h1><script>{store_script}</script></body></html>"
            webbrowser.open(data_url)
            print("✅ Token stored and site opened!")
    
    elif choice == "2":
        print("\n🎯 FULL VERIFICATION FLOW")
        print("=" * 50)
        print("📝 This will test the complete user journey:")
        print("   1. Visit adult site (content hidden)")
        print("   2. Redirect to verification page")
        print("   3. Upload ID document")
        print("   4. Complete device registration")
        print("   5. Return to site with access")
        print()
        clear_tokens_browser()
        time.sleep(2)
        webbrowser.open('http://localhost:3000')
        print("✅ Browser opened! Follow the verification flow.")
    
    elif choice == "3":
        print("\n🎯 CLEAR TOKENS")
        print("=" * 50)
        clear_tokens_browser()
        print("✅ Token clearing page opened!")
    
    elif choice == "4":
        print("\n🎯 MANUAL TEST")
        print("=" * 50)
        webbrowser.open('http://localhost:3000')
        print("✅ Site opened for manual testing!")
    
    else:
        print("❌ Invalid choice")
        return
    
    print("\n📋 Services running at:")
    print("   🔐 BlockVerify API: http://localhost:8000")
    print("   🔞 Demo Adult Site: http://localhost:3000")
    print("\nPress Ctrl+C to stop all services")
    
    try:
        # Keep processes running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping services...")
        api_process.terminate()
        adult_site_process.terminate()
        print("✅ All services stopped")

if __name__ == "__main__":
    main() 