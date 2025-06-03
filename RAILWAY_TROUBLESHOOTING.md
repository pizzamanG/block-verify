# Railway Deployment Troubleshooting

## Current Issue: Health Check Failing

Your app builds successfully but the `/health` endpoint is not responding, causing Railway's health check to fail.

## 🔧 **Quick Fix Options**

### Option 1: Use the Improved Main App (Recommended)

I've made the main app more resilient with better error handling:

1. **Commit the improved version**:
   ```bash
   git add .
   git commit -m "Improve app resilience for Railway deployment"
   git push origin main
   ```

2. **Clear Railway cache** and redeploy:
   - Railway Dashboard → Your Service → Settings → Redeploy
   - Check "Clear build cache"
   - Deploy

### Option 2: Test with Minimal App (For Debugging)

If the main app still fails, use the minimal test app to verify basic deployment:

1. **Update railway.toml** to use minimal app:
   ```toml
   [build]
   builder = "DOCKERFILE"
   dockerfilePath = "Dockerfile.minimal"

   [deploy]
   healthcheckPath = "/health"
   restartPolicyType = "ON_FAILURE"
   restartPolicyMaxRetries = 10
   ```

2. **Commit and deploy**:
   ```bash
   git add .
   git commit -m "Test minimal app deployment"
   git push origin main
   ```

3. **If minimal app works**, gradually add back complexity.

### Option 3: Check Railway Logs

1. **View deployment logs** in Railway dashboard
2. **Look for specific error messages** in the build/runtime logs
3. **Common issues to look for**:
   - Import errors
   - Missing environment variables
   - Database connection failures
   - Port binding issues

## 🔍 **Environment Variables to Set**

Make sure these are set in Railway:

```env
# Essential
PORT=8000
PYTHONPATH=/app

# Database (if using PostgreSQL addon)
DATABASE_URL=${{Postgres.DATABASE_URL}}

# Optional (for full functionality)
ISSUER_KEY_FILE=/app/issuer_ed25519.jwk
ENVIRONMENT=production
LOG_LEVEL=INFO
```

## 🐛 **Common Issues & Solutions**

### 1. Static Files Error
**Error**: `StaticFiles directory not found`
**Solution**: The improved main.py now handles missing frontend directory gracefully.

### 2. Database Connection Error
**Error**: Database connection fails during startup
**Solution**: The improved main.py can start without database and show degraded status.

### 3. Import Errors
**Error**: Missing Python modules
**Solution**: All dependencies are in the root `requirements.txt`.

### 4. Port Binding Issues
**Error**: `$PORT` not expanded properly
**Solution**: The improved `start.sh` script handles this correctly.

## 📋 **Deployment Checklist**

- ✅ Root `requirements.txt` with all dependencies
- ✅ `Dockerfile` in root directory
- ✅ `start.sh` script with proper PORT handling
- ✅ Resilient `backend/app/main.py` with error handling
- ✅ Railway environment variables set
- ✅ Build cache cleared

## 🚨 **Emergency Fallback**

If nothing works, you can deploy just the production API file:

1. **Create simple deployment**:
   ```dockerfile
   FROM python:3.11-slim
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   COPY production_api.py .
   COPY issuer_ed25519.jwk .
   CMD ["uvicorn", "production_api:app", "--host", "0.0.0.0", "--port", "8000"]
   ```

2. **Update railway.toml**:
   ```toml
   [deploy]
   healthcheckPath = "/health"
   ```

## 📞 **Next Steps**

1. **Try Option 1 first** (improved main app)
2. **Check Railway logs** for specific errors
3. **Try Option 2** (minimal app) if Option 1 fails
4. **Share specific error messages** from Railway logs for more targeted help

The improved version should handle most common deployment issues gracefully! 🎯 