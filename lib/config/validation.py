"""
Strategy parameter validation - Orchestrator.

Provides comprehensive validation for strategy parameters by delegating
to specialized validation modules:
- validation_backtest: Backtest configuration validation
- validation_position_sizing: Position sizing validation
- validation_risk: Risk management validation

For direct access to specific validators, import from:
- lib.config.validation_backtest
- lib.config.validation_position_sizing
- lib.config.validation_risk
"""

from __future__ import annotations

import logging
from typing import Tuple, List, Dict, Any

from .validation_backtest import validate_backtest_section
from .validation_position_sizing import validate_position_sizing_section
from .validation_risk import validate_risk_section

# Configure logging
logger = logging.getLogger(__name__)


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
        validate_backtest_section(params['backtest'], errors)
    
    # Validate position_sizing
    if 'position_sizing' in params:
        validate_position_sizing_section(params['position_sizing'], errors)
    
    # Validate risk management
    if 'risk' in params:
        validate_risk_section(params['risk'], errors)
    
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













