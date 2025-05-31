# Railway Deployment Guide

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

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Railway deployment ready"
   git push origin main
   ```

2. **In Railway Dashboard**
   - Your PostgreSQL database should already be deployed ✅
   - The API service should now build with the new Dockerfile
   - Set the environment variables above in the service settings

3. **Verify Deployment**
   - Check build logs for any errors
   - Visit your API URL: `https://your-app.up.railway.app/api/v1/health`
   - Admin dashboard: `https://your-app.up.railway.app/admin/dashboard`

## Common Issues

- **Build fails**: Check that all files are committed to Git
- **App crashes**: Verify all environment variables are set
- **Database errors**: Ensure DATABASE_URL is properly linked from PostgreSQL service 