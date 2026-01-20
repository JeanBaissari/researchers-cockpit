"""
Backtest configuration validation.

Provides validation functions for the backtest section of strategy parameters.
"""

import re
from datetime import datetime
from typing import Optional, List, Any

# Date format regex for YYYY-MM-DD validation
_DATE_PATTERN = re.compile(r'^\d{4}-\d{2}-\d{2}$')


def _validate_date_format(date_str: str) -> bool:
    """
    Validate that a date string is in YYYY-MM-DD format and represents a valid date.
    
    Args:
        date_str: Date string to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not _DATE_PATTERN.match(date_str):
        return False
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False


def _parse_date(date_str: str) -> Optional[datetime]:
    """
    Parse a date string in YYYY-MM-DD format.
    
    Args:
        date_str: Date string to parse
        
    Returns:
        datetime object or None if parsing fails
    """
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except (ValueError, TypeError):
        return None


def validate_backtest_section(backtest: Any, errors: List[str]) -> None:
    """
    Validate the backtest section of strategy parameters.
    
    Args:
        backtest: Backtest configuration dictionary
        errors: List to append validation errors to
    """
    # Guard against backtest being None
    if backtest is None:
        errors.append("'backtest' section is null/None")
        return
    
    if not isinstance(backtest, dict):
        errors.append(f"'backtest' section must be a dictionary, got {type(backtest).__name__}")
        return
    
    start_date_valid = False
    end_date_valid = False
    parsed_start = None
    parsed_end = None
    
    # Validate start_date if present
    if 'start_date' in backtest:
        start_date = backtest['start_date']
        if not isinstance(start_date, str):
            errors.append("'backtest.start_date' must be a string in YYYY-MM-DD format")
        elif not _validate_date_format(start_date):
            errors.append(
                f"'backtest.start_date' must be a valid date in YYYY-MM-DD format. "
                f"Got: '{start_date}'"
            )
        else:
            start_date_valid = True
            parsed_start = _parse_date(start_date)
    
    # Validate end_date if present
    if 'end_date' in backtest:
        end_date = backtest['end_date']
        if not isinstance(end_date, str):
            errors.append("'backtest.end_date' must be a string in YYYY-MM-DD format")
        elif not _validate_date_format(end_date):
            errors.append(
                f"'backtest.end_date' must be a valid date in YYYY-MM-DD format. "
                f"Got: '{end_date}'"
            )
        else:
            end_date_valid = True
            parsed_end = _parse_date(end_date)
    
    # Cross-validate: start_date must be before end_date
    if start_date_valid and end_date_valid and parsed_start and parsed_end:
        if parsed_start >= parsed_end:
            errors.append(
                f"'backtest.start_date' ({backtest['start_date']}) must be before "
                f"'backtest.end_date' ({backtest['end_date']})"
            )
    
    # Validate capital if present
    if 'capital' in backtest:
        capital = backtest['capital']
        if not isinstance(capital, (int, float)):
            errors.append("'backtest.capital' must be a number")
        elif capital <= 0:
            errors.append(f"'backtest.capital' must be positive. Got: {capital}")
    
    # Validate warmup_days if present
    if 'warmup_days' in backtest:
        warmup = backtest['warmup_days']
        if not isinstance(warmup, int):
            errors.append("'backtest.warmup_days' must be an integer")
        elif warmup < 0:
            errors.append(f"'backtest.warmup_days' must be non-negative. Got: {warmup}")
