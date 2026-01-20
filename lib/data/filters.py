"""
Data filtering utilities - Public API.

This module provides the public API for all filter functions from specialized
filter modules. For direct access to specific filter types, import from:
- lib.data.filters_forex: FOREX-specific filtering
- lib.data.filters_calendar: Calendar-based filtering
- lib.data.filters_gaps: Gap-filling utilities
"""

# FOREX filtering functions
from .filters_forex import (
    filter_forex_presession_bars,
    consolidate_forex_sunday_to_friday,
)

# Calendar filtering functions
from .filters_calendar import (
    filter_to_calendar_sessions,
    filter_daily_to_calendar_sessions,
)

# Gap-filling functions
from .filters_gaps import (
    apply_gap_filling,
)

__all__ = [
    # FOREX filtering
    'filter_forex_presession_bars',
    'consolidate_forex_sunday_to_friday',
    # Calendar filtering
    'filter_to_calendar_sessions',
    'filter_daily_to_calendar_sessions',
    # Gap-filling
    'apply_gap_filling',
]

