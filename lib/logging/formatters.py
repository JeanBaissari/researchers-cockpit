"""
Log formatters for structured and console output.

Provides custom formatters for:
- StructuredFormatter: JSON output for file logs
- ConsoleFormatter: Human-readable output for console
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import threading


# Thread-local storage for context values
_context: Dict[str, Any] = {}
_context_lock = threading.RLock()


def get_context_value(key: str) -> Optional[Any]:
    """
    Get a context value by key.
    
    Thread-safe operation to retrieve context values.
    
    Args:
        key: Context key to retrieve.
        
    Returns:
        Context value or None if not set.
    """
    with _context_lock:
        return _context.get(key)


def set_context_value(key: str, value: Any) -> None:
    """
    Set a context value.
    
    Thread-safe operation to set context values.
    
    Args:
        key: Context key.
        value: Value to set.
    """
    with _context_lock:
        _context[key] = value


def clear_context_value(key: str) -> None:
    """
    Clear a context value.
    
    Thread-safe operation to remove a context value.
    
    Args:
        key: Context key to clear.
    """
    with _context_lock:
        _context.pop(key, None)


def has_context_value(key: str) -> bool:
    """
    Check if a context value exists.
    
    Thread-safe operation to check for context value existence.
    
    Args:
        key: Context key to check.
        
    Returns:
        True if the key exists in context.
    """
    with _context_lock:
        return key in _context


def _get_all_context() -> Dict[str, Any]:
    """
    Get a copy of all context values.
    
    Thread-safe operation to retrieve all context.
    
    Returns:
        Copy of all context values.
    """
    with _context_lock:
        return dict(_context)


class StructuredFormatter(logging.Formatter):
    """
    JSON structured formatter for file logging.
    
    Outputs log records as JSON objects with:
    - timestamp: ISO 8601 UTC timestamp
    - level: Log level name
    - logger: Logger name
    - message: Log message
    - context: Current context values (strategy, run_id, etc.)
    - extra: Additional fields from log_with_context
    - exception: Exception info if present
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON string."""
        # Base log data
        log_data: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add context values
        context = _get_all_context()
        if context:
            log_data["context"] = context
        
        # Add extra fields (from log_with_context)
        extra_fields = getattr(record, 'extra_fields', None)
        if extra_fields:
            log_data["extra"] = extra_fields
        
        # Add exception info
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
            }
            if record.exc_text:
                log_data["exception"]["traceback"] = record.exc_text
        
        # Add source location for DEBUG level
        if record.levelno <= logging.DEBUG:
            log_data["source"] = {
                "file": record.pathname,
                "line": record.lineno,
                "function": record.funcName,
            }
        
        return json.dumps(log_data, default=str)


class ConsoleFormatter(logging.Formatter):
    """
    Human-readable formatter for console output.
    
    Outputs log records in format:
    YYYY-MM-DD HH:MM:SS | LEVEL | logger | message [context]
    
    Color coding (if terminal supports it):
    - DEBUG: dim
    - INFO: default
    - WARNING: yellow
    - ERROR: red
    - CRITICAL: bold red
    """
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[2m',      # Dim
        'INFO': '',              # Default
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[1;31m',  # Bold red
    }
    RESET = '\033[0m'
    
    def __init__(self, use_colors: bool = True):
        """
        Initialize console formatter.
        
        Args:
            use_colors: Whether to use ANSI color codes.
        """
        super().__init__()
        self.use_colors = use_colors
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record for console display."""
        # Format timestamp
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        
        # Get level with padding
        level = record.levelname.ljust(8)
        
        # Get logger name (last part only for brevity)
        logger_name = record.name.split('.')[-1] if '.' in record.name else record.name
        
        # Build message
        message = record.getMessage()
        
        # Add context info
        context = _get_all_context()
        context_str = ""
        if context:
            # Show key context items inline
            context_parts = []
            for key in ['strategy', 'phase', 'run_id', 'asset_type', 'timeframe']:
                if key in context and context[key]:
                    context_parts.append(f"{key}={context[key]}")
            if context_parts:
                context_str = f" [{', '.join(context_parts)}]"
        
        # Add extra fields
        extra_fields = getattr(record, 'extra_fields', None)
        extra_str = ""
        if extra_fields:
            # Show error code if present
            if 'error_code' in extra_fields:
                extra_str = f" (code={extra_fields['error_code']})"
        
        # Build formatted line
        formatted = f"{timestamp} | {level} | {logger_name} | {message}{context_str}{extra_str}"
        
        # Add colors if enabled
        if self.use_colors and record.levelname in self.COLORS:
            color = self.COLORS[record.levelname]
            if color:
                formatted = f"{color}{formatted}{self.RESET}"
        
        # Add exception info
        if record.exc_info:
            exc_text = self.formatException(record.exc_info)
            formatted = f"{formatted}\n{exc_text}"
        
        return formatted


# Public exports
__all__ = [
    "StructuredFormatter",
    "ConsoleFormatter",
    "_context",
    "get_context_value",
    "set_context_value",
    "clear_context_value",
    "has_context_value",
]





