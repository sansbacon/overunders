#!/usr/bin/env python3
"""
Test script to verify draft contest models are working correctly.
"""

import os
import sys
from datetime import datetime, timedelta

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import (
    User, DraftPool, DraftItem, DraftContest, DraftEntry, 
    DraftPick, DraftScoringRule, DraftItemScore, League, LeagueDraftContest
)

def test_draft_models():
    """Test the draft contest models."""
    app = create_app()
    
    with app.app_context():
        print("Testing Draft Contest Models...")
        
        # Create a test user
        user = User(
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User'
        )
        db.session.add(user)
        db.session.commit()
        print(f"✓ Created user: {user}")
        
        # Create a draft pool
        pool = DraftPool(
            pool_name='NFL Players 2024',
            description='Top NFL players for fantasy draft',
            sport='NFL',
            season='2024'
        )
        db.session.add(pool)
        db.session.commit()
        print(f"✓ Created draft pool: {pool}")
        
        # Create some draft items
        items = [
            DraftItem(
                draft_pool_id=pool.draft_pool_id,
                item_name='Josh Allen',
                thumbnail_url='https://example.com/josh_allen.jpg',
                item_metadata={'position': 'QB', 'team': 'BUF', 'age': 28},
                item_order=1
            ),
            DraftItem(
                draft_pool_id=pool.draft_pool_id,
                item_name='Christian McCaffrey',
                thumbnail_url='https://example.com/mccaffrey.jpg',
                item_metadata={'position': 'RB', 'team': 'SF', 'age': 28},
                item_order=2
            ),
            DraftItem(
                draft_pool_id=pool.draft_pool_id,
                item_name='Cooper Kupp',
                thumbnail_url='https://example.com/kupp.jpg',
                item_metadata={'position': 'WR', 'team': 'LAR', 'age': 31},
                item_order=3
            )
        ]
        
        for item in items:
            db.session.add(item)
        db.session.commit()
        print(f"✓ Created {len(items)} draft items")
        
        # Create a draft contest
        contest = DraftContest(
            contest_name='Test Fantasy Draft',
            description='A test fantasy football draft',
            created_by_user=user.user_id,
            draft_pool_id=pool.draft_pool_id,
            lock_timestamp=datetime.utcnow() + timedelta(hours=1),
            picks_per_user=3,
            draft_order_type='random',
            is_snake_draft=True
        )
        db.session.add(contest)
        db.session.commit()
        print(f"✓ Created draft contest: {contest}")
        
        # Create a draft entry
        entry = DraftEntry(
            draft_contest_id=contest.draft_contest_id,
            user_id=user.user_id,
            draft_position=1
        )
        db.session.add(entry)
        db.session.commit()
        print(f"✓ Created draft entry: {entry}")
        
        # Create scoring rules
        scoring_rules = [
            DraftScoringRule(
                draft_contest_id=contest.draft_contest_id,
                rule_name='Passing Yards',
                rule_description='1 point per 25 passing yards',
                points_per_unit=0.04,
                category='passing_yards'
            ),
            DraftScoringRule(
                draft_contest_id=contest.draft_contest_id,
                rule_name='Rushing Yards',
                rule_description='1 point per 10 rushing yards',
                points_per_unit=0.1,
                category='rushing_yards'
            ),
            DraftScoringRule(
                draft_contest_id=contest.draft_contest_id,
                rule_name='Receiving Yards',
                rule_description='1 point per 10 receiving yards',
                points_per_unit=0.1,
                category='receiving_yards'
            )
        ]
        
        for rule in scoring_rules:
            db.session.add(rule)
        db.session.commit()
        print(f"✓ Created {len(scoring_rules)} scoring rules")
        
        # Create some scores for the items
        scores = [
            DraftItemScore(
                draft_item_id=items[0].draft_item_id,  # Josh Allen
                score_value=4500,
                score_category='passing_yards',
                scoring_period='season'
            ),
            DraftItemScore(
                draft_item_id=items[1].draft_item_id,  # McCaffrey
                score_value=1200,
                score_category='rushing_yards',
                scoring_period='season'
            ),
            DraftItemScore(
                draft_item_id=items[2].draft_item_id,  # Kupp
                score_value=1400,
                score_category='receiving_yards',
                scoring_period='season'
            )
        ]
        
        for score in scores:
            db.session.add(score)
        db.session.commit()
        print(f"✓ Created {len(scores)} item scores")
        
        # Test some model methods
        print("\nTesting model methods:")
        print(f"Pool items count: {pool.get_items_count()}")
        print(f"Pool available count: {pool.get_available_count()}")
        print(f"Contest entry count: {contest.get_entry_count()}")
        print(f"Contest can start draft: {contest.can_start_draft()}")
        
        # Test item scoring
        for item in items:
            total_score = item.get_total_score(contest.draft_contest_id)
            print(f"{item.item_name} total score: {total_score}")
        
        # Create a league and add the draft contest to it
        league = League(
            league_name='Test Fantasy League',
            description='A test league for fantasy football',
            created_by_user=user.user_id,
            is_public=False
        )
        db.session.add(league)
        db.session.commit()
        print(f"✓ Created league: {league}")
        
        # Add draft contest to league
        league_draft_contest = league.add_draft_contest(contest)
        db.session.commit()
        print(f"✓ Added draft contest to league: {league_draft_contest}")
        
        # Test league methods
        print(f"League draft contest count: {league.get_draft_contest_count()}")
        print(f"League total contest count: {league.get_total_contest_count()}")
        
        print("\n✅ All draft contest models are working correctly!")
        
        # Clean up
        db.session.delete(league_draft_contest)
        db.session.delete(league)
        for score in scores:
            db.session.delete(score)
        for rule in scoring_rules:
            db.session.delete(rule)
        db.session.delete(entry)
        db.session.delete(contest)
        for item in items:
            db.session.delete(item)
        db.session.delete(pool)
        db.session.delete(user)
        db.session.commit()
        print("✓ Cleaned up test data")

if __name__ == '__main__':
    test_draft_models()
