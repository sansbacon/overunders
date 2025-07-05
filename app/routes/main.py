"""Main routes for the Over-Under Contests application."""
from flask import Blueprint, render_template, request, redirect, url_for, send_from_directory, current_app
from app.models import Contest, User
from app.utils.decorators import get_current_user
import os

main = Blueprint('main', __name__)


@main.route('/')
def index():
    """Home page showing active contests.
    
    Returns:
        Rendered template for home page
    """
    try:
        # Get active contests, ordered by creation date (newest first)
        page = request.args.get('page', 1, type=int)
        per_page = 10
        
        contests = Contest.query.filter_by(is_active=True)\
                              .order_by(Contest.created_at.desc())\
                              .paginate(page=page, per_page=per_page, error_out=False)
        
        current_user = get_current_user()
        
        return render_template('index.html', 
                             contests=contests, 
                             current_user=current_user)
    except Exception as e:
        # Log the error and return a safe response
        current_app.logger.error(f"Error in index route: {str(e)}")
        current_user = get_current_user()
        
        # Create a mock pagination object for empty contests
        class MockPagination:
            def __init__(self):
                self.items = []
                self.page = 1
                self.pages = 1
                self.per_page = 10
                self.total = 0
                self.has_prev = False
                self.has_next = False
                self.prev_num = None
                self.next_num = None
            
            def iter_pages(self):
                return []
        
        contests = MockPagination()
        
        return render_template('index.html', 
                             contests=contests, 
                             current_user=current_user)


@main.route('/about')
def about():
    """About page with application information.
    
    Returns:
        Rendered template for about page
    """
    return render_template('about.html')


@main.route('/profile')
def profile():
    """User profile page showing user's contests and entries.
    
    Returns:
        Rendered template for user profile page
    """
    current_user = get_current_user()
    if not current_user:
        return redirect(url_for('auth.login'))
    
    # Get user's created contests
    created_contests = current_user.get_contests_created()
    
    # Get user's contest entries
    contest_entries = current_user.get_contest_entries()
    
    return render_template('profile.html',
                         user=current_user,
                         created_contests=created_contests,
                         contest_entries=contest_entries)


@main.route('/favicon.ico')
def favicon():
    """Serve favicon.ico file.
    
    Returns:
        Favicon file or 404 if not found
    """
    try:
        return send_from_directory(
            os.path.join(current_app.root_path, 'static'),
            'favicon.ico',
            mimetype='image/vnd.microsoft.icon'
        )
    except FileNotFoundError:
        # Return a 204 No Content response if favicon doesn't exist
        # This prevents the 500 error
        return '', 204


@main.context_processor
def inject_user():
    """Inject current user into all templates.
    
    Returns:
        dict: Dictionary with current_user for template context
    """
    return dict(current_user=get_current_user())


@main.app_errorhandler(404)
def not_found_error(error):
    """Handle 404 errors.
    
    Args:
        error: The error object
        
    Returns:
        Rendered 404 error page
    """
    return render_template('errors/404.html'), 404


@main.app_errorhandler(403)
def forbidden_error(error):
    """Handle 403 errors.
    
    Args:
        error: The error object
        
    Returns:
        Rendered 403 error page
    """
    return render_template('errors/403.html'), 403


@main.app_errorhandler(500)
def internal_error(error):
    """Handle 500 errors.
    
    Args:
        error: The error object
        
    Returns:
        Rendered 500 error page
    """
    return render_template('errors/500.html'), 500
