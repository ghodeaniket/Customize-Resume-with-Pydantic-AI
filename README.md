# Resume Customizer: Pydantic AI Multi-Agent System

A professional resume customization service that uses multiple specialized AI agents to analyze and optimize resumes for specific job descriptions.

## Features

- **ProfilerAgent**: Analyzes resumes to create comprehensive professional profiles
- **ResearcherAgent**: Analyzes job descriptions to extract key requirements
- **StrategistAgent**: Optimizes resumes based on profiles and job requirements
- **Multi-format document support**: PDF, DOCX, and plain text
- **Advanced prompt management**: Versioned prompt templates for consistent agent behavior
- **Usage monitoring**: Track token consumption and performance metrics
- **Error handling and recovery**: Robust error management with detailed reporting

## Project Structure

```
resume_customizer/
├── core/                      # Core application components
├── agents/                    # Agent definitions & implementations
│   └── models/                # Shared agent models
├── api/                       # API endpoints
│   └── endpoints/             # API route handlers
├── services/                  # Business logic
├── repositories/              # Data access
├── infrastructure/            # External services
├── tests/                     # Test suite
└── main.py                    # Application entry point
```

## Setup

1. Clone the repository
2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Create a `.env` file with your OpenRouter API key:
   ```
   OPENROUTER_API_KEY=your_api_key_here
   MODEL_NAME=deepseek/deepseek-r1-distill-llama-70b
   ```

## Running the Application

Start the server:

```
python main.py
```

This will start the FastAPI application on http://localhost:8000.

For production deployment:

```
uvicorn main:app --host 0.0.0.0 --port 8000
```

## API Endpoints

### Health Check

```
GET /health
```

### Customize Resume (Text Input)

```
POST /resumes/customize
```

Request body:
```json
{
  "resume_content": "Full text content of the resume",
  "job_description": "Full text content of the job description",
  "model_name": "deepseek/deepseek-r1-distill-llama-70b",
  "output_format": "markdown",
  "max_tokens": 4000
}
```

### Customize Resume (File Upload)

```
POST /resumes/customize-upload
```

Form data:
- `resume_file`: Resume file (PDF, DOCX, or TXT)
- `job_description`: Job description text
- `model_name` (optional): AI model name
- `output_format` (optional): Output format (markdown, text, json)
- `max_tokens` (optional): Maximum token limit

## Running Tests

Run all tests:

```
pytest
```

Run specific test modules:

```
pytest tests/test_agents/test_profiler.py
pytest tests/test_infrastructure/test_prompt_manager.py
```

Run tests with coverage:

```
pytest --cov=.
```

## Configuration

Configuration is managed through environment variables and the `.env` file:

- `OPENROUTER_API_KEY`: API key for OpenRouter
- `MODEL_NAME`: Default AI model name
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

## Development

### Adding New Prompt Templates

1. Create a new template in `infrastructure/init_prompts.py`:

```python
new_prompt = PromptTemplate(
    version="1.0.0",
    template="Your prompt text here",
    description="Description of the prompt"
)
manager.add_template("agent_name", new_prompt)
```

2. Update the agent to use the template:

```python
prompt = self.prompt_manager.get_template("agent_name", "latest")
```

### Adding New Document Formats

Extend the `DocumentProcessor` class in `infrastructure/document_processor.py`:

```python
def _extract_from_new_format(self, content: bytes) -> str:
    # Implementation for extracting text from new format
    ...
    return extracted_text
```

Update the `extract_text_from_bytes` method to handle the new format.
