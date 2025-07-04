"""Database models for the Over-Under Contests application."""
from datetime import datetime, timedelta
from typing import List, Optional
import secrets
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
    
    # Relationships
    questions = db.relationship('Question', backref='contest', lazy='dynamic', cascade='all, delete-orphan')
    entries = db.relationship('ContestEntry', backref='contest', lazy='dynamic', cascade='all, delete-orphan')
    
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
    contest = db.relationship('Contest', backref='invitations')
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
