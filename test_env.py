#!/usr/bin/env python3
"""Test script to check if environment variables are loaded correctly."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
dotenv_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path)

# Check environment variables
openai_key = os.environ.get('OPENAI_API_KEY')
openrouter_key = os.environ.get('RESUME_CUSTOMIZER_OPENROUTER_API_KEY')
project_name = os.environ.get('RESUME_CUSTOMIZER_PROJECT_NAME')

# Print status without revealing keys
print(f"OPENAI_API_KEY: {'✓ Set' if openai_key else '✗ Not set'}")
print(f"RESUME_CUSTOMIZER_OPENROUTER_API_KEY: {'✓ Set' if openrouter_key else '✗ Not set'}")
print(f"RESUME_CUSTOMIZER_PROJECT_NAME: {project_name}")
