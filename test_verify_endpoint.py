#!/usr/bin/env python3
"""Test the verify endpoint directly"""

import requests
import json
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

def test_verify():
    # First, let's create a valid token using the token module
    from backend.app.token import mint
    
    # Create a test token
    test_device_hash = "test_device_123"
    token = mint(test_device_hash)
    print(f"Created test token: {token[:50]}...")
    
    # Now test the endpoint
    api_key = input("Enter your API key (from the demo): ")
    
    response = requests.post(
        "http://localhost:8000/api/v1/verify-token",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json={
            "token": token,
            "min_age": 18
        }
    )
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"Response Text: {response.text}")
    
    if response.status_code == 200:
        print("\nParsed JSON:")
        print(json.dumps(response.json(), indent=2))

if __name__ == "__main__":
    test_verify() 