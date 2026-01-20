"""
Strategy parameter loading.

Provides functions to load and parse strategy parameters.
"""

from __future__ import annotations

import logging
from typing import Optional, Dict, Any

from ..utils import load_yaml
from ..strategies import get_strategy_path


# Configure logging
logger = logging.getLogger(__name__)


def load_strategy_params(strategy_name: str, asset_class: Optional[str] = None) -> Dict[str, Any]:
    """
    Load parameters from a strategy's parameters.yaml file.
    
    Args:
        strategy_name: Name of strategy (e.g., 'spy_sma_cross')
        asset_class: Optional asset class. If None, searches all asset classes
        
    Returns:
        dict: Strategy parameters dictionary
        
    Raises:
        FileNotFoundError: If strategy or parameters.yaml not found
    """
    strategy_path = get_strategy_path(strategy_name, asset_class)
    params_path = strategy_path / 'parameters.yaml'
    
    if not params_path.exists():
        raise FileNotFoundError(
            f"parameters.yaml not found for strategy '{strategy_name}'. "
            f"Expected at: {params_path}"
        )
    
    logger.debug(f"Loading strategy params from {params_path}")
    return load_yaml(params_path)


def get_warmup_days(params: Dict[str, Any]) -> int:
    """
    Get required warmup days for a strategy.

    The warmup period is the number of trading days required before the strategy
    can generate valid signals. This is typically determined by the longest
    indicator period used in the strategy.

    Resolution order:
    1. Explicit 'warmup_days' in backtest section
    2. Dynamic calculation from strategy parameters (max of all *_period params)
    3. Default fallback of 30 days

    Args:
        params: Strategy parameters dictionary

    Returns:
        int: Required warmup days
    """
    # Check for explicit warmup_days in backtest section
    backtest_config = params.get('backtest', {}) or {}
    explicit_warmup = backtest_config.get('warmup_days')

    if explicit_warmup is not None:
        logger.debug(f"Using explicit warmup_days: {explicit_warmup}")
        return int(explicit_warmup)

    # Dynamic calculation: find max of all *_period parameters
    strategy_config = params.get('strategy', {}) or {}
    period_values: set[int] = set()

    # Collect all keys ending with '_period' (covers all common patterns)
    for key, value in strategy_config.items():
        if key.endswith('_period') and isinstance(value, (int, float)) and value > 0:
            period_values.add(int(value))

    if period_values:
        max_period = max(period_values)
        logger.debug(f"Calculated warmup_days from periods: {max_period} (from {len(period_values)} period params)")
        return max_period

    # Default fallback
    logger.debug("Using default warmup_days: 30")
    return 30



