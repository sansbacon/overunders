"""Decorator functions for authentication and authorization."""
from functools import wraps
from flask import session, redirect, url_for, flash, abort
from app.models import User


def login_required(f):
    """Decorator to require user login.
    
    Args:
        f: Function to decorate
        
    Returns:
        Decorated function that checks for user login
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator to require admin privileges.
    
    Args:
        f: Function to decorate
        
    Returns:
        Decorated function that checks for admin privileges
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin:
            abort(403)  # Forbidden
        
        return f(*args, **kwargs)
    return decorated_function


def contest_owner_required(f):
    """Decorator to require contest ownership or admin privileges.
    
    This decorator expects the route to have a contest_id parameter.
    
    Args:
        f: Function to decorate
        
    Returns:
        Decorated function that checks for contest ownership or admin privileges
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        
        user = User.query.get(session['user_id'])
        if not user:
            flash('User not found.', 'error')
            return redirect(url_for('auth.login'))
        
        # Admin users can access any contest
        if user.is_admin:
            return f(*args, **kwargs)
        
        # Check if user owns the contest
        contest_id = kwargs.get('contest_id')
        if contest_id:
            from app.models import Contest
            contest = Contest.query.get_or_404(contest_id)
            if contest.created_by_user != user.user_id:
                abort(403)  # Forbidden
        
        return f(*args, **kwargs)
    return decorated_function


def get_current_user():
    """Get the current logged-in user.
    
    Returns:
        User: Current user object or None if not logged in
    """
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None


def is_admin():
    """Check if current user is an admin.
    
    Returns:
        bool: True if current user is admin, False otherwise
    """
    user = get_current_user()
    return user and user.is_admin
