"""Main routes for the Over-Under Contests application."""
from flask import Blueprint, render_template, request, redirect, url_for, send_from_directory, current_app, flash
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import Length, Optional
from app import db
from app.models import Contest, User, League
from app.utils.decorators import get_current_user, login_required
import os

main = Blueprint('main', __name__)


class EditProfileForm(FlaskForm):
    """Form for editing user profile information."""
    
    first_name = StringField('First Name', validators=[Optional(), Length(max=50)])
    last_name = StringField('Last Name', validators=[Optional(), Length(max=50)])
    mobile_phone = StringField('Mobile Phone', validators=[Optional(), Length(max=20)])
    submit = SubmitField('Update Profile')


@main.route('/')
def index():
    """Home page showing active contests, featured leagues, and AI contest highlights.
    
    Returns:
        Rendered template for home page
    """
    try:
        # Get active contests, ordered by creation date (newest first)
        page = request.args.get('page', 1, type=int)
        per_page = 6  # Reduced to make room for other sections
        
        contests = Contest.query.filter_by(is_active=True)\
                              .order_by(Contest.created_at.desc())\
                              .paginate(page=page, per_page=per_page, error_out=False)
        
        current_user = get_current_user()
        
        # Get featured public leagues (top 3 by member count)
        featured_leagues = League.query.filter_by(is_active=True, is_public=True)\
                                     .join(League.memberships)\
                                     .group_by(League.league_id)\
                                     .order_by(db.func.count(League.memberships).desc())\
                                     .limit(3).all()
        
        # Get active leagues for main display (similar pagination as contests)
        leagues_page = request.args.get('leagues_page', 1, type=int)
        active_leagues = League.query.filter_by(is_active=True)\
                                   .order_by(League.created_at.desc())\
                                   .paginate(page=leagues_page, per_page=6, error_out=False)
        
        # Get recent AI-generated contests (last 5)
        ai_contests = Contest.query.filter_by(is_active=True, is_ai_generated=True)\
                                 .order_by(Contest.created_at.desc())\
                                 .limit(5).all()
        
        # Calculate AI contest statistics
        total_ai_contests = Contest.query.filter_by(is_ai_generated=True).count()
        
        # Get user's remaining AI contests if logged in
        remaining_ai_contests = 0
        if current_user:
            remaining_ai_contests = current_user.get_remaining_ai_contests_today()
        
        return render_template('index.html', 
                             contests=contests, 
                             current_user=current_user,
                             featured_leagues=featured_leagues,
                             active_leagues=active_leagues,
                             ai_contests=ai_contests,
                             total_ai_contests=total_ai_contests,
                             remaining_ai_contests=remaining_ai_contests)
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
                self.per_page = 6
                self.total = 0
                self.has_prev = False
                self.has_next = False
                self.prev_num = None
                self.next_num = None
            
            def iter_pages(self):
                return []
        
        contests = MockPagination()
        
        active_leagues = MockPagination()
        
        return render_template('index.html', 
                             contests=contests, 
                             current_user=current_user,
                             featured_leagues=[],
                             active_leagues=active_leagues,
                             ai_contests=[],
                             total_ai_contests=0,
                             remaining_ai_contests=0)


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


@main.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Edit user profile information.
    
    Returns:
        Rendered template for profile editing or redirect after update
    """
    current_user = get_current_user()
    form = EditProfileForm()
    
    if request.method == 'GET':
        # Pre-populate form with current user data
        form.first_name.data = current_user.first_name
        form.last_name.data = current_user.last_name
        form.mobile_phone.data = current_user.mobile_phone
    
    if form.validate_on_submit():
        # Update user information
        current_user.first_name = form.first_name.data.strip() if form.first_name.data else None
        current_user.last_name = form.last_name.data.strip() if form.last_name.data else None
        current_user.mobile_phone = form.mobile_phone.data.strip() if form.mobile_phone.data else None
        
        db.session.commit()
        
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('main.profile'))
    
    return render_template('edit_profile.html', form=form, user=current_user)


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
