# Railway Deployment Guide

## Simplified Deployment (No Shell Scripts!)

Following Railway's best practices:
- No `cd` commands
- No wrapper scripts
- Direct uvicorn execution
- Clean Docker setup

## Environment Variables Required

Set these in your Railway service settings:

```env
# Database (automatically set by Railway PostgreSQL)
DATABASE_URL=${{Postgres.DATABASE_URL}}

# Required Keys
ISSUER_KEY_FILE=/app/issuer_ed25519.jwk

# Admin Dashboard
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_secure_password_here

# Optional
ENVIRONMENT=production
LOG_LEVEL=INFO
```

## Deployment Steps

1. **Clear Railway Cache** (if you had previous failed deployments)
   - In Railway dashboard, go to your service
   - Settings → Redeploy → "Clear build cache"

2. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Railway deployment - complete dependencies"
   git push origin main
   ```

3. **In Railway Dashboard**
   - Your PostgreSQL database should already be deployed ✅
   - The API service should now build with the simplified Dockerfile
   - Set the environment variables above in the service settings

4. **Verify Deployment**
   - Check build logs for any errors
   - Visit your Railway URL to see the landing page
   - Test the health endpoint: `https://your-app.railway.app/api/v1/health`

## What Changed
- Removed all wrapper scripts
- Using direct uvicorn command in Dockerfile
- Proper exec form with sh -c for environment variable expansion
- No directory changes or complex shell operations
- Complete requirements.txt with all dependencies

## Dependency Notes
- All Python dependencies are in `backend/requirements.txt`
- Blockchain support requires `web3` and `eth-account`
- Stripe is optional and won't break deployment if missing

## Troubleshooting
- If you see "cd not found" errors, clear the build cache
- If you see "ModuleNotFoundError", check backend/requirements.txt
- Railway automatically sets the PORT environment variable
- The app will default to port 8000 if PORT is not set

## Common Issues

- **Build fails**: Check that all files are committed to Git
- **App crashes**: Verify all environment variables are set
- **Database errors**: Ensure DATABASE_URL is properly linked from PostgreSQL service 