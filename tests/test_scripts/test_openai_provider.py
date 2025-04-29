#!/usr/bin/env python3
"""Test OpenAI provider with OpenRouter integration."""
import asyncio
import logging
import os
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("test_provider")

async def test_pydantic_integration():
    """Test Pydantic AI integration with OpenRouter."""
    try:
        # 1. Import Pydantic AI OpenAI model
        from pydantic_ai.models.openai import OpenAIModel
        from pydantic_ai.providers.openai import OpenAIProvider
        
        # 2. Get settings
        from core.config import get_settings
        settings = get_settings()
        
        # 3. Set environment variables for OpenAI provider
        os.environ["OPENAI_API_KEY"] = settings.openrouter_api_key
        os.environ["OPENAI_BASE_URL"] = "https://openrouter.ai/api/v1"
        
        # 4. Create OpenAI provider with OpenRouter base URL
        # The provider will read from environment variables
        provider = OpenAIProvider()
        
        # 5. Create a model with the provider
        logger.info("Creating OpenAI model with OpenRouter provider")
        model = OpenAIModel("gpt-4o", provider=provider)
        
        logger.info("Successfully created model with OpenRouter provider")
        
        # Optional: Test a simple generation (commented out to avoid unnecessary API calls)
        # response = await model.generate(
        #     text="Say hello in one word.",
        #     messages=[{"role": "system", "content": "You are a helpful assistant."}]
        # )
        # logger.info(f"Model response: {response.text}")
        
        logger.info("OpenAI provider integration test passed!")
        return True
    
    except Exception as e:
        logger.error(f"OpenAI provider integration test failed: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    asyncio.run(test_pydantic_integration())
