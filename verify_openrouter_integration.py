#!/usr/bin/env python3
"""Verify OpenRouter integration with Pydantic AI."""
import asyncio
import logging
import os
import time
from typing import Optional

from core.config import get_settings
from infrastructure.init_prompts import init_prompt_manager
from infrastructure.ai_provider import AIProvider, ResumeCustomizerDeps
from infrastructure.model_provider import OpenRouterModel
from infrastructure.openrouter_client import OpenRouterClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("verification")


async def test_openrouter_client():
    """Test OpenRouter client directly."""
    settings = get_settings()
    
    if not settings.openrouter_api_key:
        logger.error("No OpenRouter API key found in settings")
        return False
    
    logger.info("Testing OpenRouter client")
    client = OpenRouterClient(
        api_key=settings.openrouter_api_key,
        base_url="https://openrouter.ai/api/v1"
    )
    
    try:
        # Simple message test
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say hello in one word."}
        ]
        
        response = await client.chat_completion(
            messages=messages,
            model=settings.default_model,
            temperature=0.7,
            max_tokens=100
        )
        
        if "choices" in response and len(response["choices"]) > 0:
            if "message" in response["choices"][0]:
                content = response["choices"][0]["message"]["content"]
                logger.info(f"OpenRouter response: {content}")
                
                if content and len(content) > 0:
                    logger.info("OpenRouter client test passed!")
                    return True
        
        logger.error("Invalid response format")
        logger.debug(f"Response: {response}")
        return False
    
    except Exception as e:
        logger.error(f"OpenRouter client test failed: {str(e)}")
        return False
    finally:
        await client.close()


async def test_model_provider():
    """Test OpenRouterModel with Pydantic AI."""
    settings = get_settings()
    
    if not settings.openrouter_api_key:
        logger.error("No OpenRouter API key found in settings")
        return False
    
    logger.info("Testing OpenRouterModel provider")
    client = OpenRouterClient(
        api_key=settings.openrouter_api_key,
        base_url="https://openrouter.ai/api/v1"
    )
    
    try:
        model = OpenRouterModel(
            client=client,
            model_name=settings.default_model
        )
        
        # Test model response
        messages = [
            {"role": "system", "content": "You are a helpful assistant."}
        ]
        
        response = await model.generate(
            text="Say hello in one word.",
            messages=messages
        )
        
        if hasattr(response, 'text') and response.text and len(response.text) > 0:
            logger.info(f"Model response: {response.text}")
            logger.info("OpenRouterModel test passed!")
            return True
        
        logger.error("Invalid model response")
        return False
    
    except Exception as e:
        logger.error(f"OpenRouterModel test failed: {str(e)}")
        return False
    finally:
        await client.close()


async def test_ai_provider():
    """Test AIProvider with dependency creation."""
    settings = get_settings()
    
    if not settings.openrouter_api_key:
        logger.error("No OpenRouter API key found in settings")
        return False
    
    logger.info("Testing AIProvider")
    
    try:
        # Create AI provider
        provider = AIProvider(
            api_key=settings.openrouter_api_key,
            default_model=settings.default_model
        )
        
        # Create dependencies
        deps = await provider.create_deps()
        
        # Verify dependencies
        if deps.model_provider is None:
            logger.error("No model provider in dependencies")
            return False
        
        if deps.http_client is None:
            logger.error("No HTTP client in dependencies")
            return False
        
        logger.info(f"Dependencies created with model: {deps.model_name}")
        logger.info("AIProvider test passed!")
        return True
    
    except Exception as e:
        logger.error(f"AIProvider test failed: {str(e)}")
        return False


async def test_prompt_init():
    """Test prompt initialization."""
    try:
        logger.info("Testing prompt initialization")
        
        # Initialize prompt manager
        prompt_manager = init_prompt_manager()
        
        # Verify templates for each agent type
        agent_types = ["profiler", "researcher", "strategist"]
        
        for agent_type in agent_types:
            template = prompt_manager.get_template(agent_type, "latest")
            logger.info(f"Template for {agent_type}: {len(template)} characters")
        
        logger.info("Prompt initialization test passed!")
        return True
    
    except Exception as e:
        logger.error(f"Prompt initialization test failed: {str(e)}")
        return False


async def verify_system():
    """Run all verification tests."""
    success = True
    
    logger.info("===== Starting System Verification =====")
    start_time = time.time()
    
    # Test prompt initialization
    if not await test_prompt_init():
        success = False
        logger.error("Prompt initialization verification failed")
    
    # Test OpenRouter client
    if not await test_openrouter_client():
        success = False
        logger.error("OpenRouter client verification failed")
    
    # Test model provider
    if not await test_model_provider():
        success = False
        logger.error("Model provider verification failed")
    
    # Test AI provider
    if not await test_ai_provider():
        success = False
        logger.error("AI provider verification failed")
    
    duration = time.time() - start_time
    
    if success:
        logger.info(f"===== All Verification Tests Passed in {duration:.2f}s =====")
    else:
        logger.error(f"===== Verification Tests Failed in {duration:.2f}s =====")
    
    return success


if __name__ == "__main__":
    asyncio.run(verify_system())
