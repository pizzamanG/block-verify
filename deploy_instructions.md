# 🚀 BlockVerify Deployment Guide

Complete guide to deploying BlockVerify to production.

## 📋 Prerequisites

- GitHub account
- Stripe account (for payments)
- Domain name (optional but recommended)

## 1. 🖥️ Backend Deployment Options

### Option A: Railway.app (Recommended - Free Tier Available)

Railway offers the best free tier with PostgreSQL included.

#### Steps:

1. **Sign up at [Railway.app](https://railway.app)**

2. **Connect your GitHub repo:**
   ```bash
   # Push your code to GitHub first
   git add .
   git commit -m "Ready for deployment"
   git push origin main
   ```

3. **Create new project on Railway:**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your BlockVerify repository

4. **Add PostgreSQL database:**
   - In your project dashboard, click "New"
   - Select "Database" → "PostgreSQL"
   - Railway will automatically create `DATABASE_URL` environment variable

5. **Set environment variables:**
   ```bash
   # In Railway dashboard, go to your service → Variables
   CHAIN_RPC_URL=https://rpc-amoy.polygon.technology
   BULLETIN_ADDRESS=0x1234567890123456789012345678901234567890
   STRIPE_SECRET_KEY=sk_test_your_stripe_key_here
   STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_key_here
   ```

6. **Deploy:**
   - Railway will automatically deploy when you push to GitHub
   - Your API will be available at `https://your-project.railway.app`

### Option B: Render.com (Free Alternative)

1. **Sign up at [Render.com](https://render.com)**

2. **Create Web Service:**
   - Connect GitHub repository
   - Use these settings:
     - Build Command: `cd backend && pip install -r requirements.txt`
     - Start Command: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`

3. **Add PostgreSQL:**
   - Create new PostgreSQL database in Render
   - Connect to your web service

4. **Set environment variables** (same as Railway)

### Option C: Heroku (Paid but reliable)

1. **Install Heroku CLI and login:**
   ```bash
   heroku login
   ```

2. **Create app:**
   ```bash
   heroku create your-blockverify-api
   heroku addons:create heroku-postgresql:mini
   ```

3. **Set environment variables:**
   ```bash
   heroku config:set CHAIN_RPC_URL=https://rpc-amoy.polygon.technology
   heroku config:set BULLETIN_ADDRESS=0x1234567890123456789012345678901234567890
   heroku config:set STRIPE_SECRET_KEY=sk_test_your_stripe_key_here
   ```

4. **Deploy:**
   ```bash
   git subtree push --prefix=backend heroku main
   ```

## 2. 🌐 Frontend/CDN Deployment

### Option A: GitHub Pages + jsDelivr (Free CDN)

1. **Enable GitHub Pages:**
   - Go to your repo → Settings → Pages
   - Source: Deploy from branch `main`
   - Folder: `/docs`

2. **Your SDK will be available at:**
   ```html
   <!-- Via jsDelivr CDN (recommended) -->
   <script src="https://cdn.jsdelivr.net/gh/yourusername/blockverify@main/client_sdk/blockverify.min.js"></script>
   
   <!-- Via GitHub Pages -->
   <script src="https://yourusername.github.io/blockverify/client_sdk/blockverify.min.js"></script>
   ```

3. **Update your client SDK to point to your deployed API:**
   ```javascript
   // In client_sdk/blockverify.js, update the API_BASE_URL
   const API_BASE_URL = 'https://your-project.railway.app';
   ```

### Option B: Netlify (Easy deployment)

1. **Connect to Netlify:**
   - Sign up at [Netlify.com](https://netlify.com)
   - Connect GitHub repository
   - Set publish directory to `docs/`

2. **Your SDK will be available at:**
   ```html
   <script src="https://your-site.netlify.app/client_sdk/blockverify.min.js"></script>
   ```

### Option C: Cloudflare Pages (Fast global CDN)

1. **Sign up at [Cloudflare](https://pages.cloudflare.com)**
2. **Connect GitHub repo**
3. **Build settings:**
   - Build command: (leave empty)
   - Build output directory: `docs`

## 3. 💳 Complete Monetization Setup

### Step 1: Stripe Configuration

1. **Create Stripe account at [stripe.com](https://stripe.com)**

2. **Get your API keys:**
   - Go to Developers → API Keys
   - Copy "Publishable key" and "Secret key"

3. **Create Products in Stripe:**
   ```bash
   # Use Stripe CLI or Dashboard to create these products:
   
   # Starter Plan - $29/month
   stripe products create --name="BlockVerify Starter" --description="10K verifications/month"
   stripe prices create --product=prod_starter --currency=usd --unit-amount=2900 --recurring='{"interval":"month"}' --lookup-key="starter_monthly"
   
   # Professional Plan - $99/month  
   stripe products create --name="BlockVerify Professional" --description="100K verifications/month"
   stripe prices create --product=prod_pro --currency=usd --unit-amount=9900 --recurring='{"interval":"month"}' --lookup-key="professional_monthly"
   
   # Enterprise Plan - $299/month
   stripe products create --name="BlockVerify Enterprise" --description="1M verifications/month"
   stripe prices create --product=prod_enterprise --currency=usd --unit-amount=29900 --recurring='{"interval":"month"}' --lookup-key="enterprise_monthly"
   ```

4. **Set up webhooks:**
   - Go to Developers → Webhooks
   - Add endpoint: `https://your-api-url.com/webhooks/stripe`
   - Select events: `invoice.payment_succeeded`, `invoice.payment_failed`, `customer.subscription.deleted`

### Step 2: Client Registration Flow

1. **Clients register via API:**
   ```bash
   curl -X POST https://your-api-url.com/billing/clients/register \
     -H "Content-Type: application/json" \
     -d '{
       "business_name": "Adult Site Inc",
       "contact_email": "admin@adultsite.com", 
       "website_url": "https://adultsite.com"
     }'
   ```

2. **Response includes API key:**
   ```json
   {
     "message": "Client registered successfully",
     "client_id": "uuid-here",
     "api_key": "bv_test_abc123...",
     "plan": "free",
     "monthly_limit": 1000
   }
   ```

### Step 3: Usage Tracking & Billing

The system automatically:
- ✅ Tracks every API call
- ✅ Enforces rate limits
- ✅ Blocks when limits exceeded
- ✅ Generates monthly invoices
- ✅ Processes payments via Stripe

### Step 4: Client Dashboard

Create a simple dashboard for clients:

```html
<!-- Client dashboard at https://your-api-url.com/dashboard -->
<!DOCTYPE html>
<html>
<head>
    <title>BlockVerify Dashboard</title>
</head>
<body>
    <div id="dashboard">
        <!-- Usage stats, billing info, API key management -->
    </div>
    
    <script>
        // Load client info using their API key
        const apiKey = prompt('Enter your API key:');
        
        fetch('/billing/me', {
            headers: { 'Authorization': `Bearer ${apiKey}` }
        })
        .then(res => res.json())
        .then(data => {
            document.getElementById('dashboard').innerHTML = `
                <h1>Welcome, ${data.business_name}</h1>
                <p>Plan: ${data.plan_type}</p>
                <p>Usage: ${data.current_usage}/${data.monthly_limit}</p>
            `;
        });
    </script>
</body>
</html>
```

## 4. 🧪 Testing Your Deployment

### Test 1: API Health Check
```bash
curl https://your-api-url.com/health
# Should return: {"status": "healthy"}
```

### Test 2: Client Registration
```bash
curl -X POST https://your-api-url.com/billing/clients/register \
  -H "Content-Type: application/json" \
  -d '{"business_name": "Test Co", "contact_email": "test@test.com"}'
```

### Test 3: SDK Integration
```html
<!DOCTYPE html>
<html>
<head>
    <title>BlockVerify Test</title>
</head>
<body>
    <h1>Age Verification Test</h1>
    
    <script src="https://cdn.jsdelivr.net/gh/yourusername/blockverify@main/client_sdk/blockverify.min.js"></script>
    <script>
        BlockVerify.init({
            apiKey: 'bv_test_your_api_key_here',
            apiUrl: 'https://your-api-url.com',
            minAge: 18,
            debug: true,
            onSuccess: (result) => {
                console.log('✅ User verified!', result);
                document.body.innerHTML += '<p style="color: green;">✅ Age verified!</p>';
            },
            onFailure: (error) => {
                console.log('❌ Verification failed:', error);
                document.body.innerHTML += '<p style="color: red;">❌ Verification required</p>';
            }
        });
    </script>
</body>
</html>
```

## 5. 📈 Going to Production

### Production Checklist:

- [ ] Switch to Polygon Mainnet (`CHAIN_RPC_URL=https://polygon-rpc.com`)
- [ ] Use production Stripe keys
- [ ] Set up custom domain
- [ ] Enable SSL/HTTPS
- [ ] Set up monitoring (Sentry, DataDog, etc.)
- [ ] Create proper backup strategy
- [ ] Set up log aggregation

### Scaling Considerations:

- **Database**: Upgrade to larger PostgreSQL instance
- **API**: Use multiple instances with load balancer
- **CDN**: Consider AWS CloudFront or Cloudflare for global distribution
- **Caching**: Add Redis for API response caching

## 🎯 Example Pricing Strategy

| Plan | Monthly Fee | Included Verifications | Overage Cost | Target Customer |
|------|-------------|----------------------|--------------|-----------------|
| Free | $0 | 1,000 | N/A (blocked) | Small sites, testing |
| Starter | $29 | 10,000 | $0.03 each | Small adult sites |
| Professional | $99 | 100,000 | $0.02 each | Medium sites |
| Enterprise | $299 | 1,000,000 | $0.01 each | Large platforms |

## 🚀 Launch Strategy

1. **Soft Launch** (Weeks 1-2):
   - Deploy to production
   - Test with 2-3 friendly adult sites
   - Fix any issues

2. **Beta Launch** (Weeks 3-4):
   - Invite 10-20 sites to test
   - Gather feedback
   - Refine pricing

3. **Public Launch** (Week 5+):
   - Create marketing site
   - Reach out to adult content platforms
   - Launch affiliate program

Your BlockVerify service is now ready for production! 🎉 