# Dual Authentication System Implementation

This document describes the dual authentication system that has been implemented for the Over-Under Contests application.

## Overview

The application now supports two authentication methods:

1. **Email-based One-Time Links** (for regular users)
2. **Username/Password Authentication** (for admin users)

## Features Implemented

### 1. Database Changes
- Added `password_hash` column to the `users` table
- Added password management methods to the `User` model:
  - `set_password(password)` - Hash and store password
  - `check_password(password)` - Verify password
  - `has_password()` - Check if password is set

### 2. Authentication Routes
- **Regular Login** (`/login`): Email-based authentication for all users
- **Admin Login** (`/admin/login`): Username/password authentication for admin users
- Both methods update the same session variables for seamless integration

### 3. Admin Management
- **Set Password** (`/admin/users/<id>/set-password`): Allow admins to set passwords for admin users
- Password requirements: minimum 8 characters
- Password confirmation validation

### 4. Templates
- **Regular Login** (`/templates/auth/login.html`): Updated with link to admin login
- **Admin Login** (`/templates/auth/admin_login.html`): New template for admin authentication
- **Set Password** (`/templates/admin/set_password.html`): Admin interface for password management

## How It Works

### For Regular Users
1. Visit `/login`
2. Enter email address
3. Receive one-time login link via email
4. Click link to authenticate

### For Admin Users
1. Visit `/admin/login` (or click "Admin Login" from regular login page)
2. Enter username and password
3. Authenticate directly without email

### Admin Password Management
1. Admin users can set passwords for other admin users via the admin panel
2. Navigate to Admin Panel → Users → Edit User → Set Password
3. Passwords must be at least 8 characters long

## Security Features

- Passwords are hashed using Werkzeug's secure password hashing
- Admin users can still use email authentication as a backup
- Session management remains the same for both authentication methods
- Password validation and confirmation requirements

## Testing

### Test Admin User Created
- **Username**: `admin`
- **Email**: `admin@example.com`
- **Password**: `admin123`

### Test Scenarios

1. **Regular User Email Login**:
   - Go to `/login`
   - Enter any registered user's email
   - Check email for login link

2. **Admin Username/Password Login**:
   - Go to `/admin/login`
   - Username: `admin`
   - Password: `admin123`

3. **Admin Password Management**:
   - Login as admin
   - Go to Admin Panel → Users
   - Find an admin user and click "Set Password"

## Files Modified/Created

### Models
- `app/models.py` - Added password fields and methods

### Routes
- `app/routes/auth.py` - Added admin login route and form
- `app/routes/admin.py` - Added password management functionality

### Templates
- `app/templates/auth/login.html` - Added admin login link
- `app/templates/auth/admin_login.html` - New admin login template
- `app/templates/admin/set_password.html` - New password management template

### Database
- Migration created and applied for `password_hash` column

### Utilities
- `create_admin.py` - Script to create test admin user

## Usage Instructions

1. **Start the application**:
   ```bash
   python run.py
   ```

2. **Access regular login**:
   - Navigate to `http://localhost:5000/login`

3. **Access admin login**:
   - Navigate to `http://localhost:5000/auth/admin-login`
   - Or click "Admin Login" from the regular login page

4. **Test admin authentication**:
   - Username: `admin`
   - Password: `admin123`

5. **Manage admin passwords**:
   - Login as admin
   - Navigate to Admin Panel
   - Go to Users section
   - Edit admin users to set/update passwords

## Backward Compatibility

- All existing functionality remains unchanged
- Regular users continue to use email authentication
- Admin users can use either email or password authentication
- No breaking changes to existing user accounts

## Security Considerations

- Passwords are securely hashed using Werkzeug
- Email authentication remains available as backup for admin users
- Session management is consistent across both authentication methods
- Password requirements enforce minimum security standards
