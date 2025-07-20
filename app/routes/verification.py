"""Routes for user verification management."""
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import User
from app.models.verification import UserVerification, VerificationRequest
from app.utils.decorators import admin_required
from app.utils.reputation import ReputationCalculator
from datetime import datetime

verification_bp = Blueprint('verification', __name__)


@verification_bp.route('/admin/verifications')
@login_required
@admin_required
def admin_verifications():
    """Admin page for managing user verifications."""
    # Get all verification requests
    pending_requests = VerificationRequest.query.filter_by(status='pending').order_by(
        VerificationRequest.requested_at.desc()
    ).all()
    
    # Get all active verifications
    active_verifications = UserVerification.query.filter_by(is_active=True).order_by(
        UserVerification.verified_at.desc()
    ).all()
    
    # Get verification statistics
    stats = {
        'pending_requests': VerificationRequest.query.filter_by(status='pending').count(),
        'approved_requests': VerificationRequest.query.filter_by(status='approved').count(),
        'rejected_requests': VerificationRequest.query.filter_by(status='rejected').count(),
        'active_verifications': UserVerification.query.filter_by(is_active=True).count(),
        'total_verified_users': db.session.query(UserVerification.user_id).filter_by(is_active=True).distinct().count()
    }
    
    return render_template('admin/verifications.html',
                         pending_requests=pending_requests,
                         active_verifications=active_verifications,
                         stats=stats,
                         verification_types=UserVerification.get_verification_types(),
                         verification_levels=UserVerification.get_verification_levels())


@verification_bp.route('/admin/verification/request/<int:request_id>')
@login_required
@admin_required
def view_verification_request(request_id):
    """View details of a verification request."""
    verification_request = VerificationRequest.query.get_or_404(request_id)
    
    # Get user's current reputation info
    user_reputation = ReputationCalculator.get_or_create_reputation_score(verification_request.user_id)
    verification_info = ReputationCalculator.get_user_verification_info(verification_request.user_id)
    
    return render_template('admin/verification_request_detail.html',
                         verification_request=verification_request,
                         user_reputation=user_reputation,
                         verification_info=verification_info,
                         verification_types=UserVerification.get_verification_types(),
                         verification_levels=UserVerification.get_verification_levels())


@verification_bp.route('/admin/verification/approve/<int:request_id>', methods=['POST'])
@login_required
@admin_required
def approve_verification_request(request_id):
    """Approve a verification request."""
    verification_request = VerificationRequest.query.get_or_404(request_id)
    
    if verification_request.status != 'pending':
        flash('This verification request has already been processed.', 'warning')
        return redirect(url_for('verification.admin_verifications'))
    
    # Get form data
    admin_notes = request.form.get('admin_notes', '')
    custom_reputation_boost = request.form.get('custom_reputation_boost', type=int)
    custom_trust_boost = request.form.get('custom_trust_boost', type=int)
    public_note = request.form.get('public_note', '')
    expires_days = request.form.get('expires_days', type=int)
    
    # Prepare custom boosts if provided
    custom_boosts = None
    if custom_reputation_boost is not None or custom_trust_boost is not None:
        custom_boosts = {}
        if custom_reputation_boost is not None:
            custom_boosts['reputation'] = custom_reputation_boost
        if custom_trust_boost is not None:
            custom_boosts['trust'] = custom_trust_boost
    
    try:
        # Approve the request
        verification = verification_request.approve(
            admin_id=current_user.user_id,
            admin_notes=admin_notes,
            custom_boosts=custom_boosts
        )
        
        # Set public note and expiration if provided
        if public_note:
            verification.public_note = public_note
        
        if expires_days and expires_days > 0:
            from datetime import timedelta
            verification.expires_at = datetime.utcnow() + timedelta(days=expires_days)
        
        db.session.commit()
        
        # Update user's reputation
        ReputationCalculator.update_user_reputation(verification_request.user_id)
        
        flash(f'Verification approved for {verification_request.user.username}. '
              f'Granted {verification.reputation_boost} reputation points and '
              f'{verification.trust_boost} trust points.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error approving verification: {str(e)}', 'danger')
    
    return redirect(url_for('verification.admin_verifications'))


@verification_bp.route('/admin/verification/reject/<int:request_id>', methods=['POST'])
@login_required
@admin_required
def reject_verification_request(request_id):
    """Reject a verification request."""
    verification_request = VerificationRequest.query.get_or_404(request_id)
    
    if verification_request.status != 'pending':
        flash('This verification request has already been processed.', 'warning')
        return redirect(url_for('verification.admin_verifications'))
    
    reason = request.form.get('rejection_reason', 'Verification request rejected.')
    
    try:
        verification_request.reject(current_user.user_id, reason)
        flash(f'Verification request rejected for {verification_request.user.username}.', 'info')
    except Exception as e:
        flash(f'Error rejecting verification: {str(e)}', 'danger')
    
    return redirect(url_for('verification.admin_verifications'))


@verification_bp.route('/admin/verification/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_verification():
    """Create a new verification for a user (admin-initiated)."""
    if request.method == 'POST':
        username = request.form.get('username')
        verification_type = request.form.get('verification_type')
        verification_level = request.form.get('verification_level')
        verification_reason = request.form.get('verification_reason')
        real_name = request.form.get('real_name')
        organization = request.form.get('organization')
        title_position = request.form.get('title_position')
        expertise_area = request.form.get('expertise_area')
        reputation_boost = request.form.get('reputation_boost', type=int)
        trust_boost = request.form.get('trust_boost', type=int)
        admin_notes = request.form.get('admin_notes')
        public_note = request.form.get('public_note')
        expires_days = request.form.get('expires_days', type=int)
        
        # Find user
        user = User.query.filter_by(username=username).first()
        if not user:
            flash(f'User "{username}" not found.', 'danger')
            return render_template('admin/create_verification.html',
                                 verification_types=UserVerification.get_verification_types(),
                                 verification_levels=UserVerification.get_verification_levels())
        
        # Check if user already has this type of verification
        existing = UserVerification.query.filter_by(
            user_id=user.user_id,
            verification_type=verification_type,
            is_active=True
        ).first()
        
        if existing and not existing.is_expired():
            flash(f'User already has an active {verification_type} verification.', 'warning')
            return render_template('admin/create_verification.html',
                                 verification_types=UserVerification.get_verification_types(),
                                 verification_levels=UserVerification.get_verification_levels())
        
        try:
            # Create verification
            verification = UserVerification(
                user_id=user.user_id,
                verified_by_admin_id=current_user.user_id,
                verification_type=verification_type,
                verification_level=verification_level,
                verification_reason=verification_reason,
                real_name=real_name,
                organization=organization,
                title_position=title_position,
                expertise_area=expertise_area,
                reputation_boost=reputation_boost or 0,
                trust_boost=trust_boost or 0,
                admin_notes=admin_notes,
                public_note=public_note
            )
            
            # Set expiration if provided
            if expires_days and expires_days > 0:
                from datetime import timedelta
                verification.expires_at = datetime.utcnow() + timedelta(days=expires_days)
            
            db.session.add(verification)
            db.session.commit()
            
            # Record reputation event
            ReputationCalculator.record_reputation_event(
                user_id=user.user_id,
                event_type='admin_verification',
                description=f"Admin verified as {verification_type} ({verification_level})",
                metadata={
                    'verification_type': verification_type,
                    'verification_level': verification_level,
                    'reputation_boost': reputation_boost or 0,
                    'trust_boost': trust_boost or 0,
                    'verified_by_admin': current_user.user_id
                }
            )
            
            # Update user's reputation
            ReputationCalculator.update_user_reputation(user.user_id)
            
            flash(f'Verification created for {user.username}. '
                  f'Granted {reputation_boost or 0} reputation points and '
                  f'{trust_boost or 0} trust points.', 'success')
            
            return redirect(url_for('verification.admin_verifications'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating verification: {str(e)}', 'danger')
    
    return render_template('admin/create_verification.html',
                         verification_types=UserVerification.get_verification_types(),
                         verification_levels=UserVerification.get_verification_levels())


@verification_bp.route('/admin/verification/revoke/<int:verification_id>', methods=['POST'])
@login_required
@admin_required
def revoke_verification(verification_id):
    """Revoke a user verification."""
    verification = UserVerification.query.get_or_404(verification_id)
    
    if not verification.is_active:
        flash('This verification is already inactive.', 'warning')
        return redirect(url_for('verification.admin_verifications'))
    
    reason = request.form.get('revocation_reason', 'Verification revoked by admin.')
    
    try:
        # Deactivate verification
        verification.is_active = False
        verification.admin_notes = f"{verification.admin_notes or ''}\n\nRevoked: {reason}".strip()
        verification.last_reviewed = datetime.utcnow()
        
        db.session.commit()
        
        # Record reputation event
        ReputationCalculator.record_reputation_event(
            user_id=verification.user_id,
            event_type='verification_revoked',
            description=f"Verification revoked: {verification.verification_type}",
            metadata={
                'verification_type': verification.verification_type,
                'verification_level': verification.verification_level,
                'revocation_reason': reason,
                'revoked_by_admin': current_user.user_id
            }
        )
        
        # Update user's reputation
        ReputationCalculator.update_user_reputation(verification.user_id)
        
        flash(f'Verification revoked for {verification.user.username}.', 'info')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error revoking verification: {str(e)}', 'danger')
    
    return redirect(url_for('verification.admin_verifications'))


@verification_bp.route('/verification/request', methods=['GET', 'POST'])
@login_required
def request_verification():
    """User page to request verification."""
    # Check if user already has pending requests
    pending_request = VerificationRequest.query.filter_by(
        user_id=current_user.user_id,
        status='pending'
    ).first()
    
    if pending_request:
        flash('You already have a pending verification request.', 'info')
        return redirect(url_for('verification.my_verifications'))
    
    if request.method == 'POST':
        requested_type = request.form.get('requested_type')
        requested_level = request.form.get('requested_level')
        justification = request.form.get('justification')
        real_name = request.form.get('real_name')
        organization = request.form.get('organization')
        title_position = request.form.get('title_position')
        expertise_area = request.form.get('expertise_area')
        supporting_links = request.form.getlist('supporting_links')
        
        # Filter out empty links
        supporting_links = [link.strip() for link in supporting_links if link.strip()]
        
        try:
            verification_request = VerificationRequest(
                user_id=current_user.user_id,
                requested_type=requested_type,
                requested_level=requested_level,
                justification=justification,
                real_name=real_name,
                organization=organization,
                title_position=title_position,
                expertise_area=expertise_area,
                supporting_links=supporting_links if supporting_links else None
            )
            
            db.session.add(verification_request)
            db.session.commit()
            
            flash('Verification request submitted successfully. An admin will review it soon.', 'success')
            return redirect(url_for('verification.my_verifications'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error submitting verification request: {str(e)}', 'danger')
    
    return render_template('verification/request_form.html',
                         verification_types=UserVerification.get_verification_types(),
                         verification_levels=UserVerification.get_verification_levels())


@verification_bp.route('/verification/my-verifications')
@login_required
def my_verifications():
    """User page to view their verifications and requests."""
    # Get user's verification requests
    verification_requests = VerificationRequest.query.filter_by(
        user_id=current_user.user_id
    ).order_by(VerificationRequest.requested_at.desc()).all()
    
    # Get user's active verifications
    active_verifications = UserVerification.query.filter_by(
        user_id=current_user.user_id,
        is_active=True
    ).all()
    
    # Filter out expired verifications
    active_verifications = [v for v in active_verifications if not v.is_expired()]
    
    # Get verification info
    verification_info = ReputationCalculator.get_user_verification_info(current_user.user_id)
    
    return render_template('verification/my_verifications.html',
                         verification_requests=verification_requests,
                         active_verifications=active_verifications,
                         verification_info=verification_info)


@verification_bp.route('/api/verification/user-search')
@login_required
@admin_required
def api_user_search():
    """API endpoint for searching users (for admin verification creation)."""
    query = request.args.get('q', '').strip()
    
    if len(query) < 2:
        return jsonify([])
    
    users = User.query.filter(
        User.username.ilike(f'%{query}%')
    ).limit(10).all()
    
    results = []
    for user in users:
        # Get user's current verifications
        verifications = UserVerification.query.filter_by(
            user_id=user.user_id,
            is_active=True
        ).all()
        
        active_verifications = [v for v in verifications if not v.is_expired()]
        
        results.append({
            'user_id': user.user_id,
            'username': user.username,
            'email': user.email,
            'created_at': user.created_at.strftime('%Y-%m-%d'),
            'is_suspended': user.is_suspended,
            'verification_count': len(active_verifications),
            'verification_types': [v.verification_type for v in active_verifications]
        })
    
    return jsonify(results)
