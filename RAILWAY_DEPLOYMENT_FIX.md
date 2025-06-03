# Railway Deployment Fix

## Issues Fixed

### 1. Missing Dependencies ✅
- **Problem**: Railway was using `demo_adult_site/requirements.txt` which was missing `web3` and other dependencies
- **Solution**: Created comprehensive `requirements.txt` in the root directory with all needed dependencies

### 2. Port Environment Variable Issue ✅  
- **Problem**: `$PORT` wasn't being expanded properly in the start command
- **Solution**: Created `start.sh` script that properly handles environment variable expansion

### 3. Health Check Endpoint ✅
- **Problem**: Railway couldn't find `/health` endpoint
- **Solution**: Added health check endpoint to `backend/app/main.py`

## Files Created/Modified

1. **`requirements.txt`** - Complete dependency list including `web3==6.11.3`
2. **`railway.toml`** - Railway configuration (removed problematic startCommand)
3. **`Dockerfile`** - Updated to use startup script
4. **`start.sh`** - Startup script with proper PORT handling
5. **`backend/app/main.py`** - Added `/health` endpoint

## Deploy Steps

1. **Commit all changes**:
   ```bash
   git add .
   git commit -m "Fix Railway deployment - add dependencies and proper startup"
   git push origin main
   ```

2. **In Railway Dashboard**:
   - Go to your service settings
   - **Clear build cache** (Settings → Redeploy → Clear build cache)
   - The deployment should now work!

3. **Set Environment Variables** (if not already set):
   ```
   DATABASE_URL=${{Postgres.DATABASE_URL}}
   ISSUER_KEY_FILE=/app/issuer_ed25519.jwk
   ENVIRONMENT=production
   ```

## Expected Result

- ✅ All dependencies will install (including `web3`)
- ✅ App will start on the correct port
- ✅ Health check at `/health` will work
- ✅ API will be accessible at your Railway URL

## Test After Deployment

Visit these URLs:
- `https://your-app.railway.app/health` - Should return health status
- `https://your-app.railway.app/` - Should show landing page
- `https://your-app.railway.app/docs` - API documentation (if not production)

## Troubleshooting

- **Build fails**: Make sure all files are committed to Git
- **App still crashes**: Check Railway logs for specific error messages
- **Health check fails**: Verify the `/health` endpoint is working locally first 