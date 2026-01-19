"""
Data processing utilities for The Researcher's Cockpit.

Provides functions for OHLCV data aggregation, normalization,
filtering, and FOREX-specific processing.
"""

# Aggregation utilities
from .aggregation import (
    aggregate_ohlcv,
    resample_to_timeframe,
    create_multi_timeframe_data,
    get_timeframe_multiplier,
)

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
    # Aggregation
    'aggregate_ohlcv',
    'resample_to_timeframe',
    'create_multi_timeframe_data',
    'get_timeframe_multiplier',
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
