"""
Centralized logging package for The Researcher's Cockpit.

Provides structured logging with consistent formatting across all modules.
Supports both console output (human-readable) and file output (structured JSON).

Usage:
    from lib.logging import configure_logging, get_logger, LogContext
    
    # Configure logging
    configure_logging(level="INFO", console=True, file=True)
    
    # Get a logger
    logger = get_logger('my_module')
    logger.info("Operation completed")
    
    # Use context for enhanced logging
    with LogContext(phase="backtest", strategy="my_strategy"):
        logger.info("Running backtest...")  # Includes context info
"""

# Core configuration
from .config import (
    configure_logging,
    shutdown_logging,
    get_logger,
    LogLevel,
)

# Context management
from .context import (
    LogContext,
    reset_context,
    get_context_value,
    set_context_value,
    clear_context_value,
    has_context_value,
)

# Formatters
from .formatters import (
    StructuredFormatter,
    ConsoleFormatter,
    _context,
)

# Error codes
from .error_codes import (
    ErrorCode,
    ErrorCodeInfo,
)

# Utility functions
from .utils import (
    log_with_context,
    log_exception,
    log_validation_result,
)

# Pre-configured loggers
from .loggers import (
    data_logger,
    strategy_logger,
    backtest_logger,
    metrics_logger,
    validation_logger,
    report_logger,
    optimization_logger,
    pipeline_logger,
    ingestion_logger,
)


# Public API exports
__all__ = [
    # Core configuration
    "configure_logging",
    "shutdown_logging",
    "get_logger",
    "LogLevel",
    # Context management
    "LogContext",
    "reset_context",
    "get_context_value",
    "set_context_value",
    "clear_context_value",
    "has_context_value",
    # Formatters
    "StructuredFormatter",
    "ConsoleFormatter",
    "_context",
    # Error codes
    "ErrorCode",
    "ErrorCodeInfo",
    # Logging utilities
    "log_with_context",
    "log_exception",
    "log_validation_result",
    # Pre-configured loggers
    "data_logger",
    "strategy_logger",
    "backtest_logger",
    "metrics_logger",
    "validation_logger",
    "report_logger",
    "optimization_logger",
    "pipeline_logger",
    "ingestion_logger",
]















