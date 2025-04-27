"""AI provider infrastructure for Resume Customizer."""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

import httpx
from pydantic_ai import RunContext

from core.exceptions import AIProviderError
from core.logging import LoggerMixin
from infrastructure.openrouter_client import OpenRouterClient


@dataclass
class ResumeCustomizerDeps:
    """Dependencies for all agents in the resume customizer."""
    
    http_client: httpx.AsyncClient
    openrouter_api_key: str
    model_name: str = "deepseek/deepseek-r1-distill-llama-70b"
    model_provider: Optional[Any] = None


class AIProvider(LoggerMixin):
    """Provider for AI model interactions."""
    
    def __init__(self, api_key: str, default_model: str):
        """Initialize AI provider.
        
        Args:
            api_key: OpenRouter API key
            default_model: Default model name
        """
        self.api_key = api_key
        self.default_model = default_model
        self.base_url = "https://openrouter.ai/api/v1"
        self._http_client = None
        self._openrouter_client = None
        
        if not api_key:
            self.log_error("Missing OpenRouter API key")
            raise AIProviderError("Missing OpenRouter API key")
            
        self.log_info(f"Initialized AIProvider with default model: {default_model}")
    
    async def create_deps(self, model_name: Optional[str] = None) -> ResumeCustomizerDeps:
        """Create dependencies for Pydantic AI agents.
        
        Args:
            model_name: Optional model name override
            
        Returns:
            ResumeCustomizerDeps: Dependencies for agents
        """
        if self._http_client is None:
            self.log_debug("Creating new HTTP client")
            self._http_client = httpx.AsyncClient(
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
        
        if self._openrouter_client is None:
            self.log_debug("Creating new OpenRouter client")
            self._openrouter_client = OpenRouterClient(
                api_key=self.api_key,
                base_url=self.base_url
            )
        
        # Use the specified model or default
        actual_model_name = model_name or self.default_model
        
        # Create custom model provider if needed
        # We're importing here to avoid circular imports
        from infrastructure.model_provider import OpenRouterModel
        model_provider = OpenRouterModel(
            client=self._openrouter_client,
            model_name=actual_model_name
        )
        
        self.log_info(f"Created dependencies with model: {actual_model_name}")
        
        return ResumeCustomizerDeps(
            http_client=self._http_client,
            openrouter_api_key=self.api_key,
            model_name=actual_model_name,
            model_provider=model_provider
        )
    
    async def close(self) -> None:
        """Close any open connections."""
        if self._http_client is not None:
            await self._http_client.aclose()
            self._http_client = None
            
        if self._openrouter_client is not None:
            await self._openrouter_client.close()
            self._openrouter_client = None
            
        self.log_debug("Closed all connections")


class PromptTemplate:
    """Versioned prompt template for agents."""
    
    def __init__(self, version: str, template: str, description: str):
        """Initialize prompt template.
        
        Args:
            version: Template version
            template: Template content
            description: Template description
        """
        self.version = version
        self.template = template
        self.description = description


class PromptManager(LoggerMixin):
    """Manager for versioned prompt templates."""
    
    def __init__(self):
        """Initialize prompt manager."""
        self.templates: Dict[str, Dict[str, PromptTemplate]] = {}
    
    def add_template(self, agent_name: str, template: PromptTemplate):
        """Add a new prompt template.
        
        Args:
            agent_name: Name of the agent
            template: Prompt template
        """
        if agent_name not in self.templates:
            self.templates[agent_name] = {}
        
        self.log_debug(f"Adding template {template.version} for agent {agent_name}")
        self.templates[agent_name][template.version] = template
    
    def get_template(self, agent_name: str, version: str = "latest") -> str:
        """Get a prompt template by version.
        
        Args:
            agent_name: Name of the agent
            version: Template version or "latest"
            
        Returns:
            str: Template content
            
        Raises:
            AIProviderError: If template not found
        """
        if agent_name not in self.templates:
            self.log_error(f"No templates found for agent {agent_name}")
            raise AIProviderError(f"No templates found for agent {agent_name}")
        
        if version == "latest":
            versions = sorted(self.templates[agent_name].keys())
            if not versions:
                self.log_error(f"No template versions found for agent {agent_name}")
                raise AIProviderError(f"No template versions found for agent {agent_name}")
            
            version = versions[-1]
        
        if version not in self.templates[agent_name]:
            self.log_error(f"Template version {version} not found for agent {agent_name}")
            raise AIProviderError(f"Template version {version} not found for agent {agent_name}")
        
        self.log_debug(f"Using template {version} for agent {agent_name}")
        return self.templates[agent_name][version].template
