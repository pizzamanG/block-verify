# 🏗️ BlockVerify System Architecture

## Overview

BlockVerify is a privacy-preserving age verification platform that combines zero-knowledge cryptography, blockchain integrity, and modern web technologies to provide seamless age verification for websites.

## High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client SDK    │    │  Verification   │    │   Business      │
│   (JavaScript)  │    │     Portal      │    │   Dashboard     │
│                 │    │   (WebAuthn)    │    │   (Analytics)   │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          │ HTTPS/API calls      │ WebAuthn/KYC        │ API calls
          │                      │                      │
┌─────────▼──────────────────────▼──────────────────────▼───────┐
│                    FastAPI Backend                           │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │
│  │   Billing   │ │    Auth     │ │ Verification│            │
│  │   Service   │ │   Service   │ │   Service   │            │
│  └─────────────┘ └─────────────┘ └─────────────┘            │
└─────────┬───────────────────────────────────────────────────┘
          │
┌─────────▼───────┐    ┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │    │   Blockchain    │    │     Stripe      │
│   Database      │    │  (Polygon)      │    │   (Payments)    │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Core Components

### 1. Client SDK (Frontend)

**File**: `client_sdk/blockverify.js`

**Responsibilities**:
- Age gate UI rendering
- Token storage and validation
- API communication
- WebAuthn integration
- Cross-site token sharing

**Key Features**:
- Beautiful modal UI with animations
- Automatic token validation
- Device-bound authentication
- Privacy-first design (no PII stored)

**Technology Stack**:
- Vanilla JavaScript (no dependencies)
- WebAuthn API for device binding
- Local/Session Storage for tokens
- CSS animations and responsive design

### 2. FastAPI Backend

**Files**: `backend/app/`

**Responsibilities**:
- JWT token minting and validation
- WebAuthn credential management
- KYC integration
- Billing and usage tracking
- Blockchain integration

**Key Modules**:

#### Authentication Service
```python
# backend/app/auth.py
- WebAuthn registration/authentication
- JWT token generation (Ed25519 signatures)
- Device binding and management
- Token revocation system
```

#### Billing Service
```python
# backend/app/billing.py
- Client registration and management
- API key generation and validation
- Usage tracking and rate limiting
- Stripe integration for payments
- Invoice generation
```

#### Verification Service
```python
# backend/app/verification.py
- Age token validation
- Blockchain integrity checks
- KYC provider integration
- Token metadata management
```

### 3. PostgreSQL Database

**Schema Design**:

```sql
-- Client Management
CREATE TABLE clients (
    id UUID PRIMARY KEY,
    business_name VARCHAR(255) NOT NULL,
    contact_email VARCHAR(255) UNIQUE NOT NULL,
    plan_type VARCHAR(50) DEFAULT 'free',
    stripe_customer_id VARCHAR(255),
    monthly_limit INTEGER DEFAULT 1000,
    current_usage INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- API Key Management
CREATE TABLE api_keys (
    id UUID PRIMARY KEY,
    client_id UUID REFERENCES clients(id),
    key_hash VARCHAR(64) UNIQUE NOT NULL,
    key_prefix VARCHAR(20) NOT NULL,
    rate_limit_per_minute INTEGER DEFAULT 100,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Usage Tracking
CREATE TABLE usage_records (
    id UUID PRIMARY KEY,
    client_id UUID REFERENCES clients(id),
    api_key_id UUID REFERENCES api_keys(id),
    usage_type VARCHAR(50) NOT NULL,
    cost_cents INTEGER DEFAULT 0,
    endpoint VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

-- WebAuthn Credentials
CREATE TABLE webauthn_credentials (
    id UUID PRIMARY KEY,
    credential_id BYTEA UNIQUE NOT NULL,
    public_key BYTEA NOT NULL,
    user_handle BYTEA NOT NULL,
    sign_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Age Tokens
CREATE TABLE age_tokens (
    id UUID PRIMARY KEY,
    token_hash VARCHAR(64) UNIQUE NOT NULL,
    credential_id UUID REFERENCES webauthn_credentials(id),
    issued_at TIMESTAMP NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    is_revoked BOOLEAN DEFAULT false
);
```

### 4. Blockchain Integration (Polygon)

**Smart Contract**: `AgeTokenBulletin.sol`

**Purpose**:
- Store issuer public key thumbprint
- Manage token revocation Merkle tree
- Provide verifiable integrity guarantees

**Key Functions**:
```solidity
contract AgeTokenBulletin {
    // Store issuer public key thumbprint
    bytes32 public issuerKeyThumbprint;
    
    // Merkle root for revoked tokens
    bytes32 public revocationRoot;
    
    // Update revocation root (only owner)
    function updateRevocationRoot(bytes32 newRoot) external onlyOwner;
    
    // Verify token is not revoked
    function isTokenRevoked(bytes32 tokenHash, bytes32[] proof) external view returns (bool);
}
```

**Deployment**:
- **Testnet**: Polygon Amoy
- **Mainnet**: Polygon (for production)
- **Gas Optimization**: Batch revocations using Merkle trees

### 5. External Integrations

#### Stripe (Payment Processing)
- Customer management
- Subscription billing
- Usage-based invoicing
- Webhook handling for payment events

#### KYC Providers
- **Jumio**: Primary KYC for real age verification
- **Stub Provider**: For testing and demos
- **Extensible**: Easy to add new providers

#### CDN/Distribution
- **jsDelivr**: Global CDN for SDK distribution
- **GitHub Pages**: Documentation and landing pages
- **Cloudflare**: Optional CDN and DDoS protection

## Data Flow

### 1. User Registration Flow

```
User visits adult site
        ↓
SDK detects no token
        ↓
Shows age verification modal
        ↓
User clicks "Verify Age"
        ↓
Redirects to verification portal
        ↓
User uploads ID document (KYC)
        ↓
WebAuthn device registration
        ↓
JWT token minted (device-bound)
        ↓
Token stored in browser
        ↓
Redirects back to original site
        ↓
SDK validates token with API
        ↓
User gains access to content
```

### 2. Token Validation Flow

```
User visits site with existing token
        ↓
SDK retrieves token from storage
        ↓
Local validation (expiry, format)
        ↓
API validation (signature, revocation)
        ↓
Blockchain verification (optional)
        ↓
Grant or deny access
```

### 3. Billing Flow

```
API call received
        ↓
Extract and validate API key
        ↓
Check rate limits
        ↓
Process request
        ↓
Record usage in database
        ↓
Calculate costs
        ↓
Monthly invoice generation
        ↓
Stripe payment processing
```

## Security Architecture

### 1. Cryptographic Foundations

- **JWT Signing**: Ed25519 (faster, more secure than RSA)
- **Device Binding**: WebAuthn FIDO2 authentication
- **Token Hashing**: SHA-256 for privacy
- **Revocation**: Merkle tree proofs for efficiency

### 2. Privacy Guarantees

- **Zero Knowledge**: No PII stored or transmitted
- **Unlinkability**: Tokens can't be correlated across sites
- **Forward Secrecy**: Past tokens remain private if key compromised
- **Selective Disclosure**: Only age information revealed

### 3. Attack Resistance

- **Token Sharing**: Device binding prevents token sharing
- **Replay Attacks**: Nonce and timestamp validation
- **Man-in-the-Middle**: TLS + certificate pinning
- **DDoS**: Rate limiting and blockchain fallback

## Performance Characteristics

### Latency
- **Token Validation**: <100ms (API + DB query)
- **Blockchain Verification**: <500ms (optional)
- **SDK Load Time**: <50ms (minified, cached)

### Throughput
- **API Capacity**: 10,000+ req/sec (horizontal scaling)
- **Database**: 100,000+ queries/sec (PostgreSQL)
- **CDN**: Unlimited (global edge distribution)

### Storage
- **Token Size**: 512 bytes (JWT + metadata)
- **Database Growth**: ~1KB per user per month
- **Blockchain**: ~32 bytes per revocation batch

## Scalability Design

### Horizontal Scaling
- **Stateless API**: Easy container replication
- **Database Sharding**: By client_id for tenant isolation
- **CDN Distribution**: Global edge caching
- **Load Balancing**: Multiple backend instances

### Caching Strategy
- **Redis**: API response caching (optional)
- **Browser Cache**: Long-lived token storage
- **CDN Cache**: Static assets and SDK files
- **Database Cache**: Query result caching

### Monitoring Points
- **API Response Times**: P95, P99 latencies
- **Error Rates**: 4xx/5xx by endpoint
- **Usage Metrics**: Verifications per second
- **Business Metrics**: Revenue, customer growth

## Deployment Architecture

### Development
```
Local PostgreSQL → FastAPI Dev Server → Frontend Dev Build
```

### Staging
```
Railway PostgreSQL → Railway FastAPI → GitHub Pages
```

### Production
```
AWS RDS PostgreSQL → AWS ECS/Fargate → CloudFront CDN
    ↓
Stripe Webhooks → Monitoring (DataDog) → Alerts (PagerDuty)
```

## Technology Choices Rationale

### Why FastAPI?
- **Performance**: 2-3x faster than Flask/Django
- **Type Safety**: Automatic validation and documentation
- **Async Support**: Handle thousands of concurrent requests
- **OpenAPI**: Auto-generated API documentation

### Why PostgreSQL?
- **ACID Compliance**: Critical for billing accuracy
- **JSON Support**: Flexible metadata storage
- **Scaling**: Read replicas and connection pooling
- **Ecosystem**: Rich tooling and extensions

### Why Polygon?
- **Low Fees**: $0.001 per transaction vs $50+ on Ethereum
- **Fast Finality**: 2-second block times
- **EVM Compatible**: Use existing Ethereum tools
- **Eco-friendly**: Proof of Stake consensus

### Why WebAuthn?
- **Security**: Hardware-backed authentication
- **UX**: Biometric authentication (Touch ID, Face ID)
- **Phishing Resistant**: Domain binding prevents attacks
- **Standards**: W3C standard with broad browser support

This architecture provides a robust, scalable, and privacy-preserving foundation for age verification that can handle millions of users while maintaining strong security and compliance guarantees. 