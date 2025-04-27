# Resume Customizer Server

## Overview

The Resume Customizer is an API-based application that helps users customize their resumes for specific job descriptions. It uses AI to analyze both the resume and job description, then generates an optimized version of the resume that is tailored to the specific job.

Recent refactoring has improved:
1. File processing with centralized content-type detection
2. Error handling and recovery from partial failures
3. Performance optimizations with lazy loading and caching
4. Code organization following YAGNI/DRY/KISS principles

## Quick Start

### Prerequisites

- Python 3.9+ installed
- Virtual environment tool (venv or conda)
- OpenAI API key (for production use) - can use dummy key for testing

### Setup and Start Server

The easiest way to get started is to use the provided setup script:

```bash
# Make the script executable if needed
chmod +x start_server.sh

# Start the server with default settings
./start_server.sh

# Or with custom port
./start_server.sh --port 54321

# For testing without real AI interaction
./start_server.sh --test-mode
```

### Manual Setup

If you prefer to set up manually:

1. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure the environment:
```bash
python server_setup.py --debug
```

4. Start the server:
```bash
python run.py --port 8000 --reload
```

## Testing the Server

### API Documentation

The API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

For detailed information about the API endpoints, see [API_DOCUMENTATION.md](API_DOCUMENTATION.md).

### Testing File Processing

To test the refactored file processing functionality, you can:

1. Use the provided test script:
```bash
python test_file_processing.py
```

2. Manually test using cURL or Postman:
```bash
# Test file upload
curl -X POST http://localhost:8000/api/v1/resumes/upload-test -F "file=@tests/files/sample_resume.txt"

# Test file processing with customization
curl -X POST http://localhost:8000/api/v1/resumes/customize-upload \
  -F "job_description=Python developer with FastAPI experience" \
  -F "resume_file=@tests/files/sample_resume.txt" \
  -F "output_format=text"
```

3. Use the web interface if available:
   - Visit http://localhost:8000/upload.html (if frontend is implemented)

## Key Features

### File Processing Improvements

1. **Centralized File Type Detection**:
   - Uses file signatures (magic numbers) as the first detection method
   - Falls back to content analysis, extension, and request MIME type
   - More reliable type detection, especially for files with incorrect extensions

2. **Error Handling & Recovery**:
   - Detailed error messages with specific recommendations
   - Partial recovery from failures (e.g., extracting text from successful pages when some pages fail)
   - Better handling of corrupt or password-protected files

3. **Performance Optimization**:
   - Lazy loading for PyMuPDF to improve startup time
   - Caching of processed documents to avoid redundant processing
   - Incremental text extraction for large documents

4. **Improved Robustness**:
   - Better text normalization and cleaning
   - Support for more document formats
   - Content-first approach to file type detection

### API Endpoints

The main endpoints to test the refactored functionality are:

- **GET /health**: Check if the server is running properly
- **POST /api/v1/resumes/upload-test**: Simple test for file upload and detection
- **POST /api/v1/resumes/customize**: Customize resume with text input
- **POST /api/v1/resumes/customize-upload**: Customize resume with file upload

## Project Structure

```
Resume Customizer/
├── api/                    # API endpoints and middleware
├── agents/                 # AI agents for customization
├── core/                   # Core functionality
│   ├── config.py           # Configuration management
│   ├── exceptions.py       # Exception classes
│   ├── logging.py          # Logging configuration
│   └── utils/              # Utility functions
│       └── file_detection.py  # Centralized file detection
├── infrastructure/         # Infrastructure components
│   ├── document_processor.py  # Document processing logic
│   └── ai_provider.py      # AI provider integration
├── services/               # Business logic services
├── tests/                  # Test files and fixtures
│   └── files/              # Sample files for testing
├── .env.example            # Example environment variables
├── main.py                 # Main application entry point
├── run.py                  # Application runner script
├── server_setup.py         # Server setup script
├── start_server.sh         # Server startup script
├── test_file_processing.py # File processing test script
└── API_DOCUMENTATION.md    # Detailed API documentation
```

## Configuration

Configuration is loaded from environment variables or a `.env` file. See [.env.example](.env.example) for available options.

Key configuration options:

- `RESUME_CUSTOMIZER_LOG_LEVEL`: Log level (DEBUG, INFO, WARNING, ERROR)
- `RESUME_CUSTOMIZER_OPENROUTER_API_KEY`: OpenRouter API key for AI
- `RESUME_CUSTOMIZER_DEFAULT_MODEL`: Default AI model to use
- `RESUME_CUSTOMIZER_MAX_UPLOAD_SIZE`: Maximum upload size in bytes
- `RESUME_CUSTOMIZER_ALLOWED_EXTENSIONS`: Allowed file extensions

## Development & Testing

### Testing Environment

For development and testing, you can use:

```bash
# Set up test environment
python server_setup.py --debug --test-mode

# Run specific tests
python -m pytest tests/test_document_processor.py -v
```

### Logs

Logs are stored in the `logs/` directory with different files for different components:
- `app.log`: General application logs
- `error.log`: Error logs
- `file_processing.log`: File processing logs
- `performance.log`: Performance metrics in JSON format

## Troubleshooting

### Common Issues

1. **Missing API Keys**:
   - For testing, you can use dummy API keys
   - For production, set real API keys in the `.env` file

2. **File Upload Issues**:
   - Check allowed extensions and maximum file size
   - Verify the upload directory exists and is writable

3. **Server Won't Start**:
   - Check for port conflicts with other services
   - Ensure all dependencies are installed correctly

### Getting Help

If you encounter any issues, check:
- The error logs in `logs/error.log`
- The API response for specific error messages
- The server console output for startup errors

## License

This project is licensed under the MIT License - see the LICENSE file for details.
