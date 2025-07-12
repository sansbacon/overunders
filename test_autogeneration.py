#!/usr/bin/env python3
"""
Test script to verify auto-generation functionality
"""
import os
import sys
from datetime import datetime

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from app import create_app
from app.utils.ai_generation import generate_nfl_contest, generate_contest_name_and_description

def test_autogeneration():
    app = create_app()
    
    with app.app_context():
        print("Testing NFL contest auto-generation...")
        
        try:
            # Test contest name and description generation
            contest_info = generate_contest_name_and_description(
                sport='NFL',
                week_number=None,
                season_year=None
            )
            
            print(f"✅ Contest Name: {contest_info['name']}")
            print(f"✅ Contest Description: {contest_info['description']}")
            
            # Test question generation
            questions_data = generate_nfl_contest(
                week_number=None,
                season_year=None,
                question_count=3
            )
            
            print(f"✅ Generated {len(questions_data)} questions:")
            for i, question in enumerate(questions_data, 1):
                print(f"   {i}. {question['question']}")
            
            print("\n🎉 Auto-generation test completed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Auto-generation test failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    test_autogeneration()
