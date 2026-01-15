"""
Backtest configuration module for The Researcher's Cockpit.

Provides configuration dataclass and validation functions for backtest execution.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

import pandas as pd

from ..config import load_settings, get_default_bundle, get_warmup_days
from ..utils import get_strategy_path


# Module-level logger
logger = logging.getLogger(__name__)


@dataclass
class BacktestConfig:
    """Configuration for backtest execution."""
    strategy_name: str
    start_date: str
    end_date: str
    capital_base: float
    bundle: str
    data_frequency: str
    asset_class: Optional[str] = None


def _prepare_backtest_config(
    strategy_name: str,
    start_date: Optional[str],
    end_date: Optional[str],
    capital_base: Optional[float],
    bundle: Optional[str],
    data_frequency: str,
    asset_class: Optional[str]
) -> BacktestConfig:
    """
    Prepare and validate backtest configuration.
    
    Args:
        strategy_name: Name of strategy
        start_date: Start date or None for default
        end_date: End date or None for today
        capital_base: Starting capital or None for default
        bundle: Bundle name or None for auto-detect
        data_frequency: 'daily' or 'minute'
        asset_class: Optional asset class hint
        
    Returns:
        BacktestConfig: Validated configuration
    """
    settings = load_settings()
    
    # Parse dates
    if start_date is None:
        start_date = settings['dates']['default_start']
    if end_date is None:
        end_date = settings['dates'].get('default_end')
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
    
    # Adjust start_date for CSV minute data to ensure enough buffer for calendar
    if bundle and bundle.startswith('csv_') and data_frequency == 'minute':
        original_start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        adjusted_start_date = original_start_date - timedelta(days=1)
        start_date = adjusted_start_date.strftime('%Y-%m-%d')
        logger.info(f"Adjusted start_date for CSV minute bundle: {original_start_date} -> {start_date}")
    
    # Get capital
    if capital_base is None:
        capital_base = settings['capital']['default_initial']
    
    # Get bundle
    if bundle is None:
        # Try to infer asset class from strategy path
        if asset_class is None:
            try:
                strategy_path = get_strategy_path(strategy_name)
                asset_class = strategy_path.parent.name
                if asset_class not in ['crypto', 'forex', 'equities']:
                    asset_class = 'equities'
            except FileNotFoundError:
                asset_class = 'equities'
        
        bundle = get_default_bundle(asset_class)

    config_return = BacktestConfig(
        strategy_name=strategy_name,
        start_date=start_date,
        end_date=end_date,
        capital_base=capital_base,
        bundle=bundle,
        data_frequency=data_frequency,
        asset_class=asset_class
    )

    return config_return


def _validate_warmup_period(
    start_date: str,
    end_date: str,
    params: Dict[str, Any],
    strategy_name: str
) -> None:
    """
    Pre-flight validation to ensure sufficient data for strategy warmup.

    Validates that the backtest period is longer than the required warmup period.
    This prevents backtests that would silently produce no trades due to
    insufficient data for indicator initialization.

    Args:
        start_date: Start date string (YYYY-MM-DD)
        end_date: End date string (YYYY-MM-DD)
        params: Strategy parameters dictionary
        strategy_name: Name of strategy (for error messages)

    Raises:
        ValueError: If backtest period is shorter than required warmup
    """
    # Check if warmup validation is enabled
    backtest_config = params.get('backtest', {})
    if not backtest_config.get('validate_warmup', True):
        logger.debug(f"Warmup validation disabled for strategy '{strategy_name}'")
        return

    # Get required warmup days
    warmup_days = get_warmup_days(params)

    # Calculate available days
    start_ts = pd.Timestamp(start_date)
    end_ts = pd.Timestamp(end_date)
    available_days = (end_ts - start_ts).days

    if available_days <= warmup_days:
        raise ValueError(
            f"Insufficient data for strategy '{strategy_name}': "
            f"strategy requires {warmup_days} days warmup, but only {available_days} days provided "
            f"({start_date} to {end_date}). "
            f"Either extend the backtest date range or reduce indicator periods in parameters.yaml."
        )

    logger.info(
        f"Warmup validation passed: {available_days} days available, "
        f"{warmup_days} days required for warmup"
    )















