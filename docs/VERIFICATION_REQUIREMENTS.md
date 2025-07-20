# Verification Requirements Configuration

This document describes the verification requirements system that allows administrators to control who can create contests and leagues based on user verification status.

## Overview

The verification requirements system provides configurable controls to:
- Require user verification for contest creation
- Require user verification for league creation
- Allow or restrict unverified user participation
- Set minimum verification levels for different actions

## Configuration Options

All configuration is done through environment variables in your `.env` file:

### Basic Requirements

```bash
# Require verification for contest creation (default: false)
REQUIRE_VERIFICATION_FOR_CONTESTS=false

# Require verification for league creation (default: false)
REQUIRE_VERIFICATION_FOR_LEAGUES=false

# Allow unverified users to participate in contests/leagues (default: true)
ALLOW_UNVERIFIED_PARTICIPATION=true
```

### Verification Levels

```bash
# Minimum verification level required for contest creation (default: basic)
MINIMUM_VERIFICATION_LEVEL_CONTESTS=basic

# Minimum verification level required for league creation (default: basic)
MINIMUM_VERIFICATION_LEVEL_LEAGUES=basic
```

Available verification levels (in order of hierarchy):
- `basic` - Basic verification level
- `enhanced` - Enhanced verification level
- `premium` - Premium verification level

## How It Works

### Contest Creation
When `REQUIRE_VERIFICATION_FOR_CONTESTS=true`:
1. Users attempting to create contests are checked for verification status
2. If not verified, they are redirected to request verification
3. If verified but below minimum level, they receive an appropriate error message
4. Only users meeting the verification requirements can create contests

### League Creation
When `REQUIRE_VERIFICATION_FOR_LEAGUES=true`:
1. Users attempting to create leagues are checked for verification status
2. If not verified, they are redirected to request verification
3. If verified but below minimum level, they receive an appropriate error message
4. Only users meeting the verification requirements can create leagues

### Participation
When `ALLOW_UNVERIFIED_PARTICIPATION=false`:
1. Unverified users cannot enter contests or join leagues
2. They are redirected to request verification when attempting to participate

### Duplicate Prevention
The system automatically prevents:
- Users from entering the same contest twice
- Users from joining the same league twice

## User Experience

### For Unverified Users
When verification is required but user is not verified:
- Clear error messages explain the requirement
- Users are automatically redirected to the verification request page
- They can still view public contests and leagues

### For Verified Users
When user meets verification requirements:
- Normal functionality with no restrictions
- No additional steps or barriers

### For Insufficient Verification Level
When user is verified but below minimum level:
- Clear message indicates the required level
- User can request higher verification level from admin

## Administrative Controls

### Verification Management
Administrators can:
- View all verification requests in the admin panel
- Approve/deny verification requests
- Set verification levels (basic, enhanced, premium)
- View user verification status and history

### Configuration Management
Administrators can:
- Enable/disable verification requirements via environment variables
- Set different requirements for contests vs leagues
- Adjust minimum verification levels
- Control participation permissions

## Implementation Details

### Verification Checker
The `VerificationChecker` class provides methods to:
- `can_create_contest(user_id)` - Check contest creation permissions
- `can_create_league(user_id)` - Check league creation permissions
- `can_participate_in_contest(user_id, contest_id)` - Check contest participation
- `can_join_league(user_id, league_id)` - Check league participation

### Route Protection
Routes are protected using:
- Direct verification checks in route handlers
- Automatic redirects to verification request page
- Clear error messaging for users

### Database Integration
The system integrates with:
- User verification tables
- Reputation system
- Contest and league models

## Security Considerations

### Verification Bypass Prevention
- All checks are server-side
- No client-side verification bypasses possible
- Database constraints prevent duplicate entries

### Admin Override
- System administrators can always create contests/leagues
- Admins can modify verification requirements
- Emergency access maintained for critical operations

## Troubleshooting

### Common Issues

**Users can't create contests/leagues:**
1. Check if verification requirements are enabled
2. Verify user's verification status in admin panel
3. Confirm minimum verification level settings

**Verification requests not working:**
1. Ensure verification routes are properly configured
2. Check admin panel access for processing requests
3. Verify email notifications are working

**Configuration not taking effect:**
1. Restart the application after changing environment variables
2. Check for typos in environment variable names
3. Verify configuration is loaded correctly

### Debug Information
Enable debug logging to see:
- Verification check results
- Configuration values being used
- User verification status details

## Migration Guide

### Enabling Verification Requirements

1. **Backup your database** before making changes
2. Set environment variables in `.env` file
3. Restart the application
4. Test with a non-admin user account
5. Verify admin panel functionality

### Recommended Rollout

1. **Phase 1**: Enable with `ALLOW_UNVERIFIED_PARTICIPATION=true`
2. **Phase 2**: Notify users about upcoming verification requirements
3. **Phase 3**: Process verification requests
4. **Phase 4**: Enable stricter requirements as needed

## API Reference

### VerificationChecker Methods

```python
# Check if user can create contests
can_create, reason = VerificationChecker.can_create_contest(user_id)

# Check if user can create leagues
can_create, reason = VerificationChecker.can_create_league(user_id)

# Check if user can participate in contests
can_participate, reason = VerificationChecker.can_participate_in_contest(user_id, contest_id)

# Check if user can join leagues
can_join, reason = VerificationChecker.can_join_league(user_id, league_id)

# Get verification requirements info
requirements = VerificationChecker.get_verification_requirements_info()

# Get user verification status
status = VerificationChecker.get_user_verification_status(user_id)
```

### Configuration Helper

```python
# Get current verification requirements
from app.utils.verification_checks import VerificationChecker
requirements = VerificationChecker.get_verification_requirements_info()
```

## Best Practices

### For Administrators
1. Start with lenient settings and gradually increase requirements
2. Communicate changes to users in advance
3. Process verification requests promptly
4. Monitor system logs for issues

### For Developers
1. Always check verification status before allowing actions
2. Provide clear error messages to users
3. Test with different verification levels
4. Handle edge cases gracefully

### For Users
1. Request verification early if planning to create content
2. Provide accurate information in verification requests
3. Contact administrators if experiencing issues
4. Understand that verification helps maintain platform quality

## Support

For technical support or questions about verification requirements:
1. Check the admin panel for verification status
2. Review application logs for error details
3. Contact system administrators
4. Refer to this documentation for configuration help
