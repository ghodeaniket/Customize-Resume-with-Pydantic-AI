#!/usr/bin/env python3
"""
Resume Customizer Server Setup Script

This script prepares and configures the Resume Customizer server environment
with appropriate settings for development and testing. It performs the following:

1. Validates the required directories exist (logs, uploads)
2. Sets up environment variables needed for the server 
3. Configures logging for development/testing
4. Provides clear instructions for starting the server

Usage:
    python server_setup.py [--port PORT] [--debug] [--test-mode]
"""

import os
import sys
import logging
import argparse
import shutil
from pathlib import Path


def setup_environment(debug: bool = True, test_mode: bool = False) -> None:
    """Set up the environment for the application.
    
    Args:
        debug: Whether to enable debug mode
        test_mode: Whether to run in test mode with minimal dependencies
    """
    # Define required directories
    required_dirs = ["logs", "uploads"]
    
    # Ensure required directories exist
    for directory in required_dirs:
        dir_path = Path.cwd() / directory
        if not dir_path.exists():
            print(f"Creating directory: {directory}")
            dir_path.mkdir(parents=True, exist_ok=True)
    
    # Check if .env file exists
    env_path = Path.cwd() / ".env"
    if not env_path.exists():
        env_example_path = Path.cwd() / ".env.example"
        if env_example_path.exists():
            print("Creating .env file from .env.example")
            shutil.copy(env_example_path, env_path)
        else:
            print("Warning: .env.example file not found. Please create a .env file manually.")
    
    # Set additional environment variables for testing
    if test_mode:
        print("Setting up test environment")
        os.environ["RESUME_CUSTOMIZER_DEBUG"] = "True"
        os.environ["RESUME_CUSTOMIZER_LOG_LEVEL"] = "DEBUG"
        os.environ["RESUME_CUSTOMIZER_TESTING"] = "True"
        
        # Use mock AI provider for testing if needed
        os.environ["RESUME_CUSTOMIZER_USE_MOCK_AI"] = "True"
    
    # Set debug mode
    if debug:
        os.environ["RESUME_CUSTOMIZER_DEBUG"] = "True"
        os.environ["RESUME_CUSTOMIZER_LOG_LEVEL"] = "DEBUG"
    
    # Validate API keys
    openai_key = os.environ.get("OPENAI_API_KEY")
    openrouter_key = os.environ.get("RESUME_CUSTOMIZER_OPENROUTER_API_KEY") or os.environ.get("OPENROUTER_API_KEY")
    
    if test_mode:
        # In test mode, use dummy keys if not provided
        if not openai_key:
            print("Setting dummy OPENAI_API_KEY for testing")
            os.environ["OPENAI_API_KEY"] = "sk-dummy-key-for-testing"
        
        if not openrouter_key:
            print("Setting dummy OPENROUTER_API_KEY for testing")
            os.environ["OPENROUTER_API_KEY"] = "sk-or-dummy-key-for-testing"
    else:
        # In normal mode, validate keys
        if not openai_key:
            print("Warning: OPENAI_API_KEY environment variable is not set")
            print("Some functionality may not work correctly")
        
        if not openrouter_key:
            print("Warning: OPENROUTER_API_KEY environment variable is not set")
            print("Please set it in the .env file or as an environment variable")
    
    print("Environment setup complete")


def setup_logging(debug: bool = True) -> None:
    """Configure logging for development and testing.
    
    Args:
        debug: Whether to enable debug mode
    """
    from core.logging import configure_logging
    
    # Set up logging
    if debug:
        os.environ["RESUME_CUSTOMIZER_LOG_LEVEL"] = "DEBUG"
    
    # Configure logging
    configure_logging()
    
    # Get logger
    logger = logging.getLogger(__name__)
    
    # Log setup
    log_level = os.environ.get("RESUME_CUSTOMIZER_LOG_LEVEL", "INFO")
    logger.info(f"Logging configured with level: {log_level}")
    
    print(f"Logging configured with level: {log_level}")
    print(f"Log files will be stored in: {Path.cwd() / 'logs'}")


def print_server_instructions(port: int = 8000) -> None:
    """Print instructions for starting the server.
    
    Args:
        port: Port to use for the server
    """
    print("\n" + "=" * 80)
    print("RESUME CUSTOMIZER SERVER SETUP COMPLETE")
    print("=" * 80)
    
    print("\nTo start the server, run one of the following commands:")
    print(f"\n1. Using run.py (recommended for development):")
    print(f"   python run.py --port {port} --reload")
    
    print(f"\n2. Using uvicorn directly:")
    print(f"   uvicorn main:app --host 0.0.0.0 --port {port} --reload")
    
    print(f"\n3. Using the run_server.py script:")
    print(f"   python run_server.py")
    
    print("\nAPI Documentation will be available at:")
    print(f"   http://localhost:{port}/docs")
    
    print("\nAPI endpoints to test the refactored file processing:")
    print(f"1. Upload Test: http://localhost:{port}/api/v1/resumes/upload-test")
    print(f"2. Resume Customization: http://localhost:{port}/api/v1/resumes/customize")
    print(f"3. Resume Customization via File Upload: http://localhost:{port}/api/v1/resumes/customize-upload")
    
    print("\nHealth Check:")
    print(f"   http://localhost:{port}/health")
    print("\n" + "=" * 80)


def main() -> int:
    """Main entry point for the script.
    
    Returns:
        int: Exit code
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Set up Resume Customizer server")
    parser.add_argument("--port", type=int, default=8000, help="Port to use for the server")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--test-mode", action="store_true", help="Set up for testing with mock services")
    
    args = parser.parse_args()
    
    try:
        # Set up environment
        setup_environment(debug=args.debug, test_mode=args.test_mode)
        
        # Import and configure server components
        from core.config import get_settings
        
        # Configure logging
        setup_logging(debug=args.debug)
        
        # Print instructions
        print_server_instructions(port=args.port)
        
        return 0
    except Exception as e:
        print(f"Error setting up server: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
