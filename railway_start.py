#!/usr/bin/env python3
"""
Railway start script for BlockVerify API
Handles PORT environment variable properly
"""
import os
import sys
import subprocess

def main():
    # Get port from environment or default to 8000
    port = os.environ.get('PORT', '8000')
    
    print(f"Starting BlockVerify API on port {port}...")
    
    # Build the uvicorn command
    cmd = [
        "uvicorn",
        "backend.app.main:app",
        "--host", "0.0.0.0",
        "--port", port
    ]
    
    # Execute uvicorn
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 