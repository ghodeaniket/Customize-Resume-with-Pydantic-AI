"""Configuration management for the Resume Customizer application."""

import os
from typing import Any, Dict, List, Optional, Union

from pydantic import AnyHttpUrl, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings for the Resume Customizer.
    
    All environment variables with the prefix RESUME_CUSTOMIZER_ will be loaded
    into this settings class.
    """
    # API Settings
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Resume Customizer"
    DEBUG: bool = False
    
    # OpenRouter Settings
    OPENROUTER_API_KEY: str
    DEFAULT_MODEL: str = "deepseek/deepseek-r1-distill-llama-70b"
    
    # OpenAI Settings (not prefixed since used directly by OpenAI library)
    # This is outside of the RESUME_CUSTOMIZER_ prefix
    OPENAI_API_KEY: Optional[str] = None
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        """Parse CORS origins from string or list."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # File Upload Settings
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB in bytes
    ALLOWED_EXTENSIONS: List[str] = ["pdf", "docx", "txt"]
    UPLOAD_DIRECTORY: str = "./uploads"
    
    # Caching
    ENABLE_CACHE: bool = True
    CACHE_TTL: int = 3600  # Default cache TTL in seconds (1 hour)
    REDIS_URL: Optional[str] = None  # Redis connection URL (None for in-memory cache)
    
    # Logging
    LOG_LEVEL: str = "INFO"
    ENABLE_PERFORMANCE_LOGGING: bool = True
    
    class Config:
        """Pydantic configuration for Settings."""
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_prefix = "RESUME_CUSTOMIZER_"  # Look for env vars with this prefix
        extra = "ignore"  # Allow extra fields in the environment


# Instantiate settings
settings = Settings()
