#!/usr/bin/env python3
"""
Script to populate NFL schedule data for testing.
This script adds sample NFL games for the 2025 season.
"""

import sys
import os
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import the app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import NFLSchedule

def populate_sample_schedule():
    """Populate the database with sample NFL schedule data."""
    
    app = create_app()
    
    with app.app_context():
        # Clear existing schedule data for 2025
        NFLSchedule.query.filter_by(season_year=2025).delete()
        
        # Sample games for Week 1, 2025 season
        week_1_games = [
            # Thursday Night Football
            {'home': 'Chiefs', 'away': 'Ravens', 'date': datetime(2025, 9, 4, 20, 15), 'time': '8:15 PM ET'},
            
            # Sunday games
            {'home': 'Bills', 'away': 'Dolphins', 'date': datetime(2025, 9, 7, 13, 0), 'time': '1:00 PM ET'},
            {'home': 'Patriots', 'away': 'Jets', 'date': datetime(2025, 9, 7, 13, 0), 'time': '1:00 PM ET'},
            {'home': 'Bengals', 'away': 'Browns', 'date': datetime(2025, 9, 7, 13, 0), 'time': '1:00 PM ET'},
            {'home': 'Steelers', 'away': 'Titans', 'date': datetime(2025, 9, 7, 13, 0), 'time': '1:00 PM ET'},
            {'home': 'Colts', 'away': 'Jaguars', 'date': datetime(2025, 9, 7, 13, 0), 'time': '1:00 PM ET'},
            {'home': 'Texans', 'away': 'Panthers', 'date': datetime(2025, 9, 7, 13, 0), 'time': '1:00 PM ET'},
            {'home': 'Chargers', 'away': 'Raiders', 'date': datetime(2025, 9, 7, 16, 25), 'time': '4:25 PM ET'},
            {'home': 'Broncos', 'away': 'Seahawks', 'date': datetime(2025, 9, 7, 16, 25), 'time': '4:25 PM ET'},
            {'home': 'Cowboys', 'away': 'Giants', 'date': datetime(2025, 9, 7, 16, 25), 'time': '4:25 PM ET'},
            {'home': 'Eagles', 'away': 'Commanders', 'date': datetime(2025, 9, 7, 16, 25), 'time': '4:25 PM ET'},
            {'home': 'Packers', 'away': 'Bears', 'date': datetime(2025, 9, 7, 20, 20), 'time': '8:20 PM ET'},
            {'home': 'Lions', 'away': 'Vikings', 'date': datetime(2025, 9, 7, 20, 20), 'time': '8:20 PM ET'},
            {'home': '49ers', 'away': 'Cardinals', 'date': datetime(2025, 9, 7, 20, 20), 'time': '8:20 PM ET'},
            {'home': 'Rams', 'away': 'Saints', 'date': datetime(2025, 9, 7, 20, 20), 'time': '8:20 PM ET'},
            
            # Monday Night Football
            {'home': 'Falcons', 'away': 'Buccaneers', 'date': datetime(2025, 9, 8, 20, 15), 'time': '8:15 PM ET'},
        ]
        
        # Add Week 1 games
        for game in week_1_games:
            schedule = NFLSchedule(
                season_year=2025,
                week_number=1,
                home_team=game['home'],
                away_team=game['away'],
                game_date=game['date'],
                game_time=game['time'],
                is_playoff=False
            )
            db.session.add(schedule)
        
        # Sample games for Week 2, 2025 season
        week_2_games = [
            # Thursday Night Football
            {'home': 'Dolphins', 'away': 'Bills', 'date': datetime(2025, 9, 11, 20, 15), 'time': '8:15 PM ET'},
            
            # Sunday games
            {'home': 'Jets', 'away': 'Patriots', 'date': datetime(2025, 9, 14, 13, 0), 'time': '1:00 PM ET'},
            {'home': 'Ravens', 'away': 'Bengals', 'date': datetime(2025, 9, 14, 13, 0), 'time': '1:00 PM ET'},
            {'home': 'Browns', 'away': 'Steelers', 'date': datetime(2025, 9, 14, 13, 0), 'time': '1:00 PM ET'},
            {'home': 'Titans', 'away': 'Colts', 'date': datetime(2025, 9, 14, 13, 0), 'time': '1:00 PM ET'},
            {'home': 'Jaguars', 'away': 'Texans', 'date': datetime(2025, 9, 14, 13, 0), 'time': '1:00 PM ET'},
            {'home': 'Chiefs', 'away': 'Chargers', 'date': datetime(2025, 9, 14, 16, 25), 'time': '4:25 PM ET'},
            {'home': 'Raiders', 'away': 'Broncos', 'date': datetime(2025, 9, 14, 16, 25), 'time': '4:25 PM ET'},
            {'home': 'Giants', 'away': 'Cowboys', 'date': datetime(2025, 9, 14, 16, 25), 'time': '4:25 PM ET'},
            {'home': 'Commanders', 'away': 'Eagles', 'date': datetime(2025, 9, 14, 16, 25), 'time': '4:25 PM ET'},
            {'home': 'Bears', 'away': 'Packers', 'date': datetime(2025, 9, 14, 20, 20), 'time': '8:20 PM ET'},
            {'home': 'Vikings', 'away': 'Lions', 'date': datetime(2025, 9, 14, 20, 20), 'time': '8:20 PM ET'},
            {'home': 'Cardinals', 'away': '49ers', 'date': datetime(2025, 9, 14, 20, 20), 'time': '8:20 PM ET'},
            {'home': 'Saints', 'away': 'Rams', 'date': datetime(2025, 9, 14, 20, 20), 'time': '8:20 PM ET'},
            {'home': 'Seahawks', 'away': 'Panthers', 'date': datetime(2025, 9, 14, 20, 20), 'time': '8:20 PM ET'},
            
            # Monday Night Football
            {'home': 'Buccaneers', 'away': 'Falcons', 'date': datetime(2025, 9, 15, 20, 15), 'time': '8:15 PM ET'},
        ]
        
        # Add Week 2 games
        for game in week_2_games:
            schedule = NFLSchedule(
                season_year=2025,
                week_number=2,
                home_team=game['home'],
                away_team=game['away'],
                game_date=game['date'],
                game_time=game['time'],
                is_playoff=False
            )
            db.session.add(schedule)
        
        # Commit all changes
        db.session.commit()
        
        print("✅ Successfully populated NFL schedule data!")
        print(f"   - Added {len(week_1_games)} games for Week 1, 2025")
        print(f"   - Added {len(week_2_games)} games for Week 2, 2025")
        print(f"   - Total: {len(week_1_games) + len(week_2_games)} games")

if __name__ == '__main__':
    populate_sample_schedule()
