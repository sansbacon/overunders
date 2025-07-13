"""Verification requirement checking utilities."""
from flask import current_app
from app.models import UserVerification
from app.utils.reputation import ReputationCalculator


class VerificationChecker:
    """Utility class for checking verification requirements."""
    
    @staticmethod
    def can_create_contest(user_id: int) -> tuple[bool, str]:
        """Check if user can create contests based on verification requirements.
        
        Args:
            user_id (int): User ID to check
            
        Returns:
            tuple[bool, str]: (can_create, reason_if_not)
        """
        # Check if verification is required for contests
        if not current_app.config.get('REQUIRE_VERIFICATION_FOR_CONTESTS', False):
            return True, ""
        
        # Get user's verification info
        verification_info = ReputationCalculator.get_user_verification_info(user_id)
        
        if not verification_info['is_verified']:
            return False, "Contest creation requires user verification. Please request verification from an administrator."
        
        # Check minimum verification level
        min_level = current_app.config.get('MINIMUM_VERIFICATION_LEVEL_CONTESTS', 'basic')
        user_level = verification_info['highest_level']
        
        if not VerificationChecker._meets_minimum_level(user_level, min_level):
            return False, f"Contest creation requires {min_level} level verification or higher. Your current level is {user_level}."
        
        return True, ""
    
    @staticmethod
    def can_create_league(user_id: int) -> tuple[bool, str]:
        """Check if user can create leagues based on verification requirements.
        
        Args:
            user_id (int): User ID to check
            
        Returns:
            tuple[bool, str]: (can_create, reason_if_not)
        """
        # Check if verification is required for leagues
        if not current_app.config.get('REQUIRE_VERIFICATION_FOR_LEAGUES', False):
            return True, ""
        
        # Get user's verification info
        verification_info = ReputationCalculator.get_user_verification_info(user_id)
        
        if not verification_info['is_verified']:
            return False, "League creation requires user verification. Please request verification from an administrator."
        
        # Check minimum verification level
        min_level = current_app.config.get('MINIMUM_VERIFICATION_LEVEL_LEAGUES', 'basic')
        user_level = verification_info['highest_level']
        
        if not VerificationChecker._meets_minimum_level(user_level, min_level):
            return False, f"League creation requires {min_level} level verification or higher. Your current level is {user_level}."
        
        return True, ""
    
    @staticmethod
    def can_participate_in_contest(user_id: int, contest_id: int = None) -> tuple[bool, str]:
        """Check if user can participate in contests.
        
        Args:
            user_id (int): User ID to check
            contest_id (int, optional): Specific contest ID
            
        Returns:
            tuple[bool, str]: (can_participate, reason_if_not)
        """
        # Participation is always allowed unless explicitly disabled
        if not current_app.config.get('ALLOW_UNVERIFIED_PARTICIPATION', True):
            verification_info = ReputationCalculator.get_user_verification_info(user_id)
            if not verification_info['is_verified']:
                return False, "Contest participation requires user verification."
        
        # Check for duplicate entry if contest_id provided
        if contest_id:
            from app.models import ContestEntry
            existing_entry = ContestEntry.query.filter_by(
                user_id=user_id,
                contest_id=contest_id
            ).first()
            
            if existing_entry:
                return False, "You have already entered this contest."
        
        return True, ""
    
    @staticmethod
    def can_join_league(user_id: int, league_id: int = None) -> tuple[bool, str]:
        """Check if user can join leagues.
        
        Args:
            user_id (int): User ID to check
            league_id (int, optional): Specific league ID
            
        Returns:
            tuple[bool, str]: (can_join, reason_if_not)
        """
        # Participation is always allowed unless explicitly disabled
        if not current_app.config.get('ALLOW_UNVERIFIED_PARTICIPATION', True):
            verification_info = ReputationCalculator.get_user_verification_info(user_id)
            if not verification_info['is_verified']:
                return False, "League participation requires user verification."
        
        # Check for duplicate membership if league_id provided
        if league_id:
            from app.models import LeagueMembership
            existing_membership = LeagueMembership.query.filter_by(
                user_id=user_id,
                league_id=league_id
            ).first()
            
            if existing_membership:
                return False, "You are already a member of this league."
        
        return True, ""
    
    @staticmethod
    def _meets_minimum_level(user_level: str, required_level: str) -> bool:
        """Check if user's verification level meets the minimum requirement.
        
        Args:
            user_level (str): User's current verification level
            required_level (str): Required minimum level
            
        Returns:
            bool: True if user meets requirement
        """
        if not user_level:
            return False
        
        level_hierarchy = {
            'basic': 1,
            'enhanced': 2,
            'premium': 3
        }
        
        user_rank = level_hierarchy.get(user_level, 0)
        required_rank = level_hierarchy.get(required_level, 1)
        
        return user_rank >= required_rank
    
    @staticmethod
    def get_verification_requirements_info() -> dict:
        """Get current verification requirements configuration.
        
        Returns:
            dict: Current verification requirements
        """
        return {
            'contest_creation_requires_verification': current_app.config.get('REQUIRE_VERIFICATION_FOR_CONTESTS', False),
            'league_creation_requires_verification': current_app.config.get('REQUIRE_VERIFICATION_FOR_LEAGUES', False),
            'unverified_participation_allowed': current_app.config.get('ALLOW_UNVERIFIED_PARTICIPATION', True),
            'minimum_level_contests': current_app.config.get('MINIMUM_VERIFICATION_LEVEL_CONTESTS', 'basic'),
            'minimum_level_leagues': current_app.config.get('MINIMUM_VERIFICATION_LEVEL_LEAGUES', 'basic')
        }
    
    @staticmethod
    def get_user_verification_status(user_id: int) -> dict:
        """Get comprehensive verification status for a user.
        
        Args:
            user_id (int): User ID
            
        Returns:
            dict: User's verification status and permissions
        """
        verification_info = ReputationCalculator.get_user_verification_info(user_id)
        requirements = VerificationChecker.get_verification_requirements_info()
        
        can_create_contest, contest_reason = VerificationChecker.can_create_contest(user_id)
        can_create_league, league_reason = VerificationChecker.can_create_league(user_id)
        can_participate, participate_reason = VerificationChecker.can_participate_in_contest(user_id)
        can_join_league, join_reason = VerificationChecker.can_join_league(user_id)
        
        return {
            'verification_info': verification_info,
            'requirements': requirements,
            'permissions': {
                'can_create_contest': can_create_contest,
                'contest_creation_reason': contest_reason,
                'can_create_league': can_create_league,
                'league_creation_reason': league_reason,
                'can_participate_in_contests': can_participate,
                'participation_reason': participate_reason,
                'can_join_leagues': can_join_league,
                'join_league_reason': join_reason
            }
        }


class VerificationDecorator:
    """Decorator class for verification checks."""
    
    @staticmethod
    def require_verification_for_contest_creation(f):
        """Decorator to require verification for contest creation."""
        from functools import wraps
        from flask import flash, redirect, url_for
        from flask_login import current_user
        
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            
            can_create, reason = VerificationChecker.can_create_contest(current_user.user_id)
            if not can_create:
                flash(reason, 'warning')
                return redirect(url_for('verification.request_verification'))
            
            return f(*args, **kwargs)
        return decorated_function
    
    @staticmethod
    def require_verification_for_league_creation(f):
        """Decorator to require verification for league creation."""
        from functools import wraps
        from flask import flash, redirect, url_for
        from flask_login import current_user
        
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            
            can_create, reason = VerificationChecker.can_create_league(current_user.user_id)
            if not can_create:
                flash(reason, 'warning')
                return redirect(url_for('verification.request_verification'))
            
            return f(*args, **kwargs)
        return decorated_function
    
    @staticmethod
    def check_contest_participation(f):
        """Decorator to check contest participation eligibility."""
        from functools import wraps
        from flask import flash, redirect, url_for, request
        from flask_login import current_user
        
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            
            # Get contest_id from kwargs or request
            contest_id = kwargs.get('contest_id') or request.view_args.get('contest_id')
            
            can_participate, reason = VerificationChecker.can_participate_in_contest(
                current_user.user_id, contest_id
            )
            if not can_participate:
                flash(reason, 'warning')
                if 'verification' in reason.lower():
                    return redirect(url_for('verification.request_verification'))
                else:
                    return redirect(url_for('contests.list'))
            
            return f(*args, **kwargs)
        return decorated_function
    
    @staticmethod
    def check_league_participation(f):
        """Decorator to check league participation eligibility."""
        from functools import wraps
        from flask import flash, redirect, url_for, request
        from flask_login import current_user
        
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            
            # Get league_id from kwargs or request
            league_id = kwargs.get('league_id') or request.view_args.get('league_id')
            
            can_join, reason = VerificationChecker.can_join_league(
                current_user.user_id, league_id
            )
            if not can_join:
                flash(reason, 'warning')
                if 'verification' in reason.lower():
                    return redirect(url_for('verification.request_verification'))
                else:
                    return redirect(url_for('leagues.list'))
            
            return f(*args, **kwargs)
        return decorated_function
