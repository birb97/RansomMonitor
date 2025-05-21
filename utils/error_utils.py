# utils/error_utils.py
"""
Utilities for consistent error handling and reporting.
"""

import logging
import traceback
from typing import Type, Optional, Any

# Base exception for all application-specific errors
class RansomIntelError(Exception):
    """Base exception for all ransomware intelligence system errors"""
    pass

# Specific exception types
class ConfigError(RansomIntelError):
    """Error related to configuration loading or validation"""
    pass

class DatabaseError(RansomIntelError):
    """Error related to database operations"""
    pass

class NetworkError(RansomIntelError):
    """Error related to network operations (API calls, etc.)"""
    pass

class ValidationError(RansomIntelError):
    """Error related to data validation"""
    pass

class ProcessingError(RansomIntelError):
    """Error related to data processing"""
    pass

def log_exception(logger, message: str, exception: Exception, level: str = "error") -> None:
    """
    Log an exception with consistent formatting.
    
    Args:
        logger: Logger instance
        message: Context message describing what was happening
        exception: The exception that was caught
        level: Logging level ('error', 'warning', 'critical', etc.)
    """
    log_method = getattr(logger, level.lower())
    
    # Format the message with exception details
    error_message = f"{message}: {str(exception)}"
    
    # Log the message
    log_method(error_message)
    
    # Log traceback for errors and criticals
    if level.lower() in ("error", "critical"):
        logger.debug(f"Traceback for {error_message}:\n{traceback.format_exc()}")

def handle_exception(
    exception: Exception,
    logger,
    message: str,
    reraise: bool = False,
    reraise_as: Optional[Type[Exception]] = None,
    default_return: Any = None,
    level: str = "error"
) -> Any:
    """
    Handle an exception with consistent logging and optional reraising.
    
    Args:
        exception: The caught exception
        logger: Logger instance
        message: Context message describing what was happening
        reraise: Whether to reraise the exception
        reraise_as: Exception type to reraise as (or None for original)
        default_return: Value to return if not reraising
        level: Logging level ('error', 'warning', 'critical', etc.)
        
    Returns:
        default_return if not reraising
        
    Raises:
        The original exception or a new exception of reraise_as type
    """
    log_exception(logger, message, exception, level)
    
    if reraise:
        if reraise_as:
            raise reraise_as(f"{message}: {str(exception)}") from exception
        raise
    
    return default_return