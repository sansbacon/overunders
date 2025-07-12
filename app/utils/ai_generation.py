"""AI-powered contest generation utilities."""
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import openai
from flask import current_app


logger = logging.getLogger(__name__)


class ContestGenerationError(Exception):
    """Exception raised when contest generation fails."""
    pass


def get_schedule_data(season_year: int, week_number: int) -> Optional[str]:
    """Get NFL schedule data for the specified week.
    
    Args:
        season_year (int): NFL season year
        week_number (int): Week number (1-18)
        
    Returns:
        Optional[str]: Formatted schedule data or None if not available
    """
    try:
        from app.models import NFLSchedule
        
        games = NFLSchedule.get_games_for_week(season_year, week_number)
        
        if not games:
            logger.info(f"No schedule data found for {season_year} Week {week_number}")
            return None
        
        # Format the schedule data for the AI prompt
        schedule_lines = []
        schedule_lines.append(f"ACTUAL NFL SCHEDULE FOR WEEK {week_number}, {season_year} SEASON:")
        
        for game in games:
            matchup = game.get_matchup()
            game_info = f"- {matchup}"
            if game.game_date:
                game_info += f" (Date: {game.game_date.strftime('%A, %B %d')})"
            if game.game_time:
                game_info += f" (Time: {game.game_time})"
            schedule_lines.append(game_info)
        
        schedule_lines.append("")
        schedule_lines.append("IMPORTANT: Use ONLY these actual matchups for your questions. Do not create fictional games.")
        
        logger.info(f"Found {len(games)} games for {season_year} Week {week_number}")
        return "\n".join(schedule_lines)
        
    except Exception as e:
        logger.warning(f"Failed to get schedule data: {e}")
        return None


def generate_nfl_contest(week_number: Optional[int] = None, season_year: Optional[int] = None, 
                        question_count: int = 5) -> List[Dict]:
    """Generate NFL contest questions using OpenAI.
    
    Args:
        week_number (int, optional): NFL week number (1-18)
        season_year (int, optional): NFL season year
        question_count (int): Number of questions to generate (1-10, default 5)
        
    Returns:
        List[Dict]: List of generated questions with metadata
        
    Raises:
        ContestGenerationError: If generation fails
    """
    if not current_app.config.get('OPENAI_API_KEY'):
        raise ContestGenerationError("OpenAI API key not configured")
    
    # Set up OpenAI API key directly (avoiding client initialization issues)
    openai.api_key = current_app.config['OPENAI_API_KEY']
    logger.info("OpenAI API key configured")
    
    # Determine current NFL season context
    current_date = datetime.now()
    if not season_year:
        # NFL season typically runs from September to February
        if current_date.month >= 9:
            season_year = current_date.year
        else:
            season_year = current_date.year - 1
    
    if not week_number:
        # Try to estimate current week (this is a rough approximation)
        if current_date.month == 9:
            week_number = min(4, max(1, current_date.day // 7))
        elif current_date.month == 10:
            week_number = min(8, 4 + (current_date.day // 7))
        elif current_date.month == 11:
            week_number = min(12, 8 + (current_date.day // 7))
        elif current_date.month == 12:
            week_number = min(16, 12 + (current_date.day // 7))
        elif current_date.month == 1:
            week_number = min(18, 16 + (current_date.day // 7))
        else:
            week_number = 1  # Default to week 1
    
    # Try to get actual schedule data from database
    schedule_data = get_schedule_data(season_year, week_number)
    
    # Build the prompt with schedule data if available
    if schedule_data:
        # Use actual schedule data
        prompt = f"""You are a sports data assistant creating realistic NFL betting questions for Week {week_number} of the {season_year} season.

{schedule_data}

BETTING LINE GUIDELINES:
- Point spreads typically range from 1-14 points, with most being 3-7 points
- Over/under totals typically range from 38-55 points, with most being 42-48 points
- Consider team strengths: strong teams (Chiefs, Bills, 49ers) vs weaker teams should have larger spreads
- Realistic spread examples: Chiefs -6.5 vs Broncos, Bills -3 vs Dolphins, Cowboys -4.5 vs Giants
- Realistic over/under examples: Chiefs vs Chargers O/U 47.5, Bills vs Patriots O/U 43.5
"""
    else:
        # Fallback to generic instructions when no schedule data is available
        prompt = f"""You are a sports data assistant creating realistic NFL betting questions for Week {week_number} of the {season_year} season.

IMPORTANT INSTRUCTIONS:
1. Use REAL NFL teams and realistic divisional/conference matchups that could occur in Week {week_number}
2. Consider the NFL schedule structure: teams play within their division twice, and against other divisions on rotation
3. Use realistic betting lines based on team strength and typical NFL scoring patterns
4. Point spreads typically range from 1-14 points, with most being 3-7 points
5. Over/under totals typically range from 38-55 points, with most being 42-48 points
6. Consider team strengths: strong teams (Chiefs, Bills, 49ers) vs weaker teams should have larger spreads

REALISTIC TEAM MATCHUPS FOR WEEK {week_number}:
- Use actual NFL teams from these divisions:
  AFC East: Bills, Dolphins, Patriots, Jets
  AFC North: Ravens, Bengals, Browns, Steelers
  AFC South: Titans, Colts, Texans, Jaguars
  AFC West: Chiefs, Chargers, Raiders, Broncos
  NFC East: Cowboys, Eagles, Giants, Commanders
  NFC North: Packers, Lions, Bears, Vikings
  NFC South: Saints, Falcons, Panthers, Buccaneers
  NFC West: 49ers, Seahawks, Cardinals, Rams

- Common Week {week_number} matchup types:
  * Divisional games (teams in same division)
  * Inter-conference games (AFC vs NFC)
  * Conference games (AFC vs AFC, NFC vs NFC)
- Avoid impossible matchups (teams don't play themselves)
- Consider realistic scheduling: strong teams often play each other, divisional rivals meet twice per season

REALISTIC BETTING LINES:
- Spread examples: Chiefs -6.5 vs Broncos, Bills -3 vs Dolphins, Cowboys -4.5 vs Giants
- Over/under examples: Chiefs vs Chargers O/U 47.5, Bills vs Patriots O/U 43.5
"""
    
    # Add common instructions for both cases
    prompt += f"""

Generate exactly {question_count} yes/no questions with the following JSON format:

[
  {{
    "game": "Team A vs Team B",
    "question": "Will [specific betting question]?",
    "line_type": "spread" or "over_under",
    "line_value": numeric_value,
    "team_favored": "Team Name" (only for spreads),
    "direction": "over", "under", or "cover"
  }}
]

EXAMPLE REALISTIC OUTPUT:
[
  {{
    "game": "Chiefs vs Raiders",
    "question": "Will the total points in the Chiefs vs Raiders game exceed 45.5?",
    "line_type": "over_under",
    "line_value": 45.5,
    "direction": "over"
  }},
  {{
    "game": "Bills vs Dolphins",
    "question": "Will the Bills win by more than 3.5 points against the Dolphins?",
    "line_type": "spread",
    "line_value": 3.5,
    "team_favored": "Bills",
    "direction": "cover"
  }}
]

Requirements:
- Mix of spread and over/under questions (roughly 50/50 split)
- Use realistic NFL team names and matchups
- Betting lines should reflect realistic team strengths
- Questions must be clear and unambiguous
- Return ONLY the JSON array, no additional text"""

    try:
        logger.info(f"Generating NFL contest for Week {week_number}, {season_year} season")
        
        # Use the legacy OpenAI API (version 0.28.1)
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that generates sports betting questions in JSON format."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        content = response.choices[0].message.content.strip()
        
        # Try to parse JSON from the response
        try:
            # Sometimes the response might have extra text, so try to find the JSON array
            start_idx = content.find('[')
            end_idx = content.rfind(']') + 1
            
            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON array found in response")
            
            json_content = content[start_idx:end_idx]
            questions = json.loads(json_content)
            
            # Validate the structure
            if not isinstance(questions, list):
                raise ValueError("Response is not a list")
            
            # Define valid NFL teams for validation
            valid_nfl_teams = {
                'Bills', 'Dolphins', 'Patriots', 'Jets',  # AFC East
                'Ravens', 'Bengals', 'Browns', 'Steelers',  # AFC North
                'Titans', 'Colts', 'Texans', 'Jaguars',  # AFC South
                'Chiefs', 'Chargers', 'Raiders', 'Broncos',  # AFC West
                'Cowboys', 'Eagles', 'Giants', 'Commanders',  # NFC East
                'Packers', 'Lions', 'Bears', 'Vikings',  # NFC North
                'Saints', 'Falcons', 'Panthers', 'Buccaneers',  # NFC South
                '49ers', 'Seahawks', 'Cardinals', 'Rams'  # NFC West
            }
            
            for i, question in enumerate(questions):
                if not isinstance(question, dict):
                    raise ValueError(f"Question {i} is not a dictionary")
                
                required_fields = ['game', 'question', 'line_type', 'line_value', 'direction']
                for field in required_fields:
                    if field not in question:
                        raise ValueError(f"Question {i} missing required field: {field}")
                
                # Validate line_type
                if question['line_type'] not in ['spread', 'over_under']:
                    raise ValueError(f"Question {i} has invalid line_type: {question['line_type']}")
                
                # Validate direction
                valid_directions = ['over', 'under', 'cover']
                if question['direction'] not in valid_directions:
                    raise ValueError(f"Question {i} has invalid direction: {question['direction']}")
                
                # For spread questions, team_favored should be present
                if question['line_type'] == 'spread' and 'team_favored' not in question:
                    raise ValueError(f"Spread question {i} missing team_favored field")
                
                # Validate that teams in the game are real NFL teams
                game = question['game']
                if ' vs ' in game:
                    teams = [team.strip() for team in game.split(' vs ')]
                    for team in teams:
                        if team not in valid_nfl_teams:
                            logger.warning(f"Question {i} contains invalid team: {team}")
                            # Don't fail validation, but log the warning
                
                # Validate betting line ranges
                line_value = question['line_value']
                if question['line_type'] == 'spread':
                    if not (0.5 <= line_value <= 21):
                        logger.warning(f"Question {i} has unusual spread value: {line_value}")
                elif question['line_type'] == 'over_under':
                    if not (30 <= line_value <= 65):
                        logger.warning(f"Question {i} has unusual over/under value: {line_value}")
            
            logger.info(f"Successfully generated {len(questions)} NFL contest questions")
            return questions
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse OpenAI response: {e}")
            logger.error(f"Response content: {content}")
            raise ContestGenerationError(f"Failed to parse AI response: {str(e)}")
    
    except openai.OpenAIError as e:
        logger.error(f"OpenAI API error: {e}")
        raise ContestGenerationError(f"AI service error: {str(e)}")
    
    except Exception as e:
        logger.error(f"Unexpected error in contest generation: {e}")
        raise ContestGenerationError(f"Unexpected error: {str(e)}")


def generate_custom_contest(prompt: str, question_count: int = 5) -> List[Dict]:
    """Generate contest questions using a custom user prompt.
    
    Args:
        prompt (str): User-provided prompt describing the contest they want
        question_count (int): Number of questions to generate (1-10, default 5)
        
    Returns:
        List[Dict]: List of generated questions with metadata
        
    Raises:
        ContestGenerationError: If generation fails
    """
    if not current_app.config.get('OPENAI_API_KEY'):
        raise ContestGenerationError("OpenAI API key not configured")
    
    # Set up OpenAI API key
    openai.api_key = current_app.config['OPENAI_API_KEY']
    logger.info("OpenAI API key configured for custom contest generation")
    
    # Build the prompt for custom contest generation
    system_prompt = f"""You are a contest creation assistant that generates yes/no prediction questions based on user prompts.

IMPORTANT INSTRUCTIONS:
1. Create exactly {question_count} yes/no questions based on the user's prompt
2. Questions should be clear, unambiguous, and answerable with "Yes" or "No"
3. Questions should be about future events that can be objectively verified
4. Avoid questions about subjective opinions or matters of taste
5. Make questions engaging and interesting for participants
6. Ensure questions are appropriate and family-friendly

RESPONSE FORMAT:
Return ONLY a JSON array with this exact structure:

[
  {{
    "question": "Will [specific question about a future event]?",
    "category": "brief category name",
    "description": "brief explanation of what makes this question interesting"
  }}
]

EXAMPLE OUTPUT:
[
  {{
    "question": "Will the temperature in New York City exceed 80°F on December 25th, 2024?",
    "category": "Weather",
    "description": "Unusual weather prediction for winter holiday"
  }},
  {{
    "question": "Will Tesla's stock price be above $300 per share at market close on January 15th, 2024?",
    "category": "Finance",
    "description": "Stock market prediction for major tech company"
  }}
]

Requirements:
- All questions must start with "Will" and end with "?"
- Questions must be about verifiable future events
- Avoid questions that are too easy or too obvious
- Make questions diverse and interesting
- Return ONLY the JSON array, no additional text"""

    user_prompt = f"""Based on this prompt, create {question_count} yes/no prediction questions:

{prompt}

Remember to create questions that are:
- About future events that can be verified
- Clear and unambiguous
- Interesting and engaging
- Appropriate for all audiences"""

    try:
        logger.info(f"Generating custom contest with prompt: {prompt[:100]}...")
        
        # Use the legacy OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        content = response.choices[0].message.content.strip()
        
        # Try to parse JSON from the response
        try:
            # Sometimes the response might have extra text, so try to find the JSON array
            start_idx = content.find('[')
            end_idx = content.rfind(']') + 1
            
            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON array found in response")
            
            json_content = content[start_idx:end_idx]
            questions = json.loads(json_content)
            
            # Validate the structure
            if not isinstance(questions, list):
                raise ValueError("Response is not a list")
            
            for i, question in enumerate(questions):
                if not isinstance(question, dict):
                    raise ValueError(f"Question {i} is not a dictionary")
                
                required_fields = ['question', 'category', 'description']
                for field in required_fields:
                    if field not in question:
                        raise ValueError(f"Question {i} missing required field: {field}")
                
                # Validate question format
                if not question['question'].startswith('Will '):
                    logger.warning(f"Question {i} doesn't start with 'Will ': {question['question']}")
                
                if not question['question'].endswith('?'):
                    logger.warning(f"Question {i} doesn't end with '?': {question['question']}")
            
            logger.info(f"Successfully generated {len(questions)} custom contest questions")
            return questions
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse OpenAI response: {e}")
            logger.error(f"Response content: {content}")
            raise ContestGenerationError(f"Failed to parse AI response: {str(e)}")
    
    except openai.OpenAIError as e:
        logger.error(f"OpenAI API error: {e}")
        raise ContestGenerationError(f"AI service error: {str(e)}")
    
    except Exception as e:
        logger.error(f"Unexpected error in custom contest generation: {e}")
        raise ContestGenerationError(f"Unexpected error: {str(e)}")


def generate_contest_name_and_description(sport: str, week_number: Optional[int] = None, 
                                        season_year: Optional[int] = None) -> Dict[str, str]:
    """Generate a contest name and description.
    
    Args:
        sport (str): Sport name (e.g., "NFL")
        week_number (int, optional): Week number
        season_year (int, optional): Season year
        
    Returns:
        Dict[str, str]: Dictionary with 'name' and 'description' keys
    """
    current_date = datetime.now()
    
    if sport.upper() == "NFL":
        if not season_year:
            if current_date.month >= 9:
                season_year = current_date.year
            else:
                season_year = current_date.year - 1
        
        if not week_number:
            # Estimate current week
            if current_date.month == 9:
                week_number = min(4, max(1, current_date.day // 7))
            elif current_date.month == 10:
                week_number = min(8, 4 + (current_date.day // 7))
            elif current_date.month == 11:
                week_number = min(12, 8 + (current_date.day // 7))
            elif current_date.month == 12:
                week_number = min(16, 12 + (current_date.day // 7))
            elif current_date.month == 1:
                week_number = min(18, 16 + (current_date.day // 7))
            else:
                week_number = 1
        
        name = f"NFL Week {week_number} - {season_year} Season"
        description = f"Predict the outcomes of NFL games for Week {week_number} of the {season_year} season. Answer Yes or No to questions about point spreads and over/under totals."
    
    else:
        name = f"{sport} Contest - {current_date.strftime('%B %Y')}"
        description = f"Predict the outcomes of {sport} games. Answer Yes or No to questions about various betting lines and game outcomes."
    
    return {
        'name': name,
        'description': description
    }


def get_suggested_lock_time(sport: str, week_number: Optional[int] = None) -> datetime:
    """Get a suggested lock time for the contest.
    
    Args:
        sport (str): Sport name
        week_number (int, optional): Week number
        
    Returns:
        datetime: Suggested lock time in UTC
    """
    current_date = datetime.now()
    
    if sport.upper() == "NFL":
        # NFL games typically start on Thursday night, with most games on Sunday
        # Lock the contest on Thursday at 8 PM ET (1 AM UTC Friday)
        days_until_thursday = (3 - current_date.weekday()) % 7  # Thursday is weekday 3
        if days_until_thursday == 0 and current_date.hour >= 20:  # If it's Thursday after 8 PM
            days_until_thursday = 7  # Next Thursday
        
        lock_date = current_date + timedelta(days=days_until_thursday)
        lock_time = lock_date.replace(hour=1, minute=0, second=0, microsecond=0)  # 1 AM UTC = 8 PM ET
        
        return lock_time
    
    else:
        # Default: lock in 3 days at 6 PM local time (approximate)
        lock_date = current_date + timedelta(days=3)
        lock_time = lock_date.replace(hour=23, minute=0, second=0, microsecond=0)  # 11 PM UTC = ~6 PM ET
        
        return lock_time
