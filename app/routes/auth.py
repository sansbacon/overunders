"""Authentication routes for the Over-Under Contests application."""
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Email, Length
from app import db, google
from app.models import User, LoginToken
from app.utils.email import send_login_email
from app.utils.oauth import handle_google_callback

auth = Blueprint('auth', __name__)


class LoginForm(FlaskForm):
    """Form for user login."""
    
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Send Login Link')


class AdminLoginForm(FlaskForm):
    """Form for admin login with username/password."""
    
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Login')


class RegisterForm(FlaskForm):
    """Form for user registration."""
    
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    mobile_phone = StringField('Mobile Phone (Optional)')
    submit = SubmitField('Register')


@auth.route('/login', methods=['GET', 'POST'])
def login():
    """Login page - sends one-time login link via email.
    
    Returns:
        Rendered login template or redirect after successful email send
    """
    form = LoginForm()
    
    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        
        # Check if user exists
        user = User.query.filter_by(email=email).first()
        if not user:
            flash('No account found with that email address. Please register first.', 'error')
            return redirect(url_for('auth.register'))
        
        # Clean up expired tokens
        LoginToken.cleanup_expired_tokens()
        
        # Create new login token
        token = LoginToken.create_token(email)
        
        # Send login email
        if send_login_email(email, token.token):
            flash('Login link sent to your email address. Please check your inbox.', 'success')
            return redirect(url_for('main.index'))
        else:
            flash('Failed to send login email. Please try again.', 'error')
    
    return render_template('auth/login.html', form=form)


@auth.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page with username/password authentication.
    
    Returns:
        Rendered admin login template or redirect after successful login
    """
    form = AdminLoginForm()
    
    if form.validate_on_submit():
        try:
            username = form.username.data.strip()
            password = form.password.data
            
            # Find user by username
            user = User.query.filter_by(username=username).first()
            
            if not user:
                flash('Invalid username or password.', 'error')
                return render_template('auth/admin_login.html', form=form)
            
            # Check if user is admin
            if not user.is_admin:
                flash('Access denied. Admin privileges required.', 'error')
                return render_template('auth/admin_login.html', form=form)
            
            # Check if user has password set
            if not user.has_password():
                flash('No password set for this admin account. Please contact system administrator.', 'error')
                return render_template('auth/admin_login.html', form=form)
            
            # Verify password
            if not user.check_password(password):
                flash('Invalid username or password.', 'error')
                return render_template('auth/admin_login.html', form=form)
            
            # Update user's last login
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            # Log user in
            session['user_id'] = user.user_id
            session['username'] = user.username
            session['is_admin'] = user.is_admin
            
            flash(f'Welcome back, {user.username}!', 'success')
            
            # Redirect to next page if specified, otherwise to admin dashboard
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            
            return redirect(url_for('admin.dashboard'))
            
        except Exception as e:
            # Log the error and show a generic error message
            from flask import current_app
            current_app.logger.error(f"Error in admin login: {str(e)}")
            flash('An error occurred during login. Please try again.', 'error')
            return render_template('auth/admin_login.html', form=form)
    
    return render_template('auth/admin_login.html', form=form)


@auth.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page for new users.
    
    Returns:
        Rendered registration template or redirect after successful registration
    """
    form = RegisterForm()
    
    if form.validate_on_submit():
        username = form.username.data.strip()
        email = form.email.data.lower().strip()
        mobile_phone = form.mobile_phone.data.strip() if form.mobile_phone.data else None
        
        # Check if username already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists. Please choose a different one.', 'error')
            return render_template('auth/register.html', form=form)
        
        # Check if email already exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered. Please use the login page.', 'error')
            return redirect(url_for('auth.login'))
        
        # Create new user
        user = User(
            username=username,
            email=email,
            mobile_phone=mobile_phone
        )
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', form=form)


@auth.route('/login/<token>')
def login_with_token(token):
    """Login using one-time token from email.
    
    Args:
        token (str): One-time login token
        
    Returns:
        Redirect to main page or login page with error
    """
    # Find and validate token
    login_token = LoginToken.query.filter_by(token=token).first()
    
    if not login_token or not login_token.is_valid():
        flash('Invalid or expired login link. Please request a new one.', 'error')
        return redirect(url_for('auth.login'))
    
    # Find user
    user = User.query.filter_by(email=login_token.email).first()
    if not user:
        flash('User account not found.', 'error')
        return redirect(url_for('auth.login'))
    
    # Mark token as used
    login_token.mark_as_used()
    
    # Update user's last login
    user.last_login = datetime.utcnow()
    db.session.commit()
    
    # Log user in
    session['user_id'] = user.user_id
    session['username'] = user.username
    session['is_admin'] = user.is_admin
    
    flash(f'Welcome back, {user.username}!', 'success')
    
    # Redirect to next page if specified, otherwise to main page
    next_page = request.args.get('next')
    if next_page:
        return redirect(next_page)
    
    return redirect(url_for('main.index'))


@auth.route('/logout')
def logout():
    """Logout current user.
    
    Returns:
        Redirect to main page
    """
    username = session.get('username', 'User')
    session.clear()
    flash(f'Goodbye, {username}!', 'info')
    return redirect(url_for('main.index'))


@auth.route('/resend-login')
def resend_login():
    """Resend login link page.
    
    Returns:
        Redirect to login page
    """
    flash('Please enter your email address to receive a new login link.', 'info')
    return redirect(url_for('auth.login'))


@auth.route('/google-login')
def google_login():
    """Initiate Google OAuth login.
    
    Returns:
        Redirect to Google OAuth authorization URL
    """
    from flask import current_app
    
    # Check if Google OAuth is configured
    if not current_app.config.get('GOOGLE_CLIENT_ID') or not current_app.config.get('GOOGLE_CLIENT_SECRET'):
        flash('Google login is not configured. Please contact the administrator.', 'error')
        return redirect(url_for('auth.login'))
    
    if not google:
        flash('Google login service is not available. Please try again later.', 'error')
        return redirect(url_for('auth.login'))
    
    try:
        redirect_uri = url_for('auth.google_callback', _external=True)
        return google.authorize_redirect(redirect_uri)
    except Exception as e:
        current_app.logger.error(f"Google OAuth initialization error: {str(e)}")
        flash('Google login is temporarily unavailable. Please use email login instead.', 'error')
        return redirect(url_for('auth.login'))


@auth.route('/google-callback')
def google_callback():
    """Handle Google OAuth callback.
    
    Returns:
        Redirect to main page or login page with error
    """
    if not google:
        flash('Google login is not configured.', 'error')
        return redirect(url_for('auth.login'))
    
    try:
        success, result = handle_google_callback(google, request)
        
        if success:
            user = result
            
            # Update user's last login
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            # Log user in
            session['user_id'] = user.user_id
            session['username'] = user.username
            session['is_admin'] = user.is_admin
            
            flash(f'Welcome, {user.username}!', 'success')
            
            # Redirect to next page if specified, otherwise to main page
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            
            return redirect(url_for('main.index'))
        else:
            error_message = result
            flash(f'Google login failed: {error_message}', 'error')
            return redirect(url_for('auth.login'))
            
    except Exception as e:
        from flask import current_app
        current_app.logger.error(f"Google OAuth callback error: {str(e)}")
        flash('An error occurred during Google login. Please try again.', 'error')
        return redirect(url_for('auth.login'))
