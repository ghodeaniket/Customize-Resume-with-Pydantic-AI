#!/usr/bin/env python3
"""
Run script for the Resume Customizer API.

This script ensures that environment variables are properly loaded before
starting the server.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import uvicorn

# Load environment variables from .env file
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

# Ensure the API keys are set
openai_api_key = os.environ.get("OPENAI_API_KEY")
openrouter_api_key = os.environ.get("RESUME_CUSTOMIZER_OPENROUTER_API_KEY")

if not openai_api_key:
    print("Error: OPENAI_API_KEY environment variable is not set.")
    print("Please make sure it's set in your .env file or environment.")
    sys.exit(1)

if not openrouter_api_key:
    print("Error: RESUME_CUSTOMIZER_OPENROUTER_API_KEY environment variable is not set.")
    print("Please make sure it's set in your .env file or environment.")
    sys.exit(1)

print(f"API keys verified and loaded successfully.")

# Run the server
if __name__ == "__main__":
    uvicorn.run(
        "resume_customizer.main:app",
        host="127.0.0.1", 
        port=54321,
        reload=True
    )
