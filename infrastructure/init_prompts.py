"""Initialize default prompts for agents."""
import logging
from infrastructure.ai_provider import PromptManager
from infrastructure.prompt_loader import PromptLoader


# Global prompt manager instance
_prompt_manager = None


def get_prompt_manager() -> PromptManager:
    """Get the global prompt manager instance.
    
    Returns:
        PromptManager: Prompt manager with default prompts
    """
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = init_prompt_manager()
    return _prompt_manager


def init_prompt_manager() -> PromptManager:
    """Initialize prompt manager with default prompts.
    
    Returns:
        PromptManager: Prompt manager with default prompts
    """
    logger = logging.getLogger(__name__)
    logger.info("Initializing prompt manager")
    
    # Create prompt manager
    manager = PromptManager()
    
    # Create prompt loader
    loader = PromptLoader()
    
    # Try to load prompts from files first
    logger.info("Attempting to load prompts from YAML files")
    loader.load_all_prompts(manager)
    
    # Ensure default prompts exist
    logger.info("Initializing default prompts")
    loader.initialize_default_prompts(manager)
    
    logger.info("Prompt manager initialization complete")
    return manager
