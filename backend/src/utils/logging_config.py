"""
Logging configuration for the backend services.

This module provides centralized logging configuration with sanitization support.
"""

import logging
import os
import sys
from typing import Any, Dict
from .log_sanitizer import sanitize_log_data


class SanitizingFormatter(logging.Formatter):
    """Custom formatter that sanitizes log records before formatting."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with sanitization."""
        # Sanitize the message if it's a string
        if isinstance(record.msg, str):
            record.msg = sanitize_log_data(record.msg)
        
        # Sanitize args if present
        if record.args:
            if isinstance(record.args, dict):
                record.args = sanitize_log_data(record.args)
            elif isinstance(record.args, tuple):
                record.args = tuple(sanitize_log_data(arg) for arg in record.args)
        
        # Format the record
        return super().format(record)


def configure_logging(
    level: str = None,
    format_string: str = None,
    enable_sanitization: bool = True
) -> None:
    """
    Configure logging for the application.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_string: Log format string
        enable_sanitization: Whether to enable log sanitization
    """
    # Get configuration from environment or use defaults
    log_level = level or os.getenv('LOG_LEVEL', 'INFO')
    log_format = format_string or os.getenv(
        'LOG_FORMAT',
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create handler
    handler = logging.StreamHandler(sys.stdout)
    
    # Use sanitizing formatter if enabled
    if enable_sanitization:
        formatter = SanitizingFormatter(log_format)
    else:
        formatter = logging.Formatter(log_format)
    
    handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    
    # Configure specific loggers
    loggers_config = {
        'temporal': log_level,
        'src.temporal': log_level,
        'src.services': log_level,
        'src.utils': log_level,
        'activity': log_level,
        'workflow': log_level,
    }
    
    for logger_name, logger_level in loggers_config.items():
        logger = logging.getLogger(logger_name)
        logger.setLevel(getattr(logging, logger_level.upper()))
        logger.propagate = True


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the given name.
    
    Args:
        name: Logger name
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


class SafeLogger:
    """
    A wrapper around the standard logger that automatically sanitizes all log data.
    """
    
    def __init__(self, logger: logging.Logger):
        """Initialize with a standard logger."""
        self._logger = logger
    
    def _sanitize_and_log(self, level: int, msg: Any, *args, **kwargs) -> None:
        """Sanitize message and arguments before logging."""
        # Sanitize the message
        sanitized_msg = sanitize_log_data(msg)
        
        # Sanitize args if present
        if args:
            sanitized_args = tuple(sanitize_log_data(arg) for arg in args)
        else:
            sanitized_args = ()
        
        # Sanitize kwargs if present
        if kwargs:
            sanitized_kwargs = sanitize_log_data(kwargs)
        else:
            sanitized_kwargs = {}
        
        # Log with sanitized data
        self._logger.log(level, sanitized_msg, *sanitized_args, **sanitized_kwargs)
    
    def debug(self, msg: Any, *args, **kwargs) -> None:
        """Log debug message with sanitization."""
        if self._logger.isEnabledFor(logging.DEBUG):
            self._sanitize_and_log(logging.DEBUG, msg, *args, **kwargs)
    
    def info(self, msg: Any, *args, **kwargs) -> None:
        """Log info message with sanitization."""
        if self._logger.isEnabledFor(logging.INFO):
            self._sanitize_and_log(logging.INFO, msg, *args, **kwargs)
    
    def warning(self, msg: Any, *args, **kwargs) -> None:
        """Log warning message with sanitization."""
        if self._logger.isEnabledFor(logging.WARNING):
            self._sanitize_and_log(logging.WARNING, msg, *args, **kwargs)
    
    def error(self, msg: Any, *args, **kwargs) -> None:
        """Log error message with sanitization."""
        if self._logger.isEnabledFor(logging.ERROR):
            self._sanitize_and_log(logging.ERROR, msg, *args, **kwargs)
    
    def critical(self, msg: Any, *args, **kwargs) -> None:
        """Log critical message with sanitization."""
        if self._logger.isEnabledFor(logging.CRITICAL):
            self._sanitize_and_log(logging.CRITICAL, msg, *args, **kwargs)
    
    def exception(self, msg: Any, *args, exc_info=True, **kwargs) -> None:
        """Log exception with sanitization."""
        self.error(msg, *args, exc_info=exc_info, **kwargs)
    
    # Delegate other attributes to the wrapped logger
    def __getattr__(self, name):
        return getattr(self._logger, name)


def get_safe_logger(name: str) -> SafeLogger:
    """
    Get a safe logger that automatically sanitizes all log data.
    
    Args:
        name: Logger name
        
    Returns:
        SafeLogger instance
    """
    return SafeLogger(logging.getLogger(name))