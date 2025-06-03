# 🚀 Deploy Full B2B BlockVerify System on Railway

## 🎯 **What We're Deploying:**
- **B2B Portal**: Company registration, API key management
- **User Dashboard**: Usage monitoring, billing management  
- **Age Verification Site**: Where users verify their age
- **Stripe Billing**: Automatic subscription management
- **Smart Notifications**: Usage alerts via email
- **Production API**: Enterprise token verification

## ✅ **Step 1: Connect Your Database**

You have a `blockverify-db` service running. Connect it to your main app:

### **In Railway Dashboard:**
1. **Go to your main app** (the one that's failing)
2. **Click "Variables" tab**
3. **Add this environment variable**:
   ```
   DATABASE_URL=${{blockverify-db.DATABASE_URL}}
   ```
   
   OR if your database service has a different name:
   ```
   DATABASE_URL=${{your-db-service-name.DATABASE_URL}}
   ```

4. **Click "Deploy"**

## 🔧 **Step 2: Required Environment Variables**

Add these to your main Railway app:

```env
# Database (required)
DATABASE_URL=${{blockverify-db.DATABASE_URL}}

# JWT Secret (required)
JWT_SECRET=your-super-secret-jwt-key-make-this-random

# Stripe (optional - for billing)
STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key
STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_publishable_key

# Email notifications (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=noreply@blockverify.com

# Environment
ENVIRONMENT=production
```

## 🚀 **Step 3: Deploy**

After adding the database connection:

```bash
git add .
git commit -m "Deploy full B2B system with database connection"
git push origin main
```

## 📊 **Step 4: What You'll Get**

### **Main Portal** - `https://your-app.railway.app`
- **Homepage**: Company registration and login
- **Dashboard**: Usage analytics and billing management
- **API Documentation**: Integration guides

### **Company Registration Flow:**
1. Visit `/register`
2. Fill out: Company name, email, domain
3. Get: API key + 10,000 free monthly calls
4. Receive: Welcome email with integration docs

### **Age Verification Site** - `https://your-app.railway.app/verify`
- Where users complete age verification
- Generates JWT tokens for your customers
- Mobile-optimized interface

### **B2B Dashboard** - `https://your-app.railway.app/dashboard`
- Real-time usage tracking
- Plan management and upgrades
- API key management
- Billing history

### **Production API** - `https://your-app.railway.app/api/v1/verify-token`
- Enterprise token verification endpoint
- Rate limiting and authentication
- Usage tracking and billing

## 🧪 **Step 5: Test the Full System**

### **1. Company Registration:**
```bash
curl -X POST "https://your-app.railway.app/api/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Company",
    "email": "test@company.com", 
    "domain": "testcompany.com"
  }'
```

### **2. Age Verification:**
Visit: `https://your-app.railway.app/verify`
- Complete verification flow
- Get JWT token

### **3. Token Verification:**
```bash
curl -X POST "https://your-app.railway.app/api/v1/verify-token" \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"token": "jwt-token-from-verification"}'
```

## 🎯 **Expected File Structure After Deployment:**

```
/
├── / (homepage)
├── /register (company signup)
├── /login (company login)
├── /dashboard (company dashboard)
├── /verify (user age verification)
├── /api/v1/verify-token (production API)
├── /health (health check)
└── /docs (API documentation)
```

## 🚨 **Troubleshooting:**

### **Database Connection Issues:**
- Check the database service name in Railway
- Ensure `DATABASE_URL` variable is set correctly
- Verify the database service is running

### **B2B Portal Not Loading:**
- Check Railway logs for errors
- Verify all required dependencies in requirements.txt
- Make sure PORT environment variable is set

### **Billing Not Working:**
- Add Stripe API keys
- Test with Stripe test keys first
- Check webhook endpoints

## 🎉 **Success Indicators:**

✅ **Health check passes**: `/health` returns "healthy"  
✅ **Registration works**: Can create company accounts  
✅ **Dashboard loads**: Company can see usage stats  
✅ **API works**: Token verification returns responses  
✅ **Billing active**: Usage tracking and overage alerts  

This is your **complete SaaS age verification platform** ready for business customers! 🚀 