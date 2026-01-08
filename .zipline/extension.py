"""
Zipline Extension: Custom Calendars Loader

This module loads custom calendars from lib.calendars for Zipline integration.
All calendar logic lives in lib/calendars/. This file is kept for Zipline compatibility.

Zipline automatically loads this file from the .zipline directory on startup.
"""

from lib.calendars import (
    CryptoCalendar,
    ForexCalendar,
    register_custom_calendars,
    register_calendar_type,
    get_calendar_for_asset_class,
    get_available_calendars,
    get_registered_calendars,
    resolve_calendar_name,
)

__all__ = [
    'CryptoCalendar',
    'ForexCalendar',
    'register_custom_calendars',
    'register_calendar_type',
    'get_calendar_for_asset_class',
    'get_available_calendars',
    'get_registered_calendars',
    'resolve_calendar_name',
]
