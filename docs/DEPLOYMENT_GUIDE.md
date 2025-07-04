# Heroku Deployment Guide

This guide explains how the Over-Under Contests application is deployed to Heroku and how database migrations are handled automatically.

## How Database Creation and Migrations Work on Heroku

### Initial Deployment

When you first deploy the app to Heroku from GitHub:

1. **Heroku Postgres Add-on**: Heroku automatically provisions a PostgreSQL database when you add the Heroku Postgres add-on
2. **Database URL**: Heroku sets the `DATABASE_URL` environment variable automatically
3. **Release Phase**: The `release: flask db upgrade` command in the `Procfile` runs automatically
4. **Database Initialization**: This creates all tables and applies all existing migrations

### Subsequent Deployments (Future Commits)

When you push new commits to GitHub that trigger a Heroku deployment:

1. **Code Update**: Heroku pulls the latest code from GitHub
2. **Build Phase**: Dependencies are installed from `requirements.txt`
3. **Release Phase**: `flask db upgrade` runs automatically before the app starts
4. **Migration Application**: Any new migration files are applied to the database
5. **App Restart**: The app starts with the updated database schema

## Deployment Configuration Files

### 1. Procfile
```
web: gunicorn run:app
release: flask db upgrade
```

- **web**: Starts the application using Gunicorn
- **release**: Runs database migrations before each deployment

### 2. Config.py - Production Settings
```python
class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    
    # Handle Heroku postgres URL format
    if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith('postgres://'):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace('postgres://', 'postgresql://', 1)
```

- Automatically uses Heroku's `DATABASE_URL`
- Handles the postgres:// to postgresql:// URL format change

### 3. Requirements.txt
Contains all Python dependencies including:
- Flask and extensions
- SQLAlchemy and Flask-Migrate
- Gunicorn (WSGI server)
- psycopg2-binary (PostgreSQL adapter)

## Heroku Setup Steps

### Initial Setup (One-time)

1. **Create Heroku App**:
   ```bash
   heroku create your-app-name
   ```

2. **Add PostgreSQL Database**:
   ```bash
   heroku addons:create heroku-postgresql:mini
   ```

3. **Set Environment Variables**:
   ```bash
   heroku config:set FLASK_ENV=production
   heroku config:set SECRET_KEY=your-secret-key
   heroku config:set SENDGRID_API_KEY=your-sendgrid-key
   heroku config:set USE_SENDGRID_API=true
   heroku config:set MAIL_DEFAULT_SENDER=your-email@domain.com
   ```

4. **Connect to GitHub**:
   - Go to Heroku Dashboard → Your App → Deploy
   - Connect to GitHub repository
   - Enable automatic deploys from main branch

### Environment Variables Required

Set these in Heroku Dashboard → Settings → Config Vars:

```
DATABASE_URL=postgres://... (automatically set by Heroku)
FLASK_ENV=production
SECRET_KEY=your-production-secret-key
SENDGRID_API_KEY=your-sendgrid-api-key
USE_SENDGRID_API=true
MAIL_DEFAULT_SENDER=noreply@yourdomain.com
```

## Migration Workflow

### Creating New Migrations (Development)

1. **Make Model Changes**: Modify models in `app/models.py`

2. **Generate Migration**:
   ```bash
   flask db migrate -m "Description of changes"
   ```

3. **Review Migration**: Check the generated file in `migrations/versions/`

4. **Test Locally**:
   ```bash
   flask db upgrade
   ```

5. **Commit and Push**:
   ```bash
   git add .
   git commit -m "Add new migration: description"
   git push origin main
   ```

### Automatic Deployment Process

When you push to GitHub:

1. **GitHub → Heroku**: Automatic deployment triggered
2. **Build**: Heroku installs dependencies
3. **Release**: `flask db upgrade` runs automatically
4. **Deploy**: App restarts with new schema

## Database Management Commands

### View Migration Status
```bash
heroku run flask db current
```

### View Migration History
```bash
heroku run flask db history
```

### Manual Migration (if needed)
```bash
heroku run flask db upgrade
```

### Access Database Console
```bash
heroku pg:psql
```

### Database Backup
```bash
heroku pg:backups:capture
heroku pg:backups:download
```

## Troubleshooting

### Migration Failures

If a migration fails during deployment:

1. **Check Logs**:
   ```bash
   heroku logs --tail
   ```

2. **Manual Migration**:
   ```bash
   heroku run flask db upgrade
   ```

3. **Rollback if Needed**:
   ```bash
   heroku run flask db downgrade
   ```

### Common Issues

1. **Migration Conflicts**: Resolve in development, create new migration
2. **Data Loss**: Always backup before major schema changes
3. **Timeout**: Large migrations may timeout, consider data migration scripts

## Best Practices

### Development Workflow

1. **Always Test Locally**: Run migrations in development first
2. **Review Generated Migrations**: Ensure they're correct before committing
3. **Backup Production**: Before major changes
4. **Small Incremental Changes**: Easier to debug and rollback

### Production Safety

1. **Backup Before Deployment**: Especially for schema changes
2. **Monitor Deployment**: Watch logs during deployment
3. **Test After Deployment**: Verify functionality works
4. **Rollback Plan**: Know how to revert if needed

## Monitoring

### Application Logs
```bash
heroku logs --tail
```

### Database Metrics
- Heroku Dashboard → Resources → Heroku Postgres
- Monitor connections, cache hit ratio, etc.

### Email Logs
- Use the admin panel at `/admin/email-logs`
- Monitor email delivery success rates

## Security Considerations

1. **Environment Variables**: Never commit secrets to Git
2. **Database Access**: Limit who has production database access
3. **Admin Accounts**: Create admin users carefully
4. **SSL**: Heroku provides SSL automatically
5. **Regular Updates**: Keep dependencies updated

## Summary

The deployment process is fully automated:

1. **Push to GitHub** → Triggers Heroku deployment
2. **Heroku builds** → Installs dependencies
3. **Release phase** → Runs `flask db upgrade` automatically
4. **App starts** → With updated database schema

This ensures that:
- Database schema is always up-to-date
- Migrations are applied consistently
- No manual intervention required
- Zero-downtime deployments (for most changes)

The key is that the `release: flask db upgrade` command in the Procfile ensures migrations run automatically before each deployment, keeping your database schema synchronized with your code changes.
