"""
Data processing utilities for The Researcher's Cockpit.

Provides functions for OHLCV data aggregation, normalization,
filtering, and FOREX-specific processing.
"""

# Aggregation utilities
try:
    from .aggregation import *
except ImportError:
    pass

# Normalization utilities
try:
    from .normalization import *
except ImportError:
    pass

# FOREX-specific utilities
try:
    from .forex import *
except ImportError:
    pass

# Data filtering utilities
from .filters import (
    filter_forex_presession_bars,
    consolidate_forex_sunday_to_friday,
    filter_to_calendar_sessions,
    apply_gap_filling,
    filter_daily_to_calendar_sessions,
    # Backward compatibility aliases
    _filter_forex_presession_bars,
    _consolidate_forex_sunday_to_friday,
    _filter_to_calendar_sessions,
    _apply_gap_filling,
    _filter_daily_to_calendar_sessions,
)

__all__ = [
    # Filters
    'filter_forex_presession_bars',
    'consolidate_forex_sunday_to_friday',
    'filter_to_calendar_sessions',
    'apply_gap_filling',
    'filter_daily_to_calendar_sessions',
    # Backward compatibility aliases
    '_filter_forex_presession_bars',
    '_consolidate_forex_sunday_to_friday',
    '_filter_to_calendar_sessions',
    '_apply_gap_filling',
    '_filter_daily_to_calendar_sessions',
]
