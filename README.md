# Resume Customizer

## Overview

The Resume Customizer is an API-based application that helps users customize their resumes for specific job descriptions. It uses AI to analyze both the resume and job description, then generates an optimized version of the resume that is tailored to the specific job.

The application uses a multi-agent architecture:
1. **Strategist Agent**: Coordinates the overall customization process
2. **Profiler Agent**: Analyzes the resume to extract skills and experience
3. **Researcher Agent**: Analyzes the job description to identify requirements

## Architecture

The application follows a layered architecture:

![Architecture Diagram](docs/architecture-diagram.mermaid)

- **API Layer**: FastAPI endpoints and middleware for HTTP interaction
- **Service Layer**: Business logic coordination
- **Agent Layer**: AI agents for specialized tasks
- **Infrastructure Layer**: Document processing, AI provider integration
- **Core Layer**: Configuration, logging, exceptions

For more detailed architecture information, see the diagrams in the `docs/` directory:
- [Architecture Diagram](docs/architecture-diagram.mermaid)
- [Sequence Diagram](docs/sequence-diagram.mermaid)
- [Deployment Diagram](docs/deployment-diagram.mermaid)

## Quick Start

### Prerequisites

- Python 3.9+ installed
- Virtual environment tool (venv or conda)
- OpenRouter API key 

### Setup and Start Server

```bash
# Clone the repository
git clone https://github.com/yourusername/resume-customizer.git
cd resume-customizer

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create a .env file (copy from example)
cp .env.example .env
# Edit .env and add your OpenRouter API key

# Start the server
python run.py
```

## Key Features

### Resume Customization

- Upload resumes in various formats (PDF, DOCX, TXT)
- Analyze job descriptions to extract key requirements
- Generate tailored resumes that emphasize relevant skills and experience
- Support multiple output formats (Markdown, Text, JSON)

### Document Processing

- Robust text extraction from PDF and DOCX files
- Content-based file type detection
- Error handling and recovery for partial failures
- Performance optimization with caching

### API Features

- Clean, RESTful API design with FastAPI
- Comprehensive error handling and validation
- Rate limiting protection
- Response caching for performance

## API Endpoints

The main endpoints are:

- **GET /health**: Check if the server is running properly
- **POST /api/v1/resumes/customize**: Customize resume with text input
- **POST /api/v1/resumes/customize-upload**: Customize resume with file upload
- **POST /api/v1/resumes/upload-test**: Test file upload and processing

For API documentation, access:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
Resume Customizer/
├── api/                    # API endpoints and middleware
├── agents/                 # AI agents for customization
│   ├── strategist.py       # Strategist agent
│   ├── profiler.py         # Profiler agent
│   ├── researcher.py       # Researcher agent
│   ├── base.py             # Base agent class
│   └── models/             # Pydantic models
├── core/                   # Core functionality
│   ├── config.py           # Configuration management
│   ├── exceptions.py       # Exception classes
│   ├── logging.py          # Logging configuration
│   └── utils/              # Utility functions
├── docs/                   # Architecture documentation
│   ├── architecture-diagram.mermaid  # Architecture diagram
│   ├── sequence-diagram.mermaid      # Sequence diagram
│   └── deployment-diagram.mermaid    # Deployment diagram
├── infrastructure/         # Infrastructure components
│   ├── document_processor.py  # Document processing
│   ├── ai_provider.py         # AI provider integration
│   ├── openrouter_client.py   # OpenRouter API client
│   ├── model_provider.py      # LLM model provider
│   └── prompt_loader.py       # Prompt template loader
├── prompts/                # Prompt templates
├── services/               # Business logic services
├── tests/                  # Tests and fixtures
│   ├── fixtures/           # Test data files
│   └── ...                 # Test modules
├── .env.example            # Example environment variables
├── main.py                 # Main application entry point
├── run.py                  # Application runner script
└── TESTING.md              # Testing documentation
```

## Configuration

Configuration is loaded from environment variables or a `.env` file. Key configuration options:

- `OPENROUTER_API_KEY`: OpenRouter API key for LLM access
- `MODEL_NAME`: Default LLM model (default: deepseek/deepseek-r1-distill-llama-70b)
- `LOG_LEVEL`: Log level (default: INFO)
- `RATE_LIMIT_PER_MINUTE`: Rate limit (default: 60)

## Testing

See [TESTING.md](TESTING.md) for detailed testing instructions and procedures.

Basic test commands:

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/test_api/
pytest tests/test_agents/

# Run with coverage report
pytest --cov=resume_customizer
```

## Deployment

The application can be deployed as a Docker container or to Kubernetes. 
See the deployment diagram for the recommended architecture:

[Deployment Diagram](docs/deployment-diagram.mermaid)

Basic Docker usage:

```bash
# Build the Docker image
docker build -t resume-customizer .

# Run the container
docker run -p 8000:8000 --env-file .env resume-customizer
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
