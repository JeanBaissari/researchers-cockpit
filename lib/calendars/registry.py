"""
Calendar Registration Module

This module provides functions to register custom calendars with Zipline.
"""

import logging
from typing import Dict, List, Optional, Type

from exchange_calendars import ExchangeCalendar

logger = logging.getLogger(__name__)

# Registry of available custom calendars
_CALENDAR_REGISTRY: Dict[str, Type[ExchangeCalendar]] = {}

# Track which calendars have been registered with Zipline
_registered_calendars: List[str] = []


def populate_registry(calendars: Dict[str, Type[ExchangeCalendar]]) -> None:
    """
    Populate the calendar registry with calendar classes.
    
    Args:
        calendars: Dictionary mapping calendar names to calendar classes
    """
    global _CALENDAR_REGISTRY
    _CALENDAR_REGISTRY.update(calendars)


def get_calendar_registry() -> Dict[str, Type[ExchangeCalendar]]:
    """
    Get the calendar registry.
    
    Returns:
        Dictionary mapping calendar names to calendar classes
    """
    return _CALENDAR_REGISTRY.copy()


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
        >>> from lib.calendars import register_custom_calendars
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


def get_registered_calendars() -> List[str]:
    """
    Get list of calendars that have been registered with Zipline.
    
    Returns:
        List of calendar names currently registered.
    """
    return list(_registered_calendars)


__all__ = [
    'populate_registry',
    'get_calendar_registry',
    'register_calendar_type',
    'register_custom_calendars',
    'get_registered_calendars',
]





