"""
Logging utility functions.

Provides helper functions for structured logging with context,
exception handling, validation result logging, and Zipline logger integration.
"""

import logging
import sys
import traceback
from typing import Any, Dict, Optional, Union, Literal

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

    record = logger.makeRecord(logger.name, level, "", 0, message, (), None)

    extra_fields = dict(kwargs)
    if error_code is not None:
        extra_fields["error_code"] = error_code.code
        extra_fields["error_category"] = error_code.category

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
        extra_fields["exception_type"] = type(exc).__name__
        extra_fields["exception_message"] = str(exc)

        if include_traceback and exc_info[2] is not None:
            tb_lines = traceback.format_exception(*exc_info)
            extra_fields["traceback"] = "".join(tb_lines)

    # Add error code if provided
    if error_code is not None:
        extra_fields["error_code"] = error_code.code
        extra_fields["error_category"] = error_code.category

    # Create and handle record
    record = logger.makeRecord(logger.name, logging.ERROR, "", 0, message, (), exc_info)
    record.extra_fields = extra_fields
    logger.handle(record)


def log_validation_result(
    logger: logging.Logger,
    result: Any,  # ValidationResult from lib.validation
    include_details: bool = True,
) -> None:
    """
    Log a ValidationResult with appropriate log levels.

    Logs errors at ERROR level, warnings at WARNING level, and success at INFO level.
    Includes issue counts and fix suggestions in structured output.

    Args:
        logger: Logger instance to use.
        result: ValidationResult object from lib.validation.
        include_details: Whether to include detailed issue information.
    """
    # Determine overall status and log level
    if hasattr(result, "is_valid"):
        is_valid = result.is_valid
    else:
        is_valid = True

    error_count = len(result.errors) if hasattr(result, "errors") else 0
    warning_count = len(result.warnings) if hasattr(result, "warnings") else 0

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
        "is_valid": is_valid,
        "error_count": error_count,
        "warning_count": warning_count,
    }

    if include_details:
        if hasattr(result, "errors") and result.errors:
            extra["errors"] = [str(e) for e in result.errors[:10]]  # Limit to 10
        if hasattr(result, "warnings") and result.warnings:
            extra["warnings"] = [str(w) for w in result.warnings[:10]]
        if hasattr(result, "fix_suggestions") and result.fix_suggestions:
            extra["fix_suggestions"] = result.fix_suggestions[:5]  # Limit to 5

    log_with_context(logger, level, summary, **extra)

    # Log individual errors at ERROR level if present
    if include_details and hasattr(result, "errors"):
        for error in result.errors[:5]:  # Limit detailed logging
            log_with_context(
                logger,
                logging.ERROR,
                str(error),
                error_code=ErrorCode.VALIDATION_ERROR,
            )


def integrate_zipline_loggers(
    blotter_level: LogLevel = "INFO",
    zipline_level: LogLevel = "WARNING",
    portal_level: LogLevel = "INFO",
    algo_warning_level: LogLevel = "WARNING",
    use_project_handlers: bool = True,
) -> None:
    """
    Integrate Zipline-Reloaded's named loggers with project logging system.

    Zipline-Reloaded uses named loggers, including:
    - 'Blotter': Order execution and trade management
    - 'ZiplineLog': General Zipline framework logging
    - 'DataPortal': Data access and pricing operations
    - 'AlgoWarning': User-facing warnings (e.g., partial fill/cancel messages)

    This function routes these loggers through the project's logging handlers,
    allowing Zipline's internal operations to appear in project logs with
    consistent formatting and context.

    Args:
        blotter_level: Log level for Blotter logger (order execution).
                      Default: "INFO" (captures order placement, fills, cancellations).
        zipline_level: Log level for ZiplineLog logger (framework operations).
                       Default: "WARNING" (only warnings/errors, reduces noise).
        portal_level: Log level for DataPortal logger (data access).
                      Default: "INFO" (captures data loading and queries).
        algo_warning_level: Log level for AlgoWarning logger (user-facing warnings).
                            Default: "WARNING" (surface actionable warnings without noise).
        use_project_handlers: If True, route Zipline logs through project handlers
                             (uses project formatters, includes context).
                             If False, use default propagation to root logger.

    Raises:
        ValueError: If any log level is invalid.

    Example:
        >>> from lib.logging import configure_logging, integrate_zipline_loggers
        >>>
        >>> # Configure project logging first
        >>> configure_logging(level="INFO", console=True, file=True)
        >>>
        >>> # Integrate Zipline loggers
        >>> integrate_zipline_loggers(
        ...     blotter_level="INFO",   # Capture order execution
        ...     zipline_level="WARNING", # Only framework warnings
        ...     portal_level="INFO"     # Capture data access
        ... )
        >>>
        >>> # Now Zipline logs will appear in project logs
        >>> from lib.backtest import run_backtest
        >>> perf, calendar = run_backtest(...)

    Note:
        - Configure project logging before calling this function
        - Zipline loggers are created automatically when Zipline modules are imported
        - Setting use_project_handlers=False allows logs to propagate to root logger
        - This function prevents duplicate logs by setting propagate=False when using project handlers

    See Also:
        - docs/api/zipline_loggers.md - Complete integration guide
        - lib.logging.config.configure_logging() - Configure project logging
    """
    # Validate log levels
    _validate_log_level(blotter_level)
    _validate_log_level(zipline_level)
    _validate_log_level(portal_level)
    _validate_log_level(algo_warning_level)

    # Map log level strings to constants
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }

    # Get project root logger (ensure it exists)
    root_logger = logging.getLogger("cockpit")

    # If no handlers exist, warn user
    if use_project_handlers and not root_logger.handlers:
        import warnings

        warnings.warn(
            "Project logging not configured. Call configure_logging() first. "
            "Zipline loggers will use default propagation.",
            UserWarning,
        )
        use_project_handlers = False

    # Configure Zipline loggers
    zipline_loggers = {
        "Blotter": level_map[blotter_level],
        "ZiplineLog": level_map[zipline_level],
        "DataPortal": level_map[portal_level],
        "AlgoWarning": level_map[algo_warning_level],
    }

    for logger_name, log_level in zipline_loggers.items():
        zipline_logger = logging.getLogger(logger_name)
        zipline_logger.setLevel(log_level)

        if use_project_handlers:
            # Add project handlers to Zipline logger
            for handler in root_logger.handlers:
                zipline_logger.addHandler(handler)

            # Prevent propagation to avoid duplicate logs
            zipline_logger.propagate = False
        else:
            # Use default propagation (logs go to root logger)
            zipline_logger.propagate = True


def get_zipline_loggers() -> Dict[str, logging.Logger]:
    """
    Get references to Zipline-Reloaded's named loggers.

    Returns:
        Dictionary mapping logger names to logger instances:
        - 'Blotter': Order execution logger
        - 'ZiplineLog': Framework logger
        - 'DataPortal': Data access logger
        - 'AlgoWarning': User-facing warnings logger

    Example:
        >>> loggers = get_zipline_loggers()
        >>> loggers['Blotter'].setLevel(logging.DEBUG)
        >>> loggers['DataPortal'].info("Custom message")
    """
    return {
        "Blotter": logging.getLogger("Blotter"),
        "ZiplineLog": logging.getLogger("ZiplineLog"),
        "DataPortal": logging.getLogger("DataPortal"),
        "AlgoWarning": logging.getLogger("AlgoWarning"),
    }


# Public exports
__all__ = [
    "log_with_context",
    "log_exception",
    "log_validation_result",
    "integrate_zipline_loggers",
    "get_zipline_loggers",
]
