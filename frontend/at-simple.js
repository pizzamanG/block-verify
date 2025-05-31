/**
 * BlockVerify - Simple Integration
 * No-cache, no-hang, just works
 */

(function() {
    'use strict';
    
    const BLOCKVERIFY_API = 'http://localhost:8000';
    const DEBUG = true;
    
    // Simple device detection
    const DEVICE_INFO = {
        isMobile: /iPhone|iPad|iPod|Android/i.test(navigator.userAgent),
        userAgent: navigator.userAgent
    };
    
    function log(msg, data = null) {
        if (DEBUG) {
            console.log(`[BlockVerify] ${msg}`, data || '');
        }
    }
    
    function getToken() {
        log('🔍 Checking for age token...');
        
        // Check if returning from verification
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('verified') === 'true') {
            log('🔄 User returned from verification');
        }
        
        // Try cookie first
        const cookieToken = document.cookie
            .split('; ')
            .find(row => row.startsWith('AgeToken='))
            ?.split('=')[1];
            
        // Try accessible cookie
        const accessToken = document.cookie
            .split('; ')
            .find(row => row.startsWith('AgeTokenAccess='))
            ?.split('=')[1];
            
        // Try localStorage
        const localToken = localStorage.getItem('AgeToken');
        
        // Debug all storage locations
        log('🔍 [DEBUG] Storage check:', {
            cookieToken: cookieToken ? cookieToken.substring(0, 20) + '...' : 'NONE',
            accessToken: accessToken ? accessToken.substring(0, 20) + '...' : 'NONE', 
            localToken: localToken ? localToken.substring(0, 20) + '...' : 'NONE',
            allCookies: document.cookie,
            localStorage: localStorage.length + ' items'
        });
        
        const token = cookieToken || accessToken || localToken;
        
        if (token) {
            log('✅ Token found', { 
                source: cookieToken ? 'cookie' : accessToken ? 'accessCookie' : 'localStorage',
                length: token.length 
            });
            // Store in localStorage if not there
            if (!localToken && token) {
                localStorage.setItem('AgeToken', token);
                log('💾 Synced token to localStorage');
            }
        } else {
            log('❌ No token found in any location');
        }
        
        return token;
    }
    
    function decodeToken(token) {
        try {
            log('🔓 Decoding JWT token...');
            log('🔍 Raw token length:', token.length);
            log('🔍 First 50 chars:', token.substring(0, 50));
            log('🔍 Last 50 chars:', token.substring(token.length - 50));
            
            // Check if it's a JWT (has 3 parts separated by dots)
            const parts = token.split('.');
            log('🔍 Token parts count:', parts.length);
            
            if (parts.length === 3) {
                // It's a JWT - decode the payload (middle part)
                let payload = parts[1];
                log('🔍 Raw payload:', payload);
                log('🔍 Raw payload length:', payload.length);
                
                // Convert base64url to base64 (JWT uses base64url encoding)
                payload = payload.replace(/-/g, '+').replace(/_/g, '/');
                log('🔍 After base64url conversion:', payload);
                
                // Add padding if needed for base64 decoding
                const paddedPayload = payload + '='.repeat((4 - payload.length % 4) % 4);
                log('🔍 After padding:', paddedPayload);
                log('🔍 Padded length:', paddedPayload.length);
                
                // Check for invalid characters
                const validBase64 = /^[A-Za-z0-9+/=]*$/.test(paddedPayload);
                log('🔍 Valid base64 format:', validBase64);
                
                if (!validBase64) {
                    log('❌ Invalid base64 characters detected');
                    log('🔍 Invalid chars:', paddedPayload.match(/[^A-Za-z0-9+/=]/g));
                    return null;
                }
                
                const decoded = JSON.parse(atob(paddedPayload));
                
                log('✅ JWT token decoded', {
                    age_over: decoded.age_over,
                    expires: new Date(decoded.exp * 1000).toLocaleString(),
                    issuer: decoded.iss
                });
                
                // Convert JWT format to legacy format for compatibility
                return {
                    ageOver: decoded.age_over,
                    exp: decoded.exp,
                    iat: decoded.iat,
                    device: decoded.sub, // Subject is the device ID in our JWT
                    iss: decoded.iss,
                    aud: decoded.aud
                };
            } else {
                // Legacy base64 format
                log('🔓 Decoding legacy base64 token...');
                const decoded = JSON.parse(atob(token));
                log('✅ Legacy token decoded', {
                    ageOver: decoded.ageOver,
                    expires: new Date(decoded.exp * 1000).toLocaleString()
                });
                return decoded;
            }
        } catch (e) {
            log('❌ Token decode failed:', e.name, e.message);
            log('🔍 Error details:', e.stack);
            log('🔍 Token that failed:', token);
            return null;
        }
    }
    
    function isTokenExpired(tokenData) {
        const isExpired = Date.now() / 1000 > tokenData.exp;
        log(`⏰ Token ${isExpired ? 'EXPIRED' : 'VALID'}`);
        return isExpired;
    }
    
    function startVerification() {
        log('🚀 Starting verification...');
        
        // Show loading
        const barrier = document.getElementById('blockverify-barrier');
        if (barrier) {
            barrier.innerHTML = `
                <div style="text-align: center; color: white;">
                    <div style="
                        border: 4px solid #333;
                        border-top: 4px solid #4CAF50;
                        border-radius: 50%;
                        width: 60px;
                        height: 60px;
                        animation: spin 1s linear infinite;
                        margin: 0 auto 2rem auto;
                    "></div>
                    <h2>🔐 Redirecting to verification...</h2>
                    <p>Please wait</p>
                </div>
                <style>
                    @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
                </style>
            `;
        }
        
        // Redirect after short delay
        setTimeout(() => {
            const returnUrl = encodeURIComponent(window.location.href);
            const verifyUrl = `${BLOCKVERIFY_API}/verify.html?return_url=${returnUrl}`;
            log('➡️ Redirecting to', verifyUrl);
            window.location.href = verifyUrl;
        }, 1500);
    }
    
    function showContent() {
        log('🎉 Showing content...');
        
        // Hide loading screen
        const loadingScreen = document.getElementById('loadingScreen');
        if (loadingScreen) {
            loadingScreen.style.display = 'none';
        }
        
        // Remove barrier
        const barrier = document.getElementById('blockverify-barrier');
        if (barrier) {
            barrier.remove();
        }
        
        // Show main content container
        const container = document.querySelector('.container');
        if (container) {
            container.style.display = 'block';
        }
        
        // Show success badge
        const badge = document.createElement('div');
        badge.innerHTML = '✅ Age Verified';
        badge.style.cssText = `
            position: fixed; 
            bottom: 20px; 
            right: 20px; 
            background: #4CAF50; 
            color: white; 
            padding: 10px 15px; 
            border-radius: 5px; 
            font-size: 14px; 
            z-index: 10000;
            box-shadow: 0 2px 10px rgba(0,0,0,0.3);
        `;
        document.body.appendChild(badge);
        
        // Remove badge after 3 seconds
        setTimeout(() => {
            if (badge.parentNode) {
                badge.remove();
            }
        }, 3000);
    }
    
    function showVerificationPrompt() {
        log('📋 Showing verification prompt');
        
        // Hide loading screen
        const loadingScreen = document.getElementById('loadingScreen');
        if (loadingScreen) {
            loadingScreen.style.display = 'none';
        }
        
        // Hide main content container
        const container = document.querySelector('.container');
        if (container) {
            container.style.display = 'none';
        }
        
        // Create barrier
        const barrier = document.createElement('div');
        barrier.id = 'blockverify-barrier';
        barrier.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
            color: white;
            font-family: Arial, sans-serif;
            z-index: 999999;
            display: flex;
            align-items: center;
            justify-content: center;
        `;
        
        barrier.innerHTML = `
            <div style="
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 3rem;
                border-radius: 15px;
                text-align: center;
                max-width: 500px;
                margin: 2rem;
                box-shadow: 0 15px 50px rgba(0,0,0,0.5);
            ">
                <h1 style="margin: 0 0 1rem 0; font-size: 3rem;">🔞</h1>
                <h2 style="margin: 0 0 1rem 0;">Age Verification Required</h2>
                <p style="font-size: 1.1rem; margin: 0 0 2rem 0;">
                    You must be 18+ to access this content
                </p>
                
                <div style="margin: 2rem 0;">
                    <button onclick="window.BlockVerify.startVerification()" style="
                        background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
                        color: white;
                        border: none;
                        padding: 1rem 2rem;
                        border-radius: 8px;
                        cursor: pointer;
                        font-size: 1.2rem;
                        font-weight: bold;
                        margin: 0.5rem;
                        box-shadow: 0 5px 15px rgba(76, 175, 80, 0.3);
                    ">
                        🔐 Verify My Age
                    </button>
                    <br>
                    <button onclick="window.history.back()" style="
                        background: transparent;
                        color: rgba(255,255,255,0.7);
                        border: 1px solid rgba(255,255,255,0.3);
                        padding: 0.5rem 1rem;
                        border-radius: 5px;
                        cursor: pointer;
                        font-size: 0.9rem;
                        margin: 0.5rem;
                    ">
                        ← Go Back
                    </button>
                </div>
                
                <p style="font-size: 0.8rem; color: rgba(255,255,255,0.6);">
                    Powered by BlockVerify • Privacy-preserving verification
                </p>
            </div>
        `;
        
        document.body.appendChild(barrier);
    }
    
    async function checkAgeVerification() {
        log('🔄 Starting age verification check...');
        
        // Check if returning from verification
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.has('verified')) {
            log('🔗 Just returned from verification');
            await new Promise(resolve => setTimeout(resolve, 1000));
        }
        
        // Get token
        const token = getToken();
        if (!token) {
            log('❌ No token - showing prompt');
            showVerificationPrompt();
            return;
        }
        
        // Decode token
        const tokenData = decodeToken(token);
        if (!tokenData || isTokenExpired(tokenData)) {
            log('❌ Invalid/expired token - showing prompt');
            showVerificationPrompt();
            return;
        }
        
        // Check age - handle both JWT (age_over) and legacy (ageOver) formats
        const ageValue = tokenData.age_over || tokenData.ageOver;
        if (ageValue >= 18) {
            log('✅ Access granted', { age: ageValue });
            showContent();
        } else {
            log('❌ Not old enough - showing prompt', { age: ageValue });
            showVerificationPrompt();
        }
    }
    
    // Auto-run when page loads
    document.addEventListener('DOMContentLoaded', function() {
        log('📄 BlockVerify loaded');
        checkAgeVerification();
    });
    
    // Expose functions
    window.BlockVerify = {
        checkAge: checkAgeVerification,
        getToken: getToken,
        startVerification: startVerification
    };
    
})(); 