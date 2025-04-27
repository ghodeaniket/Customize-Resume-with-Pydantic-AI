"""OpenRouter API client for Resume Customizer."""
import httpx
import json
from typing import Any, Dict, List, Optional, Union

from core.logging import LoggerMixin


class OpenRouterClient(LoggerMixin):
    """Client for OpenRouter API."""
    
    def __init__(
        self, 
        api_key: str, 
        base_url: str = "https://openrouter.ai/api/v1",
        application_name: str = "Resume Customizer",
        referer: str = "https://resume-customizer.example.com"
    ):
        """Initialize OpenRouter client.
        
        Args:
            api_key: OpenRouter API key
            base_url: OpenRouter API base URL
            application_name: Name of the application
            referer: HTTP referer for OpenRouter
        """
        self.api_key = api_key
        self.base_url = base_url
        self.application_name = application_name
        self.referer = referer
        
        self.log_info(f"Initializing OpenRouter client with base URL: {base_url}")
        
        # Define headers with proper Authorization header
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": referer,
            "X-Title": application_name,
            "Content-Type": "application/json"
        }
        
        # Create HTTP client with headers
        self.client = httpx.AsyncClient(
            headers=self.headers,
            timeout=120.0  # Long timeout for larger responses
        )
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """Generate a chat completion using OpenRouter.
        
        Args:
            messages: List of message dictionaries
            model: Model identifier
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            
        Returns:
            Dict: API response
        """
        url = f"{self.base_url}/chat/completions"
        
        # Build request payload
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": stream
        }
        
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        
        self.log_debug(f"Making OpenRouter API request", extra={
            "url": url,
            "model": model,
            "message_count": len(messages),
            "temperature": temperature,
            "max_tokens": max_tokens
        })
        
        try:
            # Print headers for debugging
            self.log_debug(f"Request headers: {self.headers}")
            
            response = await self.client.post(
                url,
                json=payload
            )
            
            # Log response status
            self.log_debug(f"Response status: {response.status_code}")
            
            response.raise_for_status()
            
            result = response.json()
            
            self.log_debug(f"OpenRouter API request successful", extra={
                "model": model,
                "choices": len(result.get("choices", [])),
                "usage": result.get("usage", {})
            })
            
            return result
            
        except httpx.HTTPStatusError as e:
            # Handle HTTP errors (e.g., 401, 403, 404)
            error_detail = f"HTTP error {e.response.status_code}"
            try:
                error_json = e.response.json()
                self.log_debug(f"Error response: {error_json}")
                if "error" in error_json:
                    error_detail = f"{error_detail}: {error_json['error']}"
                else:
                    error_detail = f"{error_detail}: {error_json}"
            except:
                pass
                
            self.log_error(f"OpenRouter API error: {error_detail}", extra={
                "status_code": e.response.status_code,
                "url": url,
                "response_text": e.response.text
            })
            
            raise Exception(f"OpenRouter API error: {error_detail}")
            
        except Exception as e:
            self.log_error(f"OpenRouter request failed: {str(e)}")
            raise Exception(f"OpenRouter request failed: {str(e)}")
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
