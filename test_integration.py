"""Test script for the integration of all components."""
import asyncio
import logging
import os
from dotenv import load_dotenv

from infrastructure.init_prompts import init_prompt_manager
from infrastructure.ai_provider import AIProvider


def configure_logging():
    """Configure logging for the test."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s:%(filename)s:%(lineno)d | %(message)s"
    )


async def test_integration():
    """Test the integration of all components."""
    # Load environment variables
    load_dotenv()
    
    # Configure logging
    configure_logging()
    logger = logging.getLogger("test")
    
    logger.info("Testing integration...")
    
    # Get API key from environment
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        logger.error("OPENROUTER_API_KEY environment variable is not set")
        return
    
    # Initialize prompt manager
    logger.info("Initializing prompt manager...")
    manager = init_prompt_manager()
    
    # Verify prompt templates were loaded
    for agent_type in ["profiler", "researcher", "strategist"]:
        try:
            template = manager.get_template(agent_type, "latest")
            template_preview = template[:50].replace("\n", " ")
            logger.info(f"Successfully loaded template for {agent_type}: {template_preview}...")
        except Exception as e:
            logger.error(f"Failed to get template for {agent_type}: {str(e)}")
    
    # Create AIProvider
    logger.info("Creating AIProvider...")
    model_name = "deepseek/deepseek-r1-distill-llama-70b"
    provider = AIProvider(api_key, model_name)
    
    # Create dependencies
    logger.info("Creating dependencies...")
    deps = await provider.create_deps()
    
    # Verify model provider
    if deps.model_provider:
        logger.info(f"Model provider was created for model: {deps.model_name}")
    else:
        logger.error("Model provider was not created")
        return
    
    # Create an example prompt
    prompt = "Say hello in one short sentence."
    messages = [{"role": "system", "content": "You are a helpful assistant."}]
    
    # Test that the model provider can generate a response
    logger.info("Testing model provider...")
    
    try:
        response = await deps.model_provider.generate(
            text=prompt,
            messages=messages,
            settings=None
        )
        
        # Verify the response - ModelResponse uses 'parts' for the actual text content
        response_text = response.parts[0] if response.parts else "No response"
        logger.info(f"Response parts: {response.parts}")
        logger.info(f"Response text: {response_text}")
        logger.info(f"Response model: {response.model_name}")
        logger.info("Model provider test passed!")
        
    except Exception as e:
        logger.error(f"Model provider test failed: {str(e)}")
    
    # Close the provider connections
    await provider.close()
    
    logger.info("Integration test complete.")


if __name__ == "__main__":
    asyncio.run(test_integration())
