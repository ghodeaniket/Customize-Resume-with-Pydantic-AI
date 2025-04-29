#!/usr/bin/env python3
"""Secure verification of fixes without exposing API keys."""
import asyncio
import logging
import os
import time
from typing import Dict, List, Optional, Any, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("verification.log")
    ]
)

logger = logging.getLogger("verification")

def mask_key(key: str) -> str:
    """Safely mask a key for logging purposes."""
    if not key or len(key) < 8:
        return "INVALID_KEY"
    return f"{key[:3]}...{key[-3:]}"

async def test_environment_variables() -> Tuple[bool, str]:
    """Test environment variables for OpenRouter integration."""
    try:
        logger.info("=== Testing Environment Variables ===")
        
        # Get settings
        from core.config import get_settings
        settings = get_settings()
        
        # Check OpenRouter API key without exposing it
        if not settings.openrouter_api_key:
            return False, "No OpenRouter API key found in settings"
        
        # Set environment variables
        os.environ["OPENAI_API_KEY"] = settings.openrouter_api_key
        os.environ["OPENAI_BASE_URL"] = "https://openrouter.ai/api/v1"
        
        # Verify environment variables
        if not os.environ.get("OPENAI_API_KEY"):
            return False, "Failed to set OPENAI_API_KEY environment variable"
        
        if not os.environ.get("OPENAI_BASE_URL"):
            return False, "Failed to set OPENAI_BASE_URL environment variable"
        
        logger.info("Successfully set environment variables")
        return True, "Environment variables test passed"
    
    except Exception as e:
        logger.error(f"Environment variables test failed: {str(e)}", exc_info=True)
        return False, f"Environment variables test failed: {str(e)}"

async def test_prompt_management() -> Tuple[bool, str]:
    """Test prompt template management."""
    try:
        logger.info("=== Testing Prompt Management ===")
        
        # Initialize prompt manager
        from infrastructure.init_prompts import init_prompt_manager
        prompt_manager = init_prompt_manager()
        
        # Verify templates for each agent type
        agent_types = ["profiler", "researcher", "strategist"]
        
        for agent_type in agent_types:
            template = prompt_manager.get_template(agent_type, "latest")
            logger.info(f"Retrieved template for {agent_type}: {len(template)} characters")
            
            if not template or len(template) < 100:
                return False, f"Invalid template for {agent_type}"
        
        logger.info("Successfully retrieved all prompt templates")
        return True, "Prompt management test passed"
    
    except Exception as e:
        logger.error(f"Prompt management test failed: {str(e)}", exc_info=True)
        return False, f"Prompt management test failed: {str(e)}"

async def test_agent_initialization() -> Tuple[bool, str]:
    """Test agent initialization."""
    try:
        logger.info("=== Testing Agent Initialization ===")
        
        # Get prompt manager
        from infrastructure.init_prompts import init_prompt_manager
        prompt_manager = init_prompt_manager()
        
        # Initialize ProfilerAgent
        from agents.profiler import ProfilerAgent
        agent = ProfilerAgent(prompt_manager=prompt_manager)
        
        logger.info("Successfully initialized ProfilerAgent")
        
        # Initialize ResearcherAgent
        from agents.researcher import ResearcherAgent
        researcher = ResearcherAgent(prompt_manager=prompt_manager)
        
        logger.info("Successfully initialized ResearcherAgent")
        
        # Initialize StrategistAgent
        from agents.strategist import StrategistAgent
        strategist = StrategistAgent(
            profiler_agent=agent,
            researcher_agent=researcher,
            prompt_manager=prompt_manager
        )
        
        logger.info("Successfully initialized StrategistAgent")
        
        return True, "Agent initialization test passed"
    
    except Exception as e:
        logger.error(f"Agent initialization test failed: {str(e)}", exc_info=True)
        return False, f"Agent initialization test failed: {str(e)}"

async def test_openrouter_integration() -> Tuple[bool, str]:
    """Test OpenRouter integration."""
    try:
        logger.info("=== Testing OpenRouter Integration ===")
        
        # Get settings
        from core.config import get_settings
        settings = get_settings()
        
        # Create AI provider without exposing API key
        from infrastructure.ai_provider import AIProvider
        provider = AIProvider(
            api_key=settings.openrouter_api_key,
            default_model=settings.default_model
        )
        
        # Create dependencies
        deps = await provider.create_deps()
        
        if not deps.model_provider:
            return False, "No model provider in dependencies"
        
        if not deps.http_client:
            return False, "No HTTP client in dependencies"
        
        logger.info(f"Successfully created AIProvider dependencies with model: {deps.model_name}")
        
        # Check that the model provider is correctly initialized
        model_provider = deps.model_provider
        logger.info(f"Model provider type: {type(model_provider).__name__}")
        
        if not hasattr(model_provider, "model_name"):
            return False, "Model provider doesn't have the 'model_name' attribute"
        
        if not hasattr(model_provider, "generate"):
            return False, "Model provider doesn't have the 'generate' method"
        
        logger.info("Successfully verified model provider attributes")
        
        return True, "OpenRouter integration test passed"
    
    except Exception as e:
        logger.error(f"OpenRouter integration test failed: {str(e)}", exc_info=True)
        return False, f"OpenRouter integration test failed: {str(e)}"

async def verify_all_fixes() -> bool:
    """Run all verification tests."""
    start_time = time.time()
    logger.info("===== Starting Comprehensive Verification =====")
    
    tests = [
        ("Environment Variables", test_environment_variables),
        ("Prompt Management", test_prompt_management),
        ("Agent Initialization", test_agent_initialization),
        ("OpenRouter Integration", test_openrouter_integration)
    ]
    
    all_passed = True
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"Running test: {test_name}")
        success, message = await test_func()
        results.append({"name": test_name, "success": success, "message": message})
        
        if not success:
            all_passed = False
            logger.error(f"Test failed: {test_name} - {message}")
        else:
            logger.info(f"Test passed: {test_name}")
    
    duration = time.time() - start_time
    
    # Print summary
    logger.info("\n===== Verification Summary =====")
    for result in results:
        status = "✅ PASSED" if result["success"] else "❌ FAILED"
        logger.info(f"{status} - {result['name']}: {result['message']}")
    
    if all_passed:
        logger.info(f"===== All Verification Tests Passed in {duration:.2f}s =====")
    else:
        logger.error(f"===== Some Verification Tests Failed in {duration:.2f}s =====")
    
    return all_passed

if __name__ == "__main__":
    asyncio.run(verify_all_fixes())
