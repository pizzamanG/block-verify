# 🔐 BlockVerify API Reference

## Overview

BlockVerify provides a complete API for privacy-preserving age verification. This document covers all available endpoints, authentication, and usage examples.

**Base URL**: `https://api.blockverify.com` (or your Railway deployment URL)

## Authentication

Most API endpoints require authentication using an API key. You can provide your API key in two ways:

1. **Bearer Token** (Recommended):
   ```
   Authorization: Bearer bv_prod_your_api_key_here
   ```

2. **X-API-Key Header**:
   ```
   X-API-Key: bv_prod_your_api_key_here
   ```

## Client Registration & Management

### Register a New Client

Create a new client account and receive your first API key.

**Endpoint**: `POST /api/v1/clients/register`

**Request Body**:
```json
{
  "business_name": "Your Company Name",
  "contact_email": "admin@yourcompany.com",
  "website_url": "https://yourcompany.com",
  "plan_type": "free"  // Options: free, starter, professional, enterprise
}
```

**Response**:
```json
{
  "message": "Registration successful",
  "client": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "business_name": "Your Company Name",
    "contact_email": "admin@yourcompany.com",
    "plan": "free",
    "monthly_limit": 1000
  },
  "api_key": {
    "key": "bv_prod_AbCdEfGhIjKlMnOpQrStUvWxYz123456",
    "instructions": "Save this API key securely. You won't be able to see it again."
  }
}
```

⚠️ **Important**: Save the API key immediately! It's only shown once.

### Get Current Client Info

Retrieve information about your client account.

**Endpoint**: `GET /api/v1/clients/me`

**Headers**: Requires authentication

**Response**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "business_name": "Your Company Name",
  "contact_email": "admin@yourcompany.com",
  "website_url": "https://yourcompany.com",
  "plan_type": "free",
  "monthly_usage": 250,
  "monthly_limit": 1000,
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Get Usage Statistics

Check your current usage and limits.

**Endpoint**: `GET /api/v1/clients/usage`

**Headers**: Requires authentication

**Response**:
```json
{
  "client": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "business_name": "Your Company Name",
    "plan": "free",
    "created_at": "2024-01-01T00:00:00Z"
  },
  "usage": {
    "current_month": 250,
    "limit": 1000,
    "percentage": 25.0,
    "reset_date": "2024-02-01T00:00:00Z"
  },
  "api_keys": 2,
  "active_keys": 2
}
```

### List API Keys

Get all API keys for your account.

**Endpoint**: `GET /api/v1/clients/api-keys`

**Headers**: Requires authentication

**Response**:
```json
[
  {
    "id": "key-id-1",
    "name": "Primary Key",
    "key_prefix": "bv_prod_",
    "masked_key": "bv_prod_****",
    "rate_limit_per_minute": 10,
    "is_active": true,
    "created_at": "2024-01-01T00:00:00Z",
    "last_used_at": "2024-01-15T12:00:00Z"
  }
]
```

### Create New API Key

Generate additional API keys (max 5 per client).

**Endpoint**: `POST /api/v1/clients/api-keys`

**Headers**: Requires authentication

**Request Body**:
```json
{
  "name": "Production Key"
}
```

**Response**:
```json
{
  "message": "API key created successfully",
  "api_key": {
    "id": "new-key-id",
    "name": "Production Key",
    "key": "bv_prod_NewKeyHere123456",
    "instructions": "Save this API key securely. You won't be able to see it again."
  }
}
```

### Revoke API Key

Disable an API key.

**Endpoint**: `DELETE /api/v1/clients/api-keys/{key_id}`

**Headers**: Requires authentication

**Response**:
```json
{
  "message": "API key revoked successfully"
}
```

### Get Available Plans

View all pricing plans.

**Endpoint**: `GET /api/v1/clients/plans`

**Response**:
```json
{
  "plans": [
    {
      "name": "free",
      "monthly_verifications": 1000,
      "rate_limit_per_minute": 10,
      "price_monthly": "Free"
    },
    {
      "name": "starter",
      "monthly_verifications": 10000,
      "rate_limit_per_minute": 60,
      "price_monthly": "$29.00"
    },
    {
      "name": "professional",
      "monthly_verifications": 100000,
      "rate_limit_per_minute": 300,
      "price_monthly": "$99.00"
    },
    {
      "name": "enterprise",
      "monthly_verifications": 1000000,
      "rate_limit_per_minute": 1000,
      "price_monthly": "$299.00"
    }
  ]
}
```

### Upgrade Plan

Upgrade to a higher plan.

**Endpoint**: `POST /api/v1/clients/upgrade-plan`

**Headers**: Requires authentication

**Request Body**:
```json
{
  "new_plan": "starter"
}
```

**Response**:
```json
{
  "message": "Successfully upgraded to starter plan",
  "new_limits": {
    "monthly_verifications": 10000,
    "rate_limit_per_minute": 60,
    "price_cents": 2900
  }
}
```

## Age Verification

### Verify Age Token

The main endpoint for verifying age tokens.

**Endpoint**: `POST /api/v1/verify-token`

**Headers**: Requires authentication

**Request Body**:
```json
{
  "token": "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9...",
  "min_age": 18,
  "user_agent": "Mozilla/5.0..."  // Optional
}
```

**Response (Success)**:
```json
{
  "valid": true,
  "message": "Token verified successfully",
  "metadata": {
    "age_verified": true,
    "verification_timestamp": "2024-01-15T12:00:00Z",
    "usage_remaining": 750
  }
}
```

**Response (Failure)**:
```json
{
  "valid": false,
  "message": "User does not meet minimum age requirement (18)",
  "metadata": {
    "user_age": 16,
    "required_age": 18,
    "reason": "age_requirement_not_met"
  }
}
```

**Possible Error Reasons**:
- `verification_failed` - Invalid or expired token
- `device_not_registered` - Device not found in database
- `token_mismatch` - Token doesn't match device
- `age_requirement_not_met` - User is under minimum age

### Health Check

Public endpoint to check API status.

**Endpoint**: `GET /api/v1/health`

**Response**:
```json
{
  "status": "healthy",
  "service": "BlockVerify API",
  "version": "1.0.0",
  "timestamp": "2024-01-15T12:00:00Z"
}
```

## Error Handling

All errors follow a consistent format:

```json
{
  "detail": "Error message here"
}
```

### Common Status Codes

- `200` - Success
- `400` - Bad Request (invalid input)
- `401` - Unauthorized (missing or invalid API key)
- `403` - Forbidden (account suspended)
- `404` - Not Found
- `429` - Too Many Requests (rate limit or usage limit exceeded)
- `500` - Internal Server Error

### Rate Limiting

Rate limits are enforced per API key based on your plan:

- **Free**: 10 requests/minute
- **Starter**: 60 requests/minute
- **Professional**: 300 requests/minute
- **Enterprise**: 1000 requests/minute

When rate limited, you'll receive:

```json
{
  "detail": "Rate limit exceeded. Try again in X seconds."
}
```

### Usage Limits

Monthly verification limits are enforced based on your plan. When exceeded:

```json
{
  "detail": {
    "error": "Monthly usage limit exceeded",
    "usage": 1000,
    "limit": 1000,
    "plan": "free",
    "upgrade_url": "/api/v1/clients/plans"
  }
}
```

## JavaScript SDK Integration

Our JavaScript SDK handles all the complexity for you:

```javascript
// Include the SDK
<script src="https://cdn.jsdelivr.net/gh/yourusername/blockverify@main/client_sdk/blockverify.min.js"></script>

// Initialize with your API key
BlockVerify.init({
    apiKey: 'bv_prod_your_api_key_here',
    minAge: 18,
    onSuccess: (result) => {
        console.log('User verified!', result);
    },
    onFailure: (error) => {
        console.log('Verification failed', error);
    }
});
```

## Server-Side Verification

For server-side token verification:

### Node.js Example

```javascript
const axios = require('axios');

async function verifyAge(token) {
    try {
        const response = await axios.post(
            'https://api.blockverify.com/api/v1/verify-token',
            {
                token: token,
                min_age: 18
            },
            {
                headers: {
                    'Authorization': 'Bearer bv_prod_your_api_key_here',
                    'Content-Type': 'application/json'
                }
            }
        );
        
        return response.data;
    } catch (error) {
        console.error('Verification failed:', error.response.data);
        return { valid: false };
    }
}
```

### Python Example

```python
import requests

def verify_age(token):
    url = "https://api.blockverify.com/api/v1/verify-token"
    headers = {
        "Authorization": "Bearer bv_prod_your_api_key_here",
        "Content-Type": "application/json"
    }
    data = {
        "token": token,
        "min_age": 18
    }
    
    response = requests.post(url, json=data, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Verification failed: {response.json()}")
        return {"valid": False}
```

### cURL Example

```bash
curl -X POST https://api.blockverify.com/api/v1/verify-token \
  -H "Authorization: Bearer bv_prod_your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "token": "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9...",
    "min_age": 18
  }'
```

## Admin Endpoints

Admin endpoints require special authentication (HTTP Basic Auth).

### Admin Dashboard

**Endpoint**: `GET /admin/dashboard`

**Authentication**: HTTP Basic Auth
- Username: `admin` (or set via `ADMIN_USERNAME`)
- Password: `blockverify_admin_2024` (or set via `ADMIN_PASSWORD`)

Returns an HTML dashboard with business metrics and system health.

### Admin Metrics API

**Endpoint**: `GET /admin/metrics`

**Authentication**: HTTP Basic Auth

Returns JSON metrics for programmatic access.

### Admin Health Check

**Endpoint**: `GET /admin/health`

**Authentication**: HTTP Basic Auth

Returns detailed system health information.

## Testing

Use our demo API key for testing:

```
API Key: Contact support for demo key
Base URL: https://your-railway-deployment.railway.app
```

## Support

- **Documentation**: https://docs.blockverify.com
- **Email**: support@blockverify.com
- **GitHub**: https://github.com/yourusername/blockverify

## Changelog

- **v1.0.0** (2024-01) - Initial release with simple billing system
- **v1.1.0** (Coming Soon) - Stripe payment integration 