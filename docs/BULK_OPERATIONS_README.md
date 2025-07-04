# Bulk Operations Feature

The bulk operations feature allows administrators to perform large-scale operations on the contest management system by uploading JSON files. This feature supports three main operations:

## Features

### 1. Create Contest with Questions
Create a complete contest with all questions in a single operation.

**Use Case**: Quickly set up new contests with multiple questions without manually entering each one.

**JSON Format**:
```json
{
  "contest_name": "Weather Predictions Contest",
  "description": "Predict various weather conditions for the upcoming week",
  "lock_timestamp": "2025-01-20T18:00:00",
  "is_active": true,
  "questions": [
    {
      "question_text": "Will the temperature exceed 75°F on Monday?",
      "question_order": 1
    },
    {
      "question_text": "Will it rain on Tuesday?",
      "question_order": 2
    }
  ]
}
```

### 2. Add Bulk Entries
Add multiple user entries with their answers to an existing contest.

**Use Case**: Import entries from external sources or add multiple participants at once.

**JSON Format**:
```json
{
  "contest_id": 1,
  "entries": [
    {
      "user_email": "user1@example.com",
      "answers": [
        {"question_order": 1, "answer": true},
        {"question_order": 2, "answer": false}
      ]
    },
    {
      "user_email": "user2@example.com",
      "answers": [
        {"question_order": 1, "answer": false},
        {"question_order": 2, "answer": true}
      ]
    }
  ]
}
```

### 3. Set Correct Answers
Set correct answers for all questions in a contest at once.

**Use Case**: Quickly resolve contests by setting all correct answers simultaneously.

**JSON Format**:
```json
{
  "contest_id": 1,
  "answers": [
    {"question_order": 1, "correct_answer": true},
    {"question_order": 2, "correct_answer": false}
  ]
}
```

## How to Use

### Access the Feature
1. Log in as an admin user
2. Navigate to the Admin Dashboard
3. Click on "Bulk Operations" in the Quick Actions section

### Upload Process
1. Select the operation type from the dropdown
2. Choose your JSON file
3. Click "Process File"
4. Review the results and any error messages

### Download Templates
- Click on the template download buttons to get properly formatted JSON files
- Modify the templates with your actual data
- Upload the modified files

## Validation and Safety

### JSON Validation
- All JSON files are validated against strict schemas before processing
- Detailed error messages show exactly what needs to be fixed
- Line-by-line validation for complex structures

### Data Integrity
- All operations use database transactions
- If any error occurs, all changes are rolled back
- No partial data corruption possible

### User Validation
- For bulk entries, all user emails must exist in the system
- Contest IDs are validated before processing
- Duplicate entries are automatically skipped

## Error Handling

### Common Validation Errors
- **Missing required fields**: All required fields must be present
- **Invalid data types**: Strings, integers, and booleans must be correct types
- **User not found**: User emails must exist in the system
- **Contest not found**: Contest IDs must reference existing contests
- **Invalid timestamps**: Dates must be in ISO format (YYYY-MM-DDTHH:MM:SS)

### Processing Errors
- Database connection issues
- Constraint violations
- Unexpected server errors

All errors are displayed with detailed messages to help you fix the issues.

## Technical Implementation

### Backend Components
- **Form Validation**: Flask-WTF forms with file upload validation
- **JSON Schema Validation**: Custom validation functions for each operation type
- **Database Transactions**: SQLAlchemy transactions ensure data consistency
- **Error Reporting**: Comprehensive error collection and reporting

### Frontend Components
- **File Upload Interface**: Drag-and-drop file upload with validation
- **Template Downloads**: Pre-formatted JSON templates for each operation
- **Dynamic Help Text**: Context-sensitive help based on selected operation
- **Progress Feedback**: Real-time validation and processing feedback

### Security Features
- **Admin-only Access**: All bulk operations require admin authentication
- **File Type Validation**: Only JSON files are accepted
- **Input Sanitization**: All input data is validated and sanitized
- **Transaction Safety**: Database rollback on any errors

## Sample Files

The following sample files are included in the project root:

- `sample_contest.json` - Example contest creation file
- `sample_entries.json` - Example bulk entries file  
- `sample_answers.json` - Example answers setting file

## API Endpoints

### Main Routes
- `GET /admin/bulk-operations` - Display the bulk operations page
- `POST /admin/bulk-operations` - Process uploaded JSON files
- `GET /admin/bulk-operations/template/<operation_type>` - Download JSON templates

### Helper Functions
- `validate_contest_json()` - Validate contest creation data
- `validate_entries_json()` - Validate bulk entries data
- `validate_answers_json()` - Validate answers setting data
- `process_contest_creation()` - Create contest and questions
- `process_bulk_entries()` - Add entries and answers
- `process_bulk_answers()` - Set correct answers

## Performance Considerations

### Batch Processing
- Operations are processed in batches for better performance
- Database connections are managed efficiently
- Memory usage is optimized for large files

### Limits
- Maximum 50 questions per contest
- Maximum 100 entries per bulk upload
- JSON file size limit enforced by Flask

### Optimization
- Single database transaction per operation
- Bulk inserts where possible
- Efficient query patterns

## Future Enhancements

### Potential Improvements
- **Progress Bars**: Real-time progress indicators for large uploads
- **Async Processing**: Background processing for very large files
- **Export Functionality**: Export existing data to JSON format
- **Validation Preview**: Preview validation results before processing
- **Batch Templates**: Generate templates based on existing contests

### Integration Options
- **API Endpoints**: REST API for programmatic access
- **Webhook Support**: Notifications when operations complete
- **Audit Logging**: Detailed logs of all bulk operations
- **Role-based Access**: Different permission levels for different operations

## Troubleshooting

### Common Issues
1. **File Upload Fails**: Check file size and format
2. **Validation Errors**: Review JSON syntax and required fields
3. **User Not Found**: Ensure all user emails exist in the system
4. **Permission Denied**: Verify admin user privileges

### Debug Steps
1. Download and examine template files
2. Validate JSON syntax using online tools
3. Check server logs for detailed error messages
4. Verify database connectivity and permissions

## Support

For technical support or feature requests related to bulk operations:
1. Check the validation error messages first
2. Review the sample JSON files
3. Consult the admin dashboard for system status
4. Contact system administrators for database issues
