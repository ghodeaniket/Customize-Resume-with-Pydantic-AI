"""Configuration management for Resume Customizer."""
import os
import logging
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field, validator
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


class Settings(BaseModel):
    """Application settings loaded from environment variables."""
    
    # API settings
    api_title: str = "Resume Customizer API"
    api_description: str = "Customize resumes for specific job descriptions using AI agents"
    api_version: str = "0.1.0"
    
    # OpenRouter settings
    openrouter_api_key: str = Field(
        default_factory=lambda: os.getenv("OPENROUTER_API_KEY", "")
    )
    default_model: str = Field(
        default_factory=lambda: os.getenv("MODEL_NAME", "deepseek/deepseek-r1-distill-llama-70b")
    )
    
    # Application settings
    log_level: str = Field(
        default_factory=lambda: os.getenv("LOG_LEVEL", "INFO")
    )
    
    # Token usage limits
    default_token_limit: int = Field(
        default_factory=lambda: int(os.getenv("DEFAULT_TOKEN_LIMIT", "4000"))
    )
    
    # Rate limiting
    rate_limit_per_minute: int = Field(
        default_factory=lambda: int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    )
    
    # Caching settings
    enable_response_cache: bool = Field(
        default_factory=lambda: os.getenv("ENABLE_RESPONSE_CACHE", "false").lower() == "true"
    )
    cache_ttl_seconds: int = Field(
        default_factory=lambda: int(os.getenv("CACHE_TTL_SECONDS", "300"))  # 5 minutes default
    )
    
    @validator("log_level")
    def validate_log_level(cls, v: str) -> str:
        """Validate log level.
        
        Args:
            v: Log level
            
        Returns:
            str: Valid log level
            
        Raises:
            ValueError: If log level is invalid
        """
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            logger.warning(f"Invalid log level: {v}, defaulting to INFO")
            return "INFO"
        return v.upper()
    
    @validator("default_token_limit")
    def validate_token_limit(cls, v: int) -> int:
        """Validate token limit.
        
        Args:
            v: Token limit
            
        Returns:
            int: Valid token limit
        """
        if v <= 0:
            logger.warning(f"Invalid token limit: {v}, defaulting to 4000")
            return 4000
        return v
    
    @validator("rate_limit_per_minute")
    def validate_rate_limit(cls, v: int) -> int:
        """Validate rate limit.
        
        Args:
            v: Rate limit
            
        Returns:
            int: Valid rate limit
        """
        if v <= 0:
            logger.warning(f"Invalid rate limit: {v}, defaulting to 60")
            return 60
        return v
    
    @validator("cache_ttl_seconds")
    def validate_cache_ttl(cls, v: int) -> int:
        """Validate cache TTL.
        
        Args:
            v: Cache TTL
            
        Returns:
            int: Valid cache TTL
        """
        if v < 0:
            logger.warning(f"Invalid cache TTL: {v}, defaulting to 300")
            return 300
        return v
    
    def dict_with_environment_info(self) -> Dict[str, Any]:
        """Get settings as dict with additional environment information.
        
        Returns:
            Dict[str, Any]: Settings with environment info
        """
        settings_dict = self.dict()
        
        # Add environment-specific information
        settings_dict["environment"] = os.getenv("ENVIRONMENT", "development")
        settings_dict["debug_mode"] = self.log_level.upper() == "DEBUG"
        
        # Security: Mask sensitive values
        if "openrouter_api_key" in settings_dict and settings_dict["openrouter_api_key"]:
            settings_dict["openrouter_api_key"] = "****" + settings_dict["openrouter_api_key"][-4:]
        
        return settings_dict
    

# Create global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings.
    
    Returns:
        Settings: Application settings
    """
    return settings
