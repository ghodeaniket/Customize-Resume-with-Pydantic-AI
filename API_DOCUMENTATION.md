# Resume Customizer API Documentation

## Overview

This document provides detailed information about the Resume Customizer API endpoints, particularly focusing on the refactored file processing functionality. The API allows you to upload resume files in various formats (PDF, DOCX, TXT) and customize them based on job descriptions.

The recent refactoring has improved:
1. Centralized content-type detection
2. Better error handling and recovery from partial failures
3. Performance optimizations with lazy loading and caching
4. Simplified file processing logic

## Base URL

When running locally, the base URL is:
```
http://localhost:8000
```

## Authentication

Currently, the API does not require authentication for local testing. In a production environment, authentication would be implemented using API keys.

## API Endpoints

### Health Check

#### GET /health

Checks if the API is running properly and returns system information.

**Response Example:**
```json
{
  "status": "ok",
  "api": {
    "version": "0.1.0",
    "title": "Resume Customizer API",
    "uptime_seconds": 120.5
  },
  "system": {
    "platform": "Darwin-21.6.0-x86_64-i386-64bit",
    "python_version": "3.9.13",
    "cpu_count": 8,
    "cpu_usage_percent": 12.5,
    "memory_total_mb": 16384.0,
    "memory_available_mb": 8192.0,
    "memory_used_percent": 50.0,
    "disk_total_gb": 500.0,
    "disk_free_gb": 250.0,
    "disk_used_percent": 50.0
  },
  "config": {
    "api_title": "Resume Customizer API",
    "api_description": "Customize resumes for specific job descriptions using AI agents",
    "api_version": "0.1.0",
    "environment": "development",
    "debug_mode": true
  }
}
```

### File Upload Test

#### POST /api/v1/resumes/upload-test

Test endpoint for file upload. This endpoint is particularly useful for testing the refactored file processing logic without the overhead of AI processing.

**Request:**
- Method: POST
- Content-Type: multipart/form-data
- Body:
  - `file`: The file to upload (PDF, DOCX, or TXT)

**Response Example:**
```json
{
  "data": {
    "filename": "resume.pdf",
    "content_type": "application/pdf",
    "detected_type": "application/pdf",
    "size": 125840,
    "content_sample": "Sample content from the PDF"
  },
  "metadata": {
    "headers": {
      "content-disposition": "form-data; name=\"file\"; filename=\"resume.pdf\"",
      "content-type": "application/pdf"
    },
    "cached": false
  }
}
```

### Resume Customization

#### POST /api/v1/resumes/customize

Customize a resume based on a job description by providing the resume content and job description as text.

**Request:**
- Method: POST
- Content-Type: application/json
- Body:
  ```json
  {
    "resume_content": "Your resume content here...",
    "job_description": "Job description text here...",
    "model_name": "deepseek/deepseek-r1-distill-llama-70b",
    "output_format": "markdown",
    "max_tokens": 4000
  }
  ```

**Response Example:**
```json
{
  "data": {
    "optimized_resume": {
      "content": "# John Doe\n\nSenior Software Engineer...",
      "format": "markdown",
      "sections": [
        {
          "title": "Contact Information",
          "content": "Email: john@example.com\nPhone: (123) 456-7890"
        },
        {
          "title": "Professional Summary",
          "content": "Senior Software Engineer with 8+ years of experience..."
        }
      ],
      "optimizations": [
        "Added keywords from job description",
        "Restructured experience section to highlight relevant skills"
      ],
      "keywords_included": ["Python", "FastAPI", "Docker"],
      "ats_score": 85.5,
      "improvement_areas": ["Add more quantifiable achievements"]
    },
    "usage_stats": {
      "requests": 1,
      "request_tokens": 1200,
      "response_tokens": 800,
      "total_tokens": 2000
    }
  },
  "metadata": {
    "processing_time_ms": 2500.45,
    "model_used": "deepseek/deepseek-r1-distill-llama-70b",
    "output_format": "markdown"
  }
}
```

### Resume Customization via File Upload

#### POST /api/v1/resumes/customize-upload

Customize a resume from a file upload based on a job description. This endpoint uses the refactored file processing pipeline, including:
- Improved file type detection
- Better error handling for corrupt or password-protected files
- Partial extraction recovery for documents with problematic pages

**Request:**
- Method: POST
- Content-Type: multipart/form-data
- Body:
  - `job_description`: Job description text (string)
  - `resume_file`: The resume file to upload (PDF, DOCX, or TXT)
  - `model_name`: AI model name (string, optional)
  - `output_format`: Output format (string, optional: "markdown", "text", or "json")
  - `max_tokens`: Maximum tokens (number, optional)

**Response Example:**
```json
{
  "data": {
    "optimized_resume": {
      "content": "# John Doe\n\nSenior Software Engineer...",
      "format": "markdown",
      "sections": [
        {
          "title": "Contact Information",
          "content": "Email: john@example.com\nPhone: (123) 456-7890"
        },
        {
          "title": "Professional Summary",
          "content": "Senior Software Engineer with 8+ years of experience..."
        }
      ],
      "optimizations": [
        "Added keywords from job description",
        "Restructured experience section to highlight relevant skills"
      ],
      "keywords_included": ["Python", "FastAPI", "Docker"],
      "ats_score": 85.5,
      "improvement_areas": ["Add more quantifiable achievements"]
    },
    "usage_stats": {
      "requests": 1,
      "request_tokens": 1200,
      "response_tokens": 800,
      "total_tokens": 2000
    }
  },
  "metadata": {
    "processing_time_ms": 3200.75,
    "model_used": "deepseek/deepseek-r1-distill-llama-70b",
    "file_type": "application/pdf",
    "file_size": 125840,
    "output_format": "markdown"
  }
}
```

## Testing the Refactored File Processing

### Testing Strategy

To effectively test the refactored file processing functionality:

1. **File Type Detection**: Use the `/api/v1/resumes/upload-test` endpoint with various file types, including:
   - PDF files (both normal and password-protected)
   - DOCX files
   - Plain text files
   - Files with incorrect extensions

2. **Error Handling**: Test error handling by uploading:
   - Password-protected PDFs
   - Corrupted files
   - Empty files
   - Very large files

3. **Text Extraction Validation**: Check the extracted text using the `/api/v1/resumes/customize-upload` endpoint:
   - Complex PDFs with multiple sections
   - PDFs with tables and images
   - PDFs with encoded text
   - DOCXs with complex formatting

4. **Performance**: Test performance improvements by comparing processing times:
   - Large PDF files (>5MB)
   - Multiple consecutive uploads to test caching

## Example cURL Commands

Here are some example cURL commands to test the API endpoints:

### Test Health Check
```bash
curl -X GET http://localhost:8000/health
```

### Test File Upload
```bash
curl -X POST http://localhost:8000/api/v1/resumes/upload-test \
  -F "file=@/path/to/your/resume.pdf"
```

### Test Resume Customization (Text Input)
```bash
curl -X POST http://localhost:8000/api/v1/resumes/customize \
  -H "Content-Type: application/json" \
  -d '{
    "resume_content": "Your resume content here...",
    "job_description": "Job description text here...",
    "output_format": "markdown"
  }'
```

### Test Resume Customization (File Upload)
```bash
curl -X POST http://localhost:8000/api/v1/resumes/customize-upload \
  -F "job_description=Job description text here..." \
  -F "resume_file=@/path/to/your/resume.pdf" \
  -F "output_format=markdown"
```

## Expected Error Responses

Here are some common error responses you might encounter:

### File Type Not Supported
```json
{
  "message": "Unsupported file type: application/xml",
  "details": {
    "supported_types": [
      "application/pdf",
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      "text/plain"
    ]
  }
}
```

### Password-Protected PDF
```json
{
  "message": "PDF is encrypted and cannot be processed. Please remove the password and try again.",
  "details": {
    "extraction_method": "PyPDF2",
    "error_type": "PdfReadError"
  }
}
```

### Corrupted File
```json
{
  "message": "PDF file is incomplete or corrupted. Please verify the file and try again.",
  "details": {
    "extraction_method": "PyPDF2",
    "error_type": "PdfReadError"
  }
}
```

### Empty File
```json
{
  "message": "Empty file uploaded",
  "details": {}
}
```

## Notes on Refactored Features

The recent refactoring has improved the file processing pipeline in the following ways:

1. **Centralized Content-Type Detection**: The system now uses a multi-stage approach to detect file types:
   - First checks file signatures (magic numbers)
   - Then tries to detect text content
   - Falls back to file extension and MIME type from request
   - This ensures more accurate file type detection

2. **Error Handling & Recovery**:
   - Detailed error messages with specific recommendations
   - Partial recovery from failures (e.g., extracting text from successful pages when some pages fail)
   - Better handling of corrupt or password-protected files

3. **Performance Optimizations**:
   - Lazy loading for PyMuPDF to improve startup time
   - Caching of processed documents to avoid redundant processing
   - Multiple extraction methods with fallbacks for better reliability

4. **Logging Improvements**:
   - JSON-formatted logs for better machine readability
   - Detailed context attributes in logs
   - More granular log levels for different types of events

These improvements make the Resume Customizer more robust, efficient, and user-friendly, especially when handling various file formats and potential errors.
