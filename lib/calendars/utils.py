"""
Calendar Utility Functions

This module provides utility functions for working with trading calendars.
"""

from typing import Dict, List, Optional

# Calendar aliases for common names
_CALENDAR_ALIASES = {
    '24/7': 'CRYPTO',
    'ALWAYS_OPEN': 'CRYPTO',
    'FX': 'FOREX',
    'CURRENCY': 'FOREX',
}


def resolve_calendar_name(name_or_alias: str) -> Optional[str]:
    """
    Resolve calendar name from alias.
    
    Args:
        name_or_alias: Calendar name or alias
        
    Returns:
        Resolved calendar name, or None if not found
        
    Example:
        >>> resolve_calendar_name('FX')
        'FOREX'
        >>> resolve_calendar_name('24/7')
        'CRYPTO'
    """
    # Import here to avoid circular dependency
    from .registry import get_calendar_registry
    
    upper = name_or_alias.upper()
    registry = get_calendar_registry()
    
    # Check if it's a direct match first
    if upper in registry:
        return upper
    
    # Check aliases
    return _CALENDAR_ALIASES.get(upper)


def get_available_calendars() -> List[str]:
    """
    Get list of available custom calendar names.
    
    Returns:
        List of calendar names that can be registered.
        
    Example:
        >>> calendars = get_available_calendars()
        >>> 'CRYPTO' in calendars
        True
    """
    # Import here to avoid circular dependency
    from .registry import get_calendar_registry
    
    return list(get_calendar_registry().keys())


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
        
    Example:
        >>> get_calendar_for_asset_class('crypto')
        'CRYPTO'
        >>> get_calendar_for_asset_class('forex')
        'FOREX'
        >>> get_calendar_for_asset_class('equity')
        None
    """
    # Import here to avoid circular dependency
    from .registry import get_calendar_registry
    
    asset_class_lower = asset_class.lower()
    
    # Map asset classes to calendars
    asset_calendar_map: Dict[str, str] = {
        'crypto': 'CRYPTO',
        'cryptocurrency': 'CRYPTO',
        'forex': 'FOREX',
        'fx': 'FOREX',
        'currency': 'FOREX',
    }
    
    calendar_name = asset_calendar_map.get(asset_class_lower)
    
    if calendar_name and calendar_name in get_calendar_registry():
        return calendar_name
    
    # Return None for equity/standard asset classes - use Zipline defaults
    return None


__all__ = [
    'resolve_calendar_name',
    'get_available_calendars',
    'get_calendar_for_asset_class',
]

