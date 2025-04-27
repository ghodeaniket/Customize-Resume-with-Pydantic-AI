#!/usr/bin/env python3
"""Test environment variables for OpenRouter integration."""
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("test_env")

def test_env_vars():
    """Test if environment variables are correctly set."""
    from core.config import get_settings
    settings = get_settings()
    
    logger.info("Testing OpenRouter API key in settings")
    if not settings.openrouter_api_key:
        logger.error("No OpenRouter API key found in settings")
        logger.info("Please check your .env file for OPENROUTER_API_KEY")
        return False
    
    logger.info("OpenRouter API key found in settings")
    
    # Set environment variables for Pydantic AI (simulating what happens in main.py)
    os.environ["OPENAI_API_KEY"] = settings.openrouter_api_key
    os.environ["OPENAI_BASE_URL"] = "https://openrouter.ai/api/v1"
    
    # Verify environment variables
    openai_key = os.environ.get("OPENAI_API_KEY")
    openai_url = os.environ.get("OPENAI_BASE_URL")
    
    if not openai_key:
        logger.error("Failed to set OPENAI_API_KEY environment variable")
        return False
    
    if not openai_url:
        logger.error("Failed to set OPENAI_BASE_URL environment variable")
        return False
    
    logger.info(f"OPENAI_API_KEY set: {openai_key[:5]}...{openai_key[-5:]}")
    logger.info(f"OPENAI_BASE_URL set: {openai_url}")
    
    return True

if __name__ == "__main__":
    if test_env_vars():
        logger.info("Environment variables test passed!")
    else:
        logger.error("Environment variables test failed!")
