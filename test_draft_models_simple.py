#!/usr/bin/env python3
"""
Simple test script to verify draft contest models are working correctly.
"""

import os
import sys
from datetime import datetime, timedelta

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import DraftPool, DraftItem, DraftContest, DraftScoringRule, DraftItemScore

def test_draft_models():
    """Test the draft contest models."""
    app = create_app()
    
    with app.app_context():
        print("Testing Draft Contest Models...")
        
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
        
        # Test pool methods
        print("\nTesting pool methods:")
        print(f"Pool items count: {pool.get_items_count()}")
        print(f"Pool available count: {pool.get_available_count()}")
        print(f"Available items: {[item.item_name for item in pool.get_available_items()]}")
        
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
        
        # Test item scoring
        print("\nTesting item scoring:")
        for item in items:
            total_score = item.get_total_score()
            print(f"{item.item_name} total score: {total_score}")
            print(f"  Metadata: {item.item_metadata}")
            print(f"  Is drafted: {item.is_drafted()}")
        
        print("\n✅ Basic draft models are working correctly!")
        
        # Clean up
        for score in scores:
            db.session.delete(score)
        for item in items:
            db.session.delete(item)
        db.session.delete(pool)
        db.session.commit()
        print("✓ Cleaned up test data")

if __name__ == '__main__':
    test_draft_models()
