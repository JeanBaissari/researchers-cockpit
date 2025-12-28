"""
Zipline Extension Module for Custom Calendars

This module provides custom trading calendars for crypto (24/7) and forex markets.
These calendars extend Zipline's capabilities beyond standard equity market hours.

Uses exchange_calendars v4.x API for modern calendar implementation.

Note: Calendars are NOT auto-registered on import. Call `register_custom_calendars()`
explicitly from your entry points (e.g., lib/backtest.py) to ensure controlled
initialization and avoid side effects during testing or module inspection.
"""

import logging
from datetime import time
from typing import Dict, List, Optional, Type

import pandas as pd
from exchange_calendars import ExchangeCalendar
from exchange_calendars.calendar_helpers import UTC

logger = logging.getLogger(__name__)

# Registry of available custom calendars
_CALENDAR_REGISTRY: Dict[str, Type[ExchangeCalendar]] = {}

# Track which calendars have been registered with Zipline
_registered_calendars: List[str] = []


class CryptoCalendar(ExchangeCalendar):
    """
    24/7 Trading Calendar for Cryptocurrency Markets
    
    Crypto markets trade continuously without holidays or market closures.
    This calendar reflects that reality with no off days.
    """
    
    name = "CRYPTO"
    tz = UTC
    open_times = ((None, time(0, 0)),)
    close_times = ((None, time(23, 59, 59)),)  # Fixed: use 23:59:59 for proper 24h coverage
    weekmask = "Mon Tue Wed Thu Fri Sat Sun"
    
    @property
    def regular_holidays(self) -> pd.DatetimeIndex:
        """Crypto markets don't observe holidays."""
        return pd.DatetimeIndex([])
    
    @property
    def special_closes(self) -> list:
        """No special closing times."""
        return []


class ForexCalendar(ExchangeCalendar):
    """
    Forex Trading Calendar (24/5 - Weekdays Only)
    
    Forex markets trade 24 hours on weekdays but close on weekends.
    Trading opens Sunday 5pm EST and closes Friday 5pm EST.
    
    Note: We use Mon-Fri weekmask because exchange_calendars handles
    sessions on a daily basis. The Sunday open is effectively the start
    of the Monday session in trading terms.
    """
    
    name = "FOREX"
    tz = "America/New_York"
    open_times = ((None, time(0, 0)),)  # Session starts at midnight (continuous trading)
    close_times = ((None, time(23, 59, 59)),)  # Session ends at 23:59:59
    weekmask = "Mon Tue Wed Thu Fri"  # Fixed: Standard weekday trading
    
    @property
    def regular_holidays(self) -> pd.DatetimeIndex:
        """
        Forex observes major holidays when global banking is closed.
        Returns DatetimeIndex of holidays for the calendar's date range.
        """
        # For now, return empty - can be extended to include specific holidays
        # Forex typically observes: New Year's Day, Christmas, and major US holidays
        # To add holidays, use: pd.DatetimeIndex([...]) with specific dates
        return pd.DatetimeIndex([])
    
    @property
    def special_closes(self) -> list:
        """No special closing times."""
        return []


# Populate the calendar registry
_CALENDAR_REGISTRY = {
    'CRYPTO': CryptoCalendar,
    'FOREX': ForexCalendar,
}

# Calendar aliases for common names
_CALENDAR_ALIASES = {
    '24/7': 'CRYPTO',
    'ALWAYS_OPEN': 'CRYPTO',
    'FX': 'FOREX',
    'CURRENCY': 'FOREX',
}


def resolve_calendar_name(name_or_alias: str) -> Optional[str]:
    """Resolve calendar name from alias."""
    upper = name_or_alias.upper()
    if upper in _CALENDAR_REGISTRY:
        return upper
    return _CALENDAR_ALIASES.get(upper)


def get_available_calendars() -> List[str]:
    """
    Get list of available custom calendar names.
    
    Returns:
        List of calendar names that can be registered.
    """
    return list(_CALENDAR_REGISTRY.keys())


def get_registered_calendars() -> List[str]:
    """
    Get list of calendars that have been registered with Zipline.
    
    Returns:
        List of calendar names currently registered.
    """
    return list(_registered_calendars)


def register_calendar_type(
    name: str,
    calendar_class: Type[ExchangeCalendar],
    start: Optional[str] = None,
    end: Optional[str] = None,
    force: bool = True
) -> bool:
    """
    Register a custom calendar TYPE (factory) with Zipline.

    This registers the calendar class, not an instance, allowing Zipline
    to lazily instantiate it with appropriate date bounds during bundle
    ingestion and backtest execution.

    Args:
        name: Calendar name (e.g., 'CRYPTO', 'FOREX')
        calendar_class: Calendar class (subclass of ExchangeCalendar)
        start: Deprecated, not used (kept for API compatibility)
        end: Deprecated, not used (kept for API compatibility)
        force: If True, overwrite existing calendar registration. Default True.

    Returns:
        True if registration successful, False otherwise.

    Raises:
        ValueError: If calendar_class is not a valid ExchangeCalendar subclass.
    """
    # Validate calendar class
    if not issubclass(calendar_class, ExchangeCalendar):
        raise ValueError(
            f"calendar_class must be a subclass of ExchangeCalendar, "
            f"got {type(calendar_class).__name__}"
        )

    # Import here to avoid circular imports
    try:
        from exchange_calendars.calendar_utils import global_calendar_dispatcher
    except ImportError as e:
        logger.error(f"Failed to import exchange_calendars: {e}")
        return False

    try:
        # Register the calendar TYPE (factory) instead of an instance
        # This allows Zipline to instantiate the calendar with appropriate date bounds
        global_calendar_dispatcher.register_calendar_type(
            name=name,
            calendar_type=calendar_class,
            force=force
        )

        # Track registration
        if name not in _registered_calendars:
            _registered_calendars.append(name)

        logger.info(f"Successfully registered calendar type: {name}")
        return True
    except Exception as e:
        logger.error(f"Failed to register calendar type '{name}': {e}")
        return False


def register_custom_calendars(
    calendars: Optional[List[str]] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    force: bool = True
) -> Dict[str, bool]:
    """
    Register custom calendars with Zipline.
    
    This function should be called explicitly from your entry points
    (e.g., lib/backtest.py's run_backtest function) rather than relying
    on auto-registration at import time.
    
    Args:
        calendars: List of calendar names to register. If None, registers all available.
        start: Optional start date string (YYYY-MM-DD) for all calendars.
        end: Optional end date string (YYYY-MM-DD) for all calendars.
        force: If True, overwrite existing calendar registrations. Default True.
    
    Returns:
        Dictionary mapping calendar names to registration success (True/False).
    
    Example:
        >>> from lib.extension import register_custom_calendars
        >>> results = register_custom_calendars(['CRYPTO'])
        >>> assert results['CRYPTO'] == True
    """
    if calendars is None:
        calendars = list(_CALENDAR_REGISTRY.keys())
    
    results = {}
    
    for name in calendars:
        if name not in _CALENDAR_REGISTRY:
            logger.warning(f"Unknown calendar '{name}'. Available: {list(_CALENDAR_REGISTRY.keys())}")
            results[name] = False
            continue
        
        calendar_class = _CALENDAR_REGISTRY[name]
        results[name] = register_calendar_type(
            name=name,
            calendar_class=calendar_class,
            start=start,
            end=end,
            force=force
        )
    
    # Log summary
    successful = [k for k, v in results.items() if v]
    failed = [k for k, v in results.items() if not v]

    if successful:
        logger.info(f"Registered calendars: {successful}")
    if failed:
        logger.warning(f"Failed to register calendars: {failed}")
    
    return results


def get_calendar_for_asset_class(asset_class: str) -> Optional[str]:
    """
    Get the appropriate calendar name for a given asset class.
    
    This provides integration with the strategy parameters system,
    allowing strategies to specify their asset class and automatically
    get the correct trading calendar.
    
    Args:
        asset_class: Asset class name (e.g., 'crypto', 'forex', 'equity')
    
    Returns:
        Calendar name string, or None if no custom calendar needed.
    """
    asset_class_lower = asset_class.lower()
    
    # Map asset classes to calendars
    asset_calendar_map = {
        'crypto': 'CRYPTO',
        'cryptocurrency': 'CRYPTO',
        'forex': 'FOREX',
        'fx': 'FOREX',
        'currency': 'FOREX',
    }
    
    calendar_name = asset_calendar_map.get(asset_class_lower)
    
    if calendar_name and calendar_name in _CALENDAR_REGISTRY:
        return calendar_name
    
    # Return None for equity/standard asset classes - use Zipline defaults
    return None
