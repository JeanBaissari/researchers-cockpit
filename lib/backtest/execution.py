"""
Backtest execution for The Researcher's Cockpit.

Handles Zipline algorithm setup, performance tracking, and error handling
during backtest execution.
Extracted from runner.py as part of v1.0.11 refactoring.
"""

import logging
import tempfile
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

import pandas as pd
import yaml

from ..utils import get_strategy_path

logger = logging.getLogger(__name__)


def execute_zipline_backtest(
    strategy_module: Any,
    start_ts: pd.Timestamp,
    end_ts: pd.Timestamp,
    capital_base: float,
    bundle: str,
    data_frequency: str,
    trading_calendar: Any,
    strategy_name: str,
    asset_class: Optional[str],
    params: Optional[Dict[str, Any]] = None
) -> Tuple[pd.DataFrame, Any]:
    """
    Execute a Zipline backtest with the given configuration.

    Handles custom parameter injection for optimization by creating a
    temporary parameters file.

    Args:
        strategy_module: Loaded strategy module
        start_ts: Start timestamp (timezone-naive UTC)
        end_ts: End timestamp (timezone-naive UTC)
        capital_base: Starting capital
        bundle: Bundle name
        data_frequency: 'daily' or 'minute'
        trading_calendar: Trading calendar object
        strategy_name: Strategy name
        asset_class: Asset class
        params: Optional parameter overrides (for optimization)

    Returns:
        Tuple of (performance DataFrame, trading calendar)

    Raises:
        RuntimeError: If backtest execution fails
    """
    try:
        from zipline import run_algorithm
    except ImportError:
        raise ImportError(
            "zipline-reloaded not installed. "
            "Install with: pip install zipline-reloaded"
        )

    # Ensure dates are properly normalized (timezone-naive UTC)
    assert start_ts.tz is None, "Start date must be timezone-naive"
    assert end_ts.tz is None, "End date must be timezone-naive"

    # Create empty benchmark returns
    benchmark_freq = 'min' if data_frequency == 'minute' else 'D'
    empty_benchmark = pd.Series(dtype=float, index=pd.DatetimeIndex([], freq=benchmark_freq))

    # Handle custom parameter injection for optimization
    temp_params_file = None
    backup_params = None

    if params:
        # Create temporary parameters file
        strategy_path = get_strategy_path(strategy_name, asset_class)
        original_params_file = strategy_path / 'parameters.yaml'

        # Create temp file
        fd, temp_params_file = tempfile.mkstemp(suffix='.yaml', prefix='params_')
        with open(temp_params_file, 'w') as f:
            yaml.dump(params, f, default_flow_style=False)

        # Backup original parameters
        backup_params = strategy_path / 'parameters.yaml.backup'
        if original_params_file.exists():
            shutil.copy2(original_params_file, backup_params)
        shutil.copy2(temp_params_file, original_params_file)

    try:
        # Execute backtest
        perf = run_algorithm(
            start=start_ts,
            end=end_ts,
            initialize=strategy_module.initialize,
            handle_data=strategy_module.handle_data,
            analyze=strategy_module.analyze,
            before_trading_start=strategy_module.before_trading_start,
            capital_base=capital_base,
            bundle=bundle,
            data_frequency=data_frequency,
            trading_calendar=trading_calendar,
            benchmark_returns=empty_benchmark,
        )

        return perf, trading_calendar

    except Exception as e:
        raise RuntimeError(f"Backtest execution failed: {e}") from e

    finally:
        # Restore original parameters file
        if temp_params_file:
            import os
            strategy_path = get_strategy_path(strategy_name, asset_class)
            original_params_file = strategy_path / 'parameters.yaml'

            if backup_params and backup_params.exists():
                shutil.copy2(backup_params, original_params_file)
                backup_params.unlink()

            # Clean up temp file
            if os.path.exists(temp_params_file):
                os.unlink(temp_params_file)


def get_trading_calendar(bundle: str, asset_class: Optional[str] = None):
    """
    Extract trading calendar from bundle.

    Args:
        bundle: Bundle name
        asset_class: Optional asset class hint

    Returns:
        Trading calendar object

    Raises:
        ValueError: If calendar can't be extracted
    """
    from ..bundles import load_bundle
    from ..calendars import get_calendar_for_asset_class

    bundle_data = load_bundle(bundle)

    # Attempt to get custom calendar based on asset class
    if asset_class:
        custom_calendar_name = get_calendar_for_asset_class(asset_class)
        if custom_calendar_name:
            try:
                from zipline.utils.calendar_utils import get_calendar
                calendar = get_calendar(custom_calendar_name)
                logger.info(f"Using custom trading calendar '{custom_calendar_name}' for asset class '{asset_class}'.")
                return calendar
            except Exception as e:
                logger.warning(f"Failed to retrieve custom calendar '{custom_calendar_name}': {e}. Falling back to bundle calendar.")

    # Fallback: Extract calendar from bundle
    try:
        if hasattr(bundle_data, 'equity_daily_bar_reader') and bundle_data.equity_daily_bar_reader is not None:
            calendar = bundle_data.equity_daily_bar_reader.trading_calendar
            return calendar
        elif hasattr(bundle_data, 'trading_calendar') and bundle_data.trading_calendar is not None:
            calendar = bundle_data.trading_calendar
            return calendar
        else:
            raise ValueError(f"Could not extract trading calendar from bundle '{bundle}'. "
                             f"Bundle structure: {type(bundle_data)}. "
                             f"Available attributes: {dir(bundle_data)}")
    except AttributeError:
        raise ValueError(f"Could not extract trading calendar from bundle '{bundle}'. "
                         f"Bundle structure: {type(bundle_data)}. "
                         f"Available attributes: {dir(bundle_data)}")
