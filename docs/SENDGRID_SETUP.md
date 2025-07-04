# SendGrid Setup Guide for Over-Under Contests

This guide will walk you through setting up SendGrid for your Over-Under Contests application.

## Why SendGrid?

- **Reliable delivery**: High deliverability rates
- **Free tier**: 100 emails/day forever
- **Easy setup**: Simple API integration
- **Analytics**: Email tracking and statistics
- **Production ready**: Scales with your application

## Step-by-Step Setup

### 1. Create SendGrid Account

1. Go to [https://sendgrid.com](https://sendgrid.com)
2. Click "Start for Free"
3. Fill out the registration form
4. Verify your email address
5. Complete the account setup process

### 2. Create an API Key

1. **Log in to SendGrid Dashboard**
2. **Navigate to Settings → API Keys**
3. **Click "Create API Key"**
4. **Choose "Restricted Access"** (recommended for security)
5. **Set permissions**:
   - Mail Send: **FULL ACCESS**
   - All other permissions: **No Access** (for security)
6. **Name your key** (e.g., "Over-Under-Contests-App")
7. **Click "Create & View"**
8. **Copy the API key** (you won't see it again!)

### 3. Set Up Sender Authentication

#### Option A: Single Sender Verification (Quick Start)
1. **Go to Settings → Sender Authentication**
2. **Click "Verify a Single Sender"**
3. **Fill out the form**:
   - From Name: `Over-Under Contests`
   - From Email: `your-email@yourdomain.com` (or your personal email for testing)
   - Reply To: Same as From Email
   - Company Address: Your address
4. **Click "Create"**
5. **Check your email and click the verification link**

#### Option B: Domain Authentication (Production Recommended)
1. **Go to Settings → Sender Authentication**
2. **Click "Authenticate Your Domain"**
3. **Enter your domain** (e.g., `yourdomain.com`)
4. **Follow DNS setup instructions**
5. **Verify domain ownership**

### 4. Update Your .env File

Replace the placeholder values in your `.env` file:

```env
# Email Configuration - SendGrid Setup
MAIL_SERVER=smtp.sendgrid.net
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=apikey
MAIL_PASSWORD=SG.your-actual-api-key-here
MAIL_DEFAULT_SENDER=your-verified-email@yourdomain.com
```

**Important Notes**:
- `MAIL_USERNAME` must be exactly `apikey` (this is SendGrid's requirement)
- `MAIL_PASSWORD` is your SendGrid API key (starts with `SG.`)
- `MAIL_DEFAULT_SENDER` must be the email you verified in step 3

### 5. Test Your Setup

1. **Start your Flask application**:
   ```bash
   python run.py
   ```

2. **Test the login email**:
   - Go to `http://localhost:5000/auth/login`
   - Enter your email address
   - Click "Send Login Link"
   - Check your email (and spam folder)

3. **Check for errors** in the Flask terminal output

## SendGrid Free Tier Limits

- **100 emails per day** forever
- **2,000 contacts**
- **Email validation**: 100 validations/month
- **Basic analytics**

For higher volumes, SendGrid offers paid plans starting at $14.95/month for 40,000 emails.

## Troubleshooting

### Common Issues

1. **"Authentication failed" error**:
   - Verify your API key is correct and starts with `SG.`
   - Ensure `MAIL_USERNAME=apikey` (exactly as shown)
   - Check that your API key has "Mail Send" permissions

2. **"Sender not verified" error**:
   - Complete sender verification in SendGrid dashboard
   - Use the exact email address you verified
   - Check verification email and click the link

3. **Emails not being delivered**:
   - Check SendGrid Activity dashboard for delivery status
   - Verify recipient email addresses
   - Check spam/junk folders
   - Ensure you haven't exceeded daily limits

4. **"Invalid sender" error**:
   - Make sure `MAIL_DEFAULT_SENDER` matches your verified sender
   - Complete domain authentication if using a custom domain

### Checking Email Status

1. **SendGrid Dashboard → Activity**
2. **View email delivery status, opens, clicks**
3. **Check for bounces or spam reports**

## Production Considerations

### Security
- **Store API key securely** (environment variables, not in code)
- **Use restricted API keys** with minimal permissions
- **Rotate API keys** periodically
- **Never commit API keys** to version control

### Domain Setup
- **Set up domain authentication** for better deliverability
- **Configure SPF, DKIM, and DMARC** records
- **Use a dedicated subdomain** (e.g., `mail.yourdomain.com`)

### Monitoring
- **Set up webhooks** for delivery events
- **Monitor bounce rates** and spam reports
- **Track email engagement** metrics
- **Set up alerts** for delivery issues

## Heroku Deployment

For Heroku, set environment variables:

```bash
heroku config:set MAIL_SERVER=smtp.sendgrid.net
heroku config:set MAIL_PORT=587
heroku config:set MAIL_USE_TLS=true
heroku config:set MAIL_USERNAME=apikey
heroku config:set MAIL_PASSWORD=SG.your-sendgrid-api-key
heroku config:set MAIL_DEFAULT_SENDER=noreply@yourdomain.com
```

## SendGrid Add-on for Heroku

Alternatively, you can use the SendGrid Heroku add-on:

```bash
heroku addons:create sendgrid:starter
```

This automatically sets up the environment variables for you.

## Email Templates Enhancement

Consider customizing your email templates in `app/utils/email.py` to include:
- Your branding/logo
- Consistent styling
- Unsubscribe links (for marketing emails)
- Contact information

## Next Steps

1. ✅ Create SendGrid account
2. ✅ Generate API key with Mail Send permissions
3. ✅ Verify sender email address
4. ✅ Update `.env` file with your credentials
5. ✅ Test email functionality
6. 🔄 Set up domain authentication (for production)
7. 🔄 Monitor email delivery and engagement

## Support

- **SendGrid Documentation**: [https://docs.sendgrid.com](https://docs.sendgrid.com)
- **SendGrid Support**: Available through dashboard
- **Community**: SendGrid has an active developer community

Your Over-Under Contests app is now ready to send reliable emails through SendGrid!
