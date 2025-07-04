"""Invitation utilities for sending email and SMS invitations."""
import re
from typing import List, Dict, Any
from flask import url_for, current_app
from app import db
from app.models import Contest, ContestInvitation, User
from app.utils.email import send_email


def validate_email(email: str) -> bool:
    """Validate email address format.
    
    Args:
        email (str): Email address to validate
        
    Returns:
        bool: True if valid email format, False otherwise
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_phone(phone: str) -> bool:
    """Validate phone number format (basic validation).
    
    Args:
        phone (str): Phone number to validate
        
    Returns:
        bool: True if valid phone format, False otherwise
    """
    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', phone)
    # Check if it's 10 or 11 digits (US format)
    return len(digits_only) in [10, 11]


def format_phone(phone: str) -> str:
    """Format phone number to standard format.
    
    Args:
        phone (str): Phone number to format
        
    Returns:
        str: Formatted phone number
    """
    digits_only = re.sub(r'\D', '', phone)
    if len(digits_only) == 10:
        return f"+1{digits_only}"
    elif len(digits_only) == 11 and digits_only.startswith('1'):
        return f"+{digits_only}"
    return phone


def create_invitation_email_content(contest: Contest, sender: User) -> Dict[str, str]:
    """Create email content for contest invitation.
    
    Args:
        contest (Contest): Contest to invite to
        sender (User): User sending the invitation
        
    Returns:
        Dict[str, str]: Email subject and body
    """
    contest_url = url_for('contests.view_contest', contest_id=contest.contest_id, _external=True)
    
    # Convert UTC time to Central Time
    from app.utils.timezone import convert_from_utc
    central_lock_time = convert_from_utc(contest.lock_timestamp, 'America/Chicago')
    lock_time = central_lock_time.strftime('%B %d, %Y at %I:%M %p Central Time')
    
    subject = f"You're invited to join '{contest.contest_name}' contest!"
    
    body = f"""
Hello!

{sender.get_display_name()} has invited you to participate in an exciting Over-Under contest!

**Contest Details:**
• Contest Name: {contest.contest_name}
• Created by: {sender.get_display_name()}
{f'• Description: {contest.description}' if contest.description else ''}

**How it works:**
Over-Under contests are simple and fun! You'll be presented with a series of questions where you predict whether something will happen (Yes) or not happen (No). After the contest locks, the correct answers are revealed and scores are calculated based on how many questions you got right.

**IMPORTANT - Entry Deadline:**
**Entries must be submitted before: {lock_time}**

After this time, no new entries or modifications will be accepted.

**Ready to play?**
Click here to view the contest and submit your entry:
{contest_url}

If you don't have an account yet, you can quickly register using just your email address - no password required!

Good luck and have fun!

---
Over-Under Contests
"""
    
    return {
        'subject': subject,
        'body': body
    }


def create_invitation_sms_content(contest: Contest, sender: User) -> str:
    """Create SMS content for contest invitation.
    
    Args:
        contest (Contest): Contest to invite to
        sender (User): User sending the invitation
        
    Returns:
        str: SMS message content
    """
    contest_url = url_for('contests.view_contest', contest_id=contest.contest_id, _external=True)
    lock_time = contest.lock_timestamp.strftime('%m/%d/%Y %I:%M %p UTC')
    
    message = f"""🎯 Contest Invitation!

{sender.get_display_name()} invited you to '{contest.contest_name}'

Predict Yes/No answers to win!

⏰ DEADLINE: {lock_time}

Join here: {contest_url}

Over-Under Contests"""
    
    return message


def send_email_invitation(contest: Contest, sender: User, recipient_email: str) -> bool:
    """Send email invitation for contest.
    
    Args:
        contest (Contest): Contest to invite to
        sender (User): User sending the invitation
        recipient_email (str): Email address to send to
        
    Returns:
        bool: True if sent successfully, False otherwise
    """
    try:
        current_app.logger.info(f"Creating invitation email content for contest {contest.contest_id}")
        email_content = create_invitation_email_content(contest, sender)
        
        current_app.logger.info(f"Sending invitation email to {recipient_email}")
        current_app.logger.info(f"Email subject: {email_content['subject']}")
        
        success = send_email(
            to_email=recipient_email,
            subject=email_content['subject'],
            body=email_content['body'],
            email_type='invitation',
            user_id=sender.user_id,
            contest_id=contest.contest_id
        )
        
        current_app.logger.info(f"Email send result: {success}")
        
        if success:
            # Record the invitation
            invitation = ContestInvitation(
                contest_id=contest.contest_id,
                sent_by_user_id=sender.user_id,
                recipient_email=recipient_email,
                invitation_type='email',
                status='sent'
            )
            db.session.add(invitation)
            db.session.commit()
            current_app.logger.info(f"Recorded successful invitation to {recipient_email}")
            return True
        else:
            # Record failed invitation
            invitation = ContestInvitation(
                contest_id=contest.contest_id,
                sent_by_user_id=sender.user_id,
                recipient_email=recipient_email,
                invitation_type='email',
                status='failed'
            )
            db.session.add(invitation)
            db.session.commit()
            current_app.logger.info(f"Recorded failed invitation to {recipient_email}")
            return False
            
    except Exception as e:
        current_app.logger.error(f"Error sending email invitation: {str(e)}")
        current_app.logger.error(f"Exception type: {type(e).__name__}")
        return False


def send_sms_invitation(contest: Contest, sender: User, recipient_phone: str) -> bool:
    """Send SMS invitation for contest.
    
    Args:
        contest (Contest): Contest to invite to
        sender (User): User sending the invitation
        recipient_phone (str): Phone number to send to
        
    Returns:
        bool: True if sent successfully, False otherwise
    """
    try:
        # For now, we'll just record the invitation as sent
        # In a real implementation, you would integrate with an SMS service like Twilio
        formatted_phone = format_phone(recipient_phone)
        sms_content = create_invitation_sms_content(contest, sender)
        
        # TODO: Integrate with SMS service (Twilio, etc.)
        # For now, we'll simulate success and log the message
        current_app.logger.info(f"SMS invitation would be sent to {formatted_phone}: {sms_content}")
        
        # Record the invitation
        invitation = ContestInvitation(
            contest_id=contest.contest_id,
            sent_by_user_id=sender.user_id,
            recipient_phone=formatted_phone,
            invitation_type='sms',
            status='sent'  # In real implementation, this would be based on SMS service response
        )
        db.session.add(invitation)
        db.session.commit()
        
        # For demo purposes, return True
        # In real implementation, return based on SMS service response
        return True
        
    except Exception as e:
        current_app.logger.error(f"Error sending SMS invitation: {str(e)}")
        return False


def send_bulk_invitations(contest: Contest, sender: User, emails: List[str], phones: List[str]) -> Dict[str, Any]:
    """Send bulk invitations via email and SMS.
    
    Args:
        contest (Contest): Contest to invite to
        sender (User): User sending the invitations
        emails (List[str]): List of email addresses
        phones (List[str]): List of phone numbers
        
    Returns:
        Dict[str, Any]: Results summary
    """
    results = {
        'email_sent': 0,
        'email_failed': 0,
        'sms_sent': 0,
        'sms_failed': 0,
        'total_sent': 0,
        'errors': []
    }
    
    total_invitations = len(emails) + len(phones)
    
    # Check invitation limit
    if not contest.can_send_more_invitations(total_invitations):
        remaining = contest.get_remaining_invitations()
        results['errors'].append(f"Cannot send {total_invitations} invitations. Only {remaining} invitations remaining for this contest (max 100 per contest).")
        return results
    
    # Send email invitations
    for email in emails:
        if validate_email(email):
            if send_email_invitation(contest, sender, email):
                results['email_sent'] += 1
                results['total_sent'] += 1
            else:
                results['email_failed'] += 1
                results['errors'].append(f"Failed to send email to {email}")
        else:
            results['email_failed'] += 1
            results['errors'].append(f"Invalid email format: {email}")
    
    # Send SMS invitations
    for phone in phones:
        if validate_phone(phone):
            if send_sms_invitation(contest, sender, phone):
                results['sms_sent'] += 1
                results['total_sent'] += 1
            else:
                results['sms_failed'] += 1
                results['errors'].append(f"Failed to send SMS to {phone}")
        else:
            results['sms_failed'] += 1
            results['errors'].append(f"Invalid phone format: {phone}")
    
    return results
