"""Test cases for database models."""
import pytest
from datetime import datetime, timedelta
from app import create_app, db
from app.models import User, Contest, Question, ContestEntry, EntryAnswer, LoginToken


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


def test_user_creation(app):
    """Test user model creation."""
    with app.app_context():
        user = User(
            username='testuser',
            email='test@example.com',
            mobile_phone='1234567890'
        )
        db.session.add(user)
        db.session.commit()
        
        assert user.user_id is not None
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.is_admin is False
        assert user.created_at is not None


def test_contest_creation(app):
    """Test contest model creation."""
    with app.app_context():
        # Create user first
        user = User(username='creator', email='creator@example.com')
        db.session.add(user)
        db.session.commit()
        
        # Create contest
        contest = Contest(
            contest_name='Test Contest',
            description='A test contest',
            created_by_user=user.user_id,
            lock_timestamp=datetime.utcnow() + timedelta(days=1)
        )
        db.session.add(contest)
        db.session.commit()
        
        assert contest.contest_id is not None
        assert contest.contest_name == 'Test Contest'
        assert contest.is_active is True
        assert not contest.is_locked()


def test_question_creation(app):
    """Test question model creation."""
    with app.app_context():
        # Create user and contest
        user = User(username='creator', email='creator@example.com')
        db.session.add(user)
        db.session.commit()
        
        contest = Contest(
            contest_name='Test Contest',
            created_by_user=user.user_id,
            lock_timestamp=datetime.utcnow() + timedelta(days=1)
        )
        db.session.add(contest)
        db.session.commit()
        
        # Create question
        question = Question(
            contest_id=contest.contest_id,
            question_text='Will this test pass?',
            question_order=1,
            correct_answer=True
        )
        db.session.add(question)
        db.session.commit()
        
        assert question.question_id is not None
        assert question.question_text == 'Will this test pass?'
        assert question.correct_answer is True


def test_contest_entry_creation(app):
    """Test contest entry creation."""
    with app.app_context():
        # Create user and contest
        user = User(username='participant', email='participant@example.com')
        creator = User(username='creator', email='creator@example.com')
        db.session.add_all([user, creator])
        db.session.commit()
        
        contest = Contest(
            contest_name='Test Contest',
            created_by_user=creator.user_id,
            lock_timestamp=datetime.utcnow() + timedelta(days=1)
        )
        db.session.add(contest)
        db.session.commit()
        
        # Create entry
        entry = ContestEntry(
            contest_id=contest.contest_id,
            user_id=user.user_id
        )
        db.session.add(entry)
        db.session.commit()
        
        assert entry.entry_id is not None
        assert entry.contest_id == contest.contest_id
        assert entry.user_id == user.user_id


def test_login_token_creation(app):
    """Test login token creation."""
    with app.app_context():
        token = LoginToken.create_token('test@example.com')
        
        assert token.token is not None
        assert token.email == 'test@example.com'
        assert token.is_valid()
        assert not token.is_used


def test_contest_scoring(app):
    """Test contest scoring functionality."""
    with app.app_context():
        # Create users
        creator = User(username='creator', email='creator@example.com')
        participant = User(username='participant', email='participant@example.com')
        db.session.add_all([creator, participant])
        db.session.commit()
        
        # Create contest
        contest = Contest(
            contest_name='Scoring Test',
            created_by_user=creator.user_id,
            lock_timestamp=datetime.utcnow() + timedelta(days=1)
        )
        db.session.add(contest)
        db.session.commit()
        
        # Create questions
        q1 = Question(contest_id=contest.contest_id, question_text='Q1?', question_order=1, correct_answer=True)
        q2 = Question(contest_id=contest.contest_id, question_text='Q2?', question_order=2, correct_answer=False)
        db.session.add_all([q1, q2])
        db.session.commit()
        
        # Create entry
        entry = ContestEntry(contest_id=contest.contest_id, user_id=participant.user_id)
        db.session.add(entry)
        db.session.commit()
        
        # Create answers
        a1 = EntryAnswer(entry_id=entry.entry_id, question_id=q1.question_id, user_answer=True)  # Correct
        a2 = EntryAnswer(entry_id=entry.entry_id, question_id=q2.question_id, user_answer=True)  # Incorrect
        db.session.add_all([a1, a2])
        db.session.commit()
        
        # Test scoring
        score_data = entry.calculate_score()
        assert score_data['correct_answers'] == 1
        assert score_data['total_questions'] == 2
        assert score_data['percentage'] == 50.0


if __name__ == '__main__':
    pytest.main([__file__])
