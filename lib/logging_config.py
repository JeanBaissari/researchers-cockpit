"""
Centralized logging configuration for The Researcher's Cockpit.

Provides structured logging with consistent formatting across all modules.
Supports both console output (human-readable) and file output (structured JSON).
"""

import logging
import logging.handlers
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from contextlib import contextmanager
import threading

# Thread-local storage for logging context
_context = threading.local()


class StructuredFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.

    Produces machine-parseable log entries with context fields.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }

        # Add context from thread-local storage
        if hasattr(_context, 'strategy'):
            log_entry['strategy'] = _context.strategy
        if hasattr(_context, 'run_id'):
            log_entry['run_id'] = _context.run_id
        if hasattr(_context, 'phase'):
            log_entry['phase'] = _context.phase

        # Add extra fields from record
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)

        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


class ConsoleFormatter(logging.Formatter):
    """
    Human-readable formatter for console output.

    Includes context information in a clean format.
    """

    def format(self, record: logging.LogRecord) -> str:
        # Build context prefix
        context_parts = []
        if hasattr(_context, 'strategy'):
            context_parts.append(f"[{_context.strategy}]")
        if hasattr(_context, 'phase'):
            context_parts.append(f"<{_context.phase}>")

        context_str = ' '.join(context_parts)
        if context_str:
            context_str += ' '

        # Format the base message
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        level = record.levelname
        message = record.getMessage()

        formatted = f"{timestamp} | {level:8s} | {context_str}{message}"

        # Add extra context on next line if present
        if hasattr(record, 'extra_fields') and record.extra_fields:
            extras = ' | '.join(f"{k}={v}" for k, v in record.extra_fields.items())
            formatted += f"\n    {extras}"

        return formatted


def configure_logging(
    strategy_name: Optional[str] = None,
    run_id: Optional[str] = None,
    level: str = "INFO",
    log_dir: Optional[Path] = None,
    console: bool = True,
    file: bool = True,
    structured: bool = True
) -> logging.Logger:
    """
    Configure centralized logging for the application.

    Args:
        strategy_name: Optional strategy name for context
        run_id: Optional run ID for context
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files (default: PROJECT_ROOT/logs)
        console: Enable console output
        file: Enable file output
        structured: Use JSON structured format for file logs

    Returns:
        Root logger for the 'cockpit' namespace
    """
    # Get log directory
    if log_dir is None:
        try:
            from .paths import get_logs_dir
            log_dir = get_logs_dir()
        except ImportError:
            log_dir = Path('logs')

    log_dir.mkdir(parents=True, exist_ok=True)

    # Get or create root logger
    root_logger = logging.getLogger('cockpit')
    root_logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers to avoid duplicates
    root_logger.handlers = []

    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, level.upper()))
        console_handler.setFormatter(ConsoleFormatter())
        root_logger.addHandler(console_handler)

    # File handler
    if file:
        # Daily rotating log file
        log_file = log_dir / f"cockpit_{datetime.now().strftime('%Y%m%d')}.log"

        if structured:
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5,
                encoding='utf-8'
            )
            file_handler.setFormatter(StructuredFormatter())
        else:
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=10 * 1024 * 1024,
                backupCount=5,
                encoding='utf-8'
            )
            file_handler.setFormatter(ConsoleFormatter())

        file_handler.setLevel(getattr(logging, level.upper()))
        root_logger.addHandler(file_handler)

    # Set context if provided
    if strategy_name:
        _context.strategy = strategy_name
    if run_id:
        _context.run_id = run_id

    return root_logger


@contextmanager
def LogContext(phase: str, strategy: Optional[str] = None, run_id: Optional[str] = None):
    """
    Context manager for adding phase/strategy/run_id to all logs within the block.

    Usage:
        with LogContext(phase="backtest", strategy="btc_sma_cross", run_id="20241220_143000"):
            run_backtest(...)  # All logs within include phase/strategy/run_id

    Args:
        phase: Pipeline phase (e.g., "hypothesis", "backtest", "optimize", "validate")
        strategy: Optional strategy name
        run_id: Optional run identifier
    """
    # Store previous context
    prev_phase = getattr(_context, 'phase', None)
    prev_strategy = getattr(_context, 'strategy', None)
    prev_run_id = getattr(_context, 'run_id', None)

    # Set new context
    _context.phase = phase
    if strategy:
        _context.strategy = strategy
    if run_id:
        _context.run_id = run_id

    try:
        yield
    finally:
        # Restore previous context
        if prev_phase is not None:
            _context.phase = prev_phase
        elif hasattr(_context, 'phase'):
            delattr(_context, 'phase')

        if prev_strategy is not None:
            _context.strategy = prev_strategy
        elif strategy and hasattr(_context, 'strategy'):
            delattr(_context, 'strategy')

        if prev_run_id is not None:
            _context.run_id = prev_run_id
        elif run_id and hasattr(_context, 'run_id'):
            delattr(_context, 'run_id')


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the cockpit namespace prefix.

    Args:
        name: Logger name (e.g., 'data', 'backtest', 'metrics')

    Returns:
        Logger instance
    """
    return logging.getLogger(f'cockpit.{name}')


def log_with_context(logger: logging.Logger, level: int, message: str, **kwargs) -> None:
    """
    Log a message with additional context fields.

    Args:
        logger: Logger instance
        level: Logging level (e.g., logging.INFO)
        message: Log message
        **kwargs: Additional context fields to include
    """
    record = logger.makeRecord(
        logger.name, level, '', 0, message, (), None
    )
    record.extra_fields = kwargs
    logger.handle(record)


# Legacy compatibility
def setup_logging(
    level: str = 'INFO',
    log_file: Optional[Path] = None
) -> logging.Logger:
    """
    Legacy function for backwards compatibility.

    Use configure_logging() for new code.
    """
    return configure_logging(
        level=level,
        file=log_file is not None,
        console=True
    )


# Module-level loggers for common namespaces
data_logger = get_logger('data')
strategy_logger = get_logger('strategy')
backtest_logger = get_logger('backtest')
metrics_logger = get_logger('metrics')
validation_logger = get_logger('validation')
report_logger = get_logger('report')
