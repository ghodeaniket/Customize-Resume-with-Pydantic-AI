"""Application runner script."""
import logging
import os
import sys
from typing import Optional

from dotenv import load_dotenv
import uvicorn

from core.config import get_settings
from core.logging import configure_logging
from infrastructure.init_prompts import init_prompt_manager


def setup_environment() -> None:
    """Set up the environment for the application."""
    # Load environment variables from .env file
    load_dotenv()
    
    # Configure logging
    configure_logging()
    
    # Get logger
    logger = logging.getLogger(__name__)
    
    # Check for required environment variables
    settings = get_settings()
    if not settings.openrouter_api_key:
        logger.error("OPENROUTER_API_KEY environment variable is not set")
        print("Error: OPENROUTER_API_KEY environment variable is not set")
        print("Please set it in the .env file or as an environment variable")
        sys.exit(1)


def init_application() -> None:
    """Initialize the application."""
    # Get logger
    logger = logging.getLogger(__name__)
    
    # Initialize prompt manager
    logger.info("Initializing prompt manager")
    init_prompt_manager()
    
    # Log initialization completion
    logger.info("Application initialization complete")


def run_application(
    host: str = "0.0.0.0", 
    port: int = 8000, 
    reload: bool = False,
    log_level: Optional[str] = None
) -> None:
    """Run the application.
    
    Args:
        host: Host to bind to
        port: Port to bind to
        reload: Enable auto-reload
        log_level: Log level for uvicorn
    """
    # Set up environment
    setup_environment()
    
    # Initialize application
    init_application()
    
    # Get logger
    logger = logging.getLogger(__name__)
    logger.info(f"Starting application on {host}:{port}")
    
    # Get settings
    settings = get_settings()
    
    # Determine log level
    uvicorn_log_level = log_level or settings.log_level.lower()
    
    # Run application
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level=uvicorn_log_level
    )


if __name__ == "__main__":
    # Parse command line arguments
    import argparse
    
    parser = argparse.ArgumentParser(description="Run the Resume Customizer application")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--log-level", type=str, help="Log level for uvicorn")
    
    args = parser.parse_args()
    
    # Run application
    run_application(
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level
    )
