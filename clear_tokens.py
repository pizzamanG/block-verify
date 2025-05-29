#!/usr/bin/env python3
"""
BlockVerify Token Cleaner
Clears all tokens and cookies for demo testing
"""

import webbrowser
import time

def main():
    print("🧹 BlockVerify Token Cleaner")
    print("=" * 50)
    
    # JavaScript to clear all storage
    clear_script = """
    // Clear localStorage
    localStorage.clear();
    
    // Clear sessionStorage
    sessionStorage.clear();
    
    // Clear all cookies
    document.cookie.split(";").forEach(function(c) { 
        document.cookie = c.replace(/^ +/, "").replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/;domain=localhost"); 
        document.cookie = c.replace(/^ +/, "").replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/"); 
    });
    
    // Specifically clear BlockVerify cookies
    document.cookie = "blockverify_token=;expires=Thu, 01 Jan 1970 00:00:00 UTC;path=/;";
    document.cookie = "blockverify_access=;expires=Thu, 01 Jan 1970 00:00:00 UTC;path=/;";
    document.cookie = "age_verified=;expires=Thu, 01 Jan 1970 00:00:00 UTC;path=/;";
    
    alert("✅ All BlockVerify tokens and cookies cleared!\\n\\nYou can now test the verification flow again.");
    
    // Reload the page
    setTimeout(() => window.location.reload(), 1000);
    """
    
    # Create a data URL with the clearing script
    data_url = f"data:text/html,<html><body><h1>Clearing BlockVerify Tokens...</h1><script>{clear_script}</script></body></html>"
    
    print("🌐 Opening browser to clear tokens...")
    print("📝 This will clear all localStorage, sessionStorage, and cookies")
    print("⏳ The page will reload automatically after clearing")
    
    webbrowser.open(data_url)
    
    print("\n✅ Token clearing page opened!")
    print("🔄 After the page reloads, try the verification flow again")
    print("\n💡 You can also run this script anytime to reset the demo")

if __name__ == "__main__":
    main() 