"""
Logging context management.

Provides context managers and utilities for adding contextual information
to log messages across the application.
"""

import threading
from contextlib import contextmanager
from typing import Any, Dict, Generator, Optional

from .formatters import (
    _context,
    get_context_value,
    set_context_value,
    clear_context_value,
    has_context_value,
)

# Thread-safe lock for context operations
_context_lock = threading.RLock()


def reset_context() -> None:
    """
    Clear all context values at once.
    
    Thread-safe operation useful between backtest runs or test cases.
    """
    with _context_lock:
        _context.clear()


@contextmanager
def LogContext(
    phase: str,
    strategy: Optional[str] = None,
    run_id: Optional[str] = None,
    asset_type: Optional[str] = None,
    bundle_name: Optional[str] = None,
    timeframe: Optional[str] = None,
) -> Generator[None, None, None]:
    """
    Context manager for adding context to all logs within the block.
    
    Thread-safe context management with automatic cleanup on exit.
    
    Usage:
        with LogContext(
            phase="backtest",
            strategy="btc_sma_cross",
            run_id="20241220_143000",
            asset_type="crypto",
            bundle_name="yahoo_crypto_daily",
            timeframe="daily"
        ):
            run_backtest(...)  # All logs within include full context
    
    Args:
        phase: Pipeline phase (e.g., "hypothesis", "backtest", "optimize", "validate").
        strategy: Optional strategy name.
        run_id: Optional run identifier.
        asset_type: Optional asset type (equity, forex, crypto).
        bundle_name: Optional bundle name.
        timeframe: Optional timeframe (1m, 5m, 15m, 30m, 1h, daily).
    """
    # Define context fields and their provided values
    context_fields: Dict[str, Any] = {
        'phase': phase,
        'strategy': strategy,
        'run_id': run_id,
        'asset_type': asset_type,
        'bundle_name': bundle_name,
        'timeframe': timeframe,
    }
    
    # Store previous context values (thread-safe)
    prev_values: Dict[str, Any] = {}
    with _context_lock:
        for field, value in context_fields.items():
            if value is not None or field == 'phase':  # phase is always set
                prev_values[field] = get_context_value(field)
        
        # Set new context values
        for field, value in context_fields.items():
            if value is not None:
                set_context_value(field, value)
            elif field == 'phase':
                set_context_value(field, value)
    
    try:
        yield
    finally:
        # Restore previous context (thread-safe)
        with _context_lock:
            for field, prev_value in prev_values.items():
                if prev_value is not None:
                    set_context_value(field, prev_value)
                elif has_context_value(field):
                    clear_context_value(field)


# Public exports
__all__ = [
    "LogContext",
    "reset_context",
    "get_context_value",
    "set_context_value",
    "clear_context_value",
    "has_context_value",
]















