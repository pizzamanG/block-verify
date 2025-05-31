/**
 * BlockVerify Client SDK v2.0.0
 * Privacy-preserving age verification for websites
 * 
 * Usage:
 *   <script src="https://cdn.blockverify.com/v2/blockverify.min.js"></script>
 *   <script>
 *     BlockVerify.init({
 *       apiKey: 'bv_prod_your_key_here',
 *       minAge: 18,
 *       onSuccess: (result) => console.log('User verified', result),
 *       onFailure: (error) => console.log('Verification failed', error)
 *     });
 *   </script>
 */

(function(window) {
    'use strict';

    // SDK Configuration
    const SDK_VERSION = '2.0.0';
    const API_BASE_URL = 'https://api.blockverify.com';
    const VERIFICATION_URL = 'https://verify.blockverify.com';
    const LOCAL_STORAGE_KEY = 'blockverify_token';
    const SESSION_STORAGE_KEY = 'blockverify_session';

    // Debug logging
    function log(level, message, ...args) {
        if (window.BlockVerify?.config?.debug) {
            console[level](`[BlockVerify SDK v${SDK_VERSION}]`, message, ...args);
        }
    }

    // Error classes
    class BlockVerifyError extends Error {
        constructor(code, message, details = {}) {
            super(message);
            this.name = 'BlockVerifyError';
            this.code = code;
            this.details = details;
        }
    }

    class NetworkError extends BlockVerifyError {
        constructor(message, status, response) {
            super('NETWORK_ERROR', message);
            this.status = status;
            this.response = response;
        }
    }

    class ConfigurationError extends BlockVerifyError {
        constructor(message) {
            super('CONFIG_ERROR', message);
        }
    }

    class VerificationError extends BlockVerifyError {
        constructor(message, reason) {
            super('VERIFICATION_ERROR', message);
            this.reason = reason;
        }
    }

    // Token management
    class TokenManager {
        static setToken(token) {
            try {
                localStorage.setItem(LOCAL_STORAGE_KEY, token);
                sessionStorage.setItem(SESSION_STORAGE_KEY, token);
                log('info', 'Token stored successfully');
            } catch (e) {
                log('warn', 'Failed to store token:', e);
            }
        }

        static getToken() {
            // Try localStorage first, then sessionStorage
            return localStorage.getItem(LOCAL_STORAGE_KEY) || 
                   sessionStorage.getItem(SESSION_STORAGE_KEY);
        }

        static clearToken() {
            try {
                localStorage.removeItem(LOCAL_STORAGE_KEY);
                sessionStorage.removeItem(SESSION_STORAGE_KEY);
                log('info', 'Token cleared');
            } catch (e) {
                log('warn', 'Failed to clear token:', e);
            }
        }

        static isTokenValid(token) {
            if (!token) return false;

            try {
                // For JWT tokens
                const parts = token.split('.');
                if (parts.length === 3) {
                    // Decode JWT payload
                    let payload = parts[1];
                    
                    // Convert base64url to base64
                    payload = payload.replace(/-/g, '+').replace(/_/g, '/');
                    payload = payload + '='.repeat((4 - payload.length % 4) % 4);
                    
                    const decoded = JSON.parse(atob(payload));
                    
                    // Check expiration
                    if (decoded.exp && decoded.exp < Date.now() / 1000) {
                        log('info', 'JWT token expired');
                        return false;
                    }
                    
                    return true;
                }

                // For legacy base64 tokens
                const decoded = JSON.parse(atob(token));
                if (decoded.exp && decoded.exp < Date.now() / 1000) {
                    log('info', 'Legacy token expired');
                    return false;
                }
                
                return true;
            } catch (e) {
                log('warn', 'Invalid token format:', e);
                return false;
            }
        }
    }

    // API Client
    class APIClient {
        constructor(config) {
            this.config = config;
            this.baseURL = config.apiUrl || API_BASE_URL;
        }

        async verifyToken(token, minAge = 18) {
            const url = `${this.baseURL}/v1/verify-token`;
            
            log('info', 'Verifying token with API...');
            
            try {
                const response = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${this.config.apiKey}`,
                        'User-Agent': `BlockVerify-SDK/${SDK_VERSION}`,
                        'X-SDK-Version': SDK_VERSION
                    },
                    body: JSON.stringify({
                        token: token,
                        min_age: minAge,
                        user_agent: navigator.userAgent
                    })
                });

                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({}));
                    throw new NetworkError(
                        errorData.message || `API request failed with status ${response.status}`,
                        response.status,
                        errorData
                    );
                }

                const result = await response.json();
                log('info', 'Token verification result:', result);
                
                return result;
            } catch (error) {
                if (error instanceof NetworkError) {
                    throw error;
                }
                
                log('error', 'Network error during token verification:', error);
                throw new NetworkError('Failed to verify token - network error', 0, error);
            }
        }

        async getRateLimitInfo() {
            const url = `${this.baseURL}/v1/rate-limit-info`;
            
            try {
                const response = await fetch(url, {
                    headers: {
                        'Authorization': `Bearer ${this.config.apiKey}`
                    }
                });

                if (response.ok) {
                    return await response.json();
                }
            } catch (e) {
                log('warn', 'Failed to get rate limit info:', e);
            }
            
            return null;
        }
    }

    // UI Manager
    class UIManager {
        static createModal() {
            // Remove existing modal
            const existing = document.getElementById('blockverify-modal');
            if (existing) existing.remove();

            const modal = document.createElement('div');
            modal.id = 'blockverify-modal';
            modal.innerHTML = `
                <div class="blockverify-overlay">
                    <div class="blockverify-modal">
                        <div class="blockverify-header">
                            <h2>🔐 Age Verification Required</h2>
                            <p>This site requires age verification to continue</p>
                        </div>
                        
                        <div class="blockverify-content">
                            <div class="blockverify-info">
                                <div class="blockverify-feature">
                                    <span class="blockverify-icon">🛡️</span>
                                    <div>
                                        <strong>Privacy Protected</strong>
                                        <p>No personal data stored on this site</p>
                                    </div>
                                </div>
                                <div class="blockverify-feature">
                                    <span class="blockverify-icon">⚡</span>
                                    <div>
                                        <strong>One-Time Setup</strong>
                                        <p>Verify once, access everywhere</p>
                                    </div>
                                </div>
                                <div class="blockverify-feature">
                                    <span class="blockverify-icon">🔗</span>
                                    <div>
                                        <strong>Blockchain Secured</strong>
                                        <p>Cryptographically verified identity</p>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="blockverify-actions">
                                <button id="blockverify-verify-btn" class="blockverify-btn-primary">
                                    Verify My Age
                                </button>
                                <button id="blockverify-cancel-btn" class="blockverify-btn-secondary">
                                    Leave Site
                                </button>
                            </div>
                        </div>
                        
                        <div class="blockverify-footer">
                            <p>Powered by <a href="https://blockverify.com" target="_blank">BlockVerify</a></p>
                        </div>
                    </div>
                </div>
            `;

            // Add styles
            const style = document.createElement('style');
            style.textContent = `
                #blockverify-modal {
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    z-index: 999999;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                }
                
                .blockverify-overlay {
                    position: absolute;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0, 0, 0, 0.8);
                    backdrop-filter: blur(8px);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    padding: 20px;
                    box-sizing: border-box;
                }
                
                .blockverify-modal {
                    background: white;
                    border-radius: 16px;
                    max-width: 480px;
                    width: 100%;
                    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
                    overflow: hidden;
                    animation: blockverify-modal-in 0.3s ease-out;
                }
                
                @keyframes blockverify-modal-in {
                    from {
                        opacity: 0;
                        transform: scale(0.9) translateY(20px);
                    }
                    to {
                        opacity: 1;
                        transform: scale(1) translateY(0);
                    }
                }
                
                .blockverify-header {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 24px;
                    text-align: center;
                }
                
                .blockverify-header h2 {
                    margin: 0 0 8px 0;
                    font-size: 24px;
                    font-weight: 600;
                }
                
                .blockverify-header p {
                    margin: 0;
                    opacity: 0.9;
                    font-size: 14px;
                }
                
                .blockverify-content {
                    padding: 24px;
                }
                
                .blockverify-info {
                    margin-bottom: 24px;
                }
                
                .blockverify-feature {
                    display: flex;
                    align-items: center;
                    margin-bottom: 16px;
                }
                
                .blockverify-icon {
                    font-size: 24px;
                    margin-right: 12px;
                    width: 32px;
                    text-align: center;
                }
                
                .blockverify-feature strong {
                    display: block;
                    font-size: 14px;
                    font-weight: 600;
                    color: #333;
                    margin-bottom: 2px;
                }
                
                .blockverify-feature p {
                    margin: 0;
                    font-size: 12px;
                    color: #666;
                }
                
                .blockverify-actions {
                    display: flex;
                    gap: 12px;
                    flex-direction: column;
                }
                
                .blockverify-btn-primary {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    border: none;
                    padding: 14px 24px;
                    border-radius: 8px;
                    font-size: 16px;
                    font-weight: 600;
                    cursor: pointer;
                    transition: transform 0.2s, box-shadow 0.2s;
                }
                
                .blockverify-btn-primary:hover {
                    transform: translateY(-1px);
                    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
                }
                
                .blockverify-btn-secondary {
                    background: transparent;
                    color: #666;
                    border: 2px solid #ddd;
                    padding: 12px 24px;
                    border-radius: 8px;
                    font-size: 14px;
                    cursor: pointer;
                    transition: border-color 0.2s, color 0.2s;
                }
                
                .blockverify-btn-secondary:hover {
                    border-color: #bbb;
                    color: #333;
                }
                
                .blockverify-footer {
                    background: #f8f9fa;
                    padding: 16px 24px;
                    text-align: center;
                    border-top: 1px solid #eee;
                }
                
                .blockverify-footer p {
                    margin: 0;
                    font-size: 12px;
                    color: #666;
                }
                
                .blockverify-footer a {
                    color: #667eea;
                    text-decoration: none;
                    font-weight: 500;
                }
                
                .blockverify-footer a:hover {
                    text-decoration: underline;
                }
                
                @media (max-width: 480px) {
                    .blockverify-modal {
                        margin: 10px;
                        max-width: none;
                    }
                    
                    .blockverify-actions {
                        flex-direction: column;
                    }
                }
            `;

            document.head.appendChild(style);
            document.body.appendChild(modal);

            return modal;
        }

        static showModal(config) {
            const modal = UIManager.createModal();
            
            // Event handlers
            const verifyBtn = modal.querySelector('#blockverify-verify-btn');
            const cancelBtn = modal.querySelector('#blockverify-cancel-btn');
            
            verifyBtn.addEventListener('click', () => {
                const verificationUrl = `${config.verificationUrl || VERIFICATION_URL}?` + new URLSearchParams({
                    origin: window.location.origin,
                    redirect: window.location.href,
                    sdk_version: SDK_VERSION
                });
                
                log('info', 'Redirecting to verification:', verificationUrl);
                window.location.href = verificationUrl;
            });
            
            cancelBtn.addEventListener('click', () => {
                if (config.onCancel) {
                    config.onCancel();
                } else {
                    history.back();
                }
            });

            // Prevent modal dismissal by clicking overlay
            modal.querySelector('.blockverify-overlay').addEventListener('click', (e) => {
                if (e.target === e.currentTarget) {
                    // Optionally allow dismissal
                    if (config.allowDismiss) {
                        UIManager.hideModal();
                    }
                }
            });

            return modal;
        }

        static hideModal() {
            const modal = document.getElementById('blockverify-modal');
            if (modal) {
                modal.style.animation = 'blockverify-modal-out 0.2s ease-in forwards';
                setTimeout(() => modal.remove(), 200);
            }
        }
    }

    // Main BlockVerify SDK
    class BlockVerifySDK {
        constructor() {
            this.config = {};
            this.apiClient = null;
            this.initialized = false;
        }

        init(options = {}) {
            // Validate required config
            if (!options.apiKey) {
                throw new ConfigurationError('API key is required');
            }

            if (!options.apiKey.startsWith('bv_')) {
                throw new ConfigurationError('Invalid API key format');
            }

            this.config = {
                apiKey: options.apiKey,
                minAge: options.minAge || 18,
                autoVerify: options.autoVerify !== false,
                debug: options.debug || false,
                verificationUrl: options.verificationUrl,
                apiUrl: options.apiUrl,
                onSuccess: options.onSuccess,
                onFailure: options.onFailure,
                onCancel: options.onCancel,
                allowDismiss: options.allowDismiss || false
            };

            this.apiClient = new APIClient(this.config);
            this.initialized = true;

            log('info', 'BlockVerify SDK initialized', {
                minAge: this.config.minAge,
                autoVerify: this.config.autoVerify
            });

            // Auto-verify if enabled
            if (this.config.autoVerify) {
                this.checkAge();
            }

            return this;
        }

        async checkAge() {
            if (!this.initialized) {
                throw new ConfigurationError('SDK not initialized. Call BlockVerify.init() first.');
            }

            log('info', 'Starting age verification check...');

            try {
                // Check for existing token
                const token = TokenManager.getToken();
                
                if (token && TokenManager.isTokenValid(token)) {
                    log('info', 'Found valid token, verifying with API...');
                    
                    const result = await this.apiClient.verifyToken(token, this.config.minAge);
                    
                    if (result.valid) {
                        log('info', 'Age verification successful');
                        
                        if (this.config.onSuccess) {
                            this.config.onSuccess(result);
                        }
                        
                        return { verified: true, result };
                    } else {
                        log('warn', 'Token verification failed:', result.metadata?.reason);
                        TokenManager.clearToken();
                    }
                } else if (token) {
                    log('info', 'Found expired/invalid token, clearing...');
                    TokenManager.clearToken();
                }

                // Check if we're returning from verification
                const urlParams = new URLSearchParams(window.location.search);
                if (urlParams.get('blockverify_verified') === 'true') {
                    log('info', 'Returned from verification, checking for new token...');
                    
                    // Small delay to allow token to be set
                    await new Promise(resolve => setTimeout(resolve, 1000));
                    
                    const newToken = TokenManager.getToken();
                    if (newToken && TokenManager.isTokenValid(newToken)) {
                        const result = await this.apiClient.verifyToken(newToken, this.config.minAge);
                        
                        if (result.valid) {
                            // Clean URL
                            const url = new URL(window.location);
                            url.searchParams.delete('blockverify_verified');
                            window.history.replaceState({}, '', url);
                            
                            if (this.config.onSuccess) {
                                this.config.onSuccess(result);
                            }
                            
                            return { verified: true, result };
                        }
                    }
                }

                // No valid token found, show verification prompt
                log('info', 'No valid token found, showing verification prompt');
                
                this.showVerificationPrompt();
                
                if (this.config.onFailure) {
                    this.config.onFailure(new VerificationError('Age verification required', 'no_token'));
                }
                
                return { verified: false, reason: 'verification_required' };
                
            } catch (error) {
                log('error', 'Age verification error:', error);
                
                if (this.config.onFailure) {
                    this.config.onFailure(error);
                }
                
                // Show verification prompt as fallback
                this.showVerificationPrompt();
                
                return { verified: false, error: error.message };
            }
        }

        showVerificationPrompt() {
            UIManager.showModal(this.config);
        }

        hideVerificationPrompt() {
            UIManager.hideModal();
        }

        clearToken() {
            TokenManager.clearToken();
            log('info', 'Token cleared manually');
        }

        async getStatus() {
            if (!this.initialized) {
                return { initialized: false };
            }

            const token = TokenManager.getToken();
            const rateLimitInfo = await this.apiClient.getRateLimitInfo();

            return {
                initialized: true,
                hasToken: !!token,
                tokenValid: token ? TokenManager.isTokenValid(token) : false,
                config: {
                    minAge: this.config.minAge,
                    autoVerify: this.config.autoVerify
                },
                rateLimitInfo
            };
        }
    }

    // Global SDK instance
    const blockVerifySDK = new BlockVerifySDK();

    // Expose SDK to global scope
    window.BlockVerify = blockVerifySDK;

    // Auto-initialize if config is present
    if (window.blockverifyConfig) {
        blockVerifySDK.init(window.blockverifyConfig);
    }

    // Handle token setting from verification page
    window.addEventListener('message', (event) => {
        if (event.origin !== VERIFICATION_URL.replace('/verify', '')) return;
        
        if (event.data.type === 'BLOCKVERIFY_TOKEN') {
            TokenManager.setToken(event.data.token);
            log('info', 'Token received via postMessage');
            
            // Re-check age after token is set
            if (blockVerifySDK.initialized) {
                blockVerifySDK.checkAge();
            }
        }
    });

    log('info', 'BlockVerify SDK loaded');

})(window); 