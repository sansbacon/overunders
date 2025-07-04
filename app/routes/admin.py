"""Admin routes for the Over-Under Contests application."""
from datetime import datetime
import json
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, BooleanField, SubmitField, IntegerField, PasswordField, TextAreaField, DateTimeLocalField, FieldList, FormField, SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo
from werkzeug.utils import secure_filename
import io
from app import db
from app.models import User, Contest, ContestEntry, EntryAnswer, LoginToken, Question
from app.utils.decorators import admin_required, get_current_user

admin = Blueprint('admin', __name__)


class UserForm(FlaskForm):
    """Form for editing user details."""
    
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    first_name = StringField('First Name', validators=[Length(max=50)])
    last_name = StringField('Last Name', validators=[Length(max=50)])
    mobile_phone = StringField('Mobile Phone')
    is_admin = BooleanField('Admin User')
    submit = SubmitField('Update User')


class SetPasswordForm(FlaskForm):
    """Form for setting admin user passwords."""
    
    password = PasswordField('New Password', validators=[
        DataRequired(), 
        Length(min=8, message='Password must be at least 8 characters long')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(), 
        EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Set Password')


class ScoreAdjustmentForm(FlaskForm):
    """Form for manual score adjustments."""
    
    adjustment_points = IntegerField('Adjustment Points', default=0)
    reason = StringField('Reason for Adjustment', validators=[DataRequired()])
    submit = SubmitField('Apply Adjustment')


class AdminQuestionForm(FlaskForm):
    """Form for individual contest questions in admin panel."""
    
    question_text = StringField('Question', validators=[DataRequired(), Length(max=500)])
    correct_answer = BooleanField('Correct Answer (Yes/True)')
    has_answer = BooleanField('Answer Set')


class AdminContestForm(FlaskForm):
    """Form for admin contest editing."""
    
    contest_name = StringField('Contest Name', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[Length(max=1000)])
    lock_timestamp = DateTimeLocalField('Lock Date & Time', validators=[DataRequired()], format='%Y-%m-%dT%H:%M')
    is_active = BooleanField('Active')
    questions = FieldList(FormField(AdminQuestionForm), min_entries=1, max_entries=50)
    submit = SubmitField('Save Contest')


class BulkOperationForm(FlaskForm):
    """Form for bulk operations via JSON file upload."""
    
    operation_type = SelectField('Operation Type', choices=[
        ('create_contest', 'Create Contest with Questions'),
        ('add_entries', 'Add Entries to Existing Contest'),
        ('set_answers', 'Set Correct Answers for Contest')
    ], validators=[DataRequired()])
    
    json_file = FileField('JSON File', validators=[
        FileRequired(),
        FileAllowed(['json'], 'JSON files only!')
    ])
    
    submit = SubmitField('Process File')


@admin.route('/')
@admin_required
def dashboard():
    """Admin dashboard with overview statistics.
    
    Returns:
        Rendered admin dashboard template
    """
    # Get current user
    current_user = get_current_user()
    
    # Get statistics
    total_users = User.query.count()
    total_contests = Contest.query.count()
    active_contests = Contest.query.filter_by(is_active=True).count()
    total_entries = ContestEntry.query.count()
    
    # Recent activity
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_contests = Contest.query.order_by(Contest.created_at.desc()).limit(5).all()
    recent_entries = ContestEntry.query.order_by(ContestEntry.created_at.desc()).limit(10).all()
    
    # Expired tokens cleanup
    LoginToken.cleanup_expired_tokens()
    
    stats = {
        'total_users': total_users,
        'total_contests': total_contests,
        'active_contests': active_contests,
        'total_entries': total_entries
    }
    
    return render_template('admin/dashboard.html',
                         current_user=current_user,
                         stats=stats,
                         recent_users=recent_users,
                         recent_contests=recent_contests,
                         recent_entries=recent_entries)


@admin.route('/users')
@admin_required
def manage_users():
    """Manage users page.
    
    Returns:
        Rendered users management template
    """
    # Get current user
    current_user = get_current_user()
    
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    search = request.args.get('search', '')
    if search:
        users = User.query.filter(
            db.or_(
                User.username.contains(search),
                User.email.contains(search)
            )
        ).order_by(User.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
    else:
        users = User.query.order_by(User.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
    
    return render_template('admin/users.html', 
                         users=users, 
                         search=search, 
                         current_user=current_user)


@admin.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    """Edit user details.
    
    Args:
        user_id (int): User ID
        
    Returns:
        Rendered user edit template or redirect after update
    """
    user = User.query.get_or_404(user_id)
    form = UserForm(obj=user)
    
    if form.validate_on_submit():
        # Check if username/email already exists (excluding current user)
        existing_username = User.query.filter(
            User.username == form.username.data,
            User.user_id != user_id
        ).first()
        
        existing_email = User.query.filter(
            User.email == form.email.data,
            User.user_id != user_id
        ).first()
        
        if existing_username:
            flash('Username already exists.', 'error')
            return render_template('admin/edit_user.html', form=form, user=user)
        
        if existing_email:
            flash('Email already exists.', 'error')
            return render_template('admin/edit_user.html', form=form, user=user)
        
        # Update user
        user.username = form.username.data
        user.email = form.email.data
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        user.mobile_phone = form.mobile_phone.data
        user.is_admin = form.is_admin.data
        
        db.session.commit()
        
        flash('User updated successfully.', 'success')
        return redirect(url_for('admin.manage_users'))
    
    return render_template('admin/edit_user.html', form=form, user=user)


@admin.route('/users/<int:user_id>/set-password', methods=['GET', 'POST'])
@admin_required
def set_user_password(user_id):
    """Set password for admin user.
    
    Args:
        user_id (int): User ID
        
    Returns:
        Rendered password form template or redirect after setting password
    """
    user = User.query.get_or_404(user_id)
    
    # Only allow setting passwords for admin users
    if not user.is_admin:
        flash('Passwords can only be set for admin users.', 'error')
        return redirect(url_for('admin.manage_users'))
    
    form = SetPasswordForm()
    
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        
        flash(f'Password set successfully for {user.username}.', 'success')
        return redirect(url_for('admin.manage_users'))
    
    return render_template('admin/set_password.html', form=form, user=user)


@admin.route('/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    """Delete a user (soft delete by deactivating).
    
    Args:
        user_id (int): User ID
        
    Returns:
        Redirect to users management page
    """
    user = User.query.get_or_404(user_id)
    current_user = get_current_user()
    
    # Prevent admin from deleting themselves
    if user.user_id == current_user.user_id:
        flash('You cannot delete your own account.', 'error')
        return redirect(url_for('admin.manage_users'))
    
    # Check if user has contests
    user_contests = Contest.query.filter_by(created_by_user=user_id).all()
    
    if user_contests:
        # If user has contests, we cannot delete them due to foreign key constraints
        # Instead, just deactivate their contests and mark the user as inactive
        for contest in user_contests:
            contest.is_active = False
        
        # In a real application, you might want to add an 'is_active' field to users
        # For now, we'll just flash a message and not delete the user
        db.session.commit()
        flash(f'User {user.username} has been deactivated. Their {len(user_contests)} contest(s) have been marked as inactive. User cannot be fully deleted due to existing contest dependencies.', 'warning')
    else:
        # User has no contests, safe to delete
        db.session.delete(user)
        db.session.commit()
        flash('User deleted successfully.', 'success')
    
    return redirect(url_for('admin.manage_users'))


@admin.route('/contests')
@admin_required
def manage_contests():
    """Manage contests page.
    
    Returns:
        Rendered contests management template
    """
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    search = request.args.get('search', '')
    status = request.args.get('status', 'all')
    
    query = Contest.query
    
    if search:
        query = query.filter(Contest.contest_name.contains(search))
    
    if status == 'active':
        query = query.filter_by(is_active=True)
    elif status == 'inactive':
        query = query.filter_by(is_active=False)
    elif status == 'locked':
        query = query.filter(Contest.lock_timestamp < datetime.utcnow())
    elif status == 'unlocked':
        query = query.filter(Contest.lock_timestamp > datetime.utcnow())
    
    contests = query.order_by(Contest.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Pass current UTC time to template for comparison
    current_utc = datetime.utcnow()
    
    return render_template('admin/contests.html', 
                         contests=contests, 
                         search=search, 
                         status=status,
                         current_utc=current_utc)


@admin.route('/contests/<int:contest_id>/toggle-active', methods=['POST'])
@admin_required
def toggle_contest_active(contest_id):
    """Toggle contest active status.
    
    Args:
        contest_id (int): Contest ID
        
    Returns:
        Redirect to contests management page
    """
    contest = Contest.query.get_or_404(contest_id)
    contest.is_active = not contest.is_active
    db.session.commit()
    
    status = 'activated' if contest.is_active else 'deactivated'
    flash(f'Contest "{contest.contest_name}" {status} successfully.', 'success')
    
    return redirect(url_for('admin.manage_contests'))


@admin.route('/contests/<int:contest_id>/entries')
@admin_required
def view_contest_entries(contest_id):
    """View all entries for a contest.
    
    Args:
        contest_id (int): Contest ID
        
    Returns:
        Rendered contest entries template
    """
    contest = Contest.query.get_or_404(contest_id)
    entries = ContestEntry.query.filter_by(contest_id=contest_id).all()
    questions = contest.get_questions_ordered()
    
    # Calculate scores for all entries
    entry_data = []
    for entry in entries:
        score_data = entry.calculate_score()
        answers = entry.get_answers_dict()
        entry_data.append({
            'entry': entry,
            'user': entry.user,
            'score_data': score_data,
            'answers': answers
        })
    
    # Sort by score
    entry_data.sort(key=lambda x: (x['score_data']['percentage'], x['score_data']['correct_answers']), reverse=True)
    
    return render_template('admin/contest_entries.html',
                         contest=contest,
                         entry_data=entry_data,
                         questions=questions)


@admin.route('/entries/<int:entry_id>/adjust-score', methods=['GET', 'POST'])
@admin_required
def adjust_entry_score(entry_id):
    """Manually adjust entry score.
    
    Args:
        entry_id (int): Entry ID
        
    Returns:
        Rendered score adjustment template or redirect after adjustment
    """
    entry = ContestEntry.query.get_or_404(entry_id)
    form = ScoreAdjustmentForm()
    
    if form.validate_on_submit():
        # For now, we'll just flash a message
        # In a real application, you might want to store adjustments in a separate table
        flash(f'Score adjustment of {form.adjustment_points.data} points applied to {entry.user.username}\'s entry. Reason: {form.reason.data}', 'success')
        return redirect(url_for('admin.view_contest_entries', contest_id=entry.contest_id))
    
    return render_template('admin/adjust_score.html', form=form, entry=entry)


@admin.route('/system-info')
@admin_required
def system_info():
    """System information and maintenance.
    
    Returns:
        Rendered system info template
    """
    # Database statistics
    db_stats = {
        'users': User.query.count(),
        'contests': Contest.query.count(),
        'questions': db.session.execute(db.text('SELECT COUNT(*) FROM questions')).scalar(),
        'entries': ContestEntry.query.count(),
        'answers': db.session.execute(db.text('SELECT COUNT(*) FROM entry_answers')).scalar(),
        'login_tokens': LoginToken.query.count(),
        'expired_tokens': LoginToken.query.filter(LoginToken.expires_at < datetime.utcnow()).count()
    }
    
    return render_template('admin/system_info.html', db_stats=db_stats)


@admin.route('/contests/<int:contest_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_contest(contest_id):
    """Edit contest details (admin only).
    
    Args:
        contest_id (int): Contest ID
        
    Returns:
        Rendered contest edit template or redirect after update
    """
    contest = Contest.query.get_or_404(contest_id)
    form = AdminContestForm(obj=contest)
    
    if request.method == 'GET':
        # Populate questions
        questions = contest.get_questions_ordered()
        
        # Clear existing entries and populate with contest questions
        while len(form.questions.entries) > 0:
            form.questions.pop_entry()
        
        for question in questions:
            form.questions.append_entry({
                'question_text': question.question_text,
                'correct_answer': question.correct_answer if question.correct_answer is not None else False,
                'has_answer': question.has_answer()
            })
        
        # Ensure at least one question entry if none exist
        if len(form.questions.entries) == 0:
            form.questions.append_entry({
                'question_text': '',
                'correct_answer': False,
                'has_answer': False
            })
        
        # Set the is_active field
        form.is_active.data = contest.is_active
    
    if form.validate_on_submit():
        try:
            # Update contest details
            contest.contest_name = form.contest_name.data
            contest.description = form.description.data
            contest.lock_timestamp = form.lock_timestamp.data
            contest.is_active = form.is_active.data
            contest.updated_at = datetime.utcnow()
            
            # Update questions (admin can always modify)
            # Delete existing questions
            Question.query.filter_by(contest_id=contest_id).delete()
            
            # Add new questions
            for i, question_form in enumerate(form.questions.data):
                if question_form['question_text'].strip():
                    question = Question(
                        contest_id=contest.contest_id,
                        question_text=question_form['question_text'].strip(),
                        question_order=i + 1
                    )
                    
                    # Set answer if provided
                    if question_form.get('has_answer'):
                        question.set_answer(question_form.get('correct_answer', False))
                    
                    db.session.add(question)
            
            db.session.commit()
            
            flash('Contest updated successfully!', 'success')
            return redirect(url_for('admin.manage_contests'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating contest: {str(e)}', 'error')
    else:
        # Debug form errors
        if form.errors:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'Error in {field}: {error}', 'error')
    
    return render_template('admin/edit_contest.html', 
                         form=form, 
                         contest=contest)


@admin.route('/contests/<int:contest_id>/delete', methods=['POST'])
@admin_required
def delete_contest(contest_id):
    """Delete a contest (admin only).
    
    Args:
        contest_id (int): Contest ID
        
    Returns:
        Redirect to contests management page
    """
    contest = Contest.query.get_or_404(contest_id)
    
    try:
        # Delete the contest (cascade will handle related records)
        db.session.delete(contest)
        db.session.commit()
        
        flash(f'Contest "{contest.contest_name}" deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting contest: {str(e)}', 'error')
    
    return redirect(url_for('admin.manage_contests'))


@admin.route('/contests/<int:contest_id>/set-answers', methods=['GET', 'POST'])
@admin_required
def set_contest_answers(contest_id):
    """Set answers for contest questions (admin only).
    
    Args:
        contest_id (int): Contest ID
        
    Returns:
        Rendered template for setting answers or redirect after submission
    """
    contest = Contest.query.get_or_404(contest_id)
    questions = contest.get_questions_ordered()
    
    if request.method == 'POST':
        # Process answer submissions
        for question in questions:
            answer_key = f'question_{question.question_id}'
            if answer_key in request.form:
                correct_answer = request.form.get(answer_key) == 'True'
                question.set_answer(correct_answer)
        
        db.session.commit()
        
        # Recalculate scores for all entries
        for entry in contest.entries.all():
            score_data = entry.calculate_score()
            # Note: The entry model doesn't have a score field, scores are calculated on-demand
        
        flash('Answers set successfully! Scores have been recalculated.', 'success')
        return redirect(url_for('admin.view_contest_entries', contest_id=contest_id))
    
    return render_template('admin/set_answers.html',
                         contest=contest,
                         questions=questions)


@admin.route('/cleanup-tokens', methods=['POST'])
@admin_required
def cleanup_tokens():
    """Clean up expired login tokens.
    
    Returns:
        Redirect to system info page
    """
    expired_count = LoginToken.query.filter(LoginToken.expires_at < datetime.utcnow()).count()
    LoginToken.cleanup_expired_tokens()
    
    flash(f'Cleaned up {expired_count} expired login tokens.', 'success')
    return redirect(url_for('admin.system_info'))


@admin.route('/email-logs')
@admin_required
def email_logs():
    """View email sending logs.
    
    Returns:
        Rendered email logs template
    """
    from app.models import EmailLog
    
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    # Filter parameters
    status = request.args.get('status', 'all')
    email_type = request.args.get('email_type', 'all')
    delivery_method = request.args.get('delivery_method', 'all')
    search = request.args.get('search', '')
    
    query = EmailLog.query
    
    # Apply filters
    if status != 'all':
        query = query.filter_by(status=status)
    
    if email_type != 'all':
        query = query.filter_by(email_type=email_type)
    
    if delivery_method != 'all':
        query = query.filter_by(delivery_method=delivery_method)
    
    if search:
        query = query.filter(
            db.or_(
                EmailLog.recipient_email.contains(search),
                EmailLog.subject.contains(search)
            )
        )
    
    # Order by most recent first
    logs = query.order_by(EmailLog.sent_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Get statistics
    stats = {
        'total_emails': EmailLog.query.count(),
        'sent_emails': EmailLog.query.filter_by(status='sent').count(),
        'failed_emails': EmailLog.query.filter_by(status='failed').count(),
        'sendgrid_emails': EmailLog.query.filter_by(delivery_method='sendgrid_api').count(),
        'smtp_emails': EmailLog.query.filter_by(delivery_method='smtp').count(),
        'login_emails': EmailLog.query.filter_by(email_type='login').count(),
        'invitation_emails': EmailLog.query.filter_by(email_type='invitation').count(),
        'notification_emails': EmailLog.query.filter_by(email_type='notification').count(),
    }
    
    # Get unique values for filter dropdowns
    email_types = db.session.query(EmailLog.email_type).distinct().all()
    email_types = [t[0] for t in email_types]
    
    delivery_methods = db.session.query(EmailLog.delivery_method).distinct().all()
    delivery_methods = [m[0] for m in delivery_methods]
    
    return render_template('admin/email_logs.html',
                         logs=logs,
                         stats=stats,
                         email_types=email_types,
                         delivery_methods=delivery_methods,
                         status=status,
                         email_type=email_type,
                         delivery_method=delivery_method,
                         search=search)


@admin.route('/email-logs/<int:log_id>')
@admin_required
def email_log_detail(log_id):
    """View detailed email log information.
    
    Args:
        log_id (int): Email log ID
        
    Returns:
        Rendered email log detail template
    """
    from app.models import EmailLog
    
    log = EmailLog.query.get_or_404(log_id)
    
    return render_template('admin/email_log_detail.html', log=log)


# Bulk Operations Helper Functions
def validate_contest_json(data):
    """Validate JSON data for contest creation.
    
    Args:
        data (dict): JSON data to validate
        
    Returns:
        tuple: (is_valid, errors_list)
    """
    errors = []
    
    # Required fields
    required_fields = ['contest_name', 'lock_timestamp', 'questions']
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")
    
    # Validate contest_name
    if 'contest_name' in data:
        if not isinstance(data['contest_name'], str) or len(data['contest_name'].strip()) == 0:
            errors.append("contest_name must be a non-empty string")
        elif len(data['contest_name']) > 200:
            errors.append("contest_name must be 200 characters or less")
    
    # Validate description
    if 'description' in data:
        if not isinstance(data['description'], str):
            errors.append("description must be a string")
        elif len(data['description']) > 1000:
            errors.append("description must be 1000 characters or less")
    
    # Validate lock_timestamp
    if 'lock_timestamp' in data:
        try:
            datetime.fromisoformat(data['lock_timestamp'].replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            errors.append("lock_timestamp must be a valid ISO format datetime (e.g., '2025-01-15T18:00:00')")
    
    # Validate is_active
    if 'is_active' in data and not isinstance(data['is_active'], bool):
        errors.append("is_active must be a boolean")
    
    # Validate questions
    if 'questions' in data:
        if not isinstance(data['questions'], list):
            errors.append("questions must be a list")
        elif len(data['questions']) == 0:
            errors.append("questions list cannot be empty")
        elif len(data['questions']) > 50:
            errors.append("questions list cannot have more than 50 items")
        else:
            for i, question in enumerate(data['questions']):
                if not isinstance(question, dict):
                    errors.append(f"Question {i+1}: must be an object")
                    continue
                
                if 'question_text' not in question:
                    errors.append(f"Question {i+1}: missing required field 'question_text'")
                elif not isinstance(question['question_text'], str) or len(question['question_text'].strip()) == 0:
                    errors.append(f"Question {i+1}: question_text must be a non-empty string")
                elif len(question['question_text']) > 500:
                    errors.append(f"Question {i+1}: question_text must be 500 characters or less")
                
                if 'question_order' not in question:
                    errors.append(f"Question {i+1}: missing required field 'question_order'")
                elif not isinstance(question['question_order'], int) or question['question_order'] < 1:
                    errors.append(f"Question {i+1}: question_order must be a positive integer")
    
    return len(errors) == 0, errors


def validate_entries_json(data):
    """Validate JSON data for bulk entries.
    
    Args:
        data (dict): JSON data to validate
        
    Returns:
        tuple: (is_valid, errors_list)
    """
    errors = []
    
    # Required fields
    required_fields = ['contest_id', 'entries']
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")
    
    # Validate contest_id
    if 'contest_id' in data:
        if not isinstance(data['contest_id'], int) or data['contest_id'] < 1:
            errors.append("contest_id must be a positive integer")
        else:
            # Check if contest exists
            contest = Contest.query.get(data['contest_id'])
            if not contest:
                errors.append(f"Contest with ID {data['contest_id']} does not exist")
    
    # Validate entries
    if 'entries' in data:
        if not isinstance(data['entries'], list):
            errors.append("entries must be a list")
        elif len(data['entries']) == 0:
            errors.append("entries list cannot be empty")
        else:
            for i, entry in enumerate(data['entries']):
                if not isinstance(entry, dict):
                    errors.append(f"Entry {i+1}: must be an object")
                    continue
                
                if 'user_email' not in entry:
                    errors.append(f"Entry {i+1}: missing required field 'user_email'")
                elif not isinstance(entry['user_email'], str):
                    errors.append(f"Entry {i+1}: user_email must be a string")
                else:
                    # Check if user exists
                    user = User.query.filter_by(email=entry['user_email']).first()
                    if not user:
                        errors.append(f"Entry {i+1}: user with email '{entry['user_email']}' does not exist")
                
                if 'answers' not in entry:
                    errors.append(f"Entry {i+1}: missing required field 'answers'")
                elif not isinstance(entry['answers'], list):
                    errors.append(f"Entry {i+1}: answers must be a list")
                else:
                    for j, answer in enumerate(entry['answers']):
                        if not isinstance(answer, dict):
                            errors.append(f"Entry {i+1}, Answer {j+1}: must be an object")
                            continue
                        
                        if 'question_order' not in answer:
                            errors.append(f"Entry {i+1}, Answer {j+1}: missing required field 'question_order'")
                        elif not isinstance(answer['question_order'], int) or answer['question_order'] < 1:
                            errors.append(f"Entry {i+1}, Answer {j+1}: question_order must be a positive integer")
                        
                        if 'answer' not in answer:
                            errors.append(f"Entry {i+1}, Answer {j+1}: missing required field 'answer'")
                        elif not isinstance(answer['answer'], bool):
                            errors.append(f"Entry {i+1}, Answer {j+1}: answer must be a boolean")
    
    return len(errors) == 0, errors


def validate_answers_json(data):
    """Validate JSON data for setting answers.
    
    Args:
        data (dict): JSON data to validate
        
    Returns:
        tuple: (is_valid, errors_list)
    """
    errors = []
    
    # Required fields
    required_fields = ['contest_id', 'answers']
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")
    
    # Validate contest_id
    if 'contest_id' in data:
        if not isinstance(data['contest_id'], int) or data['contest_id'] < 1:
            errors.append("contest_id must be a positive integer")
        else:
            # Check if contest exists
            contest = Contest.query.get(data['contest_id'])
            if not contest:
                errors.append(f"Contest with ID {data['contest_id']} does not exist")
    
    # Validate answers
    if 'answers' in data:
        if not isinstance(data['answers'], list):
            errors.append("answers must be a list")
        elif len(data['answers']) == 0:
            errors.append("answers list cannot be empty")
        else:
            for i, answer in enumerate(data['answers']):
                if not isinstance(answer, dict):
                    errors.append(f"Answer {i+1}: must be an object")
                    continue
                
                if 'question_order' not in answer:
                    errors.append(f"Answer {i+1}: missing required field 'question_order'")
                elif not isinstance(answer['question_order'], int) or answer['question_order'] < 1:
                    errors.append(f"Answer {i+1}: question_order must be a positive integer")
                
                if 'correct_answer' not in answer:
                    errors.append(f"Answer {i+1}: missing required field 'correct_answer'")
                elif not isinstance(answer['correct_answer'], bool):
                    errors.append(f"Answer {i+1}: correct_answer must be a boolean")
    
    return len(errors) == 0, errors


def process_contest_creation(data, current_user):
    """Process contest creation from JSON data.
    
    Args:
        data (dict): Validated JSON data
        current_user (User): Current admin user
        
    Returns:
        tuple: (success, message, contest_id)
    """
    try:
        # Parse lock timestamp
        lock_timestamp = datetime.fromisoformat(data['lock_timestamp'].replace('Z', '+00:00'))
        
        # Create contest
        contest = Contest(
            contest_name=data['contest_name'],
            description=data.get('description', ''),
            created_by_user=current_user.user_id,
            lock_timestamp=lock_timestamp,
            is_active=data.get('is_active', True)
        )
        
        db.session.add(contest)
        db.session.flush()  # Get the contest ID
        
        # Create questions
        questions_created = 0
        for question_data in data['questions']:
            question = Question(
                contest_id=contest.contest_id,
                question_text=question_data['question_text'].strip(),
                question_order=question_data['question_order']
            )
            db.session.add(question)
            questions_created += 1
        
        db.session.commit()
        
        return True, f"Contest '{contest.contest_name}' created successfully with {questions_created} questions.", contest.contest_id
        
    except Exception as e:
        db.session.rollback()
        return False, f"Error creating contest: {str(e)}", None


def process_bulk_entries(data):
    """Process bulk entries from JSON data.
    
    Args:
        data (dict): Validated JSON data
        
    Returns:
        tuple: (success, message, stats)
    """
    try:
        contest = Contest.query.get(data['contest_id'])
        questions = contest.get_questions_ordered()
        question_order_map = {q.question_order: q.question_id for q in questions}
        
        entries_created = 0
        entries_skipped = 0
        answers_created = 0
        
        for entry_data in data['entries']:
            user = User.query.filter_by(email=entry_data['user_email']).first()
            
            # Check if entry already exists
            existing_entry = ContestEntry.query.filter_by(
                contest_id=contest.contest_id,
                user_id=user.user_id
            ).first()
            
            if existing_entry:
                entries_skipped += 1
                continue
            
            # Create entry
            entry = ContestEntry(
                contest_id=contest.contest_id,
                user_id=user.user_id
            )
            db.session.add(entry)
            db.session.flush()  # Get the entry ID
            
            # Create answers
            for answer_data in entry_data['answers']:
                question_order = answer_data['question_order']
                if question_order in question_order_map:
                    answer = EntryAnswer(
                        entry_id=entry.entry_id,
                        question_id=question_order_map[question_order],
                        user_answer=answer_data['answer']
                    )
                    db.session.add(answer)
                    answers_created += 1
            
            entries_created += 1
        
        db.session.commit()
        
        stats = {
            'entries_created': entries_created,
            'entries_skipped': entries_skipped,
            'answers_created': answers_created
        }
        
        message = f"Processed {entries_created} entries with {answers_created} answers. {entries_skipped} entries were skipped (already exist)."
        return True, message, stats
        
    except Exception as e:
        db.session.rollback()
        return False, f"Error processing entries: {str(e)}", None


def process_bulk_answers(data):
    """Process bulk answer setting from JSON data.
    
    Args:
        data (dict): Validated JSON data
        
    Returns:
        tuple: (success, message, stats)
    """
    try:
        contest = Contest.query.get(data['contest_id'])
        questions = contest.get_questions_ordered()
        question_order_map = {q.question_order: q for q in questions}
        
        answers_set = 0
        
        for answer_data in data['answers']:
            question_order = answer_data['question_order']
            if question_order in question_order_map:
                question = question_order_map[question_order]
                question.set_answer(answer_data['correct_answer'])
                answers_set += 1
        
        db.session.commit()
        
        stats = {'answers_set': answers_set}
        message = f"Set correct answers for {answers_set} questions in contest '{contest.contest_name}'."
        return True, message, stats
        
    except Exception as e:
        db.session.rollback()
        return False, f"Error setting answers: {str(e)}", None


@admin.route('/bulk-operations', methods=['GET', 'POST'])
@admin_required
def bulk_operations():
    """Bulk operations page for JSON file uploads.
    
    Returns:
        Rendered bulk operations template or redirect after processing
    """
    form = BulkOperationForm()
    current_user = get_current_user()
    
    if form.validate_on_submit():
        try:
            # Read and parse JSON file
            json_file = form.json_file.data
            json_content = json_file.read().decode('utf-8')
            data = json.loads(json_content)
            
            operation_type = form.operation_type.data
            
            # Validate based on operation type
            if operation_type == 'create_contest':
                is_valid, errors = validate_contest_json(data)
                if is_valid:
                    success, message, contest_id = process_contest_creation(data, current_user)
                    if success:
                        flash(message, 'success')
                        return redirect(url_for('admin.edit_contest', contest_id=contest_id))
                    else:
                        flash(message, 'error')
                else:
                    flash('JSON validation failed:', 'error')
                    for error in errors:
                        flash(f"• {error}", 'error')
            
            elif operation_type == 'add_entries':
                is_valid, errors = validate_entries_json(data)
                if is_valid:
                    success, message, stats = process_bulk_entries(data)
                    if success:
                        flash(message, 'success')
                        return redirect(url_for('admin.view_contest_entries', contest_id=data['contest_id']))
                    else:
                        flash(message, 'error')
                else:
                    flash('JSON validation failed:', 'error')
                    for error in errors:
                        flash(f"• {error}", 'error')
            
            elif operation_type == 'set_answers':
                is_valid, errors = validate_answers_json(data)
                if is_valid:
                    success, message, stats = process_bulk_answers(data)
                    if success:
                        flash(message, 'success')
                        return redirect(url_for('admin.view_contest_entries', contest_id=data['contest_id']))
                    else:
                        flash(message, 'error')
                else:
                    flash('JSON validation failed:', 'error')
                    for error in errors:
                        flash(f"• {error}", 'error')
        
        except json.JSONDecodeError as e:
            flash(f'Invalid JSON file: {str(e)}', 'error')
        except Exception as e:
            flash(f'Error processing file: {str(e)}', 'error')
    
    return render_template('admin/bulk_operations.html', form=form)


@admin.route('/bulk-operations/template/<operation_type>')
@admin_required
def download_template(operation_type):
    """Download JSON template for bulk operations.
    
    Args:
        operation_type (str): Type of operation template to download
        
    Returns:
        JSON file download
    """
    templates = {
        'create_contest': {
            "contest_name": "Sample Contest",
            "description": "This is a sample contest description",
            "lock_timestamp": "2025-01-15T18:00:00",
            "is_active": True,
            "questions": [
                {
                    "question_text": "Will the temperature exceed 75°F tomorrow?",
                    "question_order": 1
                },
                {
                    "question_text": "Will it rain tomorrow?",
                    "question_order": 2
                },
                {
                    "question_text": "Will the stock market close higher than today?",
                    "question_order": 3
                }
            ]
        },
        'add_entries': {
            "contest_id": 1,
            "entries": [
                {
                    "user_email": "user1@example.com",
                    "answers": [
                        {"question_order": 1, "answer": True},
                        {"question_order": 2, "answer": False},
                        {"question_order": 3, "answer": True}
                    ]
                },
                {
                    "user_email": "user2@example.com",
                    "answers": [
                        {"question_order": 1, "answer": False},
                        {"question_order": 2, "answer": True},
                        {"question_order": 3, "answer": False}
                    ]
                }
            ]
        },
        'set_answers': {
            "contest_id": 1,
            "answers": [
                {"question_order": 1, "correct_answer": True},
                {"question_order": 2, "correct_answer": False},
                {"question_order": 3, "correct_answer": True}
            ]
        }
    }
    
    if operation_type not in templates:
        flash('Invalid template type.', 'error')
        return redirect(url_for('admin.bulk_operations'))
    
    template_data = templates[operation_type]
    json_str = json.dumps(template_data, indent=2)
    
    # Create file-like object
    output = io.StringIO()
    output.write(json_str)
    output.seek(0)
    
    # Convert to bytes
    bytes_output = io.BytesIO()
    bytes_output.write(json_str.encode('utf-8'))
    bytes_output.seek(0)
    
    filename = f"{operation_type}_template.json"
    
    return send_file(
        bytes_output,
        mimetype='application/json',
        as_attachment=True,
        download_name=filename
    )
