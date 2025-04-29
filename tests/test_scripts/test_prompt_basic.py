#!/usr/bin/env python3
"""Basic test for prompt template and agent initialization."""
import logging
import os
from pathlib import Path
import yaml

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

class SimplePromptManager:
    """Simplified prompt manager for testing."""
    
    def __init__(self):
        """Initialize a simple prompt manager."""
        self.templates = {
            "profiler": {
                "1.0.0": "You are a profiler agent. Extract information from resumes."
            },
            "researcher": {
                "1.0.0": "You are a researcher agent. Analyze job descriptions."
            },
            "strategist": {
                "1.0.0": "You are a strategist agent. Create optimized resumes."
            }
        }
    
    def get_template(self, agent_type, version="latest"):
        """Get a prompt template by version."""
        if agent_type not in self.templates:
            raise ValueError(f"No templates found for agent {agent_type}")
        
        if version == "latest":
            versions = sorted(self.templates[agent_type].keys())
            if not versions:
                raise ValueError(f"No template versions found for agent {agent_type}")
            
            version = versions[-1]
        
        if version not in self.templates[agent_type]:
            raise ValueError(f"Template version {version} not found for agent {agent_type}")
        
        return self.templates[agent_type][version]

def test_prompt_files():
    """Test prompt template files."""
    prompt_dir = Path("prompts")
    
    # Check if prompt directories exist
    for agent_type in ["profiler", "researcher", "strategist"]:
        agent_dir = prompt_dir / agent_type
        if not agent_dir.exists():
            logger.error(f"No prompt directory found for {agent_type}")
            return False
        
        # Check for prompt files
        prompt_files = list(agent_dir.glob("*.yaml"))
        if not prompt_files:
            logger.error(f"No prompt templates found for {agent_type}")
            return False
        
        logger.info(f"Found {len(prompt_files)} prompt templates for {agent_type}")
        
        # Load each prompt file
        for prompt_file in prompt_files:
            try:
                with open(prompt_file, "r", encoding="utf-8") as f:
                    template_data = yaml.safe_load(f)
                
                if "version" not in template_data:
                    logger.error(f"Missing version in {prompt_file}")
                    return False
                
                if "template" not in template_data:
                    logger.error(f"Missing template in {prompt_file}")
                    return False
                
                logger.info(f"Successfully loaded {prompt_file.name}, version {template_data['version']}")
                
            except Exception as e:
                logger.error(f"Failed to load {prompt_file}: {str(e)}")
                return False
    
    return True

def main():
    """Run basic prompt and agent initialization tests."""
    
    # 1. Test prompt files
    logger.info("Testing prompt template files")
    if not test_prompt_files():
        return False
    
    # 2. Test simple prompt manager
    logger.info("Testing simple prompt manager")
    prompt_manager = SimplePromptManager()
    
    try:
        # Test retrieving templates
        for agent_type in ["profiler", "researcher", "strategist"]:
            template = prompt_manager.get_template(agent_type)
            logger.info(f"Got template for {agent_type}: {template}")
    except Exception as e:
        logger.error(f"Simple prompt manager test failed: {str(e)}")
        return False
    
    logger.info("All basic tests passed!")
    return True

if __name__ == "__main__":
    main()
