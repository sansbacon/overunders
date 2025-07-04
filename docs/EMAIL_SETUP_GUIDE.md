# Email Setup Guide for Over-Under Contests

This guide will help you configure email sending for your Over-Under Contests application. The app uses email for:
- One-time login links (passwordless authentication)
- Contest notifications
- Admin notifications

## Quick Setup Options

### Option 1: Gmail (Recommended for Development)

1. **Enable 2-Factor Authentication** on your Gmail account
2. **Generate an App Password**:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate a password for "Mail"
   - Copy the 16-character password

3. **Update your `.env` file**:
   ```
   MAIL_SERVER=smtp.gmail.com
   MAIL_PORT=587
   MAIL_USE_TLS=true
   MAIL_USERNAME=your-email@gmail.com
   MAIL_PASSWORD=your-16-character-app-password
   MAIL_DEFAULT_SENDER=your-email@gmail.com
   ```

### Option 2: Outlook/Hotmail

```
MAIL_SERVER=smtp-mail.outlook.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@outlook.com
MAIL_PASSWORD=your-password
MAIL_DEFAULT_SENDER=your-email@outlook.com
```

### Option 3: Yahoo Mail

```
MAIL_SERVER=smtp.mail.yahoo.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@yahoo.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@yahoo.com
```

### Option 4: SendGrid (Recommended for Production)

1. Sign up for SendGrid (free tier available)
2. Create an API key
3. Update your `.env` file:
   ```
   MAIL_SERVER=smtp.sendgrid.net
   MAIL_PORT=587
   MAIL_USE_TLS=true
   MAIL_USERNAME=apikey
   MAIL_PASSWORD=your-sendgrid-api-key
   MAIL_DEFAULT_SENDER=your-verified-sender@yourdomain.com
   ```

### Option 5: Mailgun

```
MAIL_SERVER=smtp.mailgun.org
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-mailgun-username
MAIL_PASSWORD=your-mailgun-password
MAIL_DEFAULT_SENDER=your-email@yourdomain.com
```

## Testing Email Configuration

After updating your `.env` file, test the email functionality:

1. **Start your Flask application**:
   ```bash
   python run.py
   ```

2. **Test login email**:
   - Go to the login page
   - Enter your email address
   - Check if you receive the login email

3. **Check Flask logs** for any email errors in the terminal

## Development vs Production

### Development
- Use Gmail with app password for easy setup
- Set `MAIL_USE_TLS=true` for secure connections
- Test with your personal email

### Production
- Use a dedicated email service (SendGrid, Mailgun, etc.)
- Use environment variables for sensitive data
- Set up proper domain authentication (SPF, DKIM)
- Monitor email delivery rates

## Troubleshooting

### Common Issues

1. **"Authentication failed" error**:
   - Check username/password are correct
   - For Gmail, ensure you're using an app password, not your regular password
   - Verify 2FA is enabled for Gmail

2. **"Connection refused" error**:
   - Check MAIL_SERVER and MAIL_PORT settings
   - Verify your internet connection
   - Some networks block SMTP ports

3. **Emails not being received**:
   - Check spam/junk folders
   - Verify the recipient email address
   - Check email service logs

4. **SSL/TLS errors**:
   - Ensure MAIL_USE_TLS=true for port 587
   - Use MAIL_USE_SSL=true for port 465 (if supported)

### Debug Mode

To see detailed email errors, check the Flask application logs in your terminal when running the app.

## Security Best Practices

1. **Never commit email passwords** to version control
2. **Use app passwords** instead of regular passwords when possible
3. **Use environment variables** for all sensitive configuration
4. **Enable 2FA** on your email accounts
5. **Use dedicated email services** for production applications

## Email Templates

The app includes two types of emails:

1. **Login emails** (`send_login_email`):
   - Contains one-time login link
   - Expires in 30 minutes
   - HTML and plain text versions

2. **Contest notifications** (`send_contest_notification`):
   - Contest creation, locking, and results
   - Customizable content

You can modify the email templates in `app/utils/email.py` to match your branding.

## Production Deployment

For Heroku deployment, set environment variables using:

```bash
heroku config:set MAIL_SERVER=smtp.sendgrid.net
heroku config:set MAIL_PORT=587
heroku config:set MAIL_USE_TLS=true
heroku config:set MAIL_USERNAME=apikey
heroku config:set MAIL_PASSWORD=your-sendgrid-api-key
heroku config:set MAIL_DEFAULT_SENDER=noreply@yourdomain.com
```

## Next Steps

1. Choose an email provider from the options above
2. Update your `.env` file with the correct settings
3. Test the email functionality
4. Consider setting up a custom domain for production use

For any issues, check the Flask application logs and verify your email provider's documentation.
