"""
Backward compatibility wrapper for lib.extension.

This module re-exports calendar functions from lib.calendars
for backward compatibility with older code.

DEPRECATED: Import directly from lib.calendars instead.
"""

import warnings

warnings.warn(
    "lib.extension is deprecated. Use lib.calendars instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export everything from lib.calendars
from .calendars import (
    CryptoCalendar,
    ForexCalendar,
    register_custom_calendars,
    get_calendar_for_asset_class,
    resolve_calendar_name,
    get_available_calendars,
    register_calendar_type,
    get_calendar_registry,
    get_registered_calendars,
    populate_registry,
)

__all__ = [
    'CryptoCalendar',
    'ForexCalendar',
    'register_custom_calendars',
    'get_calendar_for_asset_class',
    'resolve_calendar_name',
    'get_available_calendars',
    'register_calendar_type',
    'get_calendar_registry',
    'get_registered_calendars',
    'populate_registry',
]
