# Resume Customizer

A FastAPI application that uses Pydantic AI's multi-agent capabilities to create a lean, type-safe resume customization service matching a team's existing workflow (Profiler → Researcher → Strategist) while ensuring scalability for future enhancements.

## Overview

The Resume Customizer application automates the process of tailoring resumes for specific job descriptions using AI. It analyzes both the resume and job description, then generates an optimized version of the resume that highlights relevant skills and experiences.

### Core Features (Phase 1)

- Professional profile extraction from resumes
- Detailed job requirement analysis
- Strategic resume customization and optimization
- Clean, type-safe API with proper error handling
- Comprehensive logging and monitoring

## Architecture

The system is implemented as a FastAPI application with three specialized Pydantic AI agents coordinated through agent delegation patterns:

### Architecture Layers

1. **API Layer**: FastAPI endpoints that handle HTTP requests/responses
2. **Agent Layer**: Three specialized Pydantic AI agents with defined responsibilities:
   - **ProfilerAgent**: Analyzes resumes and creates comprehensive professional profiles
   - **ResearcherAgent**: Analyzes job descriptions to extract key requirements
   - **StrategistAgent**: Optimizes resumes based on profiles and job analyses
3. **Service Layer**: Business logic and coordination between agents
4. **Repository Layer**: Data access and storage management
5. **Infrastructure Layer**: External service connections (OpenRouter, document processing)

## Getting Started

### Prerequisites

- Python 3.10 or higher
- An OpenRouter API key

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/resume-customizer.git
   cd resume-customizer
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file based on `.env.example` and add your OpenRouter API key:
   ```
   RESUME_CUSTOMIZER_OPENROUTER_API_KEY=your-api-key-here
   ```

### Running the Application

1. Start the FastAPI server:
   ```
   uvicorn resume_customizer.main:app --reload
   ```

2. Access the API documentation at `http://localhost:8000/docs`

## API Endpoints

### Analyze Resume

```
POST /api/v1/resumes/analyze
```

Analyzes a resume and extracts a comprehensive professional profile.

### Analyze Job Description

```
POST /api/v1/resumes/analyze-job
```

Analyzes a job description and extracts key requirements and insights.

### Customize Resume

```
POST /api/v1/resumes/customize
```

Customizes a resume based on job requirements to maximize alignment and ATS compatibility.

## Development

### Project Structure

```
resume_customizer/
├── core/                      # Core application components
│   ├── config.py              # Configuration management
│   ├── exceptions.py          # Custom exception types
│   └── logging.py             # Logging configuration
├── agents/                    # Agent definitions & implementations
│   ├── profiler.py            # ProfilerAgent implementation
│   ├── researcher.py          # ResearcherAgent implementation
│   ├── strategist.py          # StrategistAgent implementation
│   └── models/                # Shared agent models
│       ├── profile.py         # Resume profile models
│       ├── job.py             # Job requirement models
│       └── resume.py          # Resume output models
├── api/                       # API endpoints
│   ├── endpoints/             # API route handlers
│   │   └── resumes.py         # Resume customization endpoints
│   ├── dependencies.py        # API dependencies
│   └── responses.py           # Response models
├── services/                  # Business logic
│   ├── customizer.py          # Resume customization service
│   └── document.py            # Document processing service
├── repositories/              # Data access
│   ├── base.py                # Base repository interface
│   ├── resume.py              # Resume data operations
│   └── job.py                 # Job data operations
├── infrastructure/            # External services
│   ├── ai_provider.py         # AI model provider integration
│   └── document_processor.py  # Document extraction tools
└── main.py                    # Application entry point
```

### Running Tests

```
pytest
```

## Future Enhancements (Phase 2 & 3)

- Multi-format document processing (PDF, DOCX)
- File upload capabilities
- Enhanced prompt management with version tracking
- Usage monitoring and analytics
- Agent evaluation framework
- User feedback collection

## License

This project is licensed under the MIT License - see the LICENSE file for details.
