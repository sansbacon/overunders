# Email Authentication and DMARC Fix Guide

## Problem
Your emails are being blocked due to DMARC policy violations:
```
550 5.7.26 Unauthenticated email from overunders.games is not accepted due to domain's DMARC policy
```

This happens when:
1. Your domain has a DMARC policy set to `reject` or `quarantine`
2. The email doesn't pass SPF and/or DKIM authentication
3. The "From" address domain doesn't match the sending server's authentication

## Immediate Solutions

### Option 1: Use SendGrid with Domain Authentication (Recommended)

**Step 1: Set up SendGrid Domain Authentication**

1. **Login to SendGrid Dashboard**
2. **Go to Settings → Sender Authentication**
3. **Click "Authenticate Your Domain"**
4. **Enter your domain: `overunders.games`**
5. **Choose "Yes" for branded links**
6. **SendGrid will provide DNS records**

**Step 2: Add DNS Records**
Add these records to your domain's DNS (through your domain registrar):

```
Type: CNAME
Name: s1._domainkey.overunders.games
Value: s1.domainkey.u[XXXXX].wl[XXX].sendgrid.net

Type: CNAME  
Name: s2._domainkey.overunders.games
Value: s2.domainkey.u[XXXXX].wl[XXX].sendgrid.net

Type: CNAME
Name: em[XXXX].overunders.games
Value: u[XXXXX].wl[XXX].sendgrid.net
```

**Step 3: Update Environment Variables**
```bash
heroku config:set USE_SENDGRID_API=true
heroku config:set MAIL_DEFAULT_SENDER=noreply@overunders.games
heroku config:set SENDGRID_API_KEY=your_sendgrid_api_key
```

### Option 2: Use a Subdomain (Quick Fix)

**Step 1: Use a subdomain for emails**
```bash
heroku config:set MAIL_DEFAULT_SENDER=noreply@mail.overunders.games
```

**Step 2: Set up DNS for subdomain**
Add SPF record for the subdomain:
```
Type: TXT
Name: mail.overunders.games
Value: v=spf1 include:sendgrid.net ~all
```

### Option 3: Modify DMARC Policy (Temporary)

**Current DMARC policy is likely:**
```
v=DMARC1; p=reject; rua=mailto:admin@overunders.games
```

**Change to (temporarily):**
```
v=DMARC1; p=none; rua=mailto:admin@overunders.games
```

⚠️ **Warning**: This reduces email security for your domain.

## Complete Email Authentication Setup

### 1. SPF Record
Add this TXT record to your domain:
```
Type: TXT
Name: overunders.games
Value: v=spf1 include:sendgrid.net ~all
```

### 2. DKIM Records
SendGrid will provide these when you authenticate your domain.

### 3. DMARC Record
After SPF and DKIM are working:
```
Type: TXT
Name: _dmarc.overunders.games
Value: v=DMARC1; p=quarantine; rua=mailto:admin@overunders.games; pct=100
```

## Application Configuration Updates

### Update Config for SendGrid Domain Authentication

```python
# In config.py - already configured correctly
SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
USE_SENDGRID_API = os.environ.get('USE_SENDGRID_API', 'false').lower() in ['true', 'on', '1']
MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
```

### Environment Variables Needed
```bash
# Required for authenticated sending
SENDGRID_API_KEY=SG.your_api_key_here
USE_SENDGRID_API=true
MAIL_DEFAULT_SENDER=noreply@overunders.games

# Optional: Custom reply-to
MAIL_REPLY_TO=support@overunders.games
```

## Testing Email Authentication

### 1. SendGrid Domain Verification
- Check SendGrid dashboard for green checkmarks
- All DNS records must be verified

### 2. SPF Check
```bash
dig TXT overunders.games | grep spf
```

### 3. DKIM Check
```bash
dig TXT s1._domainkey.overunders.games
dig TXT s2._domainkey.overunders.games
```

### 4. DMARC Check
```bash
dig TXT _dmarc.overunders.games
```

### 5. Send Test Email
Use the admin panel to send a test email and check the email logs.

## Troubleshooting Common Issues

### Issue 1: DNS Propagation
- DNS changes can take up to 48 hours to propagate
- Use online DNS checkers to verify records

### Issue 2: SendGrid Domain Not Verified
- Ensure all DNS records are added correctly
- Check for typos in DNS record values
- Contact SendGrid support if verification fails

### Issue 3: DMARC Still Failing
- Verify SPF includes SendGrid: `include:sendgrid.net`
- Ensure DKIM records are properly configured
- Check DMARC alignment (domain in From header matches authenticated domain)

## Alternative Email Providers

If SendGrid doesn't work, consider:

### 1. Mailgun
```bash
heroku addons:create mailgun:starter
```

### 2. Amazon SES
- Requires domain verification
- More complex setup but very reliable

### 3. Postmark
- Excellent deliverability
- Simple domain authentication

## Monitoring and Maintenance

### 1. DMARC Reports
Set up DMARC reporting to monitor authentication:
```
v=DMARC1; p=quarantine; rua=mailto:dmarc-reports@overunders.games; pct=100
```

### 2. Regular Testing
- Test email delivery monthly
- Monitor bounce rates in SendGrid
- Check email logs in admin panel

### 3. Domain Reputation
- Maintain good sending practices
- Monitor spam complaints
- Keep bounce rates low

## Immediate Action Plan

**Step 1 (5 minutes)**: Change sender email to subdomain
```bash
heroku config:set MAIL_DEFAULT_SENDER=noreply@mail.overunders.games
```

**Step 2 (30 minutes)**: Set up SendGrid domain authentication
- Follow SendGrid domain authentication wizard
- Add provided DNS records

**Step 3 (24-48 hours)**: Wait for DNS propagation
- Monitor email logs for successful delivery
- Test with different email providers

**Step 4**: Gradually increase email volume
- Start with small batches
- Monitor delivery rates
- Adjust DMARC policy as needed

## Security Best Practices

1. **Use strong DMARC policy** after authentication is working
2. **Monitor DMARC reports** for unauthorized usage
3. **Rotate SendGrid API keys** regularly
4. **Use dedicated IP** for high volume (SendGrid Pro+)
5. **Implement email rate limiting** to avoid being flagged as spam

## Support Resources

- **SendGrid Support**: https://support.sendgrid.com/
- **DMARC Analyzer**: https://www.dmarcanalyzer.com/
- **MXToolbox**: https://mxtoolbox.com/dmarc.aspx
- **Google Postmaster Tools**: https://postmaster.google.com/

The key is to properly authenticate your domain with SendGrid so that emails sent through their service pass SPF, DKIM, and DMARC checks.
