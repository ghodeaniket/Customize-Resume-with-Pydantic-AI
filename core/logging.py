"""Logging configuration for Resume Customizer."""
import logging
import os
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
    log_level_str = settings.log_level.upper()
    log_level = LOG_LEVELS.get(log_level_str, logging.INFO)
    
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(os.getcwd(), 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    # Create file handler for logging to file
    file_handler = logging.FileHandler(os.path.join(logs_dir, 'app.log'))
    file_handler.setLevel(log_level)
    
    # Create console handler for logging to stdout
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    # Create formatters
    file_formatter = logging.Formatter('%(asctime)s | %(levelname)-8s | %(name)s:%(filename)s:%(lineno)d | %(message)s')
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    file_handler.setFormatter(file_formatter)
    console_handler.setFormatter(console_formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add handlers to root logger
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Configure specific loggers
    for logger_name, logger_level in [
        ('httpx', logging.WARNING),
        ('uvicorn', logging.WARNING),
        ('PyPDF2', logging.WARNING),
    ]:
        logging.getLogger(logger_name).setLevel(logger_level)
    
    # Log configuration info
    logging.info(f"Logging configured with level: {log_level_str}")
    

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
    
    def log_warning(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log warning message.
        
        Args:
            message: Message to log
            extra: Optional extra information to include in log
        """
        self.logger.warning(message, extra=extra)
