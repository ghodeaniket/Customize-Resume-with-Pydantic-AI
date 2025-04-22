"""Agent infrastructure for the Resume Customizer application.

This module defines the shared agent infrastructure components like 
dependencies and base classes.
"""

from dataclasses import dataclass
from typing import Optional

import httpx
from pydantic import BaseModel

from resume_customizer.core.config import settings


@dataclass
class ResumeCustomizerDeps:
    """Dependencies for all agents in the resume customizer.
    
    This class is used to pass shared dependencies like HTTP clients and
    configuration to all agents in the application.
    
    Attributes:
        http_client: AsyncClient for making HTTP requests
        openrouter_api_key: API key for OpenRouter
        model_name: Name of the model to use for generation
    """
    http_client: httpx.AsyncClient
    openrouter_api_key: str = settings.OPENROUTER_API_KEY
    model_name: str = settings.DEFAULT_MODEL


class AgentResponseMetadata(BaseModel):
    """Metadata about an agent response.
    
    Attributes:
        source_agent: Name of the agent that generated the response
        token_usage: Number of tokens used for the response
        completion_time_ms: Time taken to generate the response in milliseconds
    """
    source_agent: str
    token_usage: Optional[int] = None
    completion_time_ms: Optional[int] = None
