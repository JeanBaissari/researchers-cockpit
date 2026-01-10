"""
Strategy parameter validation.

Provides comprehensive validation for strategy parameters.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Optional, Tuple, List, Dict, Any


# Configure logging
logger = logging.getLogger(__name__)

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


def validate_strategy_params(params: Dict[str, Any], strategy_name: str) -> Tuple[bool, List[str]]:
    """
    Validate strategy parameters.
    
    Checks:
    - Required fields exist
    - Type correctness
    - Range validity
    - Enum values
    - Backtest section validity (dates, capital, warmup)
    - Date order validation (start_date < end_date)
    
    Args:
        params: Strategy parameters dictionary
        strategy_name: Name of strategy (for error messages)
        
    Returns:
        Tuple of (is_valid, list_of_errors)
        - is_valid: True if all validations pass
        - list_of_errors: List of error messages (empty if valid)
    """
    errors: List[str] = []
    
    # Check required fields
    if 'strategy' not in params:
        errors.append("Missing required section: 'strategy'")
        logger.warning(f"Validation failed for '{strategy_name}': missing 'strategy' section")
        return False, errors
    
    strategy = params['strategy']
    
    # Guard against strategy being None
    if strategy is None:
        errors.append("'strategy' section is null/None")
        logger.warning(f"Validation failed for '{strategy_name}': 'strategy' section is None")
        return False, errors
    
    # Ensure strategy is a dict
    if not isinstance(strategy, dict):
        errors.append(f"'strategy' section must be a dictionary, got {type(strategy).__name__}")
        logger.warning(f"Validation failed for '{strategy_name}': 'strategy' is not a dict")
        return False, errors
    
    # Required: asset_symbol
    if 'asset_symbol' not in strategy or not strategy['asset_symbol']:
        errors.append("Missing required parameter: 'strategy.asset_symbol'")
    elif not isinstance(strategy['asset_symbol'], str):
        errors.append("'strategy.asset_symbol' must be a string")
    
    # Required: rebalance_frequency
    valid_frequencies = ['daily', 'weekly', 'monthly']
    if 'rebalance_frequency' not in strategy:
        errors.append("Missing required parameter: 'strategy.rebalance_frequency'")
    elif strategy['rebalance_frequency'] not in valid_frequencies:
        errors.append(
            f"'strategy.rebalance_frequency' must be one of: {valid_frequencies}. "
            f"Got: {strategy['rebalance_frequency']}"
        )
    
    # Validate backtest section
    if 'backtest' in params:
        _validate_backtest_section(params['backtest'], errors)
    
    # Validate position_sizing
    if 'position_sizing' in params:
        _validate_position_sizing_section(params['position_sizing'], errors)
    
    # Validate risk management
    if 'risk' in params:
        _validate_risk_section(params['risk'], errors)
    
    # Validate minutes_after_open
    if 'minutes_after_open' in strategy:
        minutes = strategy['minutes_after_open']
        if not isinstance(minutes, int):
            errors.append("'strategy.minutes_after_open' must be an integer")
        elif not (0 <= minutes <= 60):
            errors.append(
                f"'strategy.minutes_after_open' must be between 0 and 60. Got: {minutes}"
            )
    
    # Log validation result
    if errors:
        logger.warning(f"Validation failed for '{strategy_name}': {len(errors)} error(s)")
        for error in errors:
            logger.debug(f"  - {error}")
    else:
        logger.debug(f"Validation passed for '{strategy_name}'")
    
    return len(errors) == 0, errors


def _validate_backtest_section(backtest: Any, errors: List[str]) -> None:
    """Validate the backtest section of strategy parameters."""
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


def _validate_position_sizing_section(ps: Any, errors: List[str]) -> None:
    """Validate the position_sizing section of strategy parameters."""
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


def _validate_risk_section(risk: Any, errors: List[str]) -> None:
    """Validate the risk section of strategy parameters."""
    # Guard against risk being None
    if risk is None:
        errors.append("'risk' section is null/None")
        return
    
    if not isinstance(risk, dict):
        errors.append(f"'risk' section must be a dictionary, got {type(risk).__name__}")
        return
    
    if 'stop_loss_pct' in risk:
        stop_loss = risk['stop_loss_pct']
        if not isinstance(stop_loss, (int, float)):
            errors.append("'risk.stop_loss_pct' must be a number")
        elif stop_loss <= 0:
            errors.append(
                f"'risk.stop_loss_pct' must be positive. Got: {stop_loss}"
            )
        elif stop_loss > 1.0:
            errors.append(
                f"'risk.stop_loss_pct' should typically be <= 1.0 (100%). Got: {stop_loss}"
            )
    
    if 'take_profit_pct' in risk and 'stop_loss_pct' in risk:
        take_profit = risk['take_profit_pct']
        stop_loss = risk['stop_loss_pct']
        if isinstance(take_profit, (int, float)) and isinstance(stop_loss, (int, float)):
            if take_profit <= stop_loss:
                errors.append(
                    f"'risk.take_profit_pct' ({take_profit}) should be greater than "
                    f"'risk.stop_loss_pct' ({stop_loss})"
                )
    
    if 'use_stop_loss' in risk:
        if not isinstance(risk['use_stop_loss'], bool):
            errors.append("'risk.use_stop_loss' must be a boolean")
    
    if 'use_trailing_stop' in risk:
        if not isinstance(risk['use_trailing_stop'], bool):
            errors.append("'risk.use_trailing_stop' must be a boolean")
    
    if 'use_take_profit' in risk:
        if not isinstance(risk['use_take_profit'], bool):
            errors.append("'risk.use_take_profit' must be a boolean")





