"""
Trading Calendars Package (v1.12.0+)

This package provides custom trading calendars for different asset classes:
- CryptoCalendar: 24/7 trading (no holidays, no weekends)
- ForexCalendar: 24/5 trading (Sun evening - Fri evening, includes Sundays)

For direct calendar access, use Zipline's APIs:
    from zipline.utils.calendar_utils import get_calendar, register_calendar
    calendar = get_calendar('FOREX')
    sessions = calendar.sessions_in_range(start, end)

Migration Notes (v1.12.0):
- SessionManager removed → Use get_calendar() directly
- FOREX calendar now includes Sundays (weekmask updated in v1.12.0)
- No session alignment workarounds needed

Usage:
    from lib.calendars import register_custom_calendars, CryptoCalendar

    # Register calendars with Zipline
    register_custom_calendars(['CRYPTO', 'FOREX'])

    # Get calendar for asset class
    from lib.calendars import get_calendar_for_asset_class
    calendar_name = get_calendar_for_asset_class('crypto')  # Returns 'CRYPTO'
"""

# Calendar classes
from .crypto import CryptoCalendar
from .forex import ForexCalendar

# Registry functions
from .registry import (
    populate_registry,
    get_calendar_registry,
    register_calendar_type,
    register_custom_calendars,
    get_registered_calendars,
)

# Utility functions
from .utils import (
    resolve_calendar_name,
    get_available_calendars,
    get_calendar_for_asset_class,
)

# Populate the registry with available calendars
populate_registry(
    {
        "CRYPTO": CryptoCalendar,
        "FOREX": ForexCalendar,
    }
)

__all__ = [
    # Calendar classes
    "CryptoCalendar",
    "ForexCalendar",
    # Registry functions
    "populate_registry",
    "get_calendar_registry",
    "register_calendar_type",
    "register_custom_calendars",
    "get_registered_calendars",
    # Utility functions
    "resolve_calendar_name",
    "get_available_calendars",
    "get_calendar_for_asset_class",
]
