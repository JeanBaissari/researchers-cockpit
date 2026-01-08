"""
Trading Calendars Package

This package provides custom trading calendars for different asset classes:
- CryptoCalendar: 24/7 trading (no holidays, no weekends)
- ForexCalendar: 24/5 trading (weekdays only)

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
populate_registry({
    'CRYPTO': CryptoCalendar,
    'FOREX': ForexCalendar,
})

__all__ = [
    # Calendar classes
    'CryptoCalendar',
    'ForexCalendar',
    # Registry functions
    'populate_registry',
    'get_calendar_registry',
    'register_calendar_type',
    'register_custom_calendars',
    'get_registered_calendars',
    # Utility functions
    'resolve_calendar_name',
    'get_available_calendars',
    'get_calendar_for_asset_class',
]

