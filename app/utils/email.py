"""Email utility functions."""
from typing import Optional
from flask import current_app, url_for
from flask_mail import Message
from app import mail

# SendGrid imports
try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail, From, To, Subject, PlainTextContent, HtmlContent
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False
    current_app.logger.warning("SendGrid library not available, falling back to SMTP")


def send_login_email(email: str, token: str) -> bool:
    """Send login email with one-time token.
    
    Args:
        email (str): Recipient email address
        token (str): One-time login token
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        login_url = url_for('auth.login_with_token', token=token, _external=True)
        
        subject = "Your Over-Under Contests Login Link"
        
        body = f"""
        Hello!
        
        You requested to log in to Over-Under Contests. Click the link below to access your account:
        
        {login_url}
        
        This link will expire in 30 minutes for security reasons.
        
        If you didn't request this login, you can safely ignore this email.
        
        Best regards,
        Over-Under Contests Team
        """
        
        html_body = f"""
        <html>
        <body>
            <h2>Over-Under Contests Login</h2>
            <p>Hello!</p>
            <p>You requested to log in to Over-Under Contests. Click the button below to access your account:</p>
            <p>
                <a href="{login_url}" 
                   style="background-color: #007bff; color: white; padding: 12px 24px; 
                          text-decoration: none; border-radius: 4px; display: inline-block;">
                    Log In to Your Account
                </a>
            </p>
            <p>Or copy and paste this link into your browser:</p>
            <p><a href="{login_url}">{login_url}</a></p>
            <p><small>This link will expire in 30 minutes for security reasons.</small></p>
            <p>If you didn't request this login, you can safely ignore this email.</p>
            <hr>
            <p><small>Best regards,<br>Over-Under Contests Team</small></p>
        </body>
        </html>
        """
        
        # Find user for logging
        from app.models import User
        user = User.query.filter_by(email=email).first()
        user_id = user.user_id if user else None
        
        return send_email(
            to_email=email,
            subject=subject,
            body=body,
            html_body=html_body,
            email_type='login',
            user_id=user_id
        )
        
    except Exception as e:
        current_app.logger.error(f"Failed to send login email to {email}: {str(e)}")
        return False


def send_contest_notification(email: str, contest_name: str, message_type: str, 
                            additional_info: Optional[str] = None) -> bool:
    """Send contest-related notification email.
    
    Args:
        email (str): Recipient email address
        contest_name (str): Name of the contest
        message_type (str): Type of notification ('created', 'locked', 'results')
        additional_info (str, optional): Additional information to include
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        subject_map = {
            'created': f"New Contest Created: {contest_name}",
            'locked': f"Contest Locked: {contest_name}",
            'results': f"Contest Results Available: {contest_name}"
        }
        
        body_map = {
            'created': f"A new contest '{contest_name}' has been created and is now available for entries.",
            'locked': f"The contest '{contest_name}' has been locked. No more entries or modifications are allowed.",
            'results': f"Results are now available for the contest '{contest_name}'."
        }
        
        subject = subject_map.get(message_type, f"Contest Update: {contest_name}")
        body = body_map.get(message_type, f"Update regarding contest '{contest_name}'.")
        
        if additional_info:
            body += f"\n\n{additional_info}"
        
        body += "\n\nVisit Over-Under Contests to view more details."
        
        msg = Message(
            subject=subject,
            recipients=[email],
            body=body
        )
        
        mail.send(msg)
        return True
        
    except Exception as e:
        current_app.logger.error(f"Failed to send contest notification to {email}: {str(e)}")
        return False


def send_email_via_sendgrid(to_email: str, subject: str, body: str, html_body: Optional[str] = None, 
                           email_type: str = 'generic', user_id: int = None, contest_id: int = None) -> bool:
    """Send email using SendGrid API.
    
    Args:
        to_email (str): Recipient email address
        subject (str): Email subject
        body (str): Email body (plain text)
        html_body (str, optional): HTML email body
        email_type (str): Type of email for logging
        user_id (int, optional): Associated user ID
        contest_id (int, optional): Associated contest ID
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    from app.models import EmailLog
    
    try:
        api_key = current_app.config.get('SENDGRID_API_KEY')
        from_email = current_app.config.get('MAIL_DEFAULT_SENDER')
        
        # Fallback sender emails to avoid DMARC issues
        if not from_email:
            # Try common fallback patterns
            fallback_senders = [
                'noreply@mail.overunders.games',  # Subdomain approach
                'noreply@overunders.games',       # Main domain (if authenticated)
                'no-reply@overunders.games',      # Alternative format
            ]
            from_email = fallback_senders[0]  # Use first fallback
            current_app.logger.warning(f"MAIL_DEFAULT_SENDER not set, using fallback: {from_email}")
        
        if not api_key:
            error_msg = "SendGrid API key not configured"
            current_app.logger.error(error_msg)
            EmailLog.log_email(to_email, subject, email_type, 'sendgrid_api', 'failed', 
                             error_msg, user_id=user_id, contest_id=contest_id)
            return False
        
        current_app.logger.info(f"Sending email via SendGrid API to {to_email}")
        current_app.logger.info(f"From email: {from_email}")
        current_app.logger.info(f"Subject: {subject}")
        
        # Create the email message
        message = Mail(
            from_email=From(from_email),
            to_emails=To(to_email),
            subject=Subject(subject),
            plain_text_content=PlainTextContent(body)
        )
        
        # Add HTML content if provided
        if html_body:
            message.content = [
                PlainTextContent(body),
                HtmlContent(html_body)
            ]
        
        # Send the email
        sg = SendGridAPIClient(api_key=api_key)
        response = sg.send(message)
        
        current_app.logger.info(f"SendGrid response status: {response.status_code}")
        current_app.logger.info(f"SendGrid response body: {response.body}")
        current_app.logger.info(f"SendGrid response headers: {response.headers}")
        
        # SendGrid returns 202 for successful acceptance
        if response.status_code == 202:
            current_app.logger.info(f"Email sent successfully via SendGrid to {to_email}")
            EmailLog.log_email(to_email, subject, email_type, 'sendgrid_api', 'sent',
                             response_code=response.status_code, 
                             response_body=str(response.body),
                             user_id=user_id, contest_id=contest_id)
            return True
        else:
            error_msg = f"SendGrid returned unexpected status code: {response.status_code}"
            current_app.logger.error(error_msg)
            EmailLog.log_email(to_email, subject, email_type, 'sendgrid_api', 'failed',
                             error_msg, response.status_code, str(response.body),
                             user_id=user_id, contest_id=contest_id)
            return False
            
    except Exception as e:
        error_msg = f"Failed to send email via SendGrid: {str(e)}"
        current_app.logger.error(f"Failed to send email via SendGrid to {to_email}: {str(e)}")
        current_app.logger.error(f"Exception type: {type(e).__name__}")
        EmailLog.log_email(to_email, subject, email_type, 'sendgrid_api', 'failed',
                         error_msg, user_id=user_id, contest_id=contest_id)
        return False


def send_email_via_smtp(to_email: str, subject: str, body: str, html_body: Optional[str] = None,
                       email_type: str = 'generic', user_id: int = None, contest_id: int = None) -> bool:
    """Send email using SMTP (Flask-Mail).
    
    Args:
        to_email (str): Recipient email address
        subject (str): Email subject
        body (str): Email body (plain text)
        html_body (str, optional): HTML email body
        email_type (str): Type of email for logging
        user_id (int, optional): Associated user ID
        contest_id (int, optional): Associated contest ID
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    from app.models import EmailLog
    
    try:
        current_app.logger.info(f"Sending email via SMTP to {to_email}")
        current_app.logger.info(f"Mail server: {current_app.config.get('MAIL_SERVER')}")
        current_app.logger.info(f"Mail username: {current_app.config.get('MAIL_USERNAME')}")
        current_app.logger.info(f"Mail default sender: {current_app.config.get('MAIL_DEFAULT_SENDER')}")
        
        msg = Message(
            subject=subject,
            recipients=[to_email],
            body=body,
            html=html_body
        )
        
        mail.send(msg)
        current_app.logger.info(f"Email sent successfully via SMTP to {to_email}")
        EmailLog.log_email(to_email, subject, email_type, 'smtp', 'sent',
                         user_id=user_id, contest_id=contest_id)
        return True
        
    except Exception as e:
        error_msg = f"Failed to send email via SMTP: {str(e)}"
        current_app.logger.error(f"Failed to send email via SMTP to {to_email}: {str(e)}")
        current_app.logger.error(f"Exception type: {type(e).__name__}")
        current_app.logger.error(f"Exception details: {str(e)}")
        EmailLog.log_email(to_email, subject, email_type, 'smtp', 'failed',
                         error_msg, user_id=user_id, contest_id=contest_id)
        return False


def send_email(to_email: str, subject: str, body: str, html_body: Optional[str] = None,
              email_type: str = 'generic', user_id: int = None, contest_id: int = None) -> bool:
    """Send a generic email using the best available method.
    
    Args:
        to_email (str): Recipient email address
        subject (str): Email subject
        body (str): Email body (plain text)
        html_body (str, optional): HTML email body
        email_type (str): Type of email for logging
        user_id (int, optional): Associated user ID
        contest_id (int, optional): Associated contest ID
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    # Try SendGrid API first if configured and available
    if (current_app.config.get('USE_SENDGRID_API') and 
        SENDGRID_AVAILABLE and 
        current_app.config.get('SENDGRID_API_KEY')):
        
        current_app.logger.info("Using SendGrid API for email delivery")
        success = send_email_via_sendgrid(to_email, subject, body, html_body, email_type, user_id, contest_id)
        
        if success:
            return True
        else:
            current_app.logger.warning("SendGrid API failed, falling back to SMTP")
    
    # Fall back to SMTP
    current_app.logger.info("Using SMTP for email delivery")
    return send_email_via_smtp(to_email, subject, body, html_body, email_type, user_id, contest_id)
