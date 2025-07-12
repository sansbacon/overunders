"""League routes for the Over-Under Contests application."""
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SubmitField, IntegerField, SelectField
from wtforms.validators import DataRequired, Length, Optional, NumberRange
from app import db
from app.models import League, LeagueMembership, LeagueContest, Contest, User
from app.utils.decorators import login_required, get_current_user

leagues = Blueprint('leagues', __name__)


def league_admin_required(f):
    """Decorator to require league admin access."""
    def decorated_function(*args, **kwargs):
        league_id = kwargs.get('league_id')
        if not league_id:
            flash('League not found.', 'error')
            return redirect(url_for('leagues.list_leagues'))
        
        league = League.query.get_or_404(league_id)
        current_user = get_current_user()
        
        if not current_user:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth.login'))
        
        # Check if user is league creator or admin
        if (league.created_by_user != current_user.user_id and 
            not league.is_admin(current_user) and 
            not current_user.is_admin):
            flash('You do not have permission to manage this league.', 'error')
            return redirect(url_for('leagues.view_league', league_id=league_id))
        
        return f(*args, **kwargs)
    
    decorated_function.__name__ = f.__name__
    return decorated_function


class LeagueForm(FlaskForm):
    """Form for creating and editing leagues."""
    
    league_name = StringField('League Name', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[Length(max=1000)])
    is_public = BooleanField('Public League', description='Allow anyone to join this league')
    win_bonus_points = IntegerField('Win Bonus Points', 
                                   validators=[DataRequired(), NumberRange(min=0, max=50)],
                                   default=5,
                                   description='Bonus points awarded for winning a contest')
    submit = SubmitField('Save League')


class JoinLeagueForm(FlaskForm):
    """Form for joining a league."""
    
    submit = SubmitField('Join League')


class AddContestForm(FlaskForm):
    """Form for adding contests to a league."""
    
    contest_id = SelectField('Contest', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Add Contest')


class InviteMemberForm(FlaskForm):
    """Form for inviting members to a league."""
    
    email_addresses = TextAreaField('Email Addresses', 
                                   validators=[Length(max=2000)],
                                   render_kw={'placeholder': 'Enter email addresses, one per line or separated by commas'})
    submit = SubmitField('Send Invitations')


@leagues.route('/')
def list_leagues():
    """List all leagues.
    
    Returns:
        Rendered template with leagues list
    """
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    current_user = get_current_user()
    
    # Get public leagues and user's leagues
    if current_user:
        # Show public leagues and leagues the user is a member of
        user_league_ids = [m.league_id for m in current_user.league_memberships]
        leagues_query = League.query.filter(
            db.or_(
                League.is_public == True,
                League.league_id.in_(user_league_ids)
            ),
            League.is_active == True
        ).order_by(League.created_at.desc())
    else:
        # Show only public leagues for non-logged-in users
        leagues_query = League.query.filter_by(is_public=True, is_active=True)\
                                   .order_by(League.created_at.desc())
    
    leagues_pagination = leagues_query.paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('leagues/list.html', 
                         leagues=leagues_pagination,
                         current_user=current_user)


@leagues.route('/<int:league_id>')
def view_league(league_id):
    """View league details and leaderboard.
    
    Args:
        league_id (int): League ID
        
    Returns:
        Rendered template with league details
    """
    league = League.query.get_or_404(league_id)
    current_user = get_current_user()
    
    # Check if user can view this league
    if not league.is_public and current_user and not league.is_member(current_user):
        flash('You do not have permission to view this league.', 'error')
        return redirect(url_for('leagues.list_leagues'))
    
    # Get league leaderboard
    leaderboard = league.get_leaderboard()
    
    # Get league contests
    contests = league.get_contests()
    
    # Check if user is a member
    is_member = current_user and league.is_member(current_user) if current_user else False
    is_admin = current_user and league.is_admin(current_user) if current_user else False
    
    return render_template('leagues/detail.html',
                         league=league,
                         leaderboard=leaderboard,
                         contests=contests,
                         is_member=is_member,
                         is_admin=is_admin,
                         current_user=current_user)


@leagues.route('/create', methods=['GET', 'POST'])
@login_required
def create_league():
    """Create a new league.
    
    Returns:
        Rendered template for league creation or redirect after creation
    """
    form = LeagueForm()
    current_user = get_current_user()
    
    if form.validate_on_submit():
        # Create league
        league = League(
            league_name=form.league_name.data,
            description=form.description.data,
            created_by_user=current_user.user_id,
            is_public=form.is_public.data,
            win_bonus_points=form.win_bonus_points.data
        )
        
        db.session.add(league)
        db.session.flush()  # Get league ID
        
        # Add creator as admin member
        membership = LeagueMembership(
            league_id=league.league_id,
            user_id=current_user.user_id,
            is_admin=True
        )
        db.session.add(membership)
        
        db.session.commit()
        
        flash('League created successfully!', 'success')
        return redirect(url_for('leagues.view_league', league_id=league.league_id))
    
    return render_template('leagues/form.html', 
                         form=form, 
                         title='Create League')


@leagues.route('/<int:league_id>/edit', methods=['GET', 'POST'])
@login_required
@league_admin_required
def edit_league(league_id):
    """Edit an existing league.
    
    Args:
        league_id (int): League ID
        
    Returns:
        Rendered template for league editing or redirect after update
    """
    league = League.query.get_or_404(league_id)
    form = LeagueForm(obj=league)
    
    if form.validate_on_submit():
        # Update league details
        league.league_name = form.league_name.data
        league.description = form.description.data
        league.is_public = form.is_public.data
        league.win_bonus_points = form.win_bonus_points.data
        league.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash('League updated successfully!', 'success')
        return redirect(url_for('leagues.view_league', league_id=league_id))
    
    return render_template('leagues/form.html', 
                         form=form, 
                         league=league,
                         title='Edit League')


@leagues.route('/<int:league_id>/join', methods=['POST'])
@login_required
def join_league(league_id):
    """Join a league.
    
    Args:
        league_id (int): League ID
        
    Returns:
        Redirect to league view
    """
    league = League.query.get_or_404(league_id)
    current_user = get_current_user()
    
    # Check if league is public or user has permission
    if not league.is_public:
        flash('This league is private and requires an invitation.', 'error')
        return redirect(url_for('leagues.view_league', league_id=league_id))
    
    # Check if user is already a member
    if league.is_member(current_user):
        flash('You are already a member of this league.', 'info')
        return redirect(url_for('leagues.view_league', league_id=league_id))
    
    # Add user as member
    membership = LeagueMembership(
        league_id=league_id,
        user_id=current_user.user_id,
        is_admin=False
    )
    db.session.add(membership)
    db.session.commit()
    
    flash('Successfully joined the league!', 'success')
    return redirect(url_for('leagues.view_league', league_id=league_id))


@leagues.route('/<int:league_id>/leave', methods=['POST'])
@login_required
def leave_league(league_id):
    """Leave a league.
    
    Args:
        league_id (int): League ID
        
    Returns:
        Redirect to leagues list
    """
    league = League.query.get_or_404(league_id)
    current_user = get_current_user()
    
    # Check if user is a member
    membership = league.memberships.filter_by(user_id=current_user.user_id).first()
    if not membership:
        flash('You are not a member of this league.', 'error')
        return redirect(url_for('leagues.view_league', league_id=league_id))
    
    # Don't allow creator to leave if they're the only admin
    if league.created_by_user == current_user.user_id:
        admin_count = league.memberships.filter_by(is_admin=True).count()
        if admin_count <= 1:
            flash('You cannot leave the league as you are the only admin. Please assign another admin first.', 'error')
            return redirect(url_for('leagues.view_league', league_id=league_id))
    
    # Remove membership
    db.session.delete(membership)
    db.session.commit()
    
    flash('You have left the league.', 'info')
    return redirect(url_for('leagues.list_leagues'))


@leagues.route('/<int:league_id>/manage', methods=['GET', 'POST'])
@login_required
@league_admin_required
def manage_league(league_id):
    """Manage league members and contests.
    
    Args:
        league_id (int): League ID
        
    Returns:
        Rendered template for league management
    """
    league = League.query.get_or_404(league_id)
    current_user = get_current_user()
    
    # Get league members
    members = league.get_members()
    
    # Get available contests (created by league members)
    member_ids = [m.user_id for m in members]
    available_contests = Contest.query.filter(
        Contest.created_by_user.in_(member_ids),
        Contest.is_active == True
    ).order_by(Contest.created_at.desc()).all()
    
    # Filter out contests already in the league
    league_contest_ids = [lc.contest_id for lc in league.league_contests.all()]
    available_contests = [c for c in available_contests if c.contest_id not in league_contest_ids]
    
    # Forms
    add_contest_form = AddContestForm()
    add_contest_form.contest_id.choices = [(c.contest_id, f"{c.contest_name} (by {c.creator.username})") 
                                          for c in available_contests]
    
    invite_form = InviteMemberForm()
    
    if request.method == 'POST':
        if 'add_contest' in request.form and add_contest_form.validate():
            contest = Contest.query.get(add_contest_form.contest_id.data)
            if contest:
                league.add_contest(contest)
                db.session.commit()
                flash(f'Contest "{contest.contest_name}" added to league!', 'success')
            return redirect(url_for('leagues.manage_league', league_id=league_id))
        
        elif 'invite_members' in request.form and invite_form.validate():
            # Parse email addresses
            emails = []
            if invite_form.email_addresses.data:
                email_text = invite_form.email_addresses.data.strip()
                # Split by newlines and commas, then clean up
                raw_emails = []
                for line in email_text.split('\n'):
                    raw_emails.extend([email.strip() for email in line.split(',')])
                emails = [email for email in raw_emails if email]
            
            if emails:
                # TODO: Implement league invitation system
                flash(f'League invitations will be sent to {len(emails)} email addresses.', 'info')
            else:
                flash('Please enter at least one email address.', 'error')
            
            return redirect(url_for('leagues.manage_league', league_id=league_id))
    
    return render_template('leagues/manage.html',
                         league=league,
                         members=members,
                         add_contest_form=add_contest_form,
                         invite_form=invite_form,
                         current_user=current_user)


@leagues.route('/<int:league_id>/remove-contest/<int:contest_id>', methods=['POST'])
@login_required
@league_admin_required
def remove_contest(league_id, contest_id):
    """Remove a contest from a league.
    
    Args:
        league_id (int): League ID
        contest_id (int): Contest ID
        
    Returns:
        Redirect to league management
    """
    league = League.query.get_or_404(league_id)
    contest = Contest.query.get_or_404(contest_id)
    
    if league.remove_contest(contest):
        db.session.commit()
        flash(f'Contest "{contest.contest_name}" removed from league.', 'success')
    else:
        flash('Contest not found in league.', 'error')
    
    return redirect(url_for('leagues.manage_league', league_id=league_id))


@leagues.route('/<int:league_id>/remove-member/<int:user_id>', methods=['POST'])
@login_required
@league_admin_required
def remove_member(league_id, user_id):
    """Remove a member from a league.
    
    Args:
        league_id (int): League ID
        user_id (int): User ID
        
    Returns:
        Redirect to league management
    """
    league = League.query.get_or_404(league_id)
    user = User.query.get_or_404(user_id)
    current_user = get_current_user()
    
    # Don't allow removing the creator
    if league.created_by_user == user_id:
        flash('Cannot remove the league creator.', 'error')
        return redirect(url_for('leagues.manage_league', league_id=league_id))
    
    # Don't allow removing yourself
    if current_user.user_id == user_id:
        flash('Use the "Leave League" option to remove yourself.', 'error')
        return redirect(url_for('leagues.manage_league', league_id=league_id))
    
    membership = league.memberships.filter_by(user_id=user_id).first()
    if membership:
        db.session.delete(membership)
        db.session.commit()
        flash(f'{user.username} has been removed from the league.', 'success')
    else:
        flash('User is not a member of this league.', 'error')
    
    return redirect(url_for('leagues.manage_league', league_id=league_id))


@leagues.route('/<int:league_id>/toggle-admin/<int:user_id>', methods=['POST'])
@login_required
@league_admin_required
def toggle_admin(league_id, user_id):
    """Toggle admin status for a league member.
    
    Args:
        league_id (int): League ID
        user_id (int): User ID
        
    Returns:
        JSON response
    """
    league = League.query.get_or_404(league_id)
    user = User.query.get_or_404(user_id)
    current_user = get_current_user()
    
    # Don't allow changing creator's admin status
    if league.created_by_user == user_id:
        return jsonify({'error': 'Cannot change admin status of league creator'}), 400
    
    membership = league.memberships.filter_by(user_id=user_id).first()
    if not membership:
        return jsonify({'error': 'User is not a member of this league'}), 400
    
    # Toggle admin status
    membership.is_admin = not membership.is_admin
    db.session.commit()
    
    action = 'promoted to' if membership.is_admin else 'removed from'
    flash(f'{user.username} has been {action} admin.', 'success')
    
    return jsonify({
        'success': True,
        'is_admin': membership.is_admin,
        'message': f'{user.username} has been {action} admin.'
    })


@leagues.route('/<int:league_id>/leaderboard')
def league_leaderboard(league_id):
    """View detailed league leaderboard.
    
    Args:
        league_id (int): League ID
        
    Returns:
        Rendered template with detailed leaderboard
    """
    league = League.query.get_or_404(league_id)
    current_user = get_current_user()
    
    # Check if user can view this league
    if not league.is_public and current_user and not league.is_member(current_user):
        flash('You do not have permission to view this league.', 'error')
        return redirect(url_for('leagues.list_leagues'))
    
    # Get league leaderboard
    leaderboard = league.get_leaderboard()
    
    # Get league contests for reference
    contests = league.get_contests()
    
    return render_template('leagues/leaderboard.html',
                         league=league,
                         leaderboard=leaderboard,
                         contests=contests,
                         current_user=current_user)


@leagues.route('/my-leagues')
@login_required
def my_leagues():
    """View user's leagues.
    
    Returns:
        Rendered template with user's leagues
    """
    current_user = get_current_user()
    
    # Get leagues the user is a member of
    user_leagues = []
    for membership in current_user.league_memberships:
        if membership.league.is_active:
            user_leagues.append({
                'league': membership.league,
                'membership': membership,
                'is_admin': membership.is_admin
            })
    
    # Sort by join date (most recent first)
    user_leagues.sort(key=lambda x: x['membership'].joined_at, reverse=True)
    
    return render_template('leagues/my_leagues.html',
                         user_leagues=user_leagues,
                         current_user=current_user)
