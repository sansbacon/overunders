"""Database models for the Over-Under Contests application."""
from datetime import datetime, timedelta
from typing import List, Optional
import secrets
import json
from werkzeug.security import generate_password_hash, check_password_hash
from app import db


class User(db.Model):
    """User model for storing user account information."""
    
    __tablename__ = 'users'
    
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    mobile_phone = db.Column(db.String(20), nullable=True)
    password_hash = db.Column(db.String(255), nullable=True)  # For admin users only
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Google OAuth fields
    google_id = db.Column(db.String(100), unique=True, nullable=True)
    google_email = db.Column(db.String(120), nullable=True)
    google_name = db.Column(db.String(100), nullable=True)
    google_picture = db.Column(db.String(500), nullable=True)
    auth_provider = db.Column(db.String(20), default='email', nullable=False)  # 'email', 'google'
    
    # Moderation and trust fields
    trust_score = db.Column(db.Integer, default=100, nullable=False)  # 0-100 trust score
    warning_count = db.Column(db.Integer, default=0, nullable=False)  # Number of warnings received
    is_suspended = db.Column(db.Boolean, default=False, nullable=False)  # Whether user is suspended
    suspended_until = db.Column(db.DateTime, nullable=True)  # When suspension expires
    suspension_reason = db.Column(db.Text, nullable=True)  # Reason for suspension
    
    # Relationships
    contests = db.relationship('Contest', backref='creator', lazy='dynamic')
    entries = db.relationship('ContestEntry', backref='user', lazy='dynamic')
    
    def __repr__(self) -> str:
        """String representation of User."""
        return f'<User {self.username}>'
    
    def get_contests_created(self) -> List['Contest']:
        """Get all contests created by this user.
        
        Returns:
            List[Contest]: List of contests created by user
        """
        return self.contests.all()
    
    def get_contest_entries(self) -> List['ContestEntry']:
        """Get all contest entries by this user.
        
        Returns:
            List[ContestEntry]: List of contest entries by user
        """
        return self.entries.all()
    
    def set_password(self, password: str) -> None:
        """Set password hash for admin users.
        
        Args:
            password (str): Plain text password
        """
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password: str) -> bool:
        """Check if provided password matches stored hash.
        
        Args:
            password (str): Plain text password to check
            
        Returns:
            bool: True if password matches, False otherwise
        """
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)
    
    def has_password(self) -> bool:
        """Check if user has a password set.
        
        Returns:
            bool: True if user has password, False otherwise
        """
        return self.password_hash is not None
    
    def get_display_name(self) -> str:
        """Get display name with first/last name in parentheses if available.
        
        Returns:
            str: Username with optional first/last name in parentheses
        """
        if self.first_name or self.last_name:
            name_parts = []
            if self.first_name:
                name_parts.append(self.first_name)
            if self.last_name:
                name_parts.append(self.last_name)
            full_name = ' '.join(name_parts)
            return f"{self.username} ({full_name})"
        return self.username
    
    def get_full_name(self) -> str:
        """Get full name (first + last name).
        
        Returns:
            str: Full name or empty string if not available
        """
        name_parts = []
        if self.first_name:
            name_parts.append(self.first_name)
        if self.last_name:
            name_parts.append(self.last_name)
        return ' '.join(name_parts)
    
    def get_ai_contests_today(self) -> int:
        """Get count of AI-generated contests created by this user today.
        
        Returns:
            int: Number of AI-generated contests created today
        """
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        return Contest.query.filter(
            Contest.created_by_user == self.user_id,
            Contest.is_ai_generated == True,
            Contest.created_at >= today_start,
            Contest.created_at < today_end
        ).count()
    
    def can_create_ai_contest(self) -> bool:
        """Check if user can create another AI-generated contest today.
        
        Returns:
            bool: True if user can create AI contest, False otherwise
        """
        if self.is_admin:
            return True
        
        daily_limit = 3
        contests_today = self.get_ai_contests_today()
        return contests_today < daily_limit
    
    def get_remaining_ai_contests_today(self) -> int:
        """Get number of remaining AI contests user can create today.
        
        Returns:
            int: Number of remaining AI contests for today
        """
        if self.is_admin:
            return 999  # Unlimited for admins
        
        daily_limit = 3
        contests_today = self.get_ai_contests_today()
        return max(0, daily_limit - contests_today)


class Contest(db.Model):
    """Contest model for storing contest information."""
    
    __tablename__ = 'contests'
    
    contest_id = db.Column(db.Integer, primary_key=True)
    contest_name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_by_user = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    lock_timestamp = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_ai_generated = db.Column(db.Boolean, default=False, nullable=False)
    
    # Moderation fields
    moderation_status = db.Column(db.String(20), default='approved', nullable=False)  # 'approved', 'flagged', 'blocked', 'pending'
    moderation_notes = db.Column(db.Text, nullable=True)  # Notes from moderation review
    flagged_at = db.Column(db.DateTime, nullable=True)  # When content was flagged
    reviewed_at = db.Column(db.DateTime, nullable=True)  # When content was reviewed
    reviewed_by_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)  # Who reviewed it
    
    # Relationships
    questions = db.relationship('Question', backref='contest', lazy='dynamic', cascade='all, delete-orphan')
    entries = db.relationship('ContestEntry', backref='contest', lazy='dynamic', cascade='all, delete-orphan')
    invitations = db.relationship('ContestInvitation', backref='contest', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self) -> str:
        """String representation of Contest."""
        return f'<Contest {self.contest_name}>'
    
    def is_locked(self) -> bool:
        """Check if contest is locked for modifications.
        
        Returns:
            bool: True if contest is locked, False otherwise
        """
        return datetime.utcnow() > self.lock_timestamp
    
    def has_entries(self) -> bool:
        """Check if contest has any entries.
        
        Returns:
            bool: True if contest has entries, False otherwise
        """
        return self.entries.count() > 0
    
    def can_modify_questions(self) -> bool:
        """Check if questions can be modified.
        
        Returns:
            bool: True if questions can be modified, False otherwise
        """
        return not self.has_entries()
    
    def get_questions_ordered(self) -> List['Question']:
        """Get questions ordered by question_order.
        
        Returns:
            List[Question]: Ordered list of questions
        """
        return self.questions.order_by(Question.question_order).all()
    
    def get_leaderboard(self) -> List[dict]:
        """Get leaderboard for this contest.
        
        Returns:
            List[dict]: Leaderboard data with user info and scores
        """
        leaderboard = []
        for entry in self.entries.all():
            score_data = entry.calculate_score()
            leaderboard.append({
                'user': entry.user,
                'entry': entry,
                'score': score_data['correct_answers'],
                'correct_answers': score_data['correct_answers'],
                'total_questions': score_data['total_questions'],
                'answered_questions': score_data['answered_questions'],
                'percentage': score_data['percentage']
            })
        
        # Sort by correct answers (desc), then by percentage (desc)
        leaderboard.sort(key=lambda x: (x['correct_answers'], x['percentage']), reverse=True)
        return leaderboard
    
    def has_all_answers(self) -> bool:
        """Check if all questions have answers set.
        
        Returns:
            bool: True if all questions have answers, False otherwise
        """
        questions = self.get_questions_ordered()
        return all(question.has_answer() for question in questions)
    
    def get_questions_without_answers(self) -> List['Question']:
        """Get questions that don't have answers set yet.
        
        Returns:
            List[Question]: Questions without answers
        """
        return [q for q in self.get_questions_ordered() if not q.has_answer()]
    
    def get_invitation_count(self) -> int:
        """Get total number of invitations sent for this contest.
        
        Returns:
            int: Total invitation count
        """
        return len(self.invitations)
    
    def can_send_more_invitations(self, count: int = 1) -> bool:
        """Check if more invitations can be sent (max 100 per contest).
        
        Args:
            count (int): Number of invitations to send
            
        Returns:
            bool: True if invitations can be sent, False otherwise
        """
        current_count = self.get_invitation_count()
        return (current_count + count) <= 100
    
    def get_remaining_invitations(self) -> int:
        """Get number of remaining invitations that can be sent.
        
        Returns:
            int: Number of remaining invitations
        """
        return max(0, 100 - self.get_invitation_count())


class Question(db.Model):
    """Question model for storing contest questions."""
    
    __tablename__ = 'questions'
    
    question_id = db.Column(db.Integer, primary_key=True)
    contest_id = db.Column(db.Integer, db.ForeignKey('contests.contest_id'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    question_order = db.Column(db.Integer, nullable=False)
    correct_answer = db.Column(db.Boolean, nullable=True)  # True for Yes, False for No, None if not set yet
    answer_set_at = db.Column(db.DateTime, nullable=True)  # When the answer was set
    
    # Moderation fields
    moderation_status = db.Column(db.String(20), default='approved', nullable=False)  # 'approved', 'flagged', 'blocked', 'pending'
    moderation_notes = db.Column(db.Text, nullable=True)  # Notes from moderation review
    flagged_at = db.Column(db.DateTime, nullable=True)  # When content was flagged
    reviewed_at = db.Column(db.DateTime, nullable=True)  # When content was reviewed
    reviewed_by_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)  # Who reviewed it
    
    # Relationships
    answers = db.relationship('EntryAnswer', backref='question', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self) -> str:
        """String representation of Question."""
        return f'<Question {self.question_id}: {self.question_text[:50]}...>'
    
    def has_answer(self) -> bool:
        """Check if question has an answer set.
        
        Returns:
            bool: True if answer is set, False otherwise
        """
        return self.correct_answer is not None
    
    def set_answer(self, answer: bool) -> None:
        """Set the correct answer for this question.
        
        Args:
            answer (bool): True for Yes, False for No
        """
        self.correct_answer = answer
        self.answer_set_at = datetime.utcnow()


class ContestEntry(db.Model):
    """Contest entry model for storing user entries to contests."""
    
    __tablename__ = 'contest_entries'
    
    entry_id = db.Column(db.Integer, primary_key=True)
    contest_id = db.Column(db.Integer, db.ForeignKey('contests.contest_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    answers = db.relationship('EntryAnswer', backref='entry', lazy='dynamic', cascade='all, delete-orphan')
    
    # Unique constraint
    __table_args__ = (db.UniqueConstraint('contest_id', 'user_id', name='unique_user_contest_entry'),)
    
    def __repr__(self) -> str:
        """String representation of ContestEntry."""
        return f'<ContestEntry {self.entry_id}: User {self.user_id} in Contest {self.contest_id}>'
    
    def can_modify(self) -> bool:
        """Check if entry can be modified.
        
        Returns:
            bool: True if entry can be modified, False otherwise
        """
        return not self.contest.is_locked()
    
    def calculate_score(self) -> dict:
        """Calculate score for this entry.
        
        Returns:
            dict: Score information including correct answers, total questions, answered questions, and percentage
        """
        questions = self.contest.get_questions_ordered()
        total_questions = len(questions)
        answered_questions = len([q for q in questions if q.has_answer()])
        correct_answers = 0
        
        for question in questions:
            # Only count questions that have answers set
            if question.has_answer():
                answer = self.answers.filter_by(question_id=question.question_id).first()
                if answer and answer.user_answer == question.correct_answer:
                    correct_answers += 1
        
        percentage = (correct_answers / answered_questions * 100) if answered_questions > 0 else 0
        
        return {
            'correct_answers': correct_answers,
            'total_questions': total_questions,
            'answered_questions': answered_questions,
            'percentage': round(percentage, 1)
        }
    
    def get_answers_dict(self) -> dict:
        """Get answers as a dictionary keyed by question_id.
        
        Returns:
            dict: Dictionary of question_id -> user_answer
        """
        return {answer.question_id: answer.user_answer for answer in self.answers.all()}


class EntryAnswer(db.Model):
    """Entry answer model for storing individual answers to questions."""
    
    __tablename__ = 'entry_answers'
    
    answer_id = db.Column(db.Integer, primary_key=True)
    entry_id = db.Column(db.Integer, db.ForeignKey('contest_entries.entry_id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.question_id'), nullable=False)
    user_answer = db.Column(db.Boolean, nullable=False)  # True for Yes, False for No
    
    # Unique constraint
    __table_args__ = (db.UniqueConstraint('entry_id', 'question_id', name='unique_entry_question_answer'),)
    
    def __repr__(self) -> str:
        """String representation of EntryAnswer."""
        return f'<EntryAnswer {self.answer_id}: Entry {self.entry_id}, Question {self.question_id}>'


class ContestInvitation(db.Model):
    """Model for contest invitations."""
    
    __tablename__ = 'contest_invitations'
    
    invitation_id = db.Column(db.Integer, primary_key=True)
    contest_id = db.Column(db.Integer, db.ForeignKey('contests.contest_id'), nullable=False)
    sent_by_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    recipient_email = db.Column(db.String(255))
    recipient_phone = db.Column(db.String(20))
    invitation_type = db.Column(db.String(10), nullable=False)  # 'email' or 'sms'
    status = db.Column(db.String(20), default='pending')  # 'pending', 'sent', 'failed'
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    sent_by = db.relationship('User', backref='sent_invitations')


class EmailLog(db.Model):
    """Model for email sending logs."""
    
    __tablename__ = 'email_logs'
    
    log_id = db.Column(db.Integer, primary_key=True)
    recipient_email = db.Column(db.String(255), nullable=False)
    subject = db.Column(db.String(500), nullable=False)
    email_type = db.Column(db.String(50), nullable=False)  # 'login', 'invitation', 'notification', 'generic'
    delivery_method = db.Column(db.String(20), nullable=False)  # 'sendgrid_api', 'smtp'
    status = db.Column(db.String(20), nullable=False)  # 'sent', 'failed'
    error_message = db.Column(db.Text)
    response_code = db.Column(db.Integer)
    response_body = db.Column(db.Text)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Optional relationships
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    contest_id = db.Column(db.Integer, db.ForeignKey('contests.contest_id'))
    
    # Relationships
    user = db.relationship('User', backref='email_logs')
    contest = db.relationship('Contest', backref='email_logs')
    
    def __repr__(self):
        return f'<EmailLog {self.log_id}: {self.email_type} to {self.recipient_email} - {self.status}>'
    
    @classmethod
    def log_email(cls, recipient_email: str, subject: str, email_type: str, 
                  delivery_method: str, status: str, error_message: str = None,
                  response_code: int = None, response_body: str = None,
                  user_id: int = None, contest_id: int = None):
        """Create an email log entry.
        
        Args:
            recipient_email (str): Email address
            subject (str): Email subject
            email_type (str): Type of email
            delivery_method (str): Method used to send
            status (str): Success or failure status
            error_message (str, optional): Error message if failed
            response_code (int, optional): HTTP response code
            response_body (str, optional): Response body
            user_id (int, optional): Associated user ID
            contest_id (int, optional): Associated contest ID
        """
        log_entry = cls(
            recipient_email=recipient_email,
            subject=subject,
            email_type=email_type,
            delivery_method=delivery_method,
            status=status,
            error_message=error_message,
            response_code=response_code,
            response_body=response_body,
            user_id=user_id,
            contest_id=contest_id
        )
        db.session.add(log_entry)
        db.session.commit()
        return log_entry
    
    def __repr__(self) -> str:
        """String representation of ContestInvitation."""
        recipient = self.recipient_email or self.recipient_phone
        return f'<ContestInvitation {self.invitation_id}: {self.invitation_type} to {recipient}>'


class NFLSchedule(db.Model):
    """NFL schedule model for storing game schedules."""
    
    __tablename__ = 'nfl_schedules'
    
    schedule_id = db.Column(db.Integer, primary_key=True)
    season_year = db.Column(db.Integer, nullable=False)
    week_number = db.Column(db.Integer, nullable=False)
    home_team = db.Column(db.String(50), nullable=False)
    away_team = db.Column(db.String(50), nullable=False)
    game_date = db.Column(db.DateTime, nullable=True)
    game_time = db.Column(db.String(20), nullable=True)
    is_playoff = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self) -> str:
        """String representation of NFLSchedule."""
        return f'<NFLSchedule {self.season_year} Week {self.week_number}: {self.away_team} @ {self.home_team}>'
    
    @classmethod
    def get_games_for_week(cls, season_year: int, week_number: int) -> List['NFLSchedule']:
        """Get all games for a specific week.
        
        Args:
            season_year (int): NFL season year
            week_number (int): Week number (1-18)
            
        Returns:
            List[NFLSchedule]: List of games for the week
        """
        return cls.query.filter_by(
            season_year=season_year,
            week_number=week_number
        ).all()
    
    @classmethod
    def get_matchup_string(cls, home_team: str, away_team: str) -> str:
        """Get formatted matchup string.
        
        Args:
            home_team (str): Home team name
            away_team (str): Away team name
            
        Returns:
            str: Formatted matchup (e.g., "Cowboys vs Eagles")
        """
        return f"{away_team} vs {home_team}"
    
    def get_matchup(self) -> str:
        """Get formatted matchup string for this game.
        
        Returns:
            str: Formatted matchup
        """
        return self.get_matchup_string(self.home_team, self.away_team)


class League(db.Model):
    """League model for storing league information."""
    
    __tablename__ = 'leagues'
    
    league_id = db.Column(db.Integer, primary_key=True)
    league_name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_by_user = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_public = db.Column(db.Boolean, default=False, nullable=False)
    win_bonus_points = db.Column(db.Integer, default=5, nullable=False)
    
    # Moderation fields
    moderation_status = db.Column(db.String(20), default='approved', nullable=False)  # 'approved', 'flagged', 'blocked', 'pending'
    moderation_notes = db.Column(db.Text, nullable=True)  # Notes from moderation review
    flagged_at = db.Column(db.DateTime, nullable=True)  # When content was flagged
    reviewed_at = db.Column(db.DateTime, nullable=True)  # When content was reviewed
    reviewed_by_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)  # Who reviewed it
    
    # Relationships
    creator = db.relationship('User', backref='created_leagues', foreign_keys=[created_by_user])
    memberships = db.relationship('LeagueMembership', backref='league', lazy='dynamic', cascade='all, delete-orphan')
    league_contests = db.relationship('LeagueContest', backref='league', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self) -> str:
        """String representation of League."""
        return f'<League {self.league_name}>'
    
    def get_members(self) -> List['User']:
        """Get all members of this league.
        
        Returns:
            List[User]: List of users who are members of this league
        """
        return [membership.user for membership in self.memberships.all()]
    
    def get_member_count(self) -> int:
        """Get count of league members.
        
        Returns:
            int: Number of members in the league
        """
        return self.memberships.count()
    
    def is_member(self, user: 'User') -> bool:
        """Check if user is a member of this league.
        
        Args:
            user (User): User to check
            
        Returns:
            bool: True if user is a member, False otherwise
        """
        return self.memberships.filter_by(user_id=user.user_id).first() is not None
    
    def is_admin(self, user: 'User') -> bool:
        """Check if user is an admin of this league.
        
        Args:
            user (User): User to check
            
        Returns:
            bool: True if user is an admin, False otherwise
        """
        membership = self.memberships.filter_by(user_id=user.user_id).first()
        return membership and membership.is_admin
    
    def get_contests(self) -> List['Contest']:
        """Get all contests in this league ordered by contest_order.
        
        Returns:
            List[Contest]: List of contests in the league
        """
        league_contests = self.league_contests.order_by(LeagueContest.contest_order).all()
        return [lc.contest for lc in league_contests]
    
    def get_contest_count(self) -> int:
        """Get count of contests in this league.
        
        Returns:
            int: Number of contests in the league
        """
        return self.league_contests.count()
    
    def get_leaderboard(self) -> List[dict]:
        """Get overall league leaderboard combining all contest results.
        
        Returns:
            List[dict]: Leaderboard data with user info, total points, and contest wins
        """
        leaderboard = {}
        contests = self.get_contests()
        
        # Initialize leaderboard for all members
        for member in self.get_members():
            leaderboard[member.user_id] = {
                'user': member,
                'total_points': 0,
                'contest_wins': 0,
                'contests_participated': 0,
                'contests_completed': 0,
                'contest_details': []
            }
        
        # Process each contest
        for contest in contests:
            if contest.is_locked() and contest.has_all_answers():
                contest_leaderboard = contest.get_leaderboard()
                
                # Track who participated in this contest
                participants = {entry['user'].user_id for entry in contest_leaderboard}
                
                for i, entry in enumerate(contest_leaderboard, 1):
                    user_id = entry['user'].user_id
                    if user_id in leaderboard:
                        # Add points from this contest
                        points = entry['correct_answers']
                        
                        # Add win bonus if they won this contest
                        if i == 1:
                            points += self.win_bonus_points
                            leaderboard[user_id]['contest_wins'] += 1
                        
                        leaderboard[user_id]['total_points'] += points
                        leaderboard[user_id]['contests_completed'] += 1
                        leaderboard[user_id]['contest_details'].append({
                            'contest': contest,
                            'position': i,
                            'score': entry['correct_answers'],
                            'bonus_points': self.win_bonus_points if i == 1 else 0,
                            'total_points': points
                        })
                
                # Update participation count for all league members who participated
                for user_id in participants:
                    if user_id in leaderboard:
                        leaderboard[user_id]['contests_participated'] += 1
        
        # Convert to list and sort by total points (desc), then by contest wins (desc)
        leaderboard_list = list(leaderboard.values())
        leaderboard_list.sort(key=lambda x: (x['total_points'], x['contest_wins']), reverse=True)
        
        return leaderboard_list
    
    def add_contest(self, contest: 'Contest') -> 'LeagueContest':
        """Add a contest to this league.
        
        Args:
            contest (Contest): Contest to add
            
        Returns:
            LeagueContest: The created league contest relationship
        """
        # Get the next order number
        max_order = db.session.query(db.func.max(LeagueContest.contest_order))\
                             .filter_by(league_id=self.league_id).scalar() or 0
        
        league_contest = LeagueContest(
            league_id=self.league_id,
            contest_id=contest.contest_id,
            contest_order=max_order + 1
        )
        db.session.add(league_contest)
        return league_contest
    
    def remove_contest(self, contest: 'Contest') -> bool:
        """Remove a contest from this league.
        
        Args:
            contest (Contest): Contest to remove
            
        Returns:
            bool: True if contest was removed, False if not found
        """
        league_contest = self.league_contests.filter_by(contest_id=contest.contest_id).first()
        if league_contest:
            db.session.delete(league_contest)
            return True
        return False


class LeagueMembership(db.Model):
    """League membership model for tracking users in leagues."""
    
    __tablename__ = 'league_memberships'
    
    membership_id = db.Column(db.Integer, primary_key=True)
    league_id = db.Column(db.Integer, db.ForeignKey('leagues.league_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    
    # Relationships
    user = db.relationship('User', backref='league_memberships')
    
    # Unique constraint
    __table_args__ = (db.UniqueConstraint('league_id', 'user_id', name='unique_league_user_membership'),)
    
    def __repr__(self) -> str:
        """String representation of LeagueMembership."""
        return f'<LeagueMembership {self.membership_id}: User {self.user_id} in League {self.league_id}>'


class LeagueContest(db.Model):
    """League contest model for linking contests to leagues."""
    
    __tablename__ = 'league_contests'
    
    league_contest_id = db.Column(db.Integer, primary_key=True)
    league_id = db.Column(db.Integer, db.ForeignKey('leagues.league_id'), nullable=False)
    contest_id = db.Column(db.Integer, db.ForeignKey('contests.contest_id'), nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    contest_order = db.Column(db.Integer, default=1, nullable=False)
    
    # Relationships
    contest = db.relationship('Contest', backref='league_contests')
    
    # Unique constraint
    __table_args__ = (db.UniqueConstraint('league_id', 'contest_id', name='unique_league_contest'),)
    
    def __repr__(self) -> str:
        """String representation of LeagueContest."""
        return f'<LeagueContest {self.league_contest_id}: Contest {self.contest_id} in League {self.league_id}>'


class LoginToken(db.Model):
    """Login token model for one-time email authentication."""
    
    __tablename__ = 'login_tokens'
    
    token_id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    token = db.Column(db.String(64), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self) -> str:
        """String representation of LoginToken."""
        return f'<LoginToken {self.token_id}: {self.email}>'
    
    @staticmethod
    def generate_token() -> str:
        """Generate a secure random token.
        
        Returns:
            str: Secure random token
        """
        return secrets.token_urlsafe(32)
    
    def is_valid(self) -> bool:
        """Check if token is valid (not used and not expired).
        
        Returns:
            bool: True if token is valid, False otherwise
        """
        return not self.used and datetime.utcnow() < self.expires_at
    
    def mark_as_used(self) -> None:
        """Mark token as used."""
        self.used = True
        db.session.commit()
    
    @classmethod
    def create_token(cls, email: str, expiration_minutes: int = 30) -> 'LoginToken':
        """Create a new login token for the given email.
        
        Args:
            email (str): Email address
            expiration_minutes (int): Token expiration time in minutes
            
        Returns:
            LoginToken: New login token instance
        """
        token = cls(
            email=email,
            token=cls.generate_token(),
            expires_at=datetime.utcnow() + timedelta(minutes=expiration_minutes)
        )
        db.session.add(token)
        db.session.commit()
        return token
    
    @classmethod
    def cleanup_expired_tokens(cls) -> None:
        """Remove expired tokens from database."""
        expired_tokens = cls.query.filter(cls.expires_at < datetime.utcnow()).all()
        for token in expired_tokens:
            db.session.delete(token)
        db.session.commit()


class ContentModerationLog(db.Model):
    """Model for content moderation logs."""
    
    __tablename__ = 'content_moderation_logs'
    
    log_id = db.Column(db.Integer, primary_key=True)
    content_type = db.Column(db.String(50), nullable=False)  # 'contest', 'league', 'question', etc.
    content_id = db.Column(db.Integer, nullable=True)  # ID of the content being moderated
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)
    content_text = db.Column(db.Text, nullable=False)  # The actual text that was moderated
    moderation_result = db.Column(db.JSON, nullable=False)  # JSON result from moderation
    action_taken = db.Column(db.String(50), nullable=False)  # 'approved', 'flagged', 'blocked', 'reviewed'
    moderator_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='moderation_logs')
    moderator = db.relationship('User', foreign_keys=[moderator_id], backref='moderation_actions')
    
    def __repr__(self) -> str:
        """String representation of ContentModerationLog."""
        return f'<ContentModerationLog {self.log_id}: {self.content_type} - {self.action_taken}>'
    
    @classmethod
    def log_moderation(cls, content_type: str, content_text: str, moderation_result: dict,
                      action_taken: str, content_id: int = None, user_id: int = None,
                      moderator_id: int = None):
        """Create a moderation log entry.
        
        Args:
            content_type (str): Type of content being moderated
            content_text (str): The text content
            moderation_result (dict): Result from moderation check
            action_taken (str): Action taken based on moderation
            content_id (int, optional): ID of the content
            user_id (int, optional): ID of user who created content
            moderator_id (int, optional): ID of moderator who reviewed
        """
        log_entry = cls(
            content_type=content_type,
            content_id=content_id,
            user_id=user_id,
            content_text=content_text,
            moderation_result=moderation_result,
            action_taken=action_taken,
            moderator_id=moderator_id
        )
        db.session.add(log_entry)
        db.session.commit()
        return log_entry


class ContentReport(db.Model):
    """Model for user reports of inappropriate content."""
    
    __tablename__ = 'content_reports'
    
    report_id = db.Column(db.Integer, primary_key=True)
    content_type = db.Column(db.String(50), nullable=False)  # 'contest', 'league', 'question', etc.
    content_id = db.Column(db.Integer, nullable=False)  # ID of the reported content
    reported_by_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    report_reason = db.Column(db.String(100), nullable=False)  # 'spam', 'inappropriate', 'offensive', etc.
    report_description = db.Column(db.Text, nullable=True)  # Additional details from reporter
    status = db.Column(db.String(20), default='pending', nullable=False)  # 'pending', 'reviewed', 'dismissed', 'action_taken'
    reviewed_by_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)
    review_notes = db.Column(db.Text, nullable=True)  # Notes from moderator review
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    reported_by = db.relationship('User', foreign_keys=[reported_by_user_id], backref='reports_made')
    reviewed_by = db.relationship('User', foreign_keys=[reviewed_by_user_id], backref='reports_reviewed')
    
    def __repr__(self) -> str:
        """String representation of ContentReport."""
        return f'<ContentReport {self.report_id}: {self.content_type} {self.content_id} - {self.status}>'
    
    def mark_reviewed(self, reviewer_id: int, status: str, notes: str = None):
        """Mark report as reviewed.
        
        Args:
            reviewer_id (int): ID of reviewing moderator
            status (str): New status for the report
            notes (str, optional): Review notes
        """
        self.reviewed_by_user_id = reviewer_id
        self.status = status
        self.review_notes = notes
        self.reviewed_at = datetime.utcnow()
        db.session.commit()


class UserWarning(db.Model):
    """Model for user warnings and disciplinary actions."""
    
    __tablename__ = 'user_warnings'
    
    warning_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    issued_by_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    warning_type = db.Column(db.String(50), nullable=False)  # 'content_violation', 'spam', 'harassment', etc.
    reason = db.Column(db.Text, nullable=False)  # Detailed reason for warning
    content_type = db.Column(db.String(50), nullable=True)  # Related content type if applicable
    content_id = db.Column(db.Integer, nullable=True)  # Related content ID if applicable
    severity = db.Column(db.String(20), nullable=False)  # 'low', 'medium', 'high', 'critical'
    is_active = db.Column(db.Boolean, default=True, nullable=False)  # Whether warning is still active
    expires_at = db.Column(db.DateTime, nullable=True)  # When warning expires (if applicable)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='warnings_received')
    issued_by = db.relationship('User', foreign_keys=[issued_by_user_id], backref='warnings_issued')
    
    def __repr__(self) -> str:
        """String representation of UserWarning."""
        return f'<UserWarning {self.warning_id}: {self.warning_type} - {self.severity}>'
    
    def is_expired(self) -> bool:
        """Check if warning has expired.
        
        Returns:
            bool: True if warning has expired
        """
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    def deactivate(self):
        """Deactivate the warning."""
        self.is_active = False
        db.session.commit()


class UserVerification(db.Model):
    """Model for user verification requests and status."""
    
    __tablename__ = 'user_verifications'
    
    verification_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    verification_type = db.Column(db.String(50), nullable=False)  # 'identity', 'email', 'phone', 'document'
    verification_level = db.Column(db.String(20), nullable=False)  # 'basic', 'enhanced', 'premium'
    status = db.Column(db.String(20), default='pending', nullable=False)  # 'pending', 'approved', 'rejected', 'expired'
    
    # Verification data
    submitted_data = db.Column(db.JSON, nullable=True)  # Data submitted for verification
    verification_method = db.Column(db.String(50), nullable=True)  # Method used for verification
    verification_notes = db.Column(db.Text, nullable=True)  # Notes about verification process
    
    # Admin review
    reviewed_by_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)
    review_notes = db.Column(db.Text, nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    
    # Timestamps
    requested_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    approved_at = db.Column(db.DateTime, nullable=True)
    expires_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='verification_requests')
    reviewed_by = db.relationship('User', foreign_keys=[reviewed_by_user_id], backref='verifications_reviewed')
    
    def __repr__(self) -> str:
        """String representation of UserVerification."""
        return f'<UserVerification {self.verification_id}: {self.user_id} - {self.verification_level} - {self.status}>'
    
    def is_active(self) -> bool:
        """Check if verification is currently active.
        
        Returns:
            bool: True if verification is active and not expired
        """
        if self.status != 'approved':
            return False
        
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
        
        return True
    
    def approve(self, reviewer_id: int, notes: str = None, expires_in_days: int = None):
        """Approve the verification request.
        
        Args:
            reviewer_id (int): ID of the reviewing admin
            notes (str, optional): Review notes
            expires_in_days (int, optional): Days until verification expires
        """
        self.status = 'approved'
        self.reviewed_by_user_id = reviewer_id
        self.review_notes = notes
        self.reviewed_at = datetime.utcnow()
        self.approved_at = datetime.utcnow()
        
        if expires_in_days:
            self.expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        
        db.session.commit()
    
    def reject(self, reviewer_id: int, notes: str = None):
        """Reject the verification request.
        
        Args:
            reviewer_id (int): ID of the reviewing admin
            notes (str, optional): Review notes explaining rejection
        """
        self.status = 'rejected'
        self.reviewed_by_user_id = reviewer_id
        self.review_notes = notes
        self.reviewed_at = datetime.utcnow()
        db.session.commit()
    
    @classmethod
    def get_user_verifications(cls, user_id: int, active_only: bool = True) -> List['UserVerification']:
        """Get verifications for a user.
        
        Args:
            user_id (int): User ID
            active_only (bool): Whether to return only active verifications
            
        Returns:
            List[UserVerification]: List of user verifications
        """
        query = cls.query.filter_by(user_id=user_id)
        
        if active_only:
            query = query.filter_by(status='approved')
        
        return query.order_by(cls.requested_at.desc()).all()
    
    @classmethod
    def get_highest_verification_level(cls, user_id: int) -> Optional[str]:
        """Get the highest active verification level for a user.
        
        Args:
            user_id (int): User ID
            
        Returns:
            Optional[str]: Highest verification level or None if no active verifications
        """
        verifications = cls.get_user_verifications(user_id, active_only=True)
        active_verifications = [v for v in verifications if v.is_active()]
        
        if not active_verifications:
            return None
        
        # Define level hierarchy
        level_hierarchy = {'basic': 1, 'enhanced': 2, 'premium': 3}
        
        highest_level = None
        highest_rank = 0
        
        for verification in active_verifications:
            rank = level_hierarchy.get(verification.verification_level, 0)
            if rank > highest_rank:
                highest_rank = rank
                highest_level = verification.verification_level
        
        return highest_level


class UserReputation(db.Model):
    """Model for tracking user reputation and trust metrics."""
    
    __tablename__ = 'user_reputations'
    
    reputation_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False, unique=True)
    
    # Core reputation metrics
    reputation_score = db.Column(db.Integer, default=100, nullable=False)  # Base reputation score
    trust_level = db.Column(db.String(20), default='new', nullable=False)  # 'new', 'trusted', 'veteran', 'expert'
    
    # Activity metrics
    contests_created = db.Column(db.Integer, default=0, nullable=False)
    contests_participated = db.Column(db.Integer, default=0, nullable=False)
    leagues_created = db.Column(db.Integer, default=0, nullable=False)
    leagues_joined = db.Column(db.Integer, default=0, nullable=False)
    
    # Performance metrics
    contest_wins = db.Column(db.Integer, default=0, nullable=False)
    top_3_finishes = db.Column(db.Integer, default=0, nullable=False)
    total_contest_points = db.Column(db.Integer, default=0, nullable=False)
    average_accuracy = db.Column(db.Float, default=0.0, nullable=False)
    
    # Community metrics
    positive_feedback_count = db.Column(db.Integer, default=0, nullable=False)
    negative_feedback_count = db.Column(db.Integer, default=0, nullable=False)
    helpful_votes = db.Column(db.Integer, default=0, nullable=False)
    
    # Moderation metrics
    content_flags_received = db.Column(db.Integer, default=0, nullable=False)
    warnings_received = db.Column(db.Integer, default=0, nullable=False)
    suspensions_count = db.Column(db.Integer, default=0, nullable=False)
    
    # Verification status
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    verification_level = db.Column(db.String(20), nullable=True)  # 'basic', 'enhanced', 'premium'
    verified_at = db.Column(db.DateTime, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_activity_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = db.relationship('User', backref='reputation', uselist=False)
    
    def __repr__(self) -> str:
        """String representation of UserReputation."""
        return f'<UserReputation {self.user_id}: {self.reputation_score} - {self.trust_level}>'
    
    def calculate_reputation_score(self) -> int:
        """Calculate reputation score based on various factors.
        
        Returns:
            int: Calculated reputation score
        """
        base_score = 100
        
        # Activity bonuses
        activity_bonus = min(50, (self.contests_created * 5) + (self.contests_participated * 2))
        
        # Performance bonuses
        performance_bonus = (self.contest_wins * 10) + (self.top_3_finishes * 5)
        
        # Community bonuses
        community_bonus = (self.positive_feedback_count * 2) + self.helpful_votes
        
        # Verification bonus
        verification_bonus = 0
        if self.is_verified:
            verification_bonus = {'basic': 20, 'enhanced': 40, 'premium': 60}.get(self.verification_level, 0)
        
        # Penalties
        moderation_penalty = (self.content_flags_received * 5) + (self.warnings_received * 10) + (self.suspensions_count * 25)
        negative_feedback_penalty = self.negative_feedback_count * 3
        
        # Calculate final score
        calculated_score = (base_score + activity_bonus + performance_bonus + 
                          community_bonus + verification_bonus - 
                          moderation_penalty - negative_feedback_penalty)
        
        return max(0, min(1000, calculated_score))  # Clamp between 0 and 1000
    
    def update_trust_level(self):
        """Update trust level based on reputation score and other factors."""
        score = self.reputation_score
        
        if score >= 500 and self.contests_created >= 10 and self.is_verified:
            self.trust_level = 'expert'
        elif score >= 300 and self.contests_participated >= 20:
            self.trust_level = 'veteran'
        elif score >= 150 and self.contests_participated >= 5:
            self.trust_level = 'trusted'
        else:
            self.trust_level = 'new'
    
    def update_verification_status(self):
        """Update verification status based on latest verification records."""
        latest_verification = UserVerification.query.filter_by(
            user_id=self.user_id,
            status='approved'
        ).order_by(UserVerification.approved_at.desc()).first()
        
        if latest_verification and latest_verification.is_active():
            self.is_verified = True
            self.verification_level = latest_verification.verification_level
            self.verified_at = latest_verification.approved_at
        else:
            self.is_verified = False
            self.verification_level = None
            self.verified_at = None
    
    def refresh_metrics(self):
        """Refresh all reputation metrics from current data."""
        # Update activity metrics
        self.contests_created = Contest.query.filter_by(created_by_user=self.user_id).count()
        self.contests_participated = ContestEntry.query.filter_by(user_id=self.user_id).count()
        self.leagues_created = League.query.filter_by(created_by_user=self.user_id).count()
        self.leagues_joined = LeagueMembership.query.filter_by(user_id=self.user_id).count()
        
        # Update moderation metrics
        self.warnings_received = UserWarning.query.filter_by(user_id=self.user_id, is_active=True).count()
        
        # Update verification status
        self.update_verification_status()
        
        # Recalculate reputation score
        self.reputation_score = self.calculate_reputation_score()
        
        # Update trust level
        self.update_trust_level()
        
        # Update timestamp
        self.updated_at = datetime.utcnow()
        
        db.session.commit()
    
    @classmethod
    def get_or_create(cls, user_id: int) -> 'UserReputation':
        """Get or create reputation record for a user.
        
        Args:
            user_id (int): User ID
            
        Returns:
            UserReputation: User's reputation record
        """
        reputation = cls.query.filter_by(user_id=user_id).first()
        
        if not reputation:
            reputation = cls(user_id=user_id)
            db.session.add(reputation)
            db.session.commit()
            reputation.refresh_metrics()
        
        return reputation
    
    @classmethod
    def update_user_activity(cls, user_id: int):
        """Update user's last activity timestamp.
        
        Args:
            user_id (int): User ID
        """
        reputation = cls.get_or_create(user_id)
        reputation.last_activity_at = datetime.utcnow()
        db.session.commit()


class ReputationHistory(db.Model):
    """Model for tracking reputation score changes over time."""
    
    __tablename__ = 'reputation_history'
    
    history_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    old_score = db.Column(db.Integer, nullable=False)
    new_score = db.Column(db.Integer, nullable=False)
    change_reason = db.Column(db.String(100), nullable=False)  # 'contest_win', 'verification', 'warning', etc.
    change_details = db.Column(db.JSON, nullable=True)  # Additional details about the change
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = db.relationship('User', backref='reputation_history')
    
    def __repr__(self) -> str:
        """String representation of ReputationHistory."""
        change = self.new_score - self.old_score
        return f'<ReputationHistory {self.user_id}: {change:+d} ({self.change_reason})>'
    
    @classmethod
    def log_change(cls, user_id: int, old_score: int, new_score: int, 
                   reason: str, details: dict = None):
        """Log a reputation score change.
        
        Args:
            user_id (int): User ID
            old_score (int): Previous reputation score
            new_score (int): New reputation score
            reason (str): Reason for the change
            details (dict, optional): Additional details
        """
        if old_score != new_score:  # Only log if there's actually a change
            history_entry = cls(
                user_id=user_id,
                old_score=old_score,
                new_score=new_score,
                change_reason=reason,
                change_details=details
            )
            db.session.add(history_entry)
            db.session.commit()
