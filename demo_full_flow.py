#!/usr/bin/env python3
"""
BlockVerify Full Demo Flow
Shows the complete user journey and API usage
"""

import requests
import json
import time
import webbrowser
from colorama import Fore, Style, init

# Initialize colorama for colored output
init(autoreset=True)

BASE_URL = "http://localhost:8000"

def print_header(text):
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}{text}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")

def print_success(text):
    print(f"{Fore.GREEN}✅ {text}{Style.RESET_ALL}")

def print_info(text):
    print(f"{Fore.YELLOW}ℹ️  {text}{Style.RESET_ALL}")

def print_error(text):
    print(f"{Fore.RED}❌ {text}{Style.RESET_ALL}")

def pretty_json(data):
    return json.dumps(data, indent=2)

def demo_flow():
    print(f"{Fore.MAGENTA}")
    print("""
    ____  _            _    __     __         _  __       
   | __ )| | ___   ___| | __\ \   / /__ _ __ (_)/ _|_   _ 
   |  _ \| |/ _ \ / __| |/ / \ \ / / _ \ '__| | | |_| | | |
   | |_) | | (_) | (__|   <   \ V /  __/ |  | |  _|| |_| |
   |____/|_|\___/ \___|_|\_\   \_/ \___|_|  |_|_| |  \__, |
                                                      |___/ 
    """)
    print(f"{Style.RESET_ALL}")
    
    print_header("FULL DEMO FLOW")
    
    # Step 1: Check API Health
    print_header("Step 1: Check API Health")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/health")
        if response.status_code == 200:
            print_success("API is healthy!")
            print(pretty_json(response.json()))
        else:
            print_error("API health check failed")
            return
    except Exception as e:
        print_error(f"Cannot connect to API at {BASE_URL}")
        print_info("Make sure the server is running: python run_local_demo.py")
        return

    # Step 2: View Available Plans
    print_header("Step 2: View Available Pricing Plans")
    response = requests.get(f"{BASE_URL}/api/v1/clients/plans")
    if response.status_code == 200:
        print_success("Available plans:")
        plans = response.json()["plans"]
        for plan in plans:
            print(f"\n{Fore.CYAN}{plan['name'].upper()}{Style.RESET_ALL}")
            print(f"  Price: {plan['price_monthly']}")
            print(f"  Verifications: {plan['monthly_verifications']:,}/month")
            print(f"  Rate limit: {plan['rate_limit_per_minute']}/minute")

    # Step 3: Register a New Client
    print_header("Step 3: Register a New Business Client")
    client_data = {
        "business_name": "Demo Adult Site Inc.",
        "contact_email": f"demo{int(time.time())}@example.com",
        "website_url": "https://demo-adult-site.com",
        "plan_type": "free"
    }
    
    print_info(f"Registering: {client_data['business_name']}")
    response = requests.post(f"{BASE_URL}/api/v1/clients/register", json=client_data)
    
    if response.status_code == 200:
        data = response.json()
        api_key = data["api_key"]["key"]
        client_id = data["client"]["id"]
        
        print_success("Client registered successfully!")
        print(f"\n{Fore.YELLOW}🔑 API KEY: {api_key}{Style.RESET_ALL}")
        print(f"{Fore.RED}⚠️  Save this key! You won't see it again!{Style.RESET_ALL}")
        
        # Step 4: Test API Key
        print_header("Step 4: Test API Key Authentication")
        headers = {"Authorization": f"Bearer {api_key}"}
        response = requests.get(f"{BASE_URL}/api/v1/clients/me", headers=headers)
        
        if response.status_code == 200:
            print_success("API key works! Client info:")
            print(pretty_json(response.json()))
        
        # Step 5: Check Usage Stats
        print_header("Step 5: Check Usage Statistics")
        response = requests.get(f"{BASE_URL}/api/v1/clients/usage", headers=headers)
        if response.status_code == 200:
            print_success("Current usage:")
            print(pretty_json(response.json()))
        else:
            print_error(f"Failed to get usage stats: {response.status_code}")
            if response.text:
                print(response.text)
        
        # Step 6: Simulate Token Verification
        print_header("Step 6: Simulate Age Token Verification")
        
        # This would normally be a real JWT token from a user
        fake_token = "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.test"
        
        verify_data = {
            "token": fake_token,
            "min_age": 18
        }
        
        print_info("Attempting to verify age token...")
        response = requests.post(
            f"{BASE_URL}/api/v1/verify-token", 
            json=verify_data,
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            if result["valid"]:
                print_success("Token verified successfully!")
            else:
                print_info(f"Token invalid: {result['message']}")
            print(pretty_json(result))
        elif response.status_code == 429:
            print_error("Rate limit exceeded!")
            if response.text:
                try:
                    print(pretty_json(response.json()))
                except:
                    print(response.text)
        else:
            print_info(f"Token verification returned status {response.status_code}")
            if response.text:
                try:
                    print(pretty_json(response.json()))
                except:
                    print(f"Response: {response.text}")
        
        # Step 7: Create Additional API Key
        print_header("Step 7: Create Additional API Key")
        response = requests.post(
            f"{BASE_URL}/api/v1/clients/api-keys",
            headers=headers,
            params={"name": "Production Key"}
        )
        
        if response.status_code == 200:
            print_success("New API key created!")
            new_key = response.json()["api_key"]["key"]
            print(f"\n{Fore.YELLOW}🔑 NEW KEY: {new_key}{Style.RESET_ALL}")
        
        # Step 8: List All API Keys
        print_header("Step 8: List All API Keys")
        response = requests.get(f"{BASE_URL}/api/v1/clients/api-keys", headers=headers)
        if response.status_code == 200:
            keys = response.json()
            print_success(f"Found {len(keys)} API keys:")
            for key in keys:
                print(f"\n  • {key['name']} ({key['masked_key']})")
                print(f"    Created: {key['created_at']}")
                print(f"    Active: {key['is_active']}")
        
        # Step 9: Admin Dashboard
        print_header("Step 9: Admin Dashboard Access")
        print_info("Admin dashboard URL: http://localhost:8000/admin/dashboard")
        print_info("Username: admin")
        print_info("Password: demo123")
        
        # Step 10: Integration Example
        print_header("Step 10: JavaScript SDK Integration")
        print_info("Add this to your website:")
        print(f"""
{Fore.GREEN}<script src="https://cdn.jsdelivr.net/gh/yourusername/blockverify@main/client_sdk/blockverify.min.js"></script>
<script>
BlockVerify.init({{
    apiKey: '{api_key}',
    minAge: 18,
    onSuccess: (result) => {{
        console.log('User age verified!', result);
        // Allow access to adult content
    }},
    onFailure: (error) => {{
        console.log('Age verification failed', error);
        // Redirect to age-appropriate content
    }}
}});
</script>{Style.RESET_ALL}
        """)
        
    else:
        print_error("Failed to register client")
        print(pretty_json(response.json()))

    print_header("DEMO COMPLETE!")
    print_success("You've seen the complete BlockVerify flow:")
    print("  1. ✅ Client registration")
    print("  2. ✅ API key management")
    print("  3. ✅ Token verification")
    print("  4. ✅ Usage tracking")
    print("  5. ✅ Admin dashboard")
    print("  6. ✅ SDK integration")
    
    print(f"\n{Fore.CYAN}🚀 Ready to deploy to production!{Style.RESET_ALL}")
    print_info("Next step: Push to GitHub and deploy to Railway")

if __name__ == "__main__":
    try:
        demo_flow()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted.")
    except Exception as e:
        print_error(f"Demo error: {e}")
        import traceback
        traceback.print_exc() 