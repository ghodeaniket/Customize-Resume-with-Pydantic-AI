"""Prompt management system for AI agents.

This module provides a structured approach to managing prompts with versioning
and metadata to ensure consistency, traceability, and enable A/B testing of
different prompt variants.
"""

import datetime
from typing import Dict, List, Optional
from uuid import uuid4

from loguru import logger
from pydantic import BaseModel, Field, model_validator

from resume_customizer.core.config import settings


class PromptTemplate(BaseModel):
    """Versioned prompt template for agents with metadata.
    
    Attributes:
        version: Semantic version string (e.g., "1.0.0")
        template: The actual prompt template content
        description: Human-readable description of the prompt
        tags: Optional list of tags for categorization
        created_at: Timestamp when the prompt was created
        created_by: Optional identifier of the creator
        is_active: Whether this prompt version is active
        metrics: Optional performance metrics for this prompt version
    """
    version: str
    template: str
    description: str
    tags: List[str] = Field(default_factory=list)
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    created_by: Optional[str] = None
    is_active: bool = True
    id: str = Field(default_factory=lambda: str(uuid4()))
    metrics: Dict[str, float] = Field(default_factory=dict)
    
    @model_validator(mode="after")
    def validate_version_format(self) -> "PromptTemplate":
        """Validate that the version follows semantic versioning format."""
        import re
        if not re.match(r"^\d+\.\d+\.\d+$", self.version):
            logger.warning(f"Prompt version '{self.version}' does not follow semantic versioning")
        return self


class PromptManager:
    """Manager for versioned prompt templates with support for A/B testing.
    
    This class provides functionality to:
    - Store and retrieve versioned prompts
    - Track performance metrics for different prompt versions
    - Support A/B testing of prompts
    - Export/import prompt collections
    """
    def __init__(self):
        self.templates: Dict[str, Dict[str, PromptTemplate]] = {}
        self.active_versions: Dict[str, str] = {}
        self.ab_test_weights: Dict[str, Dict[str, float]] = {}
        logger.info("Initialized PromptManager")
    
    def add_template(self, agent_name: str, template: PromptTemplate) -> None:
        """Add a new prompt template for an agent.
        
        Args:
            agent_name: Identifier for the agent
            template: The prompt template to add
        """
        if agent_name not in self.templates:
            self.templates[agent_name] = {}
        
        self.templates[agent_name][template.version] = template
        
        # Set as active version if it's the first one or explicitly marked as active
        if template.is_active or len(self.templates[agent_name]) == 1:
            self.set_active_version(agent_name, template.version)
        
        logger.info(f"Added prompt template v{template.version} for {agent_name}")
    
    def get_template(self, agent_name: str, version: Optional[str] = None) -> PromptTemplate:
        """Get a prompt template by version.
        
        Args:
            agent_name: Identifier for the agent
            version: Specific version to retrieve, or None for active version
            
        Returns:
            The prompt template
            
        Raises:
            KeyError: If the agent or version doesn't exist
        """
        if agent_name not in self.templates:
            raise KeyError(f"No templates found for agent: {agent_name}")
        
        # If specific version requested
        if version:
            if version not in self.templates[agent_name]:
                raise KeyError(f"Version {version} not found for agent: {agent_name}")
            return self.templates[agent_name][version]
        
        # Get active version
        active_version = self.active_versions.get(agent_name)
        if not active_version:
            # Default to latest version by semantic versioning
            versions = sorted(self.templates[agent_name].keys(), 
                             key=lambda v: [int(x) for x in v.split('.')])
            active_version = versions[-1]
            self.active_versions[agent_name] = active_version
        
        return self.templates[agent_name][active_version]
    
    def get_prompt_text(self, agent_name: str, version: Optional[str] = None) -> str:
        """Get the prompt template text.
        
        Args:
            agent_name: Identifier for the agent
            version: Specific version to retrieve, or None for active version
            
        Returns:
            The prompt template text
            
        Raises:
            KeyError: If the agent or version doesn't exist
        """
        template = self.get_template(agent_name, version)
        return template.template
    
    def set_active_version(self, agent_name: str, version: str) -> None:
        """Set the active version for an agent.
        
        Args:
            agent_name: Identifier for the agent
            version: Version to set as active
            
        Raises:
            KeyError: If the agent or version doesn't exist
        """
        if agent_name not in self.templates:
            raise KeyError(f"No templates found for agent: {agent_name}")
        
        if version not in self.templates[agent_name]:
            raise KeyError(f"Version {version} not found for agent: {agent_name}")
        
        # Update active status for all versions
        for v, template in self.templates[agent_name].items():
            template.is_active = (v == version)
        
        self.active_versions[agent_name] = version
        logger.info(f"Set active prompt version to {version} for {agent_name}")
    
    def setup_ab_test(self, agent_name: str, version_weights: Dict[str, float]) -> None:
        """Set up A/B testing between multiple prompt versions.
        
        Args:
            agent_name: Identifier for the agent
            version_weights: Dictionary mapping versions to their weights
            
        Raises:
            KeyError: If any version doesn't exist
            ValueError: If weights don't sum to 1.0
        """
        if agent_name not in self.templates:
            raise KeyError(f"No templates found for agent: {agent_name}")
        
        # Validate versions
        for version in version_weights:
            if version not in self.templates[agent_name]:
                raise KeyError(f"Version {version} not found for agent: {agent_name}")
        
        # Validate weights
        weight_sum = sum(version_weights.values())
        if abs(weight_sum - 1.0) > 1e-6:  # Allow for minor floating point imprecision
            raise ValueError(f"Weights must sum to 1.0, got {weight_sum}")
        
        self.ab_test_weights[agent_name] = version_weights
        logger.info(f"Set up A/B test for {agent_name} with weights: {version_weights}")
    
    def get_ab_test_version(self, agent_name: str) -> str:
        """Get a version for A/B testing based on configured weights.
        
        Args:
            agent_name: Identifier for the agent
            
        Returns:
            Selected version based on configured weights
            
        Raises:
            KeyError: If no A/B test is set up for the agent
        """
        if agent_name not in self.ab_test_weights:
            raise KeyError(f"No A/B test configured for agent: {agent_name}")
        
        import random
        
        # Use weighted random selection
        weights = self.ab_test_weights[agent_name]
        versions = list(weights.keys())
        weights_list = [weights[v] for v in versions]
        
        selected_version = random.choices(versions, weights=weights_list, k=1)[0]
        logger.debug(f"A/B test selected version {selected_version} for {agent_name}")
        
        return selected_version
    
    def record_metrics(self, agent_name: str, version: str, metrics: Dict[str, float]) -> None:
        """Record performance metrics for a prompt version.
        
        Args:
            agent_name: Identifier for the agent
            version: Prompt version
            metrics: Dictionary of metric names to values
            
        Raises:
            KeyError: If the agent or version doesn't exist
        """
        if agent_name not in self.templates:
            raise KeyError(f"No templates found for agent: {agent_name}")
        
        if version not in self.templates[agent_name]:
            raise KeyError(f"Version {version} not found for agent: {agent_name}")
        
        # Update metrics
        template = self.templates[agent_name][version]
        for key, value in metrics.items():
            # Average with existing metrics if present
            if key in template.metrics:
                template.metrics[key] = (template.metrics[key] + value) / 2
            else:
                template.metrics[key] = value
        
        logger.debug(f"Recorded metrics for {agent_name} v{version}: {metrics}")
    
    def export_templates(self, agent_name: Optional[str] = None) -> Dict:
        """Export prompt templates as a dictionary.
        
        Args:
            agent_name: Optional agent name to export only templates for that agent
            
        Returns:
            Dictionary of exported templates
        """
        if agent_name:
            if agent_name not in self.templates:
                raise KeyError(f"No templates found for agent: {agent_name}")
            
            return {
                agent_name: {
                    version: template.model_dump()
                    for version, template in self.templates[agent_name].items()
                }
            }
        else:
            return {
                agent: {
                    version: template.model_dump() 
                    for version, template in templates.items()
                }
                for agent, templates in self.templates.items()
            }
    
    def import_templates(self, data: Dict) -> None:
        """Import prompt templates from a dictionary.
        
        Args:
            data: Dictionary of templates to import
        """
        for agent_name, templates in data.items():
            for version, template_data in templates.items():
                template = PromptTemplate(**template_data)
                self.add_template(agent_name, template)
        
        logger.info(f"Imported templates for {len(data)} agents")


# Create a singleton instance
prompt_manager = PromptManager()
