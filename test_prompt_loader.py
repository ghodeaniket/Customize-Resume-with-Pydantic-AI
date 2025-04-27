"""Test script for the prompt loader."""
import logging
import os
import yaml
from pathlib import Path


def configure_logging():
    """Configure logging for the test."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s:%(filename)s:%(lineno)d | %(message)s"
    )


def test_prompt_loader():
    """Test the prompt loader."""
    # Configure logging
    configure_logging()
    logger = logging.getLogger("test")
    
    logger.info("Testing prompt loader...")
    
    # Check if prompt directories exist
    prompt_dir = Path("prompts")
    if not prompt_dir.exists():
        logger.error(f"Prompt directory {prompt_dir} does not exist")
        return
    
    # Check agent directories
    for agent_type in ["profiler", "researcher", "strategist"]:
        agent_dir = prompt_dir / agent_type
        if not agent_dir.exists():
            logger.error(f"Agent directory {agent_dir} does not exist")
            continue
            
        logger.info(f"Checking {agent_type} prompts...")
        
        # Check if any YAML files exist
        yaml_files = list(agent_dir.glob("*.yaml"))
        if not yaml_files:
            logger.warning(f"No YAML files found in {agent_dir}")
            continue
            
        # Check each YAML file
        for yaml_file in yaml_files:
            logger.info(f"Checking {yaml_file}...")
            
            try:
                with open(yaml_file, "r", encoding="utf-8") as f:
                    template_data = yaml.safe_load(f)
                
                # Validate template data
                if "version" not in template_data:
                    logger.warning(f"Missing 'version' in {yaml_file}")
                else:
                    logger.info(f"Version: {template_data['version']}")
                    
                if "description" not in template_data:
                    logger.warning(f"Missing 'description' in {yaml_file}")
                else:
                    logger.info(f"Description: {template_data['description']}")
                    
                if "template" not in template_data:
                    logger.error(f"Missing 'template' in {yaml_file}")
                else:
                    template_preview = template_data["template"][:50].replace("\n", " ")
                    logger.info(f"Template: {template_preview}...")
                    
                logger.info(f"Successfully validated {yaml_file}")
                    
            except Exception as e:
                logger.error(f"Failed to read {yaml_file}: {str(e)}")
    
    logger.info("Prompt loader test complete.")


if __name__ == "__main__":
    test_prompt_loader()
