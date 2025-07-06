# Quick Fix: Google OAuth "redirect_uri_mismatch" Error

## The Error
```
Error 400: redirect_uri_mismatch
You can't sign in to this app because it doesn't comply with Google's OAuth 2.0 policy.
Request details: redirect_uri=http://localhost:5000/auth/google-callback
```

## Quick Solution

### Step 1: Go to Google Cloud Console
1. Visit: https://console.cloud.google.com/
2. Select your project (or create one if you haven't)

### Step 2: Navigate to Credentials
1. Go to **APIs & Services** → **Credentials**
2. Find your OAuth 2.0 Client ID (or create one if missing)
3. Click the **pencil icon** to edit

### Step 3: Add Redirect URI
1. In the **Authorized redirect URIs** section, click **+ ADD URI**
2. Add: `http://localhost:5000/auth/google-callback`
3. Click **SAVE**

### Step 4: Test
1. Wait 1-2 minutes for changes to propagate
2. Try Google login again in your application

## Complete Setup (If Starting Fresh)

If you don't have Google OAuth set up at all:

### 1. Create OAuth 2.0 Credentials
1. **APIs & Services** → **Credentials** → **Create Credentials** → **OAuth 2.0 Client IDs**
2. **Application type**: Web application
3. **Name**: "Over-Under Contests Local Dev"
4. **Authorized JavaScript origins**: `http://localhost:5000`
5. **Authorized redirect URIs**: `http://localhost:5000/auth/google-callback`
6. Click **CREATE**

### 2. Configure Environment Variables
1. Copy the **Client ID** and **Client Secret**
2. Create/update your `.env` file:
   ```env
   GOOGLE_CLIENT_ID=your-client-id-here.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your-client-secret-here
   ```

### 3. Restart Flask Application
```bash
# Stop the current Flask app (Ctrl+C)
flask run
```

## Production Setup

For production deployment, also add:
- **Authorized JavaScript origins**: `https://yourdomain.com`
- **Authorized redirect URIs**: `https://yourdomain.com/auth/google-callback`

## Still Having Issues?

1. **Check environment variables** are loaded correctly
2. **Verify the redirect URI** matches exactly (including http vs https)
3. **Wait a few minutes** after making changes in Google Console
4. **Clear browser cache** and try again
5. **Check Flask logs** for detailed error messages

For complete setup instructions, see: [GOOGLE_OAUTH_SETUP.md](GOOGLE_OAUTH_SETUP.md)
