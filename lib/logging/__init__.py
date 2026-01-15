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


# Legacy compatibility - setup_logging is an alias for configure_logging
def setup_logging(level: LogLevel = 'INFO', log_file=None):
    """
    Legacy function for backwards compatibility.
    
    Use configure_logging() for new code.
    
    Args:
        level: Logging level.
        log_file: Optional log file path (ignored, uses default log directory).
        
    Returns:
        Configured root logger.
    """
    return configure_logging(
        level=level,
        file=log_file is not None,
        console=True
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
    # Legacy compatibility
    "setup_logging",
]















