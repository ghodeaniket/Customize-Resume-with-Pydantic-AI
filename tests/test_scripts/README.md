# Test Scripts

This directory contains standalone test scripts that can be run individually to test specific functionality of the Resume Customizer application.

## Available Test Scripts

- `test_agent_initialization.py` - Tests the initialization of agents
- `test_api.py` - Tests the API endpoints
- `test_docproc.py` - Tests document processing
- `test_document_processor.py` - Tests the DocumentProcessor class
- `test_file_processing.py` - Tests file processing functionality
- `test_health_check.py` - Tests the health check endpoint
- `test_init_prompts.py` - Tests prompt initialization
- `test_integration.py` - Tests integration between components
- `test_mock_agents.py` - Tests with mock agents
- `test_openai_provider.py` - Tests OpenAI provider
- `test_openrouter.py` - Tests OpenRouter integration
- `test_pdf_extraction.py` - Tests PDF extraction
- `test_processor.py` - Tests the document processor
- `test_prompt_basic.py` - Tests basic prompt functionality
- `test_prompt_init.py` - Tests prompt initialization
- `test_prompt_loader.py` - Tests the prompt loader
- `test_text_extraction.py` - Tests text extraction

## Running Test Scripts

These scripts can be run individually:

```bash
python tests/test_scripts/test_file_processing.py
```

Or as part of the test suite:

```bash
pytest tests/test_scripts/
```

## Notes

These are standalone test scripts that may rely on environment variables or external services. They are complementary to the more structured unit tests in the main test directories.
