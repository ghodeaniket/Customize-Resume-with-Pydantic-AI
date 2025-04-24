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


import os
import uuid
from pathlib import Path
import time

def setup_logging(log_level: Optional[str] = None) -> None:
    """Configure logging for the application with comprehensive coverage.
    
    Args:
        log_level: The log level to use. If None, use the value from settings.
    """
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Get log level from settings if not specified
    log_level = log_level or settings.LOG_LEVEL
    
    # Mapping of string log levels to int
    logging_levels = {
        "CRITICAL": logging.CRITICAL,
        "ERROR": logging.ERROR,
        "WARNING": logging.WARNING,
        "INFO": logging.INFO,
        "DEBUG": logging.DEBUG,
        "TRACE": 5,  # Custom trace level
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
    
    # Define log format with additional context
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<yellow>{extra[request_id]}</yellow> - "
        "<level>{message}</level>"
    )
    
    # Configure loguru handlers
    handlers = [
        # Console handler
        {
            "sink": sys.stdout,
            "format": log_format,
            "level": level,
            "diagnose": True,
            "backtrace": True,
        },
        # Application log file
        {
            "sink": logs_dir / "app.log",
            "format": log_format,
            "level": level,
            "rotation": "10 MB",
            "retention": "1 week",
            "compression": "zip",
            "diagnose": True,
        },
        # Error log file (ERROR and above)
        {
            "sink": logs_dir / "error.log",
            "format": log_format,
            "level": "ERROR",
            "rotation": "10 MB",
            "retention": "1 month",
            "compression": "zip",
            "backtrace": True,
            "diagnose": True,
        }
    ]
    
    # Add performance log if enabled
    if settings.ENABLE_PERFORMANCE_LOGGING:
        handlers.append({
            "sink": logs_dir / "performance.log",
            "format": "{time:YYYY-MM-DD HH:mm:ss.SSS} | {message}",
            "level": "INFO",
            "filter": lambda record: "performance" in record["extra"],
            "rotation": "10 MB",
            "retention": "1 month",
            "compression": "zip",
        })
    
    # Add agent log for debugging AI interactions
    handlers.append({
        "sink": logs_dir / "agent.log",
        "format": "{time:YYYY-MM-DD HH:mm:ss.SSS} | {extra[request_id]} | {message}",
        "level": "DEBUG",
        "filter": lambda record: any(x in record["name"].lower() for x in ["agent", "profiler", "researcher", "strategist"]),
        "rotation": "20 MB",
        "retention": "1 week",
        "compression": "zip",
    })
    
    # Configure loguru with all handlers
    logger.configure(handlers=handlers)
    
    # Intercept standard logging
    logging.root.handlers = [InterceptHandler()]
    
    # Add specific loggers for web framework
    for logger_name in ["uvicorn", "uvicorn.error", "fastapi"]:
        logging.getLogger(logger_name).handlers = [InterceptHandler()]
    
    # Log initialization
    logger.bind(request_id="STARTUP").info(f"Logging configured with level: {log_level}")


def get_request_logger(request_id: Optional[str] = None) -> logger:
    """Get a logger with request context.
    
    Args:
        request_id: The request ID (generated if None)
        
    Returns:
        logger: A logger with request context
    """
    if request_id is None:
        request_id = str(uuid.uuid4())[:8]
    
    return logger.bind(request_id=request_id)


def log_performance(operation: str, elapsed_time: float, details: Optional[Dict[str, Any]] = None) -> None:
    """Log performance metrics.
    
    Args:
        operation: The name of the operation
        elapsed_time: The elapsed time in seconds
        details: Optional additional details
    """
    if settings.ENABLE_PERFORMANCE_LOGGING:
        metrics = {
            "timestamp": time.time(),
            "operation": operation,
            "elapsed_time": elapsed_time,
        }
        
        if details:
            metrics.update(details)
        
        logger.bind(performance=True, request_id="PERF").info(
            f"{operation}|{elapsed_time:.4f}s|{metrics}"
        )


# Export the logger instance
app_logger = logger
