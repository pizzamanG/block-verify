# 🚀 Deploy Full B2B System with Smart Notifications

## ✅ **Fixed Issues:**
1. **Missing JWT dependency** - Added `PyJWT==2.8.0` to requirements.txt
2. **Smart usage notifications** - Email alerts at 80%, 100%, 150%, 200% usage
3. **Customer email integration** - Uses registered business emails

## 📧 **Email Notification System:**

### **Triggers:**
- ⚠️ **80% quota used**: "Approaching your monthly limit"
- 🚨 **100% quota exceeded**: "Overage billing now active" 
- 🔥 **150% usage**: "High usage detected - review immediately"
- 🚨 **200%+ usage**: "Emergency alert" (sent to customer + internal team)

### **Email Content Example:**
```
Subject: ⚠️ 85% API quota used this month

Hi Acme Adult Site,

You've used 8,500 of your 10,000 monthly API calls (85%).

Current plan: Starter
Remaining calls: 1,500

To avoid overage charges, consider upgrading:
[Upgrade Plan Button]

Overage rates:
• Starter: $0.03 per extra call
• Professional: $0.02 per extra call

Questions? Reply to this email.
```

## 🔧 **Environment Variables for Email:**

Set these in Railway for email notifications:

```env
# Required for full B2B system
DATABASE_URL=${{Postgres.DATABASE_URL}}

# Optional Stripe (for billing)
STRIPE_SECRET_KEY=sk_test_your_key
STRIPE_PUBLISHABLE_KEY=pk_test_your_key

# Email notifications (choose one option)

# Option A: Gmail SMTP (easiest)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-gmail@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=noreply@blockverify.com
FROM_NAME=BlockVerify

# Option B: SendGrid (recommended for production)
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey
SMTP_PASSWORD=your-sendgrid-api-key
FROM_EMAIL=noreply@blockverify.com

# Option C: Mailgun
SMTP_HOST=smtp.mailgun.org
SMTP_PORT=587
SMTP_USERNAME=your-mailgun-smtp-user
SMTP_PASSWORD=your-mailgun-smtp-password
```

## 🚀 **Deploy Commands:**

```bash
git add .
git commit -m "Add smart usage notifications and fix JWT dependency"
git push origin main
```

## 📊 **What Companies Will Experience:**

### **Registration Flow:**
1. Visit: `https://your-app.railway.app/register`
2. Fill out: Company name, business email, domain
3. Get: API key + 10,000 free monthly calls
4. Receive: Welcome email with integration instructions

### **Usage Monitoring:**
1. **Dashboard**: Real-time usage tracking with progress bars
2. **Email alerts**: Automatic notifications at usage thresholds
3. **Upgrade prompts**: Easy one-click plan upgrades
4. **Overage transparency**: Clear billing for extra usage

## 📧 **Email Setup Options:**

### **Quick Setup (Gmail):**
1. Create Gmail app password: https://support.google.com/accounts/answer/185833
2. Set environment variables in Railway
3. Test with your own email first

### **Production Setup (SendGrid):**
1. Create SendGrid account: https://sendgrid.com
2. Get API key from dashboard
3. Add sender verification
4. Set environment variables

### **No Email Setup:**
- System works without email
- Notifications just get logged
- Customers can still see usage in dashboard

## 🧪 **Testing the Notifications:**

### **Manual Test:**
```python
# Test email sending (run locally)
from email_service import create_notification_service

notifier = create_notification_service()
notifier.send_usage_warning(
    company_name="Test Company",
    contact_email="your-email@gmail.com", 
    current_usage=8500,
    monthly_limit=10000,
    plan_type="starter"
)
```

### **Live Test:**
1. Register test company
2. Use API to generate usage
3. Watch for email alerts
4. Check Railway logs for email sending

## 🎯 **Expected Customer Experience:**

```
Day 1: Company registers → Gets API key + welcome email
Day 15: Hits 80% usage → Receives warning email
Day 20: Hits 100% usage → Receives overage alert 
Day 25: High usage spike → Receives critical alert
```

## 🚀 **Ready to Deploy!**

Your system now includes:
- ✅ **Company registration** with API keys
- ✅ **Usage tracking** with real-time quotas
- ✅ **Smart email notifications** at key thresholds
- ✅ **Billing integration** with Stripe
- ✅ **Dashboard** for companies to monitor usage
- ✅ **Overage billing** with transparent pricing

This is a **complete SaaS platform** with professional-grade notifications! 🎉

## 📞 **Support:**
- All email templates are friendly and helpful
- Clear upgrade paths and pricing
- Support contact info included in emails
- Internal alerts for high usage customers 