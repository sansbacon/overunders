"""Admin routes for content moderation management."""
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, current_app
from flask import session
from datetime import datetime, timedelta
from sqlalchemy import desc, func
from app import db
from app.models import (
    User, Contest, League, Question, ContentModerationLog, 
    ContentReport, UserWarning
)
from app.utils.content_moderation import moderate_text, is_content_safe
from app.utils.decorators import admin_required

moderation_bp = Blueprint('moderation', __name__, url_prefix='/admin/moderation')


@moderation_bp.route('/')
@admin_required
def dashboard():
    """Content moderation dashboard."""
    # Get recent moderation activity
    recent_logs = ContentModerationLog.query.order_by(desc(ContentModerationLog.created_at)).limit(20).all()
    
    # Get pending reports
    pending_reports = ContentReport.query.filter_by(status='pending').order_by(desc(ContentReport.created_at)).all()
    
    # Get moderation statistics
    today = datetime.utcnow().date()
    week_ago = today - timedelta(days=7)
    
    stats = {
        'total_logs': ContentModerationLog.query.count(),
        'logs_today': ContentModerationLog.query.filter(
            func.date(ContentModerationLog.created_at) == today
        ).count(),
        'logs_this_week': ContentModerationLog.query.filter(
            ContentModerationLog.created_at >= week_ago
        ).count(),
        'pending_reports': ContentReport.query.filter_by(status='pending').count(),
        'total_reports': ContentReport.query.count(),
        'blocked_content_today': ContentModerationLog.query.filter(
            func.date(ContentModerationLog.created_at) == today,
            ContentModerationLog.action_taken == 'blocked'
        ).count(),
        'ai_moderation_enabled': current_app.config.get('AI_MODERATION_ENABLED', False)
    }
    
    # Get content type breakdown
    content_type_stats = db.session.query(
        ContentModerationLog.content_type,
        func.count(ContentModerationLog.log_id).label('count')
    ).group_by(ContentModerationLog.content_type).all()
    
    return render_template('admin/moderation/dashboard.html',
                         recent_logs=recent_logs,
                         pending_reports=pending_reports,
                         stats=stats,
                         content_type_stats=content_type_stats)


@moderation_bp.route('/logs')
@admin_required
def logs():
    """View moderation logs."""
    page = request.args.get('page', 1, type=int)
    content_type = request.args.get('content_type', '')
    action = request.args.get('action', '')
    
    query = ContentModerationLog.query
    
    # Apply filters
    if content_type:
        query = query.filter(ContentModerationLog.content_type == content_type)
    if action:
        query = query.filter(ContentModerationLog.action_taken == action)
    
    logs = query.order_by(desc(ContentModerationLog.created_at)).paginate(
        page=page, per_page=50, error_out=False
    )
    
    # Get filter options
    content_types = db.session.query(ContentModerationLog.content_type).distinct().all()
    actions = db.session.query(ContentModerationLog.action_taken).distinct().all()
    
    return render_template('admin/moderation/logs.html',
                         logs=logs,
                         content_types=[ct[0] for ct in content_types],
                         actions=[a[0] for a in actions],
                         current_content_type=content_type,
                         current_action=action)


@moderation_bp.route('/reports')
@admin_required
def reports():
    """View content reports."""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    
    query = ContentReport.query
    
    if status:
        query = query.filter(ContentReport.status == status)
    
    reports = query.order_by(desc(ContentReport.created_at)).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/moderation/reports.html',
                         reports=reports,
                         current_status=status)


@moderation_bp.route('/reports/<int:report_id>/review', methods=['GET', 'POST'])
@admin_required
def review_report(report_id):
    """Review a content report."""
    report = ContentReport.query.get_or_404(report_id)
    
    if request.method == 'POST':
        action = request.form.get('action')
        notes = request.form.get('notes', '').strip()
        
        if action in ['dismissed', 'action_taken']:
            # Update report status
            report.mark_reviewed(
                reviewer_id=session['user_id'],
                status=action,
                notes=notes
            )
            
            # If action was taken, we might want to take additional steps
            if action == 'action_taken':
                # Here you could implement additional actions like:
                # - Flagging the content
                # - Warning the user
                # - Suspending the user
                pass
            
            flash(f'Report has been {action.replace("_", " ")}.', 'success')
            return redirect(url_for('moderation.reports'))
    
    # Get the actual content being reported
    content = None
    if report.content_type == 'contest':
        content = Contest.query.get(report.content_id)
    elif report.content_type == 'league':
        content = League.query.get(report.content_id)
    elif report.content_type == 'question':
        content = Question.query.get(report.content_id)
    
    return render_template('admin/moderation/review_report.html',
                         report=report,
                         content=content)


@moderation_bp.route('/test', methods=['GET', 'POST'])
@admin_required
def test_moderation():
    """Test content moderation system."""
    result = None
    
    if request.method == 'POST':
        text = request.form.get('text', '').strip()
        content_type = request.form.get('content_type', 'general')
        
        if text:
            result = moderate_text(text, content_type)
    
    return render_template('admin/moderation/test.html', result=result)


@moderation_bp.route('/settings', methods=['GET', 'POST'])
@admin_required
def settings():
    """Moderation settings management."""
    if request.method == 'POST':
        # This would typically update configuration in a database
        # For now, we'll just show current settings
        flash('Settings updated successfully.', 'success')
        return redirect(url_for('moderation.settings'))
    
    settings_data = {
        'ai_moderation_enabled': current_app.config.get('AI_MODERATION_ENABLED', False),
        'auto_moderate_new_content': current_app.config.get('AUTO_MODERATE_NEW_CONTENT', True),
        'moderate_ai_generated_content': current_app.config.get('MODERATE_AI_GENERATED_CONTENT', True),
        'content_moderation_log_enabled': current_app.config.get('CONTENT_MODERATION_LOG_ENABLED', True),
    }
    
    return render_template('admin/moderation/settings.html', settings=settings_data)


@moderation_bp.route('/warnings')
@admin_required
def warnings():
    """View user warnings."""
    page = request.args.get('page', 1, type=int)
    user_id = request.args.get('user_id', type=int)
    
    query = UserWarning.query
    
    if user_id:
        query = query.filter(UserWarning.user_id == user_id)
    
    warnings = query.order_by(desc(UserWarning.created_at)).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/moderation/warnings.html', warnings=warnings)


@moderation_bp.route('/warnings/issue', methods=['GET', 'POST'])
@admin_required
def issue_warning():
    """Issue a warning to a user."""
    if request.method == 'POST':
        user_id = request.form.get('user_id', type=int)
        warning_type = request.form.get('warning_type')
        reason = request.form.get('reason', '').strip()
        severity = request.form.get('severity')
        content_type = request.form.get('content_type', '')
        content_id = request.form.get('content_id', type=int)
        
        if user_id and warning_type and reason and severity:
            user = User.query.get(user_id)
            if user:
                # Create warning
                warning = UserWarning(
                    user_id=user_id,
                    issued_by_user_id=session['user_id'],
                    warning_type=warning_type,
                    reason=reason,
                    severity=severity,
                    content_type=content_type if content_type else None,
                    content_id=content_id if content_id else None
                )
                db.session.add(warning)
                
                # Update user warning count
                user.warning_count += 1
                
                # Adjust trust score based on severity
                if severity == 'low':
                    user.trust_score = max(0, user.trust_score - 5)
                elif severity == 'medium':
                    user.trust_score = max(0, user.trust_score - 15)
                elif severity == 'high':
                    user.trust_score = max(0, user.trust_score - 30)
                elif severity == 'critical':
                    user.trust_score = max(0, user.trust_score - 50)
                    # Consider suspension for critical warnings
                    if user.warning_count >= 3:
                        user.is_suspended = True
                        user.suspended_until = datetime.utcnow() + timedelta(days=7)
                        user.suspension_reason = f"Multiple warnings including critical: {reason}"
                
                db.session.commit()
                
                flash(f'Warning issued to {user.username}.', 'success')
                return redirect(url_for('moderation.warnings'))
            else:
                flash('User not found.', 'error')
        else:
            flash('All fields are required.', 'error')
    
    # Get users for dropdown
    users = User.query.order_by(User.username).all()
    
    return render_template('admin/moderation/issue_warning.html', users=users)


@moderation_bp.route('/api/moderate', methods=['POST'])
@admin_required
def api_moderate():
    """API endpoint for real-time content moderation."""
    data = request.get_json()
    text = data.get('text', '').strip()
    content_type = data.get('content_type', 'general')
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    result = moderate_text(text, content_type)
    
    return jsonify({
        'is_safe': result.is_safe,
        'confidence': result.confidence,
        'reason': result.reason,
        'categories': result.categories,
        'flagged_words': result.flagged_words
    })


@moderation_bp.route('/flagged-content')
@admin_required
def flagged_content():
    """View flagged content across all types."""
    page = request.args.get('page', 1, type=int)
    content_type = request.args.get('content_type', '')
    
    # Get flagged contests
    flagged_contests = Contest.query.filter(Contest.moderation_status.in_(['flagged', 'blocked']))
    
    # Get flagged leagues
    flagged_leagues = League.query.filter(League.moderation_status.in_(['flagged', 'blocked']))
    
    # Get flagged questions
    flagged_questions = Question.query.filter(Question.moderation_status.in_(['flagged', 'blocked']))
    
    # Combine and paginate results
    flagged_items = []
    
    if not content_type or content_type == 'contest':
        for contest in flagged_contests:
            flagged_items.append({
                'type': 'contest',
                'id': contest.contest_id,
                'title': contest.contest_name,
                'description': contest.description,
                'status': contest.moderation_status,
                'flagged_at': contest.flagged_at,
                'notes': contest.moderation_notes,
                'creator': contest.creator
            })
    
    if not content_type or content_type == 'league':
        for league in flagged_leagues:
            flagged_items.append({
                'type': 'league',
                'id': league.league_id,
                'title': league.league_name,
                'description': league.description,
                'status': league.moderation_status,
                'flagged_at': league.flagged_at,
                'notes': league.moderation_notes,
                'creator': league.creator
            })
    
    if not content_type or content_type == 'question':
        for question in flagged_questions:
            flagged_items.append({
                'type': 'question',
                'id': question.question_id,
                'title': f"Question {question.question_order}",
                'description': question.question_text,
                'status': question.moderation_status,
                'flagged_at': question.flagged_at,
                'notes': question.moderation_notes,
                'creator': question.contest.creator
            })
    
    # Sort by flagged_at date
    flagged_items.sort(key=lambda x: x['flagged_at'] or datetime.min, reverse=True)
    
    return render_template('admin/moderation/flagged_content.html',
                         flagged_items=flagged_items,
                         current_content_type=content_type)


@moderation_bp.route('/content/<content_type>/<int:content_id>/review', methods=['POST'])
@admin_required
def review_content(content_type, content_id):
    """Review and update moderation status of content."""
    action = request.form.get('action')
    notes = request.form.get('notes', '').strip()
    
    if action not in ['approve', 'flag', 'block']:
        flash('Invalid action.', 'error')
        return redirect(request.referrer or url_for('moderation.flagged_content'))
    
    # Get the content object
    content = None
    if content_type == 'contest':
        content = Contest.query.get_or_404(content_id)
    elif content_type == 'league':
        content = League.query.get_or_404(content_id)
    elif content_type == 'question':
        content = Question.query.get_or_404(content_id)
    else:
        flash('Invalid content type.', 'error')
        return redirect(request.referrer or url_for('moderation.flagged_content'))
    
    # Update moderation status
    if action == 'approve':
        content.moderation_status = 'approved'
    elif action == 'flag':
        content.moderation_status = 'flagged'
        if not content.flagged_at:
            content.flagged_at = datetime.utcnow()
    elif action == 'block':
        content.moderation_status = 'blocked'
        if not content.flagged_at:
            content.flagged_at = datetime.utcnow()
    
    content.moderation_notes = notes
    content.reviewed_at = datetime.utcnow()
    content.reviewed_by_user_id = session['user_id']
    
    db.session.commit()
    
    flash(f'Content has been {action}ed.', 'success')
    return redirect(request.referrer or url_for('moderation.flagged_content'))
