"""
Position sizing configuration validation.

Provides validation functions for the position_sizing section of strategy parameters.
"""

from typing import List, Any


def validate_position_sizing_section(ps: Any, errors: List[str]) -> None:
    """
    Validate the position_sizing section of strategy parameters.
    
    Args:
        ps: Position sizing configuration dictionary
        errors: List to append validation errors to
    """
    # Guard against position_sizing being None
    if ps is None:
        errors.append("'position_sizing' section is null/None")
        return
    
    if not isinstance(ps, dict):
        errors.append(f"'position_sizing' section must be a dictionary, got {type(ps).__name__}")
        return
    
    if 'max_position_pct' in ps:
        max_pos = ps['max_position_pct']
        if not isinstance(max_pos, (int, float)):
            errors.append("'position_sizing.max_position_pct' must be a number")
        elif not (0.0 <= max_pos <= 1.0):
            errors.append(
                f"'position_sizing.max_position_pct' must be between 0.0 and 1.0. "
                f"Got: {max_pos}"
            )
    
    if 'method' in ps:
        valid_methods = ['fixed', 'volatility_scaled', 'kelly']
        if ps['method'] not in valid_methods:
            errors.append(
                f"'position_sizing.method' must be one of: {valid_methods}. "
                f"Got: {ps['method']}"
            )
