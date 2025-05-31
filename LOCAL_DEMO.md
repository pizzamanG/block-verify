# 🚀 BlockVerify Local Demo Guide

Run a complete BlockVerify demo on your local machine without any external dependencies!

## Quick Start (No Docker Required!)

### 1. Install Python Dependencies

```bash
pip install -r backend/requirements.txt
```

### 2. Run the Local Demo Server

```bash
python run_local_demo.py
```

This will:
- ✅ Start a local server with SQLite (no PostgreSQL needed!)
- ✅ Create a demo client automatically
- ✅ Give you an API key to test with
- ✅ Set up admin credentials: `admin` / `demo123`

### 3. Run the Full Demo Flow

In another terminal:

```bash
python demo_full_flow.py
```

This interactive demo will show you:
1. 📋 Client registration
2. 🔑 API key management
3. ✅ Token verification
4. 📊 Usage tracking
5. 🎯 Admin dashboard
6. 💻 SDK integration

## Alternative: Docker Setup

If you prefer Docker:

```bash
docker-compose -f docker-compose.local.yml up
```

This runs with PostgreSQL instead of SQLite.

## What You Can Test

### 1. **API Endpoints**

- Health Check: http://localhost:8000/api/v1/health
- API Documentation: http://localhost:8000/docs
- Admin Dashboard: http://localhost:8000/admin/dashboard

### 2. **Client Registration Flow**

```bash
# Register a new client
curl -X POST http://localhost:8000/api/v1/clients/register \
  -H "Content-Type: application/json" \
  -d '{
    "business_name": "Test Company",
    "contact_email": "test@example.com",
    "website_url": "https://test.com"
  }'
```

### 3. **Token Verification**

```bash
# Use the API key from registration
curl -X POST http://localhost:8000/api/v1/verify-token \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "token": "test_token",
    "min_age": 18
  }'
```

### 4. **Admin Dashboard**

1. Go to: http://localhost:8000/admin/dashboard
2. Login with:
   - Username: `admin`
   - Password: `demo123`
3. See real-time metrics and analytics

### 5. **JavaScript SDK Test**

Create a test HTML file:

```html
<!DOCTYPE html>
<html>
<head>
    <title>BlockVerify Test</title>
    <script src="http://localhost:8000/static/blockverify.js"></script>
</head>
<body>
    <h1>Age Verification Test</h1>
    <button onclick="testVerification()">Test Age Verification</button>
    
    <script>
    BlockVerify.init({
        apiKey: 'YOUR_API_KEY_HERE',
        apiUrl: 'http://localhost:8000',
        minAge: 18,
        onSuccess: (result) => {
            console.log('Verified!', result);
            alert('Age verified successfully!');
        },
        onFailure: (error) => {
            console.log('Failed:', error);
            alert('Age verification required');
        }
    });
    
    function testVerification() {
        BlockVerify.checkAge();
    }
    </script>
</body>
</html>
```

## Demo Data

The local demo automatically creates:
- 🏢 A demo client: "Local Demo Company"
- 🔑 An API key (shown in console)
- 📊 Sample usage data as you test

## Troubleshooting

### Port Already in Use

If port 8000 is busy:

```bash
# Use a different port
DATABASE_URL=sqlite:///demo.db uvicorn backend.app.main:app --port 8001
```

### Database Issues

The demo uses SQLite by default. To reset:

```bash
rm blockverify_demo.db
python run_local_demo.py
```

### Missing Dependencies

```bash
pip install -r backend/requirements.txt
```

## Next Steps

After testing locally:

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Ready for production"
   git push origin main
   ```

2. **Deploy to Railway**
   - Connect your GitHub repo
   - Add PostgreSQL
   - Set environment variables
   - Deploy!

3. **Test Production**
   - Use the same demo scripts with your Railway URL
   - Update `BASE_URL` in `demo_full_flow.py`

## Features Demonstrated

- ✅ **Privacy-First**: No personal data stored
- ✅ **API Key Auth**: Secure client authentication
- ✅ **Usage Tracking**: Per-client usage limits
- ✅ **Billing Ready**: 4 pricing tiers
- ✅ **Admin Dashboard**: Real-time analytics
- ✅ **JavaScript SDK**: One-line integration
- ✅ **Rate Limiting**: Per-plan limits
- ✅ **Documentation**: Auto-generated API docs

## Support

- Check logs in terminal for debugging
- API docs at http://localhost:8000/docs
- Admin dashboard for metrics
- All data stored in `blockverify_demo.db`

Happy testing! 🎉 