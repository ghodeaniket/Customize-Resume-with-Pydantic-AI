"""Error handling and recovery strategies for Resume Customizer.

This module provides robust error handling, recovery mechanisms, and
retry strategies for the AI agents and related operations.
"""

from resume_customizer.core.error_handling.strategies import (
    retry_with_exponential_backoff,
    retry_with_model_fallback,
    retry_with_simplified_prompt,
    handle_agent_error,
    register_error_handler,
)

from resume_customizer.core.error_handling.decorators import (
    with_retry,
    with_fallback,
)

__all__ = [
    "retry_with_exponential_backoff",
    "retry_with_model_fallback",
    "retry_with_simplified_prompt",
    "handle_agent_error",
    "register_error_handler",
    "with_retry",
    "with_fallback",
]
