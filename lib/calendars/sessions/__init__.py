"""
Centralized session management system.

Provides SessionManager for consistent session definitions across
bundle ingestion and backtest execution.
"""

from .manager import SessionManager, get_session_manager
from .strategies import (
    SessionStrategy,
    ForexSessionStrategy,
    CryptoSessionStrategy,
    EquitySessionStrategy,
)
from .validation import SessionMismatchReport, compare_sessions

__all__ = [
    'SessionManager',
    'get_session_manager',
    'SessionStrategy',
    'ForexSessionStrategy',
    'CryptoSessionStrategy',
    'EquitySessionStrategy',
    'SessionMismatchReport',
    'compare_sessions',
]
