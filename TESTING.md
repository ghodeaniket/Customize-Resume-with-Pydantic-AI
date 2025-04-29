# Resume Customizer Testing Guide

This guide provides steps to test the Resume Customizer API.

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
  -F "file=@tests/fixtures/test_resume.txt"

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
  -F "resume_file=@tests/fixtures/test_resume.txt" \
  -F "output_format=markdown"
```

Expected result: JSON response with optimized resume and usage statistics.

## 5. Running Unit Tests

The project includes a comprehensive test suite organized in the `tests` directory:

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/test_api/
pytest tests/test_agents/
pytest tests/test_infrastructure/
pytest tests/test_services/

# Run with coverage report
pytest --cov=resume_customizer
```

## 6. Test Structure

The test suite is organized as follows:

```
tests/
├── fixtures/              # Test data files
│   ├── test_resume.txt    # Sample resume for testing
│   └── test_job_description.txt  # Sample job description
├── agents/                # Agent tests
├── api/                   # API endpoint tests  
├── core/                  # Core functionality tests
├── services/              # Service tests
├── test_e2e.py            # End-to-end tests
└── conftest.py            # Test fixtures and configuration
```

## Notes on Expected Behavior

1. **File Types**: For testing, start with simple text files (.txt) before moving to more complex formats like PDF or DOCX.

2. **API Response**: The API returns a proper `CustomizationResponse` object with the optimized resume and usage statistics.

3. **Performance**: First-time requests may be slower due to prompt initialization and LLM API connection establishment.

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

## Architecture Documentation

For a better understanding of the system, check the architecture diagrams in the `docs` directory:

- `docs/architecture-diagram.mermaid` - Overall system architecture
- `docs/sequence-diagram.mermaid` - Interaction flow
- `docs/deployment-diagram.mermaid` - Deployment architecture
