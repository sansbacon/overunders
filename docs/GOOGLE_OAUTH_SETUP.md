# Google OAuth Setup Guide

This guide will help you set up Google OAuth authentication for your Over-Under Contests application.

## Overview

Google OAuth allows users to sign up and log in using their Google accounts, providing a seamless authentication experience without requiring them to remember additional passwords.

## Prerequisites

- A Google account
- Access to the Google Cloud Console
- Your application deployed (for production setup)

## Step 1: Create a Google Cloud Project

1. **Go to Google Cloud Console**: https://console.cloud.google.com/
2. **Create a new project** or select an existing one
3. **Note your Project ID** for reference

## Step 2: Enable Google+ API

1. **Navigate to APIs & Services** → **Library**
2. **Search for "Google+ API"** or "Google Identity"
3. **Click "Enable"** to activate the API for your project

## Step 3: Configure OAuth Consent Screen

1. **Go to APIs & Services** → **OAuth consent screen**
2. **Choose "External"** (unless you have a Google Workspace account)
3. **Fill in required information**:
   - **App name**: "Over-Under Contests" (or your app name)
   - **User support email**: Your email address
   - **Developer contact information**: Your email address
4. **Add scopes** (click "Add or Remove Scopes"):
   - `../auth/userinfo.email`
   - `../auth/userinfo.profile`
   - `openid`
5. **Save and continue**

## Step 4: Create OAuth 2.0 Credentials

1. **Go to APIs & Services** → **Credentials**
2. **Click "Create Credentials"** → **OAuth 2.0 Client IDs**
3. **Choose "Web application"**
4. **Configure the client**:
   - **Name**: "Over-Under Contests Web Client"
   - **Authorized JavaScript origins**:
     - For development: `http://localhost:5000`
     - For production: `https://yourdomain.com`
   - **Authorized redirect URIs**:
     - For development: `http://localhost:5000/auth/google-callback`
     - For production: `https://yourdomain.com/auth/google-callback`
5. **Click "Create"**
6. **Copy the Client ID and Client Secret** (you'll need these for configuration)

## Step 5: Configure Your Application

### For Local Development

1. **Create or update your `.env` file**:
   ```env
   GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your-client-secret
   ```

2. **Restart your Flask application** to load the new environment variables

### For Heroku Production

1. **Set environment variables on Heroku**:
   ```bash
   heroku config:set GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
   heroku config:set GOOGLE_CLIENT_SECRET=your-client-secret
   ```

2. **Deploy your application** with the Google OAuth code

## Step 6: Test the Integration

### Local Testing

1. **Start your Flask application**:
   ```bash
   flask run
   ```

2. **Navigate to**: http://localhost:5000/auth/login
3. **Click "Continue with Google"**
4. **Complete the Google OAuth flow**
5. **Verify you're logged in successfully**

### Production Testing

1. **Navigate to your production URL**: https://yourdomain.com/auth/login
2. **Click "Continue with Google"**
3. **Complete the Google OAuth flow**
4. **Verify you're logged in successfully**

## How It Works

### User Flow

1. **User clicks "Continue with Google"** on login or register page
2. **Redirected to Google** for authentication
3. **User grants permissions** to your application
4. **Google redirects back** to your application with authorization code
5. **Your application exchanges code** for user information
6. **User is created or updated** in your database
7. **User is logged in** to your application

### Data Stored

When a user logs in with Google, the following information is stored:

- **Google ID**: Unique identifier from Google
- **Email**: User's Google email address
- **Name**: User's display name from Google
- **Profile Picture**: URL to user's Google profile picture
- **Auth Provider**: Set to "google" to distinguish from email-only users

### Account Linking

- **Existing email users**: If a user already exists with the same email address, their account will be linked to Google
- **New users**: A new account will be created automatically
- **Username generation**: Usernames are generated from the email address and made unique

## Security Features

- **Email verification**: Only users with verified Google emails can log in
- **Secure tokens**: OAuth tokens are handled securely by the Authlib library
- **HTTPS required**: Production OAuth requires HTTPS for security
- **Scope limitation**: Only requests basic profile and email information

## Troubleshooting

### Common Issues

#### "redirect_uri_mismatch" Error
- **Cause**: The redirect URI in your Google Console doesn't match your application URL
- **Solution**: Update the authorized redirect URIs in Google Console

#### "invalid_client" Error
- **Cause**: Incorrect Client ID or Client Secret
- **Solution**: Double-check your environment variables match your Google Console credentials

#### "access_denied" Error
- **Cause**: User denied permission or email not verified
- **Solution**: User needs to grant permission and have a verified Google email

#### Google Login Button Not Appearing
- **Cause**: Google OAuth not configured or environment variables missing
- **Solution**: Ensure `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are set

### Debug Mode

To enable debug logging for OAuth issues, add this to your Flask configuration:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Production Considerations

### Domain Verification

For production use, you may need to verify your domain with Google:

1. **Go to Google Search Console**: https://search.google.com/search-console
2. **Add your domain** and verify ownership
3. **Add the verified domain** to your OAuth consent screen

### App Verification

If your app will be used by many users, you may need to go through Google's app verification process:

1. **Complete the OAuth consent screen** thoroughly
2. **Submit for verification** if prompted
3. **Provide privacy policy and terms of service** URLs

### Rate Limits

Google has rate limits for OAuth requests. For high-traffic applications:

- **Monitor your usage** in Google Cloud Console
- **Implement proper error handling** for rate limit responses
- **Consider caching user information** to reduce API calls

## Support

If you encounter issues:

1. **Check the application logs** for detailed error messages
2. **Verify your Google Console configuration** matches your application URLs
3. **Test with a different Google account** to isolate user-specific issues
4. **Review Google's OAuth documentation**: https://developers.google.com/identity/protocols/oauth2

## Additional Resources

- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Authlib Flask Integration](https://docs.authlib.org/en/latest/client/flask.html)
- [Google Cloud Console](https://console.cloud.google.com/)
