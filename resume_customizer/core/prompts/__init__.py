"""Prompt management system for Resume Customizer agents.

This module provides a structured, versioned approach to managing prompts
used by the various agents in the Resume Customizer application.
"""

from resume_customizer.core.prompts.manager import PromptManager, PromptTemplate
from resume_customizer.core.prompts.registry import (
    get_profiler_prompt,
    get_researcher_prompt,
    get_strategist_prompt,
)

__all__ = [
    "PromptManager",
    "PromptTemplate",
    "get_profiler_prompt",
    "get_researcher_prompt",
    "get_strategist_prompt",
]
