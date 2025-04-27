"""Custom model provider for Pydantic AI using OpenRouter."""
from typing import Any, Dict, List, Optional, Union
import time

from pydantic_ai.models import ModelResponse

from core.logging import LoggerMixin
from infrastructure.openrouter_client import OpenRouterClient


class OpenRouterModel(LoggerMixin):
    """Pydantic AI model implementation for OpenRouter."""
    
    def __init__(self, client: OpenRouterClient, model_name: str):
        """Initialize OpenRouter model.
        
        Args:
            client: OpenRouter client
            model_name: Model name (e.g., "deepseek/deepseek-r1-distill-llama-70b")
        """
        self.client = client
        self.model_name = model_name
        self.log_info(f"Initialized OpenRouter model with model name: {model_name}")
        
    async def generate(
        self,
        text: str,
        messages: list,
        settings: Optional[Any] = None,
        stream: bool = False,
    ) -> ModelResponse:
        """Generate a response from the model.
        
        Args:
            text: Input text
            messages: Message history
            settings: Model settings
            stream: Whether to stream the response
            
        Returns:
            ModelResponse: Model response
        """
        temperature = 0.7
        if settings and hasattr(settings, "temperature"):
            temperature = settings.temperature
        
        max_tokens = None
        if settings and hasattr(settings, "max_tokens"):
            max_tokens = settings.max_tokens
        
        # Convert Pydantic AI messages to OpenRouter format
        openrouter_messages = []
        
        # Add system message if present
        system_message = next((m for m in messages if m.get("role") == "system"), None)
        if system_message:
            openrouter_messages.append({
                "role": "system",
                "content": system_message["content"]
            })
        
        # Add user message
        openrouter_messages.append({
            "role": "user",
            "content": text
        })
        
        # Add any additional messages from history
        for msg in messages:
            if msg.get("role") in ["user", "assistant"] and "content" in msg:
                # Skip if already added
                if msg.get("role") == "user" and msg.get("content") == text:
                    continue
                
                openrouter_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        self.log_debug(f"Generating response from OpenRouter", extra={
            "model": self.model_name,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "message_count": len(openrouter_messages)
        })
        
        # Make API call
        response = await self.client.chat_completion(
            messages=openrouter_messages,
            model=self.model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream
        )
        
        # Extract response text
        response_text = ""
        if "choices" in response and len(response["choices"]) > 0:
            if "message" in response["choices"][0]:
                response_text = response["choices"][0]["message"]["content"]
        
        # Log usage statistics if available
        if "usage" in response:
            self.log_info(f"OpenRouter response usage", extra=response["usage"])
        
        # Create ModelResponse
        # Based on pydantic_ai.models.ModelResponse parameter inspection,
        # ModelResponse needs 'parts', 'model_name', 'timestamp', and 'kind'
        return ModelResponse(
            parts=[response_text],  # Pass the response text as a list of parts
            model_name=self.model_name,
            timestamp=time.time(),
            kind="llm"  # Standard kind for language model responses
        )