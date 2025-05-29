# 🔐 BlockVerify Security Architecture

## Device Binding with WebAuthn + Secure Enclaves

### How It Works

1. **User Registration:**
   ```
   User → KYC Verification → WebAuthn Registration → Token Minting
   ```

2. **WebAuthn Creates Secure Key Pair:**
   - **Private key** stored in device's secure enclave/TPM
   - **Public key** hashed and embedded in JWT token
   - **Cannot be extracted** from secure hardware

3. **Token Structure:**
   ```json
   {
     "ageOver": 18,
     "device": "sha256_hash_of_public_key",
     "iat": 1234567890,
     "exp": 1234567890
   }
   ```

### Why This Prevents Sharing

❌ **Can't copy the token** - It's tied to hardware
❌ **Can't share credentials** - Private key locked in secure enclave  
❌ **Can't fake verification** - WebAuthn challenge required
✅ **One device, one token** - Cryptographically enforced

### Secure Enclave Support
- **iOS**: Secure Enclave (A7+ chips)
- **Android**: StrongBox/TEE (Android 9+)
- **Windows**: TPM 2.0
- **macOS**: Secure Enclave (T1/T2/M1+ chips)

### Challenge-Response Flow
```javascript
// Every site visit requires this challenge
const challenge = crypto.getRandomValues(new Uint8Array(32));
const credential = await navigator.credentials.get({
  publicKey: {
    challenge,
    allowCredentials: [{
      type: 'public-key',
      id: device_hash_from_token
    }]
  }
});
// ✅ Only works if user's device has the private key
```

## Token Storage & User Experience

### Where Tokens Are Stored
1. **HTTP-only Cookie** (secure, can't be accessed by JS)
2. **localStorage** (backup, accessible to your JS library)
3. **Both synced** for reliability

### User Flow (Completely Seamless)
```
User visits ANY adult site
     ↓
at-enhanced.js checks for token
     ↓
If no token → Redirect to BlockVerify
     ↓
User verifies ONCE (KYC + WebAuthn)
     ↓
Token stored in browser
     ↓
ALL future adult sites work automatically
```

### Cross-Site Token Sharing
- Same token works across ALL participating sites
- No personal data shared with sites
- Sites only get "yes, this user is 18+"

## Business Model Details

### For Adult Sites (Your Customers)
```python
# Integration is literally this simple:
response = requests.post(
    'https://api.blockverify.com/verify-token',
    headers={'X-API-Key': 'their_api_key'},
    json={'token': user_token}
)
# They get charged per API call
```

### Pricing Tiers
- **Startup**: $0.05 per verification (first 1000 free)
- **Growth**: $0.03 per verification (volume discounts)
- **Enterprise**: $0.01 per verification + SLA

### Revenue Potential
- 1M verifications/month = $10k-$50k revenue
- Adult industry has MILLIONS of users
- Cross-site compatibility = network effects 