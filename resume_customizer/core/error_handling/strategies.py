"""Error handling strategies for AI agent operations.

This module provides various recovery strategies for handling errors in
agent operations, including retries, fallbacks, and graceful degradation.
"""

import asyncio
import functools
import random
import time
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union, cast

from loguru import logger
from pydantic_ai import (
    Agent,
    AgentError as PydanticAgentError,
    ModelTimeoutError,
    ModelRetryError,
    ModelRateLimitError,
    RunContext,
)

from resume_customizer.agents.infrastructure import ResumeCustomizerDeps
from resume_customizer.core.config import settings
from resume_customizer.core.exceptions import AgentError
from resume_customizer.core.metrics import track_agent_metrics


# Type variables for generic functions
T = TypeVar('T')
R = TypeVar('R')

# Registry of error handlers by error type and agent name
_error_handlers: Dict[Type[Exception], Dict[Optional[str], Callable]] = {}


def register_error_handler(
    error_type: Type[Exception],
    handler: Callable[[Exception, Optional[str], Dict[str, Any]], Any],
    agent_name: Optional[str] = None
) -> None:
    """Register an error handler for a specific error type.
    
    Args:
        error_type: The type of exception to handle
        handler: The handler function
        agent_name: Optional agent name to limit this handler to
    """
    if error_type not in _error_handlers:
        _error_handlers[error_type] = {}
    
    _error_handlers[error_type][agent_name] = handler
    
    logger.info(f"Registered error handler for {error_type.__name__} "
               f"for {'all agents' if agent_name is None else agent_name}")


async def handle_agent_error(
    error: Exception,
    agent_name: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
) -> Any:
    """Handle an error from an agent operation.
    
    This function dispatches to the appropriate handler based on the error type.
    
    Args:
        error: The exception that occurred
        agent_name: Optional name of the agent that raised the error
        context: Optional contextual information about the operation
        
    Returns:
        Any: The result from the error handler, if available
        
    Raises:
        The original exception if no handler is found
    """
    if context is None:
        context = {}
    
    # Track error metrics
    if agent_name:
        track_agent_metrics(agent_name, {
            "error_count": 1.0,
            "error_type": error.__class__.__name__,
        })
    
    # Find the most specific handler for this error type
    for error_type, handlers in _error_handlers.items():
        if isinstance(error, error_type):
            # Look for agent-specific handler first
            if agent_name in handlers:
                handler = handlers[agent_name]
                logger.info(f"Using agent-specific handler for {error_type.__name__} in {agent_name}")
                return await handler(error, agent_name, context)
            
            # Fall back to generic handler for this error type
            if None in handlers:
                handler = handlers[None]
                logger.info(f"Using generic handler for {error_type.__name__}")
                return await handler(error, agent_name, context)
    
    # No specific handler found, re-raise the exception
    logger.warning(f"No handler found for {error.__class__.__name__} in {agent_name or 'unknown agent'}")
    raise error


async def retry_with_exponential_backoff(
    func: Callable[..., Any],
    *args: Any,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 10.0,
    jitter: bool = True,
    retry_errors: Optional[List[Type[Exception]]] = None,
    **kwargs: Any
) -> Any:
    """Retry a function with exponential backoff.
    
    Args:
        func: The function to retry
        *args: Positional arguments to the function
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay between retries (seconds)
        max_delay: Maximum delay between retries (seconds)
        jitter: Whether to add random jitter to delays
        retry_errors: Specific error types to retry, or None for all errors
        **kwargs: Keyword arguments to the function
        
    Returns:
        Any: The result from the function if successful
        
    Raises:
        The last exception encountered if all retries fail
    """
    attempt = 0
    last_error = None
    
    while attempt <= max_retries:
        try:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        except Exception as e:
            # Check if this error type should be retried
            if retry_errors and not any(isinstance(e, err_type) for err_type in retry_errors):
                raise e
            
            attempt += 1
            last_error = e
            
            if attempt > max_retries:
                logger.warning(f"Maximum retries ({max_retries}) reached, giving up")
                raise e
            
            # Calculate delay with exponential backoff
            delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
            
            # Add jitter if enabled (±20%)
            if jitter:
                delay = delay * (0.8 + 0.4 * random.random())
            
            logger.info(f"Retry attempt {attempt}/{max_retries} after {delay:.2f}s delay")
            
            # Wait before next attempt
            await asyncio.sleep(delay)
    
    # This should never happen, but just in case
    assert last_error is not None
    raise last_error


async def retry_with_model_fallback(
    error: PydanticAgentError,
    agent_name: Optional[str],
    context: Dict[str, Any]
) -> Any:
    """Handle agent errors by falling back to a different model.
    
    This handler tries to recover from model-specific errors by retrying
    the operation with a different language model.
    
    Args:
        error: The agent error
        agent_name: Name of the agent that raised the error
        context: Contextual information about the operation
        
    Returns:
        Any: The result from the retry if successful
        
    Raises:
        AgentError: If all fallback attempts fail
    """
    # Extract the original agent and parameters
    agent = context.get("agent")
    agent_kwargs = context.get("agent_kwargs", {})
    
    if not agent:
        logger.error("Cannot use model fallback: agent not provided in context")
        raise error
    
    # Define fallback models in order of preference
    fallback_models = [
        "deepseek/deepseek-r1-mistral-7b",  # Try a smaller model first
        "openai:gpt-4-turbo",  # Then try OpenAI's GPT-4 Turbo
        "openai:gpt-3.5-turbo",  # Finally try GPT-3.5 Turbo
        "claude-3-5-sonnet",  # Try Claude as a last resort
    ]
    
    # Get the current model
    current_model = None
    if isinstance(agent_kwargs.get("deps"), ResumeCustomizerDeps):
        current_model = agent_kwargs["deps"].model_name
    
    # Remove the current model from fallbacks if present
    if current_model in fallback_models:
        fallback_models.remove(current_model)
    
    # Try each fallback model
    for model in fallback_models:
        try:
            logger.info(f"Trying fallback model {model} for {agent_name or 'unknown agent'}")
            
            # Create a new deps object with the fallback model
            if isinstance(agent_kwargs.get("deps"), ResumeCustomizerDeps):
                original_deps = agent_kwargs["deps"]
                agent_kwargs["deps"] = ResumeCustomizerDeps(
                    http_client=original_deps.http_client,
                    model_name=model
                )
            
            # Update metadata to indicate fallback
            if "metadata" not in agent_kwargs:
                agent_kwargs["metadata"] = {}
            agent_kwargs["metadata"]["using_fallback_model"] = model
            agent_kwargs["metadata"]["original_error"] = str(error)
            
            # Run the agent with the fallback model
            result = await agent.run(**agent_kwargs)
            
            logger.info(f"Successfully recovered using fallback model {model}")
            
            # Track the fallback success
            if agent_name:
                track_agent_metrics(agent_name, {
                    "fallback_success": 1.0,
                    "fallback_model": model,
                })
            
            return result
        except Exception as e:
            logger.warning(f"Fallback to model {model} failed: {str(e)}")
            
            # Track the fallback failure
            if agent_name:
                track_agent_metrics(agent_name, {
                    "fallback_failure": 1.0,
                })
    
    # All fallbacks failed, raise a custom error
    raise AgentError(
        f"All model fallbacks failed for {agent_name or 'unknown agent'}: {str(error)}",
        agent_name=agent_name
    )


async def retry_with_simplified_prompt(
    error: Union[PydanticAgentError, ModelRetryError],
    agent_name: Optional[str],
    context: Dict[str, Any]
) -> Any:
    """Handle agent errors by retrying with a simplified prompt.
    
    This handler tries to recover from prompt-complexity errors by retrying
    the operation with a simpler prompt.
    
    Args:
        error: The agent error
        agent_name: Name of the agent that raised the error
        context: Contextual information about the operation
        
    Returns:
        Any: The result from the retry if successful
        
    Raises:
        AgentError: If the simplified prompt retry fails
    """
    # Extract the original agent and parameters
    agent = context.get("agent")
    agent_kwargs = context.get("agent_kwargs", {})
    
    if not agent:
        logger.error("Cannot use simplified prompt: agent not provided in context")
        raise error
    
    # Get the original prompt
    original_prompt = agent_kwargs.get("prompt", "")
    if not original_prompt:
        logger.error("Cannot use simplified prompt: original prompt not found")
        raise error
    
    try:
        logger.info(f"Retrying with simplified prompt for {agent_name or 'unknown agent'}")
        
        # Simplify the prompt by truncating or summarizing
        simplified_prompt = _simplify_prompt(original_prompt)
        
        # Update the prompt in kwargs
        agent_kwargs["prompt"] = simplified_prompt
        
        # Update metadata to indicate simplified prompt
        if "metadata" not in agent_kwargs:
            agent_kwargs["metadata"] = {}
        agent_kwargs["metadata"]["using_simplified_prompt"] = True
        agent_kwargs["metadata"]["original_error"] = str(error)
        
        # Run the agent with the simplified prompt
        result = await agent.run(**agent_kwargs)
        
        logger.info("Successfully recovered using simplified prompt")
        
        # Track the simplified prompt success
        if agent_name:
            track_agent_metrics(agent_name, {
                "simplified_prompt_success": 1.0,
            })
        
        return result
    except Exception as e:
        logger.warning(f"Simplified prompt retry failed: {str(e)}")
        
        # Track the simplified prompt failure
        if agent_name:
            track_agent_metrics(agent_name, {
                "simplified_prompt_failure": 1.0,
            })
        
        # Raise a custom error
        raise AgentError(
            f"Simplified prompt retry failed for {agent_name or 'unknown agent'}: {str(error)}",
            agent_name=agent_name
        )


def _simplify_prompt(prompt: str) -> str:
    """Simplify a prompt by truncating or summarizing.
    
    Args:
        prompt: The original prompt
        
    Returns:
        str: The simplified prompt
    """
    # Check if the prompt is already short
    if len(prompt) < 500:
        return prompt
    
    # First attempt: truncate long content sections
    lines = prompt.split("\n")
    simplified_lines = []
    
    content_section = False
    content_lines = 0
    
    for line in lines:
        # Detect content sections (typically after empty lines)
        if line.strip() == "":
            content_section = True
            content_lines = 0
            simplified_lines.append(line)
            continue
        
        # If we're in a content section and have already included some lines,
        # truncate the rest and add an indicator
        if content_section and content_lines > 5 and len(line) > 50:
            if "[truncated]" not in simplified_lines[-1]:
                simplified_lines.append("[... content truncated for brevity ...]")
            continue
        
        # Otherwise, include the line
        simplified_lines.append(line)
        if content_section:
            content_lines += 1
    
    # Join the simplified lines
    result = "\n".join(simplified_lines)
    
    # If still too long, do a hard truncation with a note
    if len(result) > 2000:
        result = result[:1950] + "\n\n[... remainder truncated for brevity ...]"
    
    return result


# Register default handlers
register_error_handler(
    ModelTimeoutError,
    retry_with_model_fallback
)

register_error_handler(
    ModelRateLimitError,
    retry_with_exponential_backoff
)

register_error_handler(
    ModelRetryError,
    retry_with_simplified_prompt
)

# Generic fallback for any PydanticAgentError
register_error_handler(
    PydanticAgentError,
    retry_with_model_fallback
)
