"""
Data processing utilities for The Researcher's Cockpit.

Note: aggregation.py removed in v1.12.0.

For minute → daily aggregation:
- Bundle ingestion: Zipline aggregates automatically (BcolzDailyBarWriter)
- Strategy code: Use pandas.resample() directly

Migration:
    # Before (v1.11.x):
    from lib.data.aggregation import aggregate_ohlcv
    daily = aggregate_ohlcv(minute_df, 'daily')

    # After (v1.12.0):
    daily = minute_df.resample('1D').agg({
        'open': 'first', 'high': 'max', 'low': 'min',
        'close': 'last', 'volume': 'sum'
    })

Provides functions for data normalization, filtering, and FOREX-specific processing.
"""

# Normalization utilities
from .normalization import (
    normalize_to_utc,
    fill_data_gaps,
)

# FOREX-specific utilities
from .forex import (
    consolidate_sunday_to_friday,
)

# Data filtering utilities
from .filters import (
    filter_forex_presession_bars,
    consolidate_forex_sunday_to_friday,
    filter_to_calendar_sessions,
    apply_gap_filling,
    filter_daily_to_calendar_sessions,
)

__all__ = [
    # Normalization
    'normalize_to_utc',
    'fill_data_gaps',
    # FOREX
    'consolidate_sunday_to_friday',
    # Filters
    'filter_forex_presession_bars',
    'consolidate_forex_sunday_to_friday',
    'filter_to_calendar_sessions',
    'apply_gap_filling',
    'filter_daily_to_calendar_sessions',
]
