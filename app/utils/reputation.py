"""Reputation and trust system utilities."""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from app import db
from app.models import User, Contest, League, ContestEntry, LeagueMembership
from app.models import UserReputation, UserVerification


class ReputationCalculator:
    """Calculator for user reputation scores."""
    
    @classmethod
    def get_user_verification_info(cls, user_id: int) -> dict:
        """Get verification information for a user.
        
        Args:
            user_id (int): User ID
            
        Returns:
            dict: Verification information
        """
        # Get active verifications for user
        verifications = UserVerification.query.filter_by(
            user_id=user_id,
            status='approved'
        ).all()
        
        active_verifications = [v for v in verifications if v.is_active()]
        
        if not active_verifications:
            return {
                'is_verified': False,
                'verification_count': 0,
                'highest_level': None,
                'badges': [],
                'total_reputation_boost': 0,
                'reputation_multiplier': 1.0,
                'daily_limit_multiplier': 1.0
            }
        
        # Get highest level verification
        level_priority = {'premium': 3, 'enhanced': 2, 'basic': 1}
        highest_verification = max(
            active_verifications,
            key=lambda v: level_priority.get(v.verification_level, 0)
        )
        
        return {
            'is_verified': True,
            'verification_count': len(active_verifications),
            'highest_level': highest_verification.verification_level,
            'highest_type': highest_verification.verification_type,
            'badges': [],
            'total_reputation_boost': 0,
            'reputation_multiplier': 1.0,
            'daily_limit_multiplier': 1.0,
            'verifications': active_verifications
        }
    
    @classmethod
    def update_user_reputation(cls, user_id: int) -> UserReputation:
        """Update reputation for a user.
        
        Args:
            user_id (int): User ID
            
        Returns:
            UserReputation: Updated reputation
        """
        reputation = UserReputation.get_or_create(user_id)
        reputation.refresh_metrics()
        return reputation
