"""Base agent implementation for Resume Customizer."""
import time
from typing import Optional, Type, TypeVar, Union, Dict, Any

from pydantic_ai import Agent
from pydantic_ai.usage import Usage, UsageLimits

from core.logging import LoggerMixin
from infrastructure.ai_provider import ResumeCustomizerDeps, PromptManager

T = TypeVar('T')


class BaseAgent(LoggerMixin):
    """Base class for all Resume Customizer agents."""
    
    def __init__(
        self,
        prompt_manager: PromptManager,
        agent_type: str,
        output_type: Type[T]
    ):
        """Initialize base agent.
        
        Args:
            prompt_manager: Manager for prompt templates
            agent_type: Type of agent (e.g., "strategist", "profiler")
            output_type: Expected output type for the agent
        """
        self.prompt_manager = prompt_manager
        self.agent_type = agent_type
        
        # Initialize the Pydantic AI agent with test model for unit tests
        # Actual model will be provided through deps.model_provider
        self.agent = Agent(
            'test',  # Placeholder model name, will use the model from deps
            deps_type=ResumeCustomizerDeps,
            output_type=output_type,
            system_prompt=self._get_system_prompt(),
        )
        
        # Configure the agent to use the model provider from dependencies
        @self.agent.model_provider
        def get_model_provider(deps: ResumeCustomizerDeps):
            """Provide the model provider from dependencies."""
            if deps.model_provider is None:
                self.log_warning(f"No model provider found in dependencies for {self.agent_type} agent")
            return deps.model_provider
        
        # Set dynamic system prompt for model configuration
        @self.agent.system_prompt
        async def set_model(ctx):
            """Set the specific model to use via dynamic system prompt."""
            return f"You will be using the {ctx.deps.model_name} model to process the request."
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the agent.
        
        Returns:
            str: System prompt
        """
        try:
            # Attempt to get the prompt from the prompt manager
            return self.prompt_manager.get_template(self.agent_type, "latest")
        except Exception as e:
            # Log the error and use fallback prompt
            self.log_warning(f"Failed to load prompt for {self.agent_type}: {str(e)}")
            return self._get_fallback_prompt()
    
    def _get_fallback_prompt(self) -> str:
        """Get fallback system prompt when prompt manager fails.
        
        Returns:
            str: Fallback system prompt
        """
        # Base fallback prompt for generic agent
        self.log_info(f"Using fallback prompt for {self.agent_type}")
        return (
            "You are an AI assistant helping with resume customization. "
            "Your task is to analyze the provided content and provide useful output."
        )
    
    async def run(
        self, 
        input_text: str,
        deps: ResumeCustomizerDeps,
        usage: Optional[Usage] = None,
        usage_limits: Optional[UsageLimits] = None,
        extra_context: Optional[Dict[str, Any]] = None
    ) -> T:
        """Run the agent with the provided input.
        
        Args:
            input_text: Input text for the agent
            deps: Agent dependencies
            usage: Optional usage tracker
            usage_limits: Optional usage limits
            extra_context: Additional context for the agent
            
        Returns:
            T: Agent output
        """
        self.log_info(f"Running {self.agent_type} agent")
        
        # Validate that we have a model provider
        if deps.model_provider is None:
            self.log_error(f"Missing model provider for {self.agent_type} agent")
            raise ValueError(f"Missing model provider for {self.agent_type} agent")
        
        # Add logging context for operation
        log_context = {
            "agent_type": self.agent_type,
            "model_name": deps.model_name,
            "input_length": len(input_text)
        }
        
        if extra_context:
            log_context.update(extra_context)
            
        self.log_debug(f"Agent context", extra=log_context)
        
        # Manually add operation logging that was previously handled by the decorator
        operation_name = "agent_run"
        self.log_info(f"Starting {operation_name}")
        start_time = time.time()
        
        try:
            # Run the agent
            result = await self.agent.run(
                input_text,
                deps=deps,
                usage=usage,
                usage_limits=usage_limits
            )
            
            # Log token usage
            if usage:
                self.log_info(f"Agent usage", extra={
                    "requests": usage.requests,
                    "total_tokens": usage.total_tokens
                })
                
            duration_ms = (time.time() - start_time) * 1000
            self.log_info(f"Completed {operation_name} in {duration_ms:.2f}ms")
            self.log_performance(operation_name, duration_ms, True)
            
            return result.output
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.log_error(f"Error in {operation_name}: {str(e)}", exc_info=e)
            self.log_performance(operation_name, duration_ms, False, 
                               {"error": str(e), "error_type": type(e).__name__})
            raise
