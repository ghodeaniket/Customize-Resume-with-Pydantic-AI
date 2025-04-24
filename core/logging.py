"""Logging configuration for Resume Customizer."""
import logging
import sys
from typing import Any, Dict, Optional

from .config import get_settings

# Define log levels
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


def configure_logging() -> None:
    """Configure logging for the application."""
    settings = get_settings()
    
    # Get log level from settings
    log_level = LOG_LEVELS.get(settings.log_level.upper(), logging.INFO)
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    
    # Set specific loggers to desired levels
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    

class LoggerMixin:
    """Mixin class that provides logging functionality."""
    
    @property
    def logger(self) -> logging.Logger:
        """Get logger for the current class.
        
        Returns:
            logging.Logger: Logger instance
        """
        return logging.getLogger(self.__class__.__name__)
    
    def log_info(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log info message.
        
        Args:
            message: Message to log
            extra: Optional extra information to include in log
        """
        self.logger.info(message, extra=extra)
    
    def log_error(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log error message.
        
        Args:
            message: Message to log
            extra: Optional extra information to include in log
        """
        self.logger.error(message, extra=extra)
    
    def log_debug(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log debug message.
        
        Args:
            message: Message to log
            extra: Optional extra information to include in log
        """
        self.logger.debug(message, extra=extra)
