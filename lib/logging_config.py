"""
Centralized logging configuration for The Researcher's Cockpit.

This module is a thin wrapper for backward compatibility.
All logging functionality is now in the lib/logging/ package.

Usage (recommended):
    from lib.logging import configure_logging, get_logger
    
Usage (legacy, still supported):
    from lib.logging_config import configure_logging, get_logger
"""

# Re-export everything from the logging package for backward compatibility
from .logging import (
    # Core configuration
    configure_logging,
    shutdown_logging,
    get_logger,
    LogLevel,
    # Context management
    LogContext,
    reset_context,
    get_context_value,
    set_context_value,
    clear_context_value,
    has_context_value,
    # Formatters
    StructuredFormatter,
    ConsoleFormatter,
    _context,
    # Error codes
    ErrorCode,
    # Logging utilities
    log_with_context,
    log_exception,
    log_validation_result,
    # Pre-configured loggers
    data_logger,
    strategy_logger,
    backtest_logger,
    metrics_logger,
    validation_logger,
    report_logger,
    optimization_logger,
    pipeline_logger,
    ingestion_logger,
    # Legacy compatibility
    setup_logging,
)


# Public API exports (same as lib/logging)
__all__ = [
    # Core configuration
    "configure_logging",
    "shutdown_logging",
    "get_logger",
    # Context management
    "LogContext",
    "reset_context",
    "get_context_value",
    "set_context_value",
    "clear_context_value",
    "has_context_value",
    # Logging utilities
    "log_with_context",
    "log_exception",
    "log_validation_result",
    # Type definitions
    "LogLevel",
    # Legacy compatibility
    "setup_logging",
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
    # Formatters (for advanced usage)
    "StructuredFormatter",
    "ConsoleFormatter",
    "_context",
    # Error codes
    "ErrorCode",
]
