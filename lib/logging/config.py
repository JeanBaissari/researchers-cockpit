"""
Core logging configuration.

Provides functions to configure logging for The Researcher's Cockpit.
"""

import atexit
import logging
import logging.handlers
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Literal, Optional

from .formatters import (
    StructuredFormatter,
    ConsoleFormatter,
    set_context_value,
)

# Type alias for log levels
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

# Valid log levels for runtime validation
_VALID_LOG_LEVELS = frozenset({"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"})

# Thread-safe lock for context operations
_context_lock = threading.RLock()

# Track active handlers for cleanup
_active_handlers: List[logging.Handler] = []
_shutdown_registered = False


def _validate_log_level(level: str) -> str:
    """
    Validate and normalize log level string.
    
    Args:
        level: Log level string to validate.
        
    Returns:
        Normalized uppercase log level.
        
    Raises:
        ValueError: If level is not a valid log level.
    """
    normalized = level.upper()
    if normalized not in _VALID_LOG_LEVELS:
        valid_levels = ", ".join(sorted(_VALID_LOG_LEVELS))
        raise ValueError(
            f"Invalid log level '{level}'. Must be one of: {valid_levels}"
        )
    return normalized


def _get_logging_level(level: LogLevel) -> int:
    """
    Safely convert log level string to logging constant.
    
    Args:
        level: Validated log level string.
        
    Returns:
        Logging level constant (e.g., logging.INFO).
    """
    validated = _validate_log_level(level)
    return getattr(logging, validated)


def shutdown_logging() -> None:
    """
    Properly shutdown logging and close all handlers.
    
    Should be called on application exit to ensure all log messages
    are flushed and file handles are properly closed.
    """
    global _active_handlers
    
    root_logger = logging.getLogger('cockpit')
    
    # Flush and close all handlers
    for handler in _active_handlers[:]:
        try:
            handler.flush()
            handler.close()
        except Exception:
            pass  # Ignore errors during shutdown
    
    # Clear handler list
    _active_handlers.clear()
    
    # Remove handlers from logger
    root_logger.handlers = []


def _register_shutdown() -> None:
    """Register shutdown handler if not already registered."""
    global _shutdown_registered
    if not _shutdown_registered:
        atexit.register(shutdown_logging)
        _shutdown_registered = True


def configure_logging(
    strategy_name: Optional[str] = None,
    run_id: Optional[str] = None,
    level: LogLevel = "INFO",
    log_dir: Optional[Path] = None,
    console: bool = True,
    file: bool = True,
    structured: bool = True,
    asset_type: Optional[str] = None,
    bundle_name: Optional[str] = None,
    timeframe: Optional[str] = None,
) -> logging.Logger:
    """
    Configure centralized logging for the application.
    
    Args:
        strategy_name: Optional strategy name for context.
        run_id: Optional run ID for context.
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_dir: Directory for log files (default: PROJECT_ROOT/logs).
        console: Enable console output.
        file: Enable file output.
        structured: Use JSON structured format for file logs.
        asset_type: Optional asset type for context (equity, forex, crypto).
        bundle_name: Optional bundle name for context.
        timeframe: Optional timeframe for context (1m, 5m, 15m, 30m, 1h, daily).
        
    Returns:
        Root logger for the 'cockpit' namespace.
        
    Raises:
        ValueError: If level is not a valid log level.
    """
    global _active_handlers
    
    # Validate log level early
    validated_level = _validate_log_level(level)
    log_level_int = _get_logging_level(validated_level)
    
    # Get log directory - import inside function to avoid circular imports
    if log_dir is None:
        try:
            from ..paths import get_logs_dir
            log_dir = get_logs_dir()
        except ImportError:
            log_dir = Path('logs')
    
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Get or create root logger
    root_logger = logging.getLogger('cockpit')
    root_logger.setLevel(log_level_int)
    
    # Shutdown existing handlers before reconfiguring
    shutdown_logging()
    
    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level_int)
        console_handler.setFormatter(ConsoleFormatter())
        root_logger.addHandler(console_handler)
        _active_handlers.append(console_handler)
    
    # File handler
    if file:
        # Daily rotating log file with UTC timestamp
        log_file = log_dir / f"cockpit_{datetime.now(timezone.utc).strftime('%Y%m%d')}.log"
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        
        if structured:
            file_handler.setFormatter(StructuredFormatter())
        else:
            file_handler.setFormatter(ConsoleFormatter())
        
        file_handler.setLevel(log_level_int)
        root_logger.addHandler(file_handler)
        _active_handlers.append(file_handler)
    
    # Register shutdown handler
    _register_shutdown()
    
    # Set context if provided (thread-safe)
    with _context_lock:
        if strategy_name:
            set_context_value('strategy', strategy_name)
        if run_id:
            set_context_value('run_id', run_id)
        if asset_type:
            set_context_value('asset_type', asset_type)
        if bundle_name:
            set_context_value('bundle_name', bundle_name)
        if timeframe:
            set_context_value('timeframe', timeframe)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the cockpit namespace prefix.
    
    Args:
        name: Logger name (e.g., 'data', 'backtest', 'metrics').
        
    Returns:
        Logger instance.
    """
    return logging.getLogger(f'cockpit.{name}')


# Public exports
__all__ = [
    "configure_logging",
    "shutdown_logging",
    "get_logger",
    "LogLevel",
]





