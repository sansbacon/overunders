"""Decorators for content moderation integration."""
from functools import wraps
from flask import current_app, request, flash, redirect, url_for
from app.utils.content_moderation import moderate_text, ContentModerationLog
from app.models import db


def moderate_content(content_fields, content_type, redirect_route=None):
    """Decorator to automatically moderate content before processing.
    
    Args:
        content_fields (list): List of form field names to moderate
        content_type (str): Type of content being moderated
        redirect_route (str, optional): Route to redirect to if content is blocked
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Only moderate if auto-moderation is enabled
            if not current_app.config.get('AUTO_MODERATE_NEW_CONTENT', True):
                return f(*args, **kwargs)
            
            # Check if we have form data to moderate
            if request.method == 'POST' and hasattr(request, 'form'):
                blocked_content = []
                
                for field_name in content_fields:
                    if field_name in request.form:
                        content_text = request.form.get(field_name, '').strip()
                        if content_text:
                            # Moderate the content
                            result = moderate_text(content_text, content_type)
                            
                            # Log moderation if enabled
                            if current_app.config.get('CONTENT_MODERATION_LOG_ENABLED', True):
                                action = 'blocked' if not result.is_safe else 'approved'
                                ContentModerationLog.log_moderation(
                                    content_type=content_type,
                                    content_text=content_text,
                                    moderation_result=result.to_dict(),
                                    action_taken=action,
                                    user_id=getattr(request, 'current_user_id', None)
                                )
                            
                            # If content is not safe, block it
                            if not result.is_safe:
                                blocked_content.append({
                                    'field': field_name,
                                    'reason': result.reason,
                                    'categories': result.categories
                                })
                
                # If any content was blocked, show error and redirect
                if blocked_content:
                    reasons = []
                    for blocked in blocked_content:
                        field_display = blocked['field'].replace('_', ' ').title()
                        reasons.append(f"{field_display}: {blocked['reason']}")
                    
                    flash(f"Content blocked due to policy violations: {'; '.join(reasons)}", 'error')
                    
                    if redirect_route:
                        return redirect(url_for(redirect_route))
                    else:
                        # Try to redirect back to the referring page
                        return redirect(request.referrer or url_for('main.index'))
            
            # Content passed moderation, proceed with original function
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def moderate_ai_content(content_fields, content_type):
    """Decorator specifically for AI-generated content moderation.
    
    Args:
        content_fields (list): List of content fields to moderate
        content_type (str): Type of content being moderated
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Only moderate AI content if enabled
            if not current_app.config.get('MODERATE_AI_GENERATED_CONTENT', True):
                return f(*args, **kwargs)
            
            # Execute the original function first to get AI-generated content
            result = f(*args, **kwargs)
            
            # If the result contains content to moderate, check it
            if isinstance(result, dict) and any(field in result for field in content_fields):
                blocked_content = []
                
                for field_name in content_fields:
                    if field_name in result:
                        content_text = result[field_name]
                        if isinstance(content_text, str) and content_text.strip():
                            # Moderate the AI-generated content
                            moderation_result = moderate_text(content_text, content_type)
                            
                            # Log moderation if enabled
                            if current_app.config.get('CONTENT_MODERATION_LOG_ENABLED', True):
                                action = 'blocked' if not moderation_result.is_safe else 'approved'
                                ContentModerationLog.log_moderation(
                                    content_type=f"ai_{content_type}",
                                    content_text=content_text,
                                    moderation_result=moderation_result.to_dict(),
                                    action_taken=action
                                )
                            
                            # If content is not safe, mark it for regeneration
                            if not moderation_result.is_safe:
                                blocked_content.append({
                                    'field': field_name,
                                    'reason': moderation_result.reason,
                                    'original_content': content_text
                                })
                
                # If AI content was blocked, try to regenerate or return error
                if blocked_content:
                    # For now, return an error result
                    return {
                        'error': 'AI-generated content failed moderation',
                        'blocked_content': blocked_content,
                        'retry_suggested': True
                    }
            
            return result
        
        return decorated_function
    return decorator


def log_user_content_action(content_type, action='created'):
    """Decorator to log user content creation/modification actions.
    
    Args:
        content_type (str): Type of content
        action (str): Action being performed
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Execute the original function
            result = f(*args, **kwargs)
            
            # Log the action if moderation logging is enabled
            if current_app.config.get('CONTENT_MODERATION_LOG_ENABLED', True):
                # Try to extract content from the request or result
                content_text = ""
                if request.method == 'POST' and hasattr(request, 'form'):
                    # Combine relevant form fields
                    text_fields = []
                    for key, value in request.form.items():
                        if any(field in key.lower() for field in ['name', 'title', 'description', 'text', 'question']):
                            if value and value.strip():
                                text_fields.append(f"{key}: {value.strip()}")
                    content_text = "; ".join(text_fields)
                
                if content_text:
                    ContentModerationLog.log_moderation(
                        content_type=content_type,
                        content_text=content_text,
                        moderation_result={'action': action, 'logged_only': True},
                        action_taken=f'user_{action}',
                        user_id=getattr(request, 'current_user_id', None)
                    )
            
            return result
        
        return decorated_function
    return decorator
