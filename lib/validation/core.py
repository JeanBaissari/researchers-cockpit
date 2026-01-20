"""
Core validation constants and configuration.

Contains:
- Timeframe categorization constants
- Column name definitions and aliases
- Default validation thresholds
- Calendar identifiers

For validation models (ValidationResult, ValidationCheck, etc.), see models.py
"""

import logging
from typing import FrozenSet, Dict, List

import pandas as pd

# Import shared validation models
from .models import (
    ValidationSeverity,
    ValidationStatus,
    ValidationCheck,
    ValidationResult,
)

logger = logging.getLogger('cockpit.validation')

# =============================================================================
# Constants and Configuration
# =============================================================================

# Timeframe categories for validation logic
INTRADAY_TIMEFRAMES: FrozenSet[str] = frozenset({
    '1m', '2m', '5m', '15m', '30m', '1h', '60m', '90m'
})
DAILY_TIMEFRAMES: FrozenSet[str] = frozenset({
    '1d', 'daily', '1wk', 'weekly', '1mo', 'monthly'
})
ALL_TIMEFRAMES: FrozenSet[str] = INTRADAY_TIMEFRAMES | DAILY_TIMEFRAMES

# Expected column names (lowercase canonical form)
REQUIRED_OHLCV_COLUMNS: FrozenSet[str] = frozenset([
    'open', 'high', 'low', 'close', 'volume'
])
OPTIONAL_OHLCV_COLUMNS: FrozenSet[str] = frozenset([
    'adj_close', 'dividends', 'splits', 'vwap'
])

# Validation thresholds (sensible defaults)
DEFAULT_GAP_TOLERANCE_DAYS: int = 3
DEFAULT_GAP_TOLERANCE_BARS: int = 10
DEFAULT_OUTLIER_THRESHOLD_SIGMA: float = 5.0
DEFAULT_STALE_THRESHOLD_DAYS: int = 7
DEFAULT_ZERO_VOLUME_THRESHOLD_PCT: float = 10.0
DEFAULT_PRICE_JUMP_THRESHOLD_PCT: float = 50.0
DEFAULT_VOLUME_SPIKE_THRESHOLD_SIGMA: float = 5.0
DEFAULT_MIN_ROWS_DAILY: int = 20
DEFAULT_MIN_ROWS_INTRADAY: int = 100

# 24/7 calendar identifiers
CONTINUOUS_CALENDARS: FrozenSet[str] = frozenset({
    '24/7', 'FOREX', '24_7', 'CRYPTO', 'always_open'
})

# Timeframe to interval mapping
TIMEFRAME_INTERVALS: Dict[str, pd.Timedelta] = {
    '1m': pd.Timedelta(minutes=1),
    '2m': pd.Timedelta(minutes=2),
    '5m': pd.Timedelta(minutes=5),
    '15m': pd.Timedelta(minutes=15),
    '30m': pd.Timedelta(minutes=30),
    '1h': pd.Timedelta(hours=1),
    '60m': pd.Timedelta(hours=1),
    '90m': pd.Timedelta(minutes=90),
    '1d': pd.Timedelta(days=1),
    'daily': pd.Timedelta(days=1),
    '1wk': pd.Timedelta(weeks=1),
    'weekly': pd.Timedelta(weeks=1),
    '1mo': pd.Timedelta(days=30),
    'monthly': pd.Timedelta(days=30),
}

# Column aliases for case-insensitive matching
COLUMN_ALIASES: Dict[str, List[str]] = {
    'open': ['open', 'Open', 'OPEN', 'o', 'O'],
    'high': ['high', 'High', 'HIGH', 'h', 'H'],
    'low': ['low', 'Low', 'LOW', 'l', 'L'],
    'close': [
        'close', 'Close', 'CLOSE', 'c', 'C',
        'adj_close', 'Adj_Close', 'adj close', 'Adj Close'
    ],
    'volume': ['volume', 'Volume', 'VOLUME', 'vol', 'Vol', 'VOL', 'v', 'V'],
}
