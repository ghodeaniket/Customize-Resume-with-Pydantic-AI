"""Configuration management for Resume Customizer."""
import os
from typing import Optional

from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


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
    default_token_limit: int = 4000
    

# Create global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings.
    
    Returns:
        Settings: Application settings
    """
    return settings
