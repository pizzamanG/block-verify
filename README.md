# 🔐 BlockVerify

**Privacy-preserving, trust-minimized age verification for B2B use**

BlockVerify is a zero-knowledge age verification system designed for adult content platforms. Users verify once and get a persistent, device-bound age token that can be validated by any integrated business without sharing personal information.

## 🏗️ Architecture

### Core Components

1. **Smart Contract** (`AgeTokenBulletin.sol`)
   - Stores SHA-256 thumbprint of issuer's public key
   - Manages Merkle root for token revocation
   - Deployed on Polygon Amoy testnet

2. **FastAPI Backend**
   - JWT token minting with Ed25519 signatures
   - WebAuthn device binding for security
   - KYC integration (real vendor + stub for testing)
   - Token verification API with blockchain integrity checks

3. **Client Library** (`at-enhanced.js`)
   - Automatic age gate enforcement
   - Device-bound authentication via WebAuthn
   - Optional on-chain verification for extra security

4. **Business Dashboard**
   - Self-service verifier onboarding
   - Usage analytics and API key management
   - Integration code generation

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Node.js 16+
- PostgreSQL (or SQLite for development)
- Polygon Amoy testnet access

### 1. Environment Setup

```bash
# Clone and setup
git clone <your-repo>
cd blockverify

# Backend dependencies
cd backend
pip install -r requirements.txt

# Smart contract dependencies
cd ../infra/contracts
npm install
```

### 2. Environment Variables

Create `.env` file:

```bash
# Blockchain
CHAIN_RPC_URL=https://rpc-amoy.polygon.technology
PRIVATE_KEY=your_deployer_private_key
BULLETIN_ADDRESS=  # Will be set after deployment

# Database
DATABASE_URL=postgresql://user:pass@localhost/blockverify

# Keys
ISSUER_KEY_FILE=issuer_ed25519.jwk
```

### 3. Deploy & Initialize

```bash
# Run the deployment script
python deploy.py
```

This will:
- Generate Ed25519 issuer key
- Deploy smart contract (if needed)
- Push public key thumbprint to blockchain
- Initialize database schema

### 4. Start the API

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 🔧 Business Integration

### For Adult Content Platforms

1. **Register as a Verifier**
   ```bash
   curl -X POST http://localhost:8000/verifiers/register \
     -H "Content-Type: application/json" \
     -d '{
       "business_name": "Your Site",
       "contact_email": "admin@yoursite.com",
       "website_url": "https://yoursite.com",
       "use_case_description": "Adult content age verification"
     }'
   ```

2. **Add Age Gate to Your Site**
   ```html
   <script src="https://api.blockverify.com/static/at-enhanced.js"
           data-api-endpoint="https://api.blockverify.com"
           data-api-key="your_api_key"
           data-contract-address="0x..."></script>
   ```

3. **Server-Side Verification** (optional)
   ```python
   import requests
   
   response = requests.post(
       'https://api.blockverify.com/verify-token',
       headers={'X-API-Key': 'your_api_key'},
       json={'token': user_age_token}
   )
   
   if response.json()['valid']:
       # User is verified as 18+
       pass
   ```

## 🛡️ Security Features

### Zero-Knowledge Privacy
- No personal data stored or transmitted
- Device-bound tokens prevent sharing
- Users verify once, use everywhere

### Trust Minimization
- Public key thumbprint stored on-chain
- Verifiers can validate issuer integrity
- Optional on-chain verification in client library

### Revocation System
- Merkle tree-based token revocation
- On-chain revocation root updates
- Efficient batch revocation support

## 📊 API Endpoints

### User Endpoints
- `POST /webauthn/register` - Register device and mint token
- `GET /issuer_jwks.json` - Public key for verification

### Verifier Endpoints
- `POST /verifiers/register` - Business registration
- `POST /verify-token` - Token validation
- `GET /verifiers/integration-guide` - Integration docs

### Admin Endpoints
- `POST /revocation/revoke-token` - Revoke specific token
- `GET /revocation/revocation-status/{hash}` - Check revocation

## 🧪 Testing

### Run the Test Suite
```bash
cd backend
pytest tests/
```

### Manual Testing
1. Visit `http://localhost:8000/verify.html`
2. Upload any image (stub KYC)
3. Complete WebAuthn registration
4. Test age gate on protected pages

## 🚀 Production Deployment

### Docker Deployment
```bash
docker-compose up -d
```

### Environment Considerations
- Use production database (PostgreSQL)
- Set up proper SSL/TLS
- Configure CORS for your domains
- Use mainnet for production (update RPC URL)

## 🔄 Token Lifecycle

1. **User Registration**
   - KYC verification (real or stub)
   - WebAuthn device registration
   - JWT token minting with device binding

2. **Token Usage**
   - Client library checks token validity
   - WebAuthn challenge for device verification
   - Optional server-side validation

3. **Token Revocation**
   - User request or admin action
   - Merkle tree update
   - On-chain revocation root update

## 🏢 Business Model

### For Verifiers (Adult Sites)
- Pay-per-verification pricing
- Volume discounts available
- Self-service onboarding
- Real-time usage analytics

### For Users
- Free age verification
- One-time setup
- Privacy-preserving
- Works across all integrated sites

## 🛠️ Development

### Project Structure
```
blockverify/
├── backend/           # FastAPI application
├── frontend/          # Client library and dashboard
├── infra/            # Smart contracts and deployment
├── utils/            # Helper scripts
└── deploy.py         # Main deployment script
```

### Key Technologies
- **Backend**: FastAPI, SQLModel, Web3.py
- **Crypto**: Ed25519 (jwcrypto), WebAuthn
- **Blockchain**: Solidity, Hardhat, Polygon
- **Frontend**: Vanilla JS, modern CSS

## 📈 Roadmap

### Phase 1 (Current)
- ✅ Core MVP with device binding
- ✅ Smart contract deployment
- ✅ Basic verifier onboarding

### Phase 2 (Next)
- [ ] Production KYC provider integration
- [ ] Advanced analytics dashboard
- [ ] Mobile app support
- [ ] Multi-chain deployment

### Phase 3 (Future)
- [ ] Decentralized governance
- [ ] Zero-knowledge proofs for enhanced privacy
- [ ] Cross-platform identity federation

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Support

- **Documentation**: [docs.blockverify.com](https://docs.blockverify.com)
- **Issues**: GitHub Issues
- **Business Inquiries**: business@blockverify.com

---

**Built with privacy and trust minimization in mind** 🔐
