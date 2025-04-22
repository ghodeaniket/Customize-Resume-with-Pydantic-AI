"""Logging configuration for the Resume Customizer application."""

import logging
import sys
from typing import Any, Dict, List, Optional

from loguru import logger

from .config import settings


class InterceptHandler(logging.Handler):
    """Intercept standard logging and redirect to loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record to loguru.
        
        Args:
            record: The log record to emit.
        """
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_logging(log_level: Optional[str] = None) -> None:
    """Configure logging for the application.
    
    Args:
        log_level: The log level to use. If None, use the value from settings.
    """
    # Get log level from settings if not specified
    log_level = log_level or settings.LOG_LEVEL
    
    # Mapping of string log levels to int
    logging_levels = {
        "CRITICAL": logging.CRITICAL,
        "ERROR": logging.ERROR,
        "WARNING": logging.WARNING,
        "INFO": logging.INFO,
        "DEBUG": logging.DEBUG,
    }
    
    # Convert string level to int
    level = logging_levels.get(log_level.upper(), logging.INFO)
    
    # Remove default loggers
    logging.root.handlers = []
    logging.root.setLevel(level)
    
    # Intercept logging from standard library
    for name in logging.root.manager.loggerDict.keys():
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = True
    
    # Configure loguru
    logger.configure(
        handlers=[
            {
                "sink": sys.stdout,
                "format": "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
                "level": level,
                "diagnose": True,
            }
        ]
    )
    
    # Intercept standard logging
    logging.root.handlers = [InterceptHandler()]
    
    # Add specific loggers
    for logger_name in ["uvicorn", "uvicorn.error", "fastapi"]:
        logging.getLogger(logger_name).handlers = [InterceptHandler()]
    
    logger.info(f"Logging configured with level: {log_level}")


# Export the logger instance
app_logger = logger
