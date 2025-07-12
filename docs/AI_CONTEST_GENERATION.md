# AI-Powered Contest Generation

This document describes the AI-powered auto-generation feature for creating NFL contests automatically using OpenAI's GPT models.

## Overview

The auto-generation feature allows users to create NFL prediction contests automatically by leveraging artificial intelligence to generate realistic questions based on typical betting lines and scenarios. This eliminates the manual effort of creating questions while ensuring high-quality, engaging content.

## Features

- **Automatic Question Generation**: Creates 1-10 customizable yes/no questions about NFL games
- **Realistic Betting Scenarios**: Generates questions based on typical point spreads and over/under totals
- **Smart Scheduling**: Automatically sets appropriate contest lock times
- **Preview Functionality**: Preview generated questions before creating the contest
- **Flexible Parameters**: Support for different NFL weeks and seasons
- **Customizable Question Count**: Choose between 1 and 10 questions (default: 5)
- **Rate Limiting**: Non-admin users limited to 3 AI-generated contests per day

## How It Works

### 1. User Input
Users provide:
- **Sport**: Currently supports NFL (more sports planned)
- **Question Count**: Number of questions to generate (1-10, default: 5)
- **Week Number**: NFL week 1-18 (optional - defaults to current week)
- **Season Year**: NFL season year (optional - defaults to current season)
- **Timezone**: For setting the contest lock time

### 2. AI Processing
The system:
- Constructs a detailed prompt for the AI model
- Sends the request to OpenAI's GPT-3.5-turbo model
- Receives structured JSON response with questions
- Validates the response format and content

### 3. Contest Creation
The system:
- Generates appropriate contest name and description
- Sets smart lock time (typically Thursday evening for NFL)
- Creates the contest with generated questions
- Makes it immediately available for participants

## Generated Question Types

### Point Spread Questions
Example: "Will the Chiefs win by more than 3 points against the Chargers?"
- **line_type**: "spread"
- **team_favored**: The favored team
- **line_value**: Point spread value
- **direction**: "cover"

### Over/Under Questions
Example: "Will the total points in the Cowboys vs Eagles game exceed 46.5?"
- **line_type**: "over_under"
- **line_value**: Total points line
- **direction**: "over" or "under"

## API Integration

### OpenAI Configuration

Add to your `.env` file:
```env
OPENAI_API_KEY=sk-your-openai-api-key-here
```

### Request Format

The system sends a structured prompt to OpenAI requesting:
- Specified number of yes/no questions (1-10)
- Mix of spread and over/under questions
- Realistic team matchups for the specified week
- Clear, unambiguous question text
- Structured JSON response

### Response Validation

The system validates that each question includes:
- `game`: Team matchup
- `question`: Question text
- `line_type`: "spread" or "over_under"
- `line_value`: Numeric betting line
- `direction`: "over", "under", or "cover"
- `team_favored`: (for spread questions only)

## Usage

### Via Web Interface

1. Navigate to the contests page
2. Click "Auto-Generate" button
3. Select sport (NFL)
4. Optionally specify week number and season year
5. Choose timezone
6. Click "Preview Questions" to see generated content
7. Click "Generate Contest" to create the contest

### Preview Feature

The preview functionality allows users to:
- See generated questions before committing
- Review contest details (name, description, lock time)
- Verify question quality and relevance
- Make adjustments to parameters if needed

## Smart Scheduling

### NFL Lock Times
- Contests automatically lock on Thursday at 8 PM ET (1 AM UTC Friday)
- Accounts for Thursday Night Football start times
- Prevents entries after games begin

### Timezone Handling
- Lock times displayed in user's selected timezone
- Stored in UTC in the database
- Properly converted for display across different timezones

## Error Handling

### API Errors
- OpenAI API failures are caught and displayed to users
- Fallback error messages for network issues
- Logging of all API interactions for debugging

### Validation Errors
- Malformed JSON responses are detected and handled
- Missing required fields trigger appropriate error messages
- Invalid data types are caught and reported

### User-Friendly Messages
- Clear error descriptions for users
- Suggestions for resolving common issues
- Graceful degradation when AI service is unavailable

## Technical Implementation

### Core Components

1. **AI Generation Module** (`app/utils/ai_generation.py`)
   - `generate_nfl_contest()`: Main generation function
   - `generate_contest_name_and_description()`: Creates contest metadata
   - `get_suggested_lock_time()`: Calculates optimal lock time

2. **Routes** (`app/routes/contests.py`)
   - `/auto-generate`: Main generation form and processing
   - `/preview-generation`: AJAX endpoint for previewing questions

3. **Templates** (`app/templates/contests/auto_generate.html`)
   - User interface for auto-generation
   - JavaScript for preview functionality
   - Form validation and submission handling

### Database Integration

Generated contests are stored using the same models as manually created contests:
- `Contest`: Main contest record
- `Question`: Individual questions with order
- Standard relationships and constraints apply

## Configuration

### Required Environment Variables
```env
OPENAI_API_KEY=sk-your-openai-api-key-here
```

### Optional Configuration
- Model selection (currently hardcoded to gpt-3.5-turbo)
- Temperature and token limits
- Prompt customization

## Limitations and Considerations

### Current Limitations
- Only supports NFL contests
- Requires OpenAI API access
- Limited to 1-10 questions per contest
- English language only

### Future Enhancements
- Support for other sports (NBA, MLB, etc.)
- Higher question count limits
- Multiple language support
- Integration with real-time betting data
- Advanced prompt engineering

### Cost Considerations
- Each generation uses OpenAI API tokens
- Typical cost: $0.01-0.02 per contest generation
- Preview requests also consume tokens
- Consider rate limiting for high-traffic scenarios

## Troubleshooting

### Common Issues

1. **"OpenAI API key not configured"**
   - Ensure `OPENAI_API_KEY` is set in environment variables
   - Verify the API key is valid and has sufficient credits

2. **"Failed to parse AI response"**
   - Usually indicates malformed JSON from OpenAI
   - Check OpenAI service status
   - Review prompt formatting

3. **"AI service error"**
   - Network connectivity issues
   - OpenAI API rate limits exceeded
   - Invalid API key or insufficient credits

### Debugging

Enable detailed logging by setting log level to DEBUG:
```python
import logging
logging.getLogger('app.utils.ai_generation').setLevel(logging.DEBUG)
```

### Monitoring

- All generation attempts are logged
- API response times and errors are tracked
- User feedback can help identify quality issues

## Security Considerations

### API Key Protection
- Store API key in environment variables only
- Never commit API keys to version control
- Use different keys for development and production

### Input Validation
- Validate user inputs before sending to AI
- Sanitize generated content before display
- Implement rate limiting to prevent abuse

### Content Filtering
- Review generated questions for appropriateness
- Implement content filters if needed
- Monitor for potential bias in generated content

### Rate Limiting
- Non-admin users are limited to 3 AI-generated contests per day
- Admin users have unlimited AI contest generation
- Daily limits reset at midnight UTC
- Users can see their remaining daily allowance on the generation form

## Best Practices

### For Developers
- Always validate AI responses before using
- Implement proper error handling and fallbacks
- Log all API interactions for debugging
- Test with various input parameters

### For Users
- Preview questions before creating contests
- Verify generated content makes sense
- Adjust parameters if questions seem off
- Report any quality issues for improvement

## Support and Feedback

For issues or suggestions related to the AI generation feature:
- Create GitHub issues with "AI Generation" label
- Include error messages and reproduction steps
- Provide feedback on question quality
- Suggest improvements for prompts or functionality
