"""Main application runner for Over-Under Contests."""
import os
from app import create_app, db
from app.models import User, Contest, Question, ContestEntry, EntryAnswer, LoginToken

app = create_app()


@app.shell_context_processor
def make_shell_context():
    """Make database models available in Flask shell.
    
    Returns:
        dict: Dictionary of models for shell context
    """
    return {
        'db': db,
        'User': User,
        'Contest': Contest,
        'Question': Question,
        'ContestEntry': ContestEntry,
        'EntryAnswer': EntryAnswer,
        'LoginToken': LoginToken
    }


@app.cli.command()
def init_db():
    """Initialize the database with tables."""
    db.create_all()
    print("Database tables created successfully!")


@app.cli.command()
def create_admin():
    """Create an admin user."""
    username = input("Enter admin username: ")
    email = input("Enter admin email: ")
    
    # Check if user already exists
    if User.query.filter_by(username=username).first():
        print("Username already exists!")
        return
    
    if User.query.filter_by(email=email).first():
        print("Email already exists!")
        return
    
    # Create admin user
    admin_user = User(
        username=username,
        email=email.lower(),
        is_admin=True
    )
    
    db.session.add(admin_user)
    db.session.commit()
    
    print(f"Admin user '{username}' created successfully!")
    print(f"Use the login page with email '{email}' to receive a login link.")


@app.cli.command()
def seed_data():
    """Seed the database with sample data for testing."""
    from datetime import datetime, timedelta
    
    # Create sample users
    users_data = [
        {'username': 'john_doe', 'email': 'john@example.com'},
        {'username': 'jane_smith', 'email': 'jane@example.com'},
        {'username': 'bob_wilson', 'email': 'bob@example.com'},
    ]
    
    users = []
    for user_data in users_data:
        if not User.query.filter_by(email=user_data['email']).first():
            user = User(
                username=user_data['username'],
                email=user_data['email']
            )
            db.session.add(user)
            users.append(user)
    
    db.session.commit()
    
    # Create sample contest
    if not Contest.query.filter_by(contest_name='Sample Sports Contest').first():
        contest = Contest(
            contest_name='Sample Sports Contest',
            description='A sample contest about sports predictions',
            created_by_user=users[0].user_id if users else 1,
            lock_timestamp=datetime.utcnow() + timedelta(days=7)
        )
        
        db.session.add(contest)
        db.session.flush()
        
        # Add sample questions
        questions_data = [
            {'text': 'Will the home team win the next game?', 'answer': True},
            {'text': 'Will there be more than 3 goals scored?', 'answer': False},
            {'text': 'Will the game go to overtime?', 'answer': False},
            {'text': 'Will the visiting team score first?', 'answer': True},
        ]
        
        for i, q_data in enumerate(questions_data):
            question = Question(
                contest_id=contest.contest_id,
                question_text=q_data['text'],
                question_order=i + 1,
                correct_answer=q_data['answer']
            )
            db.session.add(question)
        
        db.session.commit()
        print("Sample data created successfully!")
    else:
        print("Sample data already exists!")


if __name__ == '__main__':
    app.run(debug=True)
