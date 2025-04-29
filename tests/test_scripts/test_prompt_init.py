#!/usr/bin/env python3
"""Script to test prompt template initialization."""
import logging

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

def main():
    """Test prompt initialization and agent creation."""
    try:
        # Import prompt manager
        from infrastructure.init_prompts import init_prompt_manager
        import os
        
        # Set a fake API key for testing
        os.environ["OPENAI_API_KEY"] = "sk-fake-key-for-testing-only"
        
        # Create prompt manager
        logger.info("Initializing prompt manager")
        prompt_manager = init_prompt_manager()
        
        # Try to access templates for each agent type
        agent_types = ["profiler", "researcher", "strategist"]
        
        for agent_type in agent_types:
            logger.info(f"Testing templates for {agent_type} agent")
            try:
                template = prompt_manager.get_template(agent_type, "latest")
                logger.info(f"Successfully retrieved template for {agent_type}")
                logger.info(f"Template length: {len(template)}")
            except Exception as e:
                logger.error(f"Failed to retrieve template for {agent_type}: {str(e)}")
                raise
        
        # Modify the base agent to use a test model
        from agents.base import BaseAgent
        logger.info("Patching BaseAgent for testing")
        
        # Store the original __init__ method
        original_init = BaseAgent.__init__
        
        # Define a new __init__ method for testing
        def test_init(self, prompt_manager, agent_type, output_type):
            self.prompt_manager = prompt_manager
            self.agent_type = agent_type
            self.log_info = print  # Simple logging for testing
            
            # Just validate we can get the system prompt
            system_prompt = self._get_system_prompt()
            print(f"Got system prompt for {agent_type}, length: {len(system_prompt)}")
            
        # Replace the __init__ method for testing
        BaseAgent.__init__ = test_init
        
        try:
            # Try to create an agent
            logger.info("Testing agent creation")
            from agents.profiler import ProfilerAgent
            
            agent = ProfilerAgent(prompt_manager=prompt_manager)
            logger.info("Successfully created ProfilerAgent")
        finally:
            # Restore the original __init__ method
            BaseAgent.__init__ = original_init
        
        logger.info("All tests passed!")
        return True
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    main()
