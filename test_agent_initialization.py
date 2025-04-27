#!/usr/bin/env python3
"""Test agent initialization with OpenRouter integration."""
import asyncio
import logging
import os
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("test_agent")

async def test_agent_initialization():
    """Test agent initialization with OpenRouter integration."""
    try:
        # 1. Get settings
        from core.config import get_settings
        settings = get_settings()
        
        # 2. Set environment variables
        os.environ["OPENAI_API_KEY"] = settings.openrouter_api_key
        os.environ["OPENAI_BASE_URL"] = "https://openrouter.ai/api/v1"
        
        # 3. Initialize prompt manager
        from infrastructure.init_prompts import init_prompt_manager
        prompt_manager = init_prompt_manager()
        
        # 4. Initialize agent
        from agents.profiler import ProfilerAgent
        logger.info("Creating ProfilerAgent")
        agent = ProfilerAgent(prompt_manager=prompt_manager)
        
        logger.info("Successfully created ProfilerAgent")
        
        # 5. Create dependencies for agent
        from infrastructure.ai_provider import AIProvider
        ai_provider = AIProvider(
            api_key=settings.openrouter_api_key,
            default_model=settings.default_model
        )
        
        deps = await ai_provider.create_deps()
        logger.info(f"Created dependencies with model: {deps.model_name}")
        
        # We won't actually call the API to avoid unnecessary charges
        logger.info("Agent initialization test passed!")
        return True
    
    except Exception as e:
        logger.error(f"Agent initialization test failed: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    asyncio.run(test_agent_initialization())
