"""Mock implementation of the pydantic_ai module for testing.

This module provides mock classes that match the interface of pydantic_ai
but don't require the actual package to be installed correctly.
"""

from dataclasses import dataclass
from typing import Any, Dict, Generic, Optional, Type, TypeVar

# Type variables for generic classes
T = TypeVar('T')
D = TypeVar('D')
O = TypeVar('O')


@dataclass
class AgentRunResult(Generic[O]):
    """Mock class for AgentRunResult.
    
    This matches the interface of the actual AgentRunResult class
    but doesn't require the actual pydantic_ai package.
    """
    output: O
    token_usage: Dict[str, int] = None
    model_info: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.token_usage is None:
            self.token_usage = {}
        if self.model_info is None:
            self.model_info = {}


@dataclass
class RunContext(Generic[D]):
    """Mock class for RunContext.
    
    This matches the interface of the actual RunContext class
    but doesn't require the actual pydantic_ai package.
    """
    deps: D
    
    def __init__(self, deps: D):
        self.deps = deps


class Agent(Generic[D, O]):
    """Mock class for Agent.
    
    This matches the interface of the actual Agent class
    but doesn't require the actual pydantic_ai package.
    """
    
    def __init__(
        self, 
        model_provider: str, 
        system_prompt: str = None,
        deps_type: Type[D] = None,
        output_type: Type[O] = None,
    ):
        """Initialize the agent."""
        self.model_provider = model_provider
        self.system_prompt = system_prompt
        self.deps_type = deps_type
        self.output_type = output_type
        self.tools = []
    
    def tool(self, func):
        """Decorator for registering a tool."""
        self.tools.append(func)
        return func
    
    def system_prompt(self, func):
        """Decorator for registering a dynamic system prompt."""
        self._dyn_system_prompt = func
        return func
    
    async def run(self, prompt: str, deps: D = None) -> AgentRunResult[O]:
        """Run the agent."""
        # This is a mock implementation that just returns a simulated result
        # For testing purposes, we'll create a simple instance of the output type
        if self.output_type:
            if isinstance(self.output_type, type) and hasattr(self.output_type, '__annotations__'):
                # Create an instance with default values
                output_instance = self.output_type()
            else:
                # Just use the type as is
                output_instance = self.output_type()
        else:
            output_instance = prompt  # Echo back the prompt
        
        return AgentRunResult(output=output_instance)
    
    def run_sync(self, prompt: str, deps: D = None) -> AgentRunResult[O]:
        """Synchronous version of run."""
        import asyncio
        return asyncio.run(self.run(prompt, deps))
