# Debugging Auto-Generation Feature

This guide provides comprehensive information for developers on how to debug issues with the AI contest auto-generation feature.

## Client-Side Debugging

### Browser Console Logs

When an error occurs during preview generation, detailed debugging information is logged to the browser console:

1. **Open Browser Developer Tools**: Press F12 or right-click and select "Inspect"
2. **Navigate to Console Tab**: Look for error messages with the 🔍 icon
3. **Expand Error Groups**: Click on the grouped error logs to see detailed information

#### Error Log Structure

```javascript
🔍 Preview Generation Error Details
├── Error object: [Full error object with all properties]
├── Error message: [Human-readable error message]
├── Error stack: [Stack trace showing where the error occurred]
└── Request details: [Complete request parameters sent to server]
    ├── sport: "NFL"
    ├── question_count: 5
    ├── week_number: null
    ├── season_year: null
    └── url: "/contests/preview-generation"
```

### Common Client-Side Issues

1. **Network Errors**: Check if the server is running and accessible
2. **CSRF Token Issues**: Verify the CSRF token is being sent correctly
3. **Invalid Input Data**: Check if form validation is working properly
4. **JSON Parsing Errors**: Look for malformed JSON responses

## Server-Side Debugging

### Application Logs

The server logs detailed error information for debugging purposes:

#### Log Locations

- **Development**: Console output where you run `python run.py`
- **Production**: Check your application server logs (e.g., Heroku logs, Docker logs)

#### Log Format

```
ERROR:app.routes.contests:Contest generation error: [Error message]
ERROR:app.routes.contests:Request data: {'sport': 'NFL', 'question_count': 5, ...}
ERROR:app.routes.contests:Traceback: [Full Python stack trace]
```

### Accessing Logs

#### Development Environment
```bash
# Run the application and watch console output
python run.py

# Or use logging to file
python run.py 2>&1 | tee app.log
```

#### Production Environment
```bash
# Heroku
heroku logs --tail --app your-app-name

# Docker
docker logs container-name --follow

# Standard server
tail -f /var/log/your-app/error.log
```

### Common Server-Side Issues

1. **AI Service Errors**: Check if the AI generation service is working
2. **Database Connection Issues**: Verify database connectivity
3. **Missing Environment Variables**: Check if required API keys are set
4. **Rate Limiting**: Verify if rate limits are being exceeded

## Debugging Workflow

### Step 1: Reproduce the Issue

1. Open browser developer tools (F12)
2. Navigate to the auto-generate page
3. Fill out the form with the problematic parameters
4. Click "Preview Questions"
5. Observe both browser console and server logs

### Step 2: Analyze Client-Side Logs

Look for the error group in the browser console:

```javascript
🔍 Preview Generation Error Details
```

Check:
- **Error message**: What went wrong?
- **Request details**: Were the parameters sent correctly?
- **Error stack**: Where in the JavaScript did the error occur?

### Step 3: Analyze Server-Side Logs

Look for corresponding server logs:

```
ERROR:app.routes.contests:Contest generation error: ...
```

Check:
- **Error type**: `ContestGenerationError` vs `Exception`
- **Request data**: Did the server receive the correct parameters?
- **Stack trace**: Where in the Python code did the error occur?

### Step 4: Common Debugging Scenarios

#### Scenario 1: 500 Internal Server Error

**Client Console Shows:**
```
Error message: HTTP 500: Internal Server Error
```

**Server Logs Show:**
```
ERROR:app.routes.contests:Unexpected error in preview_generation: [specific error]
```

**Action**: Check the server stack trace for the root cause

#### Scenario 2: AI Service Error

**Client Console Shows:**
```
Error message: AI service error: Failed to generate questions
```

**Server Logs Show:**
```
ERROR:app.routes.contests:Contest generation error: API key not configured
```

**Action**: Check AI service configuration and API keys

#### Scenario 3: Network Connection Error

**Client Console Shows:**
```
Error message: Network connection failed. Please check your internet connection and try again.
```

**Server Logs Show:**
```
No corresponding server logs (request never reached server)
```

**Action**: Check network connectivity and server status

## Advanced Debugging

### Enable Debug Mode

Add to your environment or config:

```python
# config.py
DEBUG = True
LOGGING_LEVEL = 'DEBUG'
```

### Custom Logging

Add temporary debug logging to specific functions:

```python
import logging
logger = logging.getLogger(__name__)

def preview_generation():
    logger.debug(f"Received request data: {request.get_json()}")
    # ... rest of function
```

### Database Query Debugging

Enable SQL query logging:

```python
# In your Flask app configuration
app.config['SQLALCHEMY_ECHO'] = True
```

### AI Service Debugging

Check the AI generation module:

```python
# app/utils/ai_generation.py
def generate_nfl_contest(week_number, season_year, question_count):
    logger.debug(f"Generating NFL contest: week={week_number}, year={season_year}, count={question_count}")
    # ... rest of function
```

## Error Categories

### 1. User Input Errors (400 Bad Request)
- Invalid question count
- Invalid week number
- Invalid season year
- Missing required parameters

### 2. AI Service Errors (400 Bad Request)
- API key not configured
- AI service unavailable
- Rate limits exceeded
- Invalid AI service response

### 3. Server Errors (500 Internal Server Error)
- Database connection issues
- Unexpected exceptions
- Configuration problems
- Code bugs

### 4. Network Errors (Client-side)
- Server unreachable
- Timeout errors
- DNS resolution issues
- Firewall blocking

## Monitoring and Alerting

### Set Up Log Monitoring

1. **Use log aggregation tools** (e.g., ELK stack, Splunk)
2. **Set up alerts** for error patterns
3. **Monitor error rates** and response times
4. **Track user experience** metrics

### Key Metrics to Monitor

- Error rate for preview generation
- Average response time
- AI service availability
- User abandonment rate

## Troubleshooting Checklist

### Before Debugging
- [ ] Verify the application is running
- [ ] Check if the issue is reproducible
- [ ] Gather user-reported error details
- [ ] Check recent deployments or changes

### During Debugging
- [ ] Open browser developer tools
- [ ] Monitor server logs in real-time
- [ ] Test with different input parameters
- [ ] Check network connectivity
- [ ] Verify AI service status

### After Fixing
- [ ] Test the fix thoroughly
- [ ] Update documentation if needed
- [ ] Monitor for recurring issues
- [ ] Consider adding preventive measures

## Getting Help

### Internal Resources
1. Check this debugging guide
2. Review application logs
3. Test in development environment
4. Check recent code changes

### External Resources
1. Flask documentation
2. AI service documentation
3. Browser developer tools guides
4. Stack Overflow for specific errors

### Escalation Path
1. Try basic troubleshooting steps
2. Gather detailed error information
3. Check with team members
4. Contact AI service support if needed
5. Consider rollback if critical issue

## Best Practices

### For Developers
1. Always check both client and server logs
2. Use descriptive error messages
3. Log sufficient context for debugging
4. Test error scenarios during development
5. Monitor production error rates

### For Users
1. Provide clear error messages
2. Offer retry mechanisms
3. Show progress indicators
4. Gracefully handle failures
5. Provide alternative options

This debugging guide should help you quickly identify and resolve issues with the auto-generation feature. Remember to always check both client-side and server-side logs for a complete picture of what's happening.
