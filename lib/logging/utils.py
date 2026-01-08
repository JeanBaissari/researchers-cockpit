"""
Logging utility functions.

Provides helper functions for structured logging with context,
exception handling, and validation result logging.
"""

import logging
import sys
import traceback
from typing import Any, Dict, Optional, Union

from .config import LogLevel, _validate_log_level, _get_logging_level
from .error_codes import ErrorCode


def log_with_context(
    logger: logging.Logger,
    level: Union[int, LogLevel],
    message: str,
    error_code: Optional[ErrorCode] = None,
    **kwargs: Any,
) -> None:
    """
    Log a message with additional context fields.
    
    Args:
        logger: Logger instance.
        level: Logging level (e.g., logging.INFO or "INFO").
        message: Log message.
        error_code: Optional error code for structured error tracking.
        **kwargs: Additional context fields to include.
        
    Raises:
        ValueError: If level string is not a valid log level.
    """
    # Convert string level to int if needed
    if isinstance(level, str):
        level = _get_logging_level(level)
    
    record = logger.makeRecord(
        logger.name, level, '', 0, message, (), None
    )
    
    extra_fields = dict(kwargs)
    if error_code is not None:
        extra_fields['error_code'] = error_code.code
        extra_fields['error_category'] = error_code.category
    
    record.extra_fields = extra_fields
    logger.handle(record)


def log_exception(
    logger: logging.Logger,
    message: str,
    exc: Optional[BaseException] = None,
    error_code: Optional[ErrorCode] = None,
    include_traceback: bool = True,
    **kwargs: Any,
) -> None:
    """
    Log an exception with consistent traceback formatting.
    
    Provides structured exception logging with optional traceback,
    error codes, and additional context fields.
    
    Args:
        logger: Logger instance.
        message: Log message describing the error context.
        exc: Exception instance (uses sys.exc_info() if None).
        error_code: Optional error code for structured error tracking.
        include_traceback: Whether to include full traceback.
        **kwargs: Additional context fields to include.
        
    Usage:
        try:
            risky_operation()
        except ValueError as e:
            log_exception(
                logger,
                "Failed to process data",
                exc=e,
                error_code=ErrorCode.VALIDATION_ERROR,
                data_source="yahoo",
            )
    """
    extra_fields = dict(kwargs)
    
    # Get exception info
    if exc is None:
        exc_info = sys.exc_info()
        exc = exc_info[1]
    else:
        exc_info = (type(exc), exc, exc.__traceback__)
    
    # Add exception details
    if exc is not None:
        extra_fields['exception_type'] = type(exc).__name__
        extra_fields['exception_message'] = str(exc)
        
        if include_traceback and exc_info[2] is not None:
            tb_lines = traceback.format_exception(*exc_info)
            extra_fields['traceback'] = ''.join(tb_lines)
    
    # Add error code if provided
    if error_code is not None:
        extra_fields['error_code'] = error_code.code
        extra_fields['error_category'] = error_code.category
    
    # Create and handle record
    record = logger.makeRecord(
        logger.name, logging.ERROR, '', 0, message, (), exc_info
    )
    record.extra_fields = extra_fields
    logger.handle(record)


def log_validation_result(
    logger: logging.Logger,
    result: Any,  # ValidationResult from lib.data_validation
    include_details: bool = True,
) -> None:
    """
    Log a ValidationResult with appropriate log levels.
    
    Logs errors at ERROR level, warnings at WARNING level, and success at INFO level.
    Includes issue counts and fix suggestions in structured output.
    
    Args:
        logger: Logger instance to use.
        result: ValidationResult object from lib.data_validation.
        include_details: Whether to include detailed issue information.
    """
    # Determine overall status and log level
    if hasattr(result, 'is_valid'):
        is_valid = result.is_valid
    else:
        is_valid = True
    
    error_count = len(result.errors) if hasattr(result, 'errors') else 0
    warning_count = len(result.warnings) if hasattr(result, 'warnings') else 0
    
    # Build summary message
    if is_valid and error_count == 0:
        if warning_count > 0:
            summary = f"Validation passed with {warning_count} warning(s)"
            level = logging.WARNING
        else:
            summary = "Validation passed successfully"
            level = logging.INFO
    else:
        summary = f"Validation failed: {error_count} error(s), {warning_count} warning(s)"
        level = logging.ERROR
    
    # Build extra context
    extra: Dict[str, Any] = {
        'is_valid': is_valid,
        'error_count': error_count,
        'warning_count': warning_count,
    }
    
    if include_details:
        if hasattr(result, 'errors') and result.errors:
            extra['errors'] = [str(e) for e in result.errors[:10]]  # Limit to 10
        if hasattr(result, 'warnings') and result.warnings:
            extra['warnings'] = [str(w) for w in result.warnings[:10]]
        if hasattr(result, 'fix_suggestions') and result.fix_suggestions:
            extra['fix_suggestions'] = result.fix_suggestions[:5]  # Limit to 5
    
    log_with_context(logger, level, summary, **extra)
    
    # Log individual errors at ERROR level if present
    if include_details and hasattr(result, 'errors'):
        for error in result.errors[:5]:  # Limit detailed logging
            log_with_context(
                logger,
                logging.ERROR,
                str(error),
                error_code=ErrorCode.VALIDATION_ERROR,
            )


# Public exports
__all__ = [
    "log_with_context",
    "log_exception",
    "log_validation_result",
]

