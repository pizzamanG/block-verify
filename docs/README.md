# 📚 BlockVerify Documentation

Welcome to the BlockVerify documentation! This guide covers everything you need to know about deploying and operating the privacy-preserving age verification platform.

## 🚀 Quick Start

1. **Deploy to Railway**
   ```bash
   git push origin main
   # Connect GitHub repo to Railway
   # Add PostgreSQL database
   # Set environment variables
   ```

2. **Register as a Client**
   ```bash
   curl -X POST https://your-api.railway.app/api/v1/clients/register \
     -H "Content-Type: application/json" \
     -d '{"business_name": "Your Company", "contact_email": "you@company.com"}'
   ```

3. **Integrate the SDK**
   ```html
   <script src="https://cdn.jsdelivr.net/gh/yourusername/blockverify@main/client_sdk/blockverify.min.js"></script>
   <script>
   BlockVerify.init({
       apiKey: 'your_api_key_here',
       minAge: 18
   });
   </script>
   ```

## 📖 Documentation Structure

### 🏗️ Technical Documentation
- **[Architecture Overview](technical/architecture.md)** - System design and data flows
- **[API Reference](api/api-reference.md)** - Complete API documentation
- **[Deployment Guide](deployment/production-checklist.md)** - Production deployment checklist

### 💼 Business Documentation
- **[Business Model](business/business-model.md)** - Revenue projections and market analysis
- **[Pricing Plans](api/api-reference.md#get-available-plans)** - Current pricing tiers

### 📊 Operations
- **[Monitoring Guide](monitoring/railway-dashboard.md)** - Admin dashboard and metrics
- **[Client Onboarding](api/api-reference.md#client-registration--management)** - How businesses get started

## 🔑 Key Features

### Privacy-First Design
- ✅ Zero-knowledge age verification
- ✅ No personal data stored
- ✅ Device-bound tokens
- ✅ GDPR/CCPA compliant

### Complete Business Platform
- ✅ Client registration system
- ✅ API key management
- ✅ Usage-based billing
- ✅ Admin dashboard
- ✅ Revenue tracking

### Developer-Friendly
- ✅ RESTful API
- ✅ JavaScript SDK
- ✅ Multiple auth methods
- ✅ Comprehensive docs

## 💰 Monetization

### Pricing Tiers
- **Free**: 1,000 verifications/month
- **Starter**: $29/month for 10,000 verifications
- **Professional**: $99/month for 100,000 verifications
- **Enterprise**: $299+/month for 1M+ verifications

### Revenue Model
- Usage-based pricing
- No setup fees
- Monthly billing
- Automatic usage tracking

## 🛠️ Technology Stack

- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL
- **Authentication**: WebAuthn + JWT
- **Deployment**: Railway/Docker
- **CDN**: jsDelivr (for SDK)

## 📞 Support

- **Documentation**: You're here!
- **API Status**: `https://your-api.railway.app/api/v1/health`
- **Admin Dashboard**: `https://your-api.railway.app/admin/dashboard`

## 🚦 System Status

All systems operational. Check the [admin dashboard](monitoring/railway-dashboard.md) for real-time metrics.

---

*BlockVerify - Privacy-preserving age verification for the modern web* 