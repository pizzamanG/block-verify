/**
 * BlockVerify Age Token Client Library
 * Privacy-preserving age verification with blockchain integrity
 */

class AgeTokenVerifier {
  constructor(config = {}) {
    this.apiEndpoint = config.apiEndpoint || 'https://api.blockverify.com';
    this.contractAddress = config.contractAddress;
    this.rpcUrl = config.rpcUrl || 'https://rpc-amoy.polygon.technology';
    this.apiKey = config.apiKey;
    this.debug = config.debug || false;
  }

  log(message) {
    if (this.debug) console.log('[AgeToken]', message);
  }

  async verifyToken(token) {
    try {
      // First verify with API
      const response = await fetch(`${this.apiEndpoint}/verify-token`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': this.apiKey
        },
        body: JSON.stringify({ token })
      });

      if (!response.ok) {
        throw new Error(`API verification failed: ${response.status}`);
      }

      const result = await response.json();
      
      // Optionally verify thumbprint on-chain for extra security
      if (this.contractAddress) {
        const onChainValid = await this.verifyThumbprintOnChain();
        result.blockchain_verified = onChainValid;
      }

      return result;
    } catch (error) {
      this.log(`Verification error: ${error.message}`);
      throw error;
    }
  }

  async verifyThumbprintOnChain() {
    try {
      // Get JWKS from issuer
      const jwksResponse = await fetch(`${this.apiEndpoint}/issuer_jwks.json`);
      const jwks = await jwksResponse.json();
      const publicKey = jwks.keys[0];
      
      // Calculate thumbprint
      const keyString = JSON.stringify(publicKey);
      const encoder = new TextEncoder();
      const data = encoder.encode(keyString);
      const hashBuffer = await crypto.subtle.digest('SHA-256', data);
      const localThumbprint = Array.from(new Uint8Array(hashBuffer));

      // Compare with on-chain thumbprint (requires Web3 provider)
      if (typeof window !== 'undefined' && window.ethereum) {
        const provider = new ethers.providers.Web3Provider(window.ethereum);
        const contract = new ethers.Contract(
          this.contractAddress,
          ['function thumbprint() view returns (bytes32)'],
          provider
        );
        
        const onChainThumbprint = await contract.thumbprint();
        const onChainBytes = ethers.utils.arrayify(onChainThumbprint);
        
        return this.arraysEqual(localThumbprint, Array.from(onChainBytes));
      }
      
      return false; // Can't verify without Web3
    } catch (error) {
      this.log(`On-chain verification error: ${error.message}`);
      return false;
    }
  }

  arraysEqual(a, b) {
    return a.length === b.length && a.every((val, i) => val === b[i]);
  }

  // Client-side age gate for users
  async checkAgeGate() {
    const token = localStorage.getItem('AgeToken') || 
                  this.getCookie('AgeToken');
    
    if (!token) {
      this.redirectToVerification();
      return false;
    }

    try {
      // Decode JWT to check expiry
      const [, payload] = token.split('.');
      const decoded = JSON.parse(atob(payload));
      
      if (Date.now() / 1000 > decoded.exp) {
        this.redirectToVerification();
        return false;
      }

      // Verify device binding with WebAuthn
      const challenge = crypto.getRandomValues(new Uint8Array(32));
      await navigator.credentials.get({
        publicKey: {
          challenge,
          timeout: 15000,
          allowCredentials: [{
            type: 'public-key',
            id: new TextEncoder().encode(decoded.device)
          }]
        }
      });

      return true;
    } catch (error) {
      this.log(`Age gate check failed: ${error.message}`);
      this.redirectToVerification();
      return false;
    }
  }

  getCookie(name) {
    const match = document.cookie.match(new RegExp(`${name}=([^;]+)`));
    return match ? match[1] : '';
  }

  redirectToVerification() {
    window.location.href = `${this.apiEndpoint}/verify.html`;
  }
}

// Auto-initialize for simple integration
(async () => {
  // Check for configuration in script tag
  const script = document.currentScript;
  const config = {
    apiEndpoint: script?.dataset.apiEndpoint,
    contractAddress: script?.dataset.contractAddress,
    apiKey: script?.dataset.apiKey,
    debug: script?.dataset.debug === 'true'
  };

  const verifier = new AgeTokenVerifier(config);
  
  // Auto-run age gate if not in verification flow
  if (!window.location.pathname.includes('verify')) {
    const isValid = await verifier.checkAgeGate();
    if (isValid) {
      document.body.style.display = 'block';
    }
  }

  // Expose globally for manual use
  window.AgeTokenVerifier = AgeTokenVerifier;
  window.ageVerifier = verifier;
})(); 