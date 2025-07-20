"""Contest routes for the Over-Under Contests application."""
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DateTimeLocalField, FieldList, FormField, BooleanField, SubmitField, SelectField, IntegerField
from wtforms.validators import DataRequired, Length, Optional, NumberRange
from app import db
from app.models import Contest, Question, ContestEntry, EntryAnswer, User
from app.utils.decorators import login_required, contest_owner_required, get_current_user
from app.utils.timezone import get_timezone_choices, convert_to_utc, convert_from_utc, get_user_timezone
from app.utils.invitations import send_bulk_invitations
from app.utils.ai_generation import generate_nfl_contest, generate_contest_name_and_description, get_suggested_lock_time, ContestGenerationError
from app.utils.verification_checks import VerificationChecker, VerificationDecorator

contests = Blueprint('contests', __name__)


class QuestionForm(FlaskForm):
    """Form for individual contest questions."""
    
    question_text = StringField('Question', validators=[DataRequired(), Length(max=500)])


class ContestForm(FlaskForm):
    """Form for creating and editing contests."""
    
    contest_name = StringField('Contest Name', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[Length(max=1000)])
    lock_timestamp = DateTimeLocalField('Lock Date & Time', validators=[DataRequired()], format='%Y-%m-%dT%H:%M')
    timezone = SelectField('Timezone', choices=get_timezone_choices(), default='US/Central')
    questions = FieldList(FormField(QuestionForm), min_entries=1, max_entries=50)
    submit = SubmitField('Save Contest')


class EntryForm(FlaskForm):
    """Form for contest entries."""
    
    submit = SubmitField('Submit Entry')


class InvitationForm(FlaskForm):
    """Form for sending contest invitations."""
    
    email_addresses = TextAreaField('Email Addresses', 
                                   validators=[Length(max=2000)],
                                   render_kw={'placeholder': 'Enter email addresses, one per line or separated by commas'})
    phone_numbers = TextAreaField('Phone Numbers', 
                                 validators=[Length(max=1000)],
                                 render_kw={'placeholder': 'Enter phone numbers, one per line or separated by commas'})
    submit = SubmitField('Send Invitations')


class AutoGenerateForm(FlaskForm):
    """Form for auto-generating contests."""
    
    generation_type = SelectField('Generation Type',
                                 choices=[('nfl', 'NFL Sports Betting'), ('custom', 'Custom Prompt')],
                                 default='nfl',
                                 validators=[DataRequired()])
    sport = SelectField('Sport', 
                       choices=[('NFL', 'NFL')], 
                       default='NFL',
                       validators=[Optional()])
    question_count = IntegerField('Number of Questions', 
                                 validators=[DataRequired(), NumberRange(min=1, max=10)],
                                 default=5,
                                 render_kw={'min': '1', 'max': '10'})
    week_number = IntegerField('Week Number', 
                              validators=[Optional(), NumberRange(min=1, max=18)],
                              render_kw={'placeholder': 'Leave blank for current week'})
    season_year = IntegerField('Season Year', 
                              validators=[Optional(), NumberRange(min=2020, max=2030)],
                              render_kw={'placeholder': 'Leave blank for current season'})
    custom_prompt = TextAreaField('Custom Prompt',
                                 validators=[Optional(), Length(max=1000)],
                                 render_kw={'placeholder': 'Describe the type of contest you want to create. For example: "Create questions about technology predictions for 2024" or "Generate questions about weather events in major cities"', 'rows': '4'})
    timezone = SelectField('Timezone', choices=get_timezone_choices(), default='US/Central')
    accepted_questions = StringField('Accepted Questions', validators=[Optional()])
    submit = SubmitField('Generate Contest')


@contests.route('/')
def list_contests():
    """List all active contests.
    
    Returns:
        Rendered template with contests list
    """
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    contests_query = Contest.query.filter_by(is_active=True).order_by(Contest.created_at.desc())
    contests_pagination = contests_query.paginate(page=page, per_page=per_page, error_out=False)
    
    current_user = get_current_user()
    
    return render_template('contests/list.html', 
                         contests=contests_pagination,
                         current_user=current_user)


@contests.route('/<int:contest_id>')
def view_contest(contest_id):
    """View contest details and leaderboard if locked.
    
    Args:
        contest_id (int): Contest ID
        
    Returns:
        Rendered template with contest details
    """
    contest = Contest.query.get_or_404(contest_id)
    current_user = get_current_user()
    
    # Check if user has an entry
    user_entry = None
    if current_user:
        user_entry = ContestEntry.query.filter_by(
            contest_id=contest_id, 
            user_id=current_user.user_id
        ).first()
    
    # Get leaderboard if contest is locked and all answers have been set
    leaderboard = None
    if contest.is_locked() and contest.has_all_answers():
        leaderboard = contest.get_leaderboard()
    
    questions = contest.get_questions_ordered()
    
    return render_template('contests/detail.html',
                         contest=contest,
                         questions=questions,
                         user_entry=user_entry,
                         leaderboard=leaderboard,
                         current_user=current_user)


@contests.route('/create', methods=['GET', 'POST'])
@login_required
def create_contest():
    """Create a new contest.
    
    Returns:
        Rendered template for contest creation or redirect after creation
    """
    # Check verification requirements
    current_user = get_current_user()
    can_create, reason = VerificationChecker.can_create_contest(current_user.user_id)
    if not can_create:
        flash(reason, 'warning')
        return redirect(url_for('verification.request_verification'))
    
    form = ContestForm()
    
    # Check for AI-generated data in session
    from flask import session
    ai_generated_data = session.get('ai_generated_data', None)
    is_ai_generated = False
    
    if request.method == 'GET' and ai_generated_data:
        # Pre-populate form with AI-generated data
        is_ai_generated = True
        
        # Set basic contest info
        form.contest_name.data = ai_generated_data['contest_name']
        form.description.data = ai_generated_data['description']
        form.timezone.data = ai_generated_data['timezone']
        
        # Convert suggested lock time to local time for display
        from datetime import datetime
        suggested_lock_time = datetime.fromisoformat(ai_generated_data['suggested_lock_time'].replace('Z', '+00:00'))
        local_lock_time = convert_from_utc(suggested_lock_time, ai_generated_data['timezone'])
        form.lock_timestamp.data = local_lock_time
        
        # Clear existing questions and add AI-generated ones
        while len(form.questions.entries) > 0:
            form.questions.pop_entry()
        
        # Debug logging
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"📝 Pre-populating {len(ai_generated_data['questions'])} questions:")
        
        # Properly populate FieldList with AI-generated questions
        for i, question_data in enumerate(ai_generated_data['questions']):
            question_text = question_data['question']
            # Create the entry data dictionary that FieldList expects
            entry_data = {'question_text': question_text}
            form.questions.append_entry(entry_data)
            logger.info(f"   Question {i+1}: {question_text[:50]}...")
        
        # Ensure we have at least one question entry
        if len(form.questions.entries) == 0:
            logger.warning("No questions were added, adding empty question form")
            form.questions.append_entry()
        
        logger.info(f"✅ Form now has {len(form.questions.entries)} question entries")
    
    if form.validate_on_submit():
        current_user = get_current_user()
        
        # Convert local time to UTC
        local_lock_time = form.lock_timestamp.data
        timezone_str = form.timezone.data
        utc_lock_time = convert_to_utc(local_lock_time, timezone_str)
        
        # Create contest
        contest = Contest(
            contest_name=form.contest_name.data,
            description=form.description.data,
            created_by_user=current_user.user_id,
            lock_timestamp=utc_lock_time,
            is_ai_generated=ai_generated_data is not None
        )
        
        db.session.add(contest)
        db.session.flush()  # Get contest ID
        
        # Add questions
        for i, question_form in enumerate(form.questions.data):
            if question_form['question_text'].strip():
                question = Question(
                    contest_id=contest.contest_id,
                    question_text=question_form['question_text'].strip(),
                    question_order=i + 1
                    # correct_answer will be None initially
                )
                db.session.add(question)
        
        db.session.commit()
        
        # Clear AI-generated data from session after successful creation
        if ai_generated_data:
            session.pop('ai_generated_data', None)
        
        flash('Contest created successfully!', 'success')
        return redirect(url_for('contests.view_contest', contest_id=contest.contest_id))
    
    # Pass additional context for AI-generated contests
    template_context = {
        'form': form, 
        'title': 'Create Contest',
        'is_ai_generated': is_ai_generated
    }
    
    return render_template('contests/form.html', **template_context)


@contests.route('/<int:contest_id>/edit', methods=['GET', 'POST'])
@login_required
@contest_owner_required
def edit_contest(contest_id):
    """Edit an existing contest.
    
    Args:
        contest_id (int): Contest ID
        
    Returns:
        Rendered template for contest editing or redirect after update
    """
    contest = Contest.query.get_or_404(contest_id)
    
    # Check if contest can be modified
    if contest.has_entries() and not get_current_user().is_admin:
        flash('Cannot modify contest questions after entries have been submitted.', 'error')
        return redirect(url_for('contests.view_contest', contest_id=contest_id))
    
    form = ContestForm(obj=contest)
    
    if request.method == 'GET':
        # Populate questions
        questions = contest.get_questions_ordered()
        form.questions.entries.clear()
        for question in questions:
            question_form = QuestionForm()
            question_form.question_text.data = question.question_text
            form.questions.append_entry(question_form)
        
        # Convert UTC time to local time for display
        user_timezone = get_user_timezone()
        if contest.lock_timestamp:
            local_time = convert_from_utc(contest.lock_timestamp, user_timezone)
            form.lock_timestamp.data = local_time
            form.timezone.data = user_timezone
    
    # If form validation failed, ensure we still have questions populated
    elif not form.validate_on_submit() and not form.questions.entries:
        # Re-populate questions if form submission failed and questions are empty
        questions = contest.get_questions_ordered()
        form.questions.entries.clear()
        for question in questions:
            question_form = QuestionForm()
            question_form.question_text.data = question.question_text
            form.questions.append_entry(question_form)
    
    if form.validate_on_submit():
        # Convert local time to UTC
        local_lock_time = form.lock_timestamp.data
        timezone_str = form.timezone.data
        utc_lock_time = convert_to_utc(local_lock_time, timezone_str)
        
        # Update contest details
        contest.contest_name = form.contest_name.data
        contest.description = form.description.data
        contest.lock_timestamp = utc_lock_time
        contest.updated_at = datetime.utcnow()
        
        # Update questions if allowed
        if contest.can_modify_questions() or get_current_user().is_admin:
            # Delete existing questions
            Question.query.filter_by(contest_id=contest_id).delete()
            
            # Add new questions
            for i, question_form in enumerate(form.questions.data):
                if question_form['question_text'].strip():
                    question = Question(
                        contest_id=contest.contest_id,
                        question_text=question_form['question_text'].strip(),
                        question_order=i + 1
                        # correct_answer will be None initially
                    )
                    db.session.add(question)
        
        db.session.commit()
        
        flash('Contest updated successfully!', 'success')
        return redirect(url_for('contests.view_contest', contest_id=contest_id))
    
    return render_template('contests/form.html', 
                         form=form, 
                         contest=contest,
                         title='Edit Contest')


@contests.route('/<int:contest_id>/delete', methods=['POST'])
@login_required
@contest_owner_required
def delete_contest(contest_id):
    """Delete a contest.
    
    Args:
        contest_id (int): Contest ID
        
    Returns:
        Redirect to contests list
    """
    contest = Contest.query.get_or_404(contest_id)
    current_user = get_current_user()
    
    # Only allow deletion if no entries or if admin
    if contest.has_entries() and not current_user.is_admin:
        flash('Cannot delete contest with existing entries.', 'error')
        return redirect(url_for('contests.view_contest', contest_id=contest_id))
    
    try:
        # For contests with entries, admins can choose to either soft delete or hard delete
        if contest.has_entries() and current_user.is_admin:
            # Soft delete - just mark as inactive to preserve data
            contest.is_active = False
            db.session.commit()
            flash('Contest deactivated successfully. Data has been preserved.', 'success')
        else:
            # Hard delete - actually remove the contest and all related data
            # The cascade='all, delete-orphan' relationships will handle cleanup
            db.session.delete(contest)
            db.session.commit()
            flash('Contest deleted successfully.', 'success')
    
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting contest: {str(e)}', 'error')
        return redirect(url_for('contests.view_contest', contest_id=contest_id))
    
    return redirect(url_for('contests.list_contests'))


@contests.route('/<int:contest_id>/enter', methods=['GET', 'POST'])
@login_required
def enter_contest(contest_id):
    """Enter or modify contest entry.
    
    Args:
        contest_id (int): Contest ID
        
    Returns:
        Rendered template for entry form or redirect after submission
    """
    contest = Contest.query.get_or_404(contest_id)
    current_user = get_current_user()
    
    # Check verification requirements for participation
    can_participate, reason = VerificationChecker.can_participate_in_contest(current_user.user_id, contest_id)
    if not can_participate:
        flash(reason, 'warning')
        if 'verification' in reason.lower():
            return redirect(url_for('verification.request_verification'))
        else:
            return redirect(url_for('contests.view_contest', contest_id=contest_id))
    
    # Check if contest is locked
    if contest.is_locked():
        flash('Contest is locked. No more entries allowed.', 'error')
        return redirect(url_for('contests.view_contest', contest_id=contest_id))
    
    # Get or create entry
    entry = ContestEntry.query.filter_by(
        contest_id=contest_id,
        user_id=current_user.user_id
    ).first()
    
    if not entry:
        entry = ContestEntry(
            contest_id=contest_id,
            user_id=current_user.user_id
        )
        db.session.add(entry)
        db.session.flush()
    
    questions = contest.get_questions_ordered()
    existing_answers = entry.get_answers_dict() if entry.entry_id else {}
    
    if request.method == 'POST':
        # Process form submission
        for question in questions:
            answer_key = f'question_{question.question_id}'
            user_answer = request.form.get(answer_key) == 'True'
            
            # Get or create answer
            answer = EntryAnswer.query.filter_by(
                entry_id=entry.entry_id,
                question_id=question.question_id
            ).first()
            
            if answer:
                answer.user_answer = user_answer
            else:
                answer = EntryAnswer(
                    entry_id=entry.entry_id,
                    question_id=question.question_id,
                    user_answer=user_answer
                )
                db.session.add(answer)
        
        entry.updated_at = datetime.utcnow()
        db.session.commit()
        
        flash('Entry submitted successfully!', 'success')
        return redirect(url_for('contests.view_contest', contest_id=contest_id))
    
    return render_template('contests/entry_form.html',
                         contest=contest,
                         questions=questions,
                         existing_answers=existing_answers,
                         entry=entry)


@contests.route('/<int:contest_id>/leaderboard')
def leaderboard(contest_id):
    """View contest leaderboard.
    
    Args:
        contest_id (int): Contest ID
        
    Returns:
        Rendered template with leaderboard
    """
    contest = Contest.query.get_or_404(contest_id)
    
    if not contest.is_locked():
        flash('Leaderboard will be available after the contest is locked.', 'info')
        return redirect(url_for('contests.view_contest', contest_id=contest_id))
    
    # Only show leaderboard if all answers have been set
    leaderboard = None
    if contest.has_all_answers():
        leaderboard = contest.get_leaderboard()
    
    questions = contest.get_questions_ordered()
    
    return render_template('contests/leaderboard.html',
                         contest=contest,
                         leaderboard=leaderboard,
                         questions=questions)


@contests.route('/my-contests')
@login_required
def my_contests():
    """View user's created contests and entries.
    
    Returns:
        Rendered template with user's contests
    """
    current_user = get_current_user()
    
    # Get user's created contests
    created_contests = current_user.get_contests_created()
    
    # Get user's contest entries
    contest_entries = current_user.get_contest_entries()
    
    # Calculate detailed statistics for contest entries
    stats = {
        'total_entries': len(contest_entries),
        'completed_contests': 0,
        'first_place_finishes': 0,
        'top_3_finishes': 0,
        'total_score': 0,
        'total_possible_score': 0,
        'positions': [],
        'average_position': 0,
        'best_position': None,
        'worst_position': None,
        'win_rate': 0,
        'top_3_rate': 0
    }
    
    if contest_entries:
        for entry in contest_entries:
            if entry.contest.is_locked() and entry.contest.has_all_answers():
                stats['completed_contests'] += 1
                
                # Calculate score for this entry
                score_data = entry.calculate_score()
                stats['total_score'] += score_data['correct_answers']
                stats['total_possible_score'] += score_data['answered_questions']
                
                # Get leaderboard to determine position
                leaderboard = entry.contest.get_leaderboard()
                user_position = None
                
                for i, leader in enumerate(leaderboard, 1):
                    if leader['user'].user_id == current_user.user_id:
                        user_position = i
                        break
                
                if user_position:
                    stats['positions'].append(user_position)
                    
                    if user_position == 1:
                        stats['first_place_finishes'] += 1
                    
                    if user_position <= 3:
                        stats['top_3_finishes'] += 1
        
        # Calculate derived statistics
        if stats['positions']:
            stats['average_position'] = round(sum(stats['positions']) / len(stats['positions']), 1)
            stats['best_position'] = min(stats['positions'])
            stats['worst_position'] = max(stats['positions'])
        
        if stats['completed_contests'] > 0:
            stats['win_rate'] = round((stats['first_place_finishes'] / stats['completed_contests']) * 100, 1)
            stats['top_3_rate'] = round((stats['top_3_finishes'] / stats['completed_contests']) * 100, 1)
        
        if stats['total_possible_score'] > 0:
            stats['overall_accuracy'] = round((stats['total_score'] / stats['total_possible_score']) * 100, 1)
        else:
            stats['overall_accuracy'] = 0
    
    return render_template('contests/my_contests.html',
                         created_contests=created_contests,
                         contest_entries=contest_entries,
                         current_user=current_user,
                         stats=stats)


@contests.route('/<int:contest_id>/set-answers', methods=['GET', 'POST'])
@login_required
@contest_owner_required
def set_answers(contest_id):
    """Set answers for contest questions after the contest is locked.
    
    Args:
        contest_id (int): Contest ID
        
    Returns:
        Rendered template for setting answers or redirect after submission
    """
    contest = Contest.query.get_or_404(contest_id)
    
    # Only allow setting answers if contest is locked
    if not contest.is_locked():
        flash('Answers can only be set after the contest is locked.', 'error')
        return redirect(url_for('contests.view_contest', contest_id=contest_id))
    
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
            entry.score = score_data['correct_answers']
        
        db.session.commit()
        
        flash('Answers set successfully! Scores have been calculated.', 'success')
        return redirect(url_for('contests.leaderboard', contest_id=contest_id))
    
    return render_template('contests/set_answers.html',
                         contest=contest,
                         questions=questions)


@contests.route('/<int:contest_id>/update-answer/<int:question_id>', methods=['POST'])
@login_required
@contest_owner_required
def update_answer(contest_id, question_id):
    """Update a single question's answer via AJAX.
    
    Args:
        contest_id (int): Contest ID
        question_id (int): Question ID
        
    Returns:
        JSON response
    """
    contest = Contest.query.get_or_404(contest_id)
    question = Question.query.get_or_404(question_id)
    
    # Verify question belongs to contest
    if question.contest_id != contest_id:
        return jsonify({'error': 'Question does not belong to this contest'}), 400
    
    # Only allow setting answers if contest is locked
    if not contest.is_locked():
        return jsonify({'error': 'Answers can only be set after contest is locked'}), 400
    
    try:
        correct_answer = request.json.get('correct_answer')
        if correct_answer is None:
            return jsonify({'error': 'Missing correct_answer field'}), 400
        
        question.set_answer(bool(correct_answer))
        db.session.commit()
        
        # Recalculate scores for all entries
        for entry in contest.entries.all():
            score_data = entry.calculate_score()
            entry.score = score_data['correct_answers']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'question_id': question_id,
            'correct_answer': question.correct_answer,
            'answer_set_at': question.answer_set_at.isoformat() if question.answer_set_at else None
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@contests.route('/<int:contest_id>/autosave-entry', methods=['POST'])
@login_required
def autosave_entry(contest_id):
    """Auto-save contest entry data.
    
    Args:
        contest_id (int): Contest ID
        
    Returns:
        JSON response indicating success or failure
    """
    try:
        contest = Contest.query.get_or_404(contest_id)
        current_user = get_current_user()
        
        # Check if contest is locked
        if contest.is_locked():
            return jsonify({'error': 'Contest is locked'}), 400
        
        # Get or create entry
        entry = ContestEntry.query.filter_by(
            contest_id=contest_id,
            user_id=current_user.user_id
        ).first()
        
        if not entry:
            entry = ContestEntry(
                contest_id=contest_id,
                user_id=current_user.user_id
            )
            db.session.add(entry)
            db.session.flush()
        
        # Get form data
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Save answers
        questions = contest.get_questions_ordered()
        for question in questions:
            answer_key = f'question_{question.question_id}'
            if answer_key in data:
                user_answer = data[answer_key] == 'True'
                
                # Get or create answer
                answer = EntryAnswer.query.filter_by(
                    entry_id=entry.entry_id,
                    question_id=question.question_id
                ).first()
                
                if answer:
                    answer.user_answer = user_answer
                else:
                    answer = EntryAnswer(
                        entry_id=entry.entry_id,
                        question_id=question.question_id,
                        user_answer=user_answer
                    )
                    db.session.add(answer)
        
        entry.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Entry auto-saved'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@contests.route('/<int:contest_id>/invite', methods=['GET', 'POST'])
@login_required
@contest_owner_required
def invite_to_contest(contest_id):
    """Send invitations to contest.
    
    Args:
        contest_id (int): Contest ID
        
    Returns:
        Rendered template for sending invitations or redirect after sending
    """
    contest = Contest.query.get_or_404(contest_id)
    current_user = get_current_user()
    form = InvitationForm()
    
    if form.validate_on_submit():
        # Parse email addresses
        emails = []
        if form.email_addresses.data:
            email_text = form.email_addresses.data.strip()
            # Split by newlines and commas, then clean up
            raw_emails = []
            for line in email_text.split('\n'):
                raw_emails.extend([email.strip() for email in line.split(',')])
            emails = [email for email in raw_emails if email]
        
        # Parse phone numbers
        phones = []
        if form.phone_numbers.data:
            phone_text = form.phone_numbers.data.strip()
            # Split by newlines and commas, then clean up
            raw_phones = []
            for line in phone_text.split('\n'):
                raw_phones.extend([phone.strip() for phone in line.split(',')])
            phones = [phone for phone in raw_phones if phone]
        
        if not emails and not phones:
            flash('Please enter at least one email address or phone number.', 'error')
            return render_template('contests/invite.html', contest=contest, form=form)
        
        # Send invitations
        results = send_bulk_invitations(contest, current_user, emails, phones)
        
        # Display results
        if results['total_sent'] > 0:
            flash(f"Successfully sent {results['total_sent']} invitations!", 'success')
            
            if results['email_sent'] > 0:
                flash(f"Email invitations sent: {results['email_sent']}", 'info')
            
            if results['sms_sent'] > 0:
                flash(f"SMS invitations sent: {results['sms_sent']}", 'info')
        
        if results['email_failed'] > 0 or results['sms_failed'] > 0:
            total_failed = results['email_failed'] + results['sms_failed']
            flash(f"Failed to send {total_failed} invitations.", 'warning')
        
        # Show specific errors
        for error in results['errors']:
            flash(error, 'error')
        
        return redirect(url_for('contests.view_contest', contest_id=contest_id))
    
    # Get invitation statistics
    invitation_stats = {
        'total_sent': contest.get_invitation_count(),
        'remaining': contest.get_remaining_invitations(),
        'email_sent': len([inv for inv in contest.invitations if inv.invitation_type == 'email']),
        'sms_sent': len([inv for inv in contest.invitations if inv.invitation_type == 'sms'])
    }
    
    return render_template('contests/invite.html', 
                         contest=contest, 
                         form=form,
                         invitation_stats=invitation_stats)


@contests.route('/auto-generate', methods=['GET', 'POST'])
@login_required
def auto_generate():
    """Auto-generate a contest using AI.
    
    Returns:
        Rendered template for auto-generation form or redirect after creation
    """
    form = AutoGenerateForm()
    current_user = get_current_user()
    
    # Check if user can create AI contests
    if current_user and not current_user.can_create_ai_contest():
        remaining = current_user.get_remaining_ai_contests_today()
        flash(f'You have reached your daily limit of 3 AI-generated contests. You can create {remaining} more tomorrow.', 'error')
        return redirect(url_for('contests.list_contests'))
    
    if form.validate_on_submit():
        try:
            # Double-check the limit before creating
            if not current_user.can_create_ai_contest():
                flash('You have reached your daily limit of AI-generated contests.', 'error')
                return render_template('contests/auto_generate.html', form=form)
            
            sport = form.sport.data
            question_count = form.question_count.data
            week_number = form.week_number.data
            season_year = form.season_year.data
            timezone_str = form.timezone.data
            
            generation_type = form.generation_type.data
            custom_prompt = form.custom_prompt.data
            
            # Check if we have accepted questions from the preview modal
            accepted_questions_json = form.accepted_questions.data
            
            # Debug logging
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"✅ Auto-generate form submitted successfully!")
            logger.info(f"   - Generation type: {generation_type}")
            logger.info(f"   - Sport: {sport}")
            logger.info(f"   - Question count: {question_count}")
            logger.info(f"   - Week: {week_number}")
            logger.info(f"   - Season: {season_year}")
            logger.info(f"   - Custom prompt: {custom_prompt[:100] if custom_prompt else 'None'}...")
            logger.info(f"   - Timezone: {timezone_str}")
            logger.info(f"   - Has accepted_questions: {bool(accepted_questions_json)}")
            if accepted_questions_json:
                logger.info(f"   - Accepted questions length: {len(accepted_questions_json)} chars")
            
            if accepted_questions_json:
                # Use the accepted questions from the preview
                import json
                logger.info("Using accepted questions from preview modal")
                accepted_data = json.loads(accepted_questions_json)
                
                # Store the generated data in session for the create form
                from flask import session
                session['ai_generated_data'] = {
                    'contest_name': accepted_data['contest_name'],
                    'description': accepted_data['description'],
                    'suggested_lock_time': accepted_data['suggested_lock_time'],
                    'questions': accepted_data['questions'],
                    'timezone': timezone_str,
                    'is_ai_generated': True
                }
                
                flash('Questions generated successfully! Please review and customize the contest details below.', 'success')
                return redirect(url_for('contests.create_contest'))
            else:
                # Generate new questions (fallback for direct form submission)
                logger.info("Generating new questions (no accepted questions found)")
                
                if generation_type == 'custom':
                    # Validate custom prompt
                    if not custom_prompt or not custom_prompt.strip():
                        flash('Please provide a custom prompt for contest generation.', 'error')
                        return render_template('contests/auto_generate.html', form=form)
                    
                    # Generate custom contest
                    from app.utils.ai_generation import generate_custom_contest
                    questions_data = generate_custom_contest(custom_prompt.strip(), question_count)
                    
                    # Create contest name and description based on prompt
                    contest_name = f"Custom Contest - {datetime.now().strftime('%B %d, %Y')}"
                    description = f"Custom prediction contest: {custom_prompt[:200]}{'...' if len(custom_prompt) > 200 else ''}"
                    
                    # Get suggested lock time (default to 3 days from now)
                    suggested_lock_time = datetime.now() + timedelta(days=3)
                    suggested_lock_time = suggested_lock_time.replace(hour=20, minute=0, second=0, microsecond=0)
                    
                else:
                    # NFL generation
                    contest_info = generate_contest_name_and_description(
                        sport=sport,
                        week_number=week_number,
                        season_year=season_year
                    )
                    
                    suggested_lock_time = get_suggested_lock_time(sport, week_number)
                    
                    # Generate questions based on sport
                    if sport.upper() == 'NFL':
                        questions_data = generate_nfl_contest(week_number, season_year, question_count)
                    else:
                        flash('Only NFL contests are currently supported for auto-generation.', 'error')
                        return render_template('contests/auto_generate.html', form=form)
                    
                    contest_name = contest_info['name']
                    description = contest_info['description']
                
                # Store the generated data in session for the create form
                from flask import session
                session['ai_generated_data'] = {
                    'contest_name': contest_name,
                    'description': description,
                    'suggested_lock_time': suggested_lock_time.isoformat(),
                    'questions': questions_data,
                    'timezone': timezone_str,
                    'is_ai_generated': True
                }
                
                flash('Questions generated successfully! Please review and customize the contest details below.', 'success')
                return redirect(url_for('contests.create_contest'))
            
        except ContestGenerationError as e:
            flash(f'Failed to generate contest: {str(e)}', 'error')
            return render_template('contests/auto_generate.html', form=form)
        
        except Exception as e:
            db.session.rollback()
            flash(f'An unexpected error occurred: {str(e)}', 'error')
            return render_template('contests/auto_generate.html', form=form)
    
    else:
        # Form validation failed - add debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Form validation failed. Errors: {form.errors}")
        logger.info(f"Form data keys: {list(request.form.keys())}")
        logger.info(f"Request method: {request.method}")
        
        # Check if this was a submission with accepted questions
        accepted_questions_json = request.form.get('accepted_questions')
        if accepted_questions_json:
            flash('There was an issue with the form submission. Please try again.', 'error')
            logger.error(f"Form validation failed with accepted questions present")
            logger.error(f"Accepted questions length: {len(accepted_questions_json)}")
        else:
            logger.info("No accepted questions found in form data")
    
    return render_template('contests/auto_generate.html', form=form)


@contests.route('/preview-generation', methods=['POST'])
@login_required
def preview_generation():
    """Preview auto-generated contest questions without creating the contest.
    
    Returns:
        JSON response with generated questions
    """
    try:
        data = request.get_json()
        generation_type = data.get('generation_type', 'nfl')
        question_count = data.get('question_count', 5)
        
        # Convert to integer if provided
        if question_count is not None:
            question_count = int(question_count)
        
        # Validate question count
        if question_count < 1 or question_count > 10:
            return jsonify({'error': 'Question count must be between 1 and 10'}), 400
        
        if generation_type == 'custom':
            # Handle custom prompt generation
            custom_prompt = data.get('custom_prompt', '').strip()
            
            if not custom_prompt:
                return jsonify({'error': 'Please provide a custom prompt'}), 400
            
            # Generate custom contest
            from app.utils.ai_generation import generate_custom_contest
            questions_data = generate_custom_contest(custom_prompt, question_count)
            
            # Create contest name and description based on prompt
            contest_name = f"Custom Contest - {datetime.now().strftime('%B %d, %Y')}"
            description = f"Custom prediction contest: {custom_prompt[:200]}{'...' if len(custom_prompt) > 200 else ''}"
            
            # Get suggested lock time (default to 3 days from now)
            from datetime import timedelta
            suggested_lock_time = datetime.now() + timedelta(days=3)
            suggested_lock_time = suggested_lock_time.replace(hour=20, minute=0, second=0, microsecond=0)
            
        else:
            # Handle NFL generation
            sport = data.get('sport', 'NFL')
            week_number = data.get('week_number')
            season_year = data.get('season_year')
            
            # Convert empty strings to None
            if week_number == '':
                week_number = None
            if season_year == '':
                season_year = None
            
            # Convert to integers if provided
            if week_number is not None:
                week_number = int(week_number)
            if season_year is not None:
                season_year = int(season_year)
            
            # Generate contest metadata
            contest_info = generate_contest_name_and_description(
                sport=sport,
                week_number=week_number,
                season_year=season_year
            )
            
            # Generate questions based on sport
            if sport.upper() == 'NFL':
                questions_data = generate_nfl_contest(week_number, season_year, question_count)
            else:
                return jsonify({'error': 'Only NFL contests are currently supported'}), 400
            
            # Get suggested lock time
            suggested_lock_time = get_suggested_lock_time(sport, week_number)
            
            contest_name = contest_info['name']
            description = contest_info['description']
        
        return jsonify({
            'success': True,
            'contest_name': contest_name,
            'description': description,
            'suggested_lock_time': suggested_lock_time.isoformat(),
            'questions': questions_data
        })
        
    except ContestGenerationError as e:
        # Log detailed error information for debugging
        import traceback
        import logging
        
        logger = logging.getLogger(__name__)
        logger.error(f"Contest generation error: {str(e)}")
        logger.error(f"Request data: {data}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        return jsonify({'error': str(e)}), 400
    
    except Exception as e:
        # Log detailed error information for debugging
        import traceback
        import logging
        
        logger = logging.getLogger(__name__)
        logger.error(f"Unexpected error in preview_generation: {str(e)}")
        logger.error(f"Request data: {data}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500
