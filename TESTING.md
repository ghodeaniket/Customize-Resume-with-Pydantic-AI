# Resume Customizer Testing Guide

This guide provides steps to test the Resume Customizer API after the recent fixes.

## Prerequisites

- Python 3.9+ installed
- Virtual environment activated
- All dependencies installed via `pip install -r requirements.txt`
- Server running (via `./start_server.sh` or `python run.py`)

## 1. Verify Server Health

```bash
# Using curl
curl http://localhost:8000/health

# Or visit in browser
# http://localhost:8000/health
```

Expected result: JSON response with status "ok" and system information.

## 2. Test File Upload

```bash
# Using curl
curl -X POST http://localhost:8000/api/v1/resumes/upload-test \
  -F "file=@tests/files/sample_resume.txt"

# Or use a tool like Postman to POST to:
# http://localhost:8000/api/v1/resumes/upload-test
```

Expected result: JSON response with file information, including detected type and content sample.

## 3. Test Resume Customization with Text Input

```bash
# Using curl
curl -X POST http://localhost:8000/api/v1/resumes/customize \
  -H "Content-Type: application/json" \
  -d '{
    "resume_content": "Your resume content here...",
    "job_description": "This is a job description for a Python developer position that requires 5+ years of experience with FastAPI...",
    "output_format": "markdown"
  }'
```

Expected result: JSON response with optimized resume and usage statistics.

## 4. Test Resume Customization with File Upload

```bash
# Using curl
curl -X POST http://localhost:8000/api/v1/resumes/customize-upload \
  -F "job_description=This is a job description for a Python developer position that requires 5+ years of experience with FastAPI..." \
  -F "resume_file=@tests/files/sample_resume.txt" \
  -F "output_format=markdown"
```

Expected result: JSON response with optimized resume and usage statistics.

## 5. Check Logs for Known Issues

After running tests, check the logs for expected warnings:

```bash
# Check main log file
cat logs/app.log

# Check file processing log
cat logs/file_processing.log
```

Expected warnings:
- "No templates found for agent profiler"
- "No templates found for agent researcher"
- "No templates found for agent strategist"

These warnings are expected and don't affect functionality because fallback prompts are in place.

## 6. Run Automated Tests

```bash
# Run the file processing test
python test_file_processing.py
```

Expected result: Successful test run with both file upload and extraction tests passing.

## Notes on Expected Behavior

1. **Template Warnings**: You will see warnings about missing templates in the logs. This is expected and doesn't affect functionality.

2. **Job Description Format**: When testing, make sure to provide actual text for the job description, not URLs.

3. **File Types**: For testing, start with simple text files (.txt) before moving to more complex formats like PDF or DOCX.

4. **API Response**: The API should now return a proper `CustomizationResponse` object without nesting it in a data/metadata structure.

## Troubleshooting

If you encounter issues:

1. **500 Internal Server Error**:
   - Check the error logs: `cat logs/error.log`
   - Look for validation errors or type mismatches

2. **File Processing Failures**:
   - Check the file processing logs: `cat logs/file_processing.log`
   - Verify the file format is supported

3. **Agent Errors**:
   - Make sure your job description is provided as plain text
   - Check that the API key in the .env file is valid

4. **Server Won't Start**:
   - Verify Python version: `python --version` (should be 3.9+)
   - Check for missing dependencies: `pip install -r requirements.txt`
   - Ensure port 8000 is not in use by another process
