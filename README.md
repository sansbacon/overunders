# Over-Under Contests

A Flask web application for creating and managing over-under prediction contests. Users can create contests, make predictions, and compete on leaderboards.

## Features

- **User Authentication**: Passwordless login via email tokens
- **Contest Management**: Create, edit, and manage prediction contests
- **Entry System**: Submit predictions with over/under values
- **Leaderboards**: Track scores and rankings
- **Admin Panel**: Comprehensive administration interface
- **Email System**: Automated notifications and login emails
- **Responsive Design**: Mobile-friendly Bootstrap interface

## Tech Stack

- **Backend**: Flask (Python)
- **Database**: SQLite (development) / PostgreSQL (production)
- **Frontend**: Bootstrap 5, HTML/CSS/JavaScript
- **Email**: SendGrid API / SMTP
- **Deployment**: Heroku
- **Database Migrations**: Flask-Migrate

## Quick Start

### Prerequisites

- Python 3.8+
- pip
- Git

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/over-under-contests.git
   cd over-under-contests
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize database**
   ```bash
   flask db upgrade
   ```

6. **Create admin user**
   ```bash
   python create_admin.py
   ```

7. **Run the application**
   ```bash
   python run.py
   ```

Visit `http://localhost:5000` to access the application.

## Environment Variables

Create a `.env` file with the following variables:

```env
# Flask Configuration
SECRET_KEY=your-secret-key-here
FLASK_ENV=development

# Database
DEV_DATABASE_URL=sqlite:///over_under_dev.db

# Email Configuration (Choose one)
# Option 1: SendGrid API (Recommended)
SENDGRID_API_KEY=your-sendgrid-api-key
USE_SENDGRID_API=true
MAIL_DEFAULT_SENDER=noreply@yourdomain.com

# Option 2: SMTP
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com

# Server Configuration (for email links)
SERVER_NAME=localhost:5000
```

## Project Structure

```
over-under-contests/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── models.py            # Database models
│   ├── routes/              # Route blueprints
│   │   ├── admin.py         # Admin panel routes
│   │   ├── auth.py          # Authentication routes
│   │   ├── contests.py      # Contest management routes
│   │   └── main.py          # Main application routes
│   ├── templates/           # Jinja2 templates
│   ├── static/              # CSS, JS, images
│   └── utils/               # Utility functions
├── migrations/              # Database migrations
├── tests/                   # Test files
├── docs/                    # Documentation
├── config.py               # Configuration classes
├── run.py                  # Application entry point
├── requirements.txt        # Python dependencies
├── Procfile               # Heroku deployment config
└── .env                   # Environment variables (not in git)
```

## Key Features

### Contest Management
- Create contests with custom questions
- Set entry deadlines and scoring rules
- Lock contests to prevent further entries
- Set correct answers and calculate scores

### User System
- Passwordless authentication via email
- User profiles and contest history
- Admin and regular user roles

### Admin Panel
- User management
- Contest administration
- Email logs and monitoring
- System information and statistics

### Email System
- Login token delivery
- Contest notifications
- Comprehensive logging and monitoring
- SendGrid API integration with SMTP fallback

## API Endpoints

### Authentication
- `POST /auth/login` - Request login token
- `GET /auth/login/<token>` - Login with token
- `POST /auth/logout` - Logout user

### Contests
- `GET /contests` - List all contests
- `GET /contests/<id>` - Contest details
- `POST /contests/<id>/enter` - Submit entry
- `GET /contests/<id>/leaderboard` - View leaderboard

### Admin
- `GET /admin/dashboard` - Admin dashboard
- `GET /admin/users` - User management
- `GET /admin/contests` - Contest management
- `GET /admin/email-logs` - Email monitoring

## Database Schema

### Users
- `user_id` (Primary Key)
- `username` (Unique)
- `email` (Unique)
- `is_admin` (Boolean)
- `created_at` (Timestamp)

### Contests
- `contest_id` (Primary Key)
- `contest_name`
- `creator_id` (Foreign Key)
- `entry_deadline`
- `is_active` (Boolean)
- `questions` (JSON)
- `correct_answers` (JSON)

### Entries
- `entry_id` (Primary Key)
- `user_id` (Foreign Key)
- `contest_id` (Foreign Key)
- `answers` (JSON)
- `score` (Integer)
- `submitted_at` (Timestamp)

## Deployment

### Heroku Deployment

1. **Create Heroku app**
   ```bash
   heroku create your-app-name
   ```

2. **Add PostgreSQL**
   ```bash
   heroku addons:create heroku-postgresql:mini
   ```

3. **Set environment variables**
   ```bash
   heroku config:set FLASK_ENV=production
   heroku config:set SECRET_KEY=your-production-secret
   heroku config:set SENDGRID_API_KEY=your-sendgrid-key
   heroku config:set USE_SENDGRID_API=true
   heroku config:set MAIL_DEFAULT_SENDER=noreply@yourdomain.com
   ```

4. **Deploy**
   ```bash
   git push heroku main
   ```

5. **Create admin user**
   ```bash
   heroku run python create_admin.py
   ```

### Database Migrations

Migrations are handled automatically on Heroku via the `release` phase in `Procfile`.

For local development:
```bash
# Create migration
flask db migrate -m "Description of changes"

# Apply migration
flask db upgrade
```

## Email Configuration

### SendGrid Setup (Recommended)

1. Create SendGrid account
2. Generate API key
3. Set up domain authentication
4. Configure environment variables

### SMTP Setup (Alternative)

1. Configure SMTP server settings
2. Set up app passwords (for Gmail)
3. Configure environment variables

See `EMAIL_AUTHENTICATION_GUIDE.md` for detailed setup instructions.

## Testing

Run tests with:
```bash
python -m pytest tests/
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Security

- Environment variables for sensitive data
- CSRF protection on forms
- Input validation and sanitization
- Secure session management
- Email authentication for login

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue on GitHub
- Check the documentation in the `docs/` folder
- Review the email setup guides

## Changelog

### v1.0.0
- Initial release
- User authentication system
- Contest management
- Admin panel
- Email logging system
- Heroku deployment support
