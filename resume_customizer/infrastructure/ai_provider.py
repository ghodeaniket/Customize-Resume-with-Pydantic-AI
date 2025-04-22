"""AI provider integration for the Resume Customizer application.

This module contains the integration with OpenRouter for AI model access.
"""

import time
from typing import Any, Dict, List, Optional, Union

import httpx
from loguru import logger

from resume_customizer.core.config import settings
from resume_customizer.core.exceptions import AIProviderError


class OpenRouterProvider:
    """Integration with OpenRouter AI provider.
    
    This class handles communication with the OpenRouter API for accessing
    various AI models.
    """
    
    BASE_URL = "https://openrouter.ai/api/v1"
    CHAT_ENDPOINT = "/chat/completions"
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the OpenRouter provider.
        
        Args:
            api_key: The API key for OpenRouter. If None, use the key from settings.
        """
        self.api_key = api_key or settings.OPENROUTER_API_KEY
    
    async def generate_response(
        self,
        http_client: httpx.AsyncClient,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """Generate a response from OpenRouter.
        
        Args:
            http_client: The HTTP client to use for the request
            messages: The messages to send to the model
            model: The model to use
            temperature: The temperature for generation
            max_tokens: The maximum number of tokens to generate
            stream: Whether to stream the response
            
        Returns:
            Dict[str, Any]: The response from OpenRouter
            
        Raises:
            AIProviderError: If there's an error with the OpenRouter API
        """
        url = f"{self.BASE_URL}{self.CHAT_ENDPOINT}"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://resumecustomizer.ai",  # Replace with your production domain
            "X-Title": "Resume Customizer"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": stream,
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        try:
            logger.debug(f"Sending request to OpenRouter (model: {model})")
            start_time = time.time()
            
            response = await http_client.post(
                url,
                headers=headers,
                json=payload,
                timeout=180.0  # 3 minutes timeout
            )
            
            elapsed_time = time.time() - start_time
            logger.debug(f"OpenRouter response received in {elapsed_time:.2f} seconds")
            
            # Check for HTTP errors
            response.raise_for_status()
            
            # Parse response
            result = response.json()
            
            # Log token usage
            if "usage" in result:
                prompt_tokens = result["usage"].get("prompt_tokens", 0)
                completion_tokens = result["usage"].get("completion_tokens", 0)
                total_tokens = result["usage"].get("total_tokens", 0)
                
                logger.info(
                    f"Token usage: {prompt_tokens} prompt + {completion_tokens} "
                    f"completion = {total_tokens} total"
                )
            
            return result
            
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP error from OpenRouter: {str(e)}"
            logger.error(error_msg)
            
            # Try to parse the error response
            try:
                error_data = e.response.json()
                error_detail = error_data.get("error", {}).get("message", str(e))
                raise AIProviderError(
                    error_detail,
                    provider="OpenRouter",
                    status_code=e.response.status_code
                )
            except (ValueError, KeyError):
                # If we can't parse the error response, use the original error
                raise AIProviderError(
                    str(e),
                    provider="OpenRouter",
                    status_code=e.response.status_code
                )
                
        except httpx.RequestError as e:
            error_msg = f"Request error to OpenRouter: {str(e)}"
            logger.error(error_msg)
            raise AIProviderError(error_msg, provider="OpenRouter")
            
        except Exception as e:
            error_msg = f"Unexpected error with OpenRouter: {str(e)}"
            logger.exception(error_msg)
            raise AIProviderError(error_msg, provider="OpenRouter")


# Instantiate the provider
openrouter_provider = OpenRouterProvider()
