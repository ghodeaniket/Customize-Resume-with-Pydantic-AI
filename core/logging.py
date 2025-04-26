"""Logging configuration for Resume Customizer."""
import logging
import os
import sys
from typing import Any, Dict, Optional, Union

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
    
    # Create file handlers for different log types
    app_handler = logging.FileHandler(os.path.join(logs_dir, 'app.log'))
    app_handler.setLevel(log_level)
    
    error_handler = logging.FileHandler(os.path.join(logs_dir, 'error.log'))
    error_handler.setLevel(logging.ERROR)
    
    agent_handler = logging.FileHandler(os.path.join(logs_dir, 'agent.log'))
    agent_handler.setLevel(log_level)
    
    file_handler = logging.FileHandler(os.path.join(logs_dir, 'file_processing.log'))
    file_handler.setLevel(logging.DEBUG)  # Always debug level for file processing
    
    performance_handler = logging.FileHandler(os.path.join(logs_dir, 'performance.log'))
    performance_handler.setLevel(logging.INFO)
    
    # Create console handler for logging to stdout
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    # Create formatters
    default_formatter = logging.Formatter('%(asctime)s | %(levelname)-8s | %(name)s:%(filename)s:%(lineno)d | %(message)s')
    detailed_formatter = logging.Formatter('%(asctime)s | %(levelname)-8s | %(name)s:%(filename)s:%(lineno)d | %(message)s | %(funcName)s | Thread: %(threadName)s')
    
    app_handler.setFormatter(default_formatter)
    error_handler.setFormatter(detailed_formatter)
    agent_handler.setFormatter(default_formatter)
    file_handler.setFormatter(detailed_formatter)
    performance_handler.setFormatter(default_formatter)
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add handlers to root logger
    root_logger.addHandler(app_handler)
    root_logger.addHandler(error_handler)
    root_logger.addHandler(console_handler)
    
    # Configure specific loggers
    # Agent logger
    agent_logger = logging.getLogger('agents')
    agent_logger.propagate = False  # Don't propagate to root
    agent_logger.addHandler(agent_handler)
    agent_logger.addHandler(error_handler)
    agent_logger.addHandler(console_handler)
    
    # File processing logger
    file_logger = logging.getLogger('infrastructure.document_processor')
    file_logger.propagate = False  # Don't propagate to root
    file_logger.addHandler(file_handler)
    file_logger.addHandler(error_handler)
    file_logger.addHandler(console_handler)
    
    # Endpoints logger
    endpoints_logger = logging.getLogger('api.endpoints')
    endpoints_logger.propagate = False
    endpoints_logger.addHandler(app_handler)
    endpoints_logger.addHandler(error_handler)
    endpoints_logger.addHandler(console_handler)
    
    # Performance logger
    perf_logger = logging.getLogger('performance')
    perf_logger.propagate = False
    perf_logger.addHandler(performance_handler)
    
    # Configure specific third-party loggers
    for logger_name, logger_level in [
        ('httpx', logging.WARNING),
        ('uvicorn', logging.WARNING),
        ('PyPDF2', logging.INFO),  # Increased from WARNING to INFO for debugging
        ('pydantic_ai', logging.INFO),
    ]:
        specific_logger = logging.getLogger(logger_name)
        specific_logger.setLevel(logger_level)
        # Add error handler for capturing errors
        specific_logger.addHandler(error_handler)
    
    # Log configuration info
    logging.info(f"STARTUP - Logging configured with level: {log_level_str}")
    

class LoggerMixin:
    """Mixin class that provides logging functionality."""
    
    @property
    def logger(self) -> logging.Logger:
        """Get logger for the current class.
        
        Returns:
            logging.Logger: Logger instance
        """
        return logging.getLogger(self.__class__.__name__)
    
    def _log(self, level: int, message: str, extra: Optional[Dict[str, Any]] = None,
             exc_info: Union[bool, Exception, None] = None) -> None:
        """Internal method to log messages with standardized format.
        
        Args:
            level: Log level (e.g., logging.INFO)
            message: Message to log
            extra: Optional extra information to include in log
            exc_info: Exception info for error logs
        """
        if extra is None:
            extra = {}
            
        # Add common context to all logs
        extra.update({
            "component": self.__class__.__name__,
        })
        
        self.logger.log(level, message, extra=extra, exc_info=exc_info)
    
    def log_info(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log info message.
        
        Args:
            message: Message to log
            extra: Optional extra information to include in log
        """
        self._log(logging.INFO, message, extra)
    
    def log_error(self, message: str, extra: Optional[Dict[str, Any]] = None, 
                  exc_info: Union[bool, Exception, None] = None) -> None:
        """Log error message.
        
        Args:
            message: Message to log
            extra: Optional extra information to include in log
            exc_info: Exception info (True, Exception object, or None)
        """
        self._log(logging.ERROR, message, extra, exc_info)
    
    def log_debug(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log debug message.
        
        Args:
            message: Message to log
            extra: Optional extra information to include in log
        """
        self._log(logging.DEBUG, message, extra)
    
    def log_warning(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log warning message.
        
        Args:
            message: Message to log
            extra: Optional extra information to include in log
        """
        self._log(logging.WARNING, message, extra)
    
    def log_exception(self, message: str, exception: Exception, 
                      extra: Optional[Dict[str, Any]] = None) -> None:
        """Log exception with full traceback.
        
        Args:
            message: Message to log
            exception: Exception object
            extra: Optional extra information to include in log
        """
        if extra is None:
            extra = {}
            
        extra.update({
            "exception_type": type(exception).__name__,
            "exception_message": str(exception)
        })
        
        self._log(logging.ERROR, message, extra, exc_info=exception)
        
    def log_file_processing(self, action: str, file_type: str, file_size: int, 
                           extra: Optional[Dict[str, Any]] = None) -> None:
        """Log file processing activity with standardized format.
        
        Args:
            action: The processing action (e.g., "extraction", "detection")
            file_type: MIME type or format of the file
            file_size: Size of the file in bytes
            extra: Optional extra information to include in log
        """
        if extra is None:
            extra = {}
            
        extra.update({
            "file_type": file_type,
            "file_size": file_size,
            "action": action
        })
        
        self._log(logging.INFO, f"FILE_PROCESSING: {action} on {file_type} file ({file_size} bytes)", extra)
        
    def log_file_error(self, error: str, file_type: str, file_size: int, 
                      exception: Optional[Exception] = None,
                      extra: Optional[Dict[str, Any]] = None) -> None:
        """Log file processing error with standardized format.
        
        Args:
            error: Error description
            file_type: MIME type or format of the file
            file_size: Size of the file in bytes
            exception: Optional exception that caused the error
            extra: Optional extra information to include in log
        """
        if extra is None:
            extra = {}
            
        extra.update({
            "file_type": file_type,
            "file_size": file_size,
            "error": error
        })
        
        message = f"FILE_ERROR: {error} on {file_type} file ({file_size} bytes)"
        if exception:
            message += f": {str(exception)}"
        
        self._log(logging.ERROR, message, extra, exc_info=exception)
        
    def log_performance(self, operation: str, duration_ms: float, 
                       success: bool = True, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log performance metrics.
        
        Args:
            operation: Name of the operation
            duration_ms: Duration in milliseconds
            success: Whether the operation was successful
            extra: Optional extra information to include in log
        """
        perf_logger = logging.getLogger('performance')
        
        if extra is None:
            extra = {}
            
        extra.update({
            "operation": operation,
            "duration_ms": duration_ms,
            "success": success,
            "component": self.__class__.__name__
        })
        
        status = "SUCCESS" if success else "FAILURE"
        perf_logger.info(
            f"PERF: {operation} - {duration_ms:.2f}ms - {status}", 
            extra=extra
        )
