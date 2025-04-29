"""Test script for the prompt initialization."""
import logging
import os
from infrastructure.init_prompts import init_prompt_manager


def configure_logging():
    """Configure logging for the test."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s:%(filename)s:%(lineno)d | %(message)s"
    )


def test_init_prompts():
    """Test the prompt initialization."""
    # Configure logging
    configure_logging()
    logger = logging.getLogger("test")
    
    logger.info("Testing prompt initialization...")
    
    # Initialize prompt manager
    manager = init_prompt_manager()
    
    # Check if templates were loaded
    for agent_type in ["profiler", "researcher", "strategist"]:
        try:
            template = manager.get_template(agent_type, "latest")
            template_preview = template[:50].replace("\n", " ")
            logger.info(f"Successfully loaded template for {agent_type}: {template_preview}...")
        except Exception as e:
            logger.error(f"Failed to get template for {agent_type}: {str(e)}")
    
    logger.info("Prompt initialization test complete.")


if __name__ == "__main__":
    test_init_prompts()
