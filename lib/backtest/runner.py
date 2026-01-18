"""
Backtest runner module for The Researcher's Cockpit.

Orchestrates backtest execution by coordinating preprocessing, execution, and results.
Refactored in v1.0.11 to split into preprocessing, execution, and orchestration modules.
"""

import logging
from typing import Optional, Tuple, Any, Dict

import pandas as pd

from ..config import load_strategy_params, validate_strategy_params
from ..calendars import register_custom_calendars, get_calendar_for_asset_class

from .strategy import _load_strategy_module
from .config import BacktestConfig, _prepare_backtest_config, _validate_warmup_period
from .preprocessing import (
    validate_calendar_consistency,
    validate_session_alignment,
    validate_strategy_symbols,
    validate_bundle_date_range,
)
from .execution import execute_zipline_backtest, get_trading_calendar

logger = logging.getLogger(__name__)


def _deep_merge_params(base: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two parameter dictionaries.

    Args:
        base: Base parameters dictionary (from parameters.yaml)
        overrides: Override parameters (from optimization)

    Returns:
        Merged dictionary with overrides applied
    """
    import copy
    result = copy.deepcopy(base)

    for key, value in overrides.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge_params(result[key], value)
        else:
            result[key] = value

    return result


def run_backtest(
    strategy_name: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    capital_base: Optional[float] = None,
    bundle: Optional[str] = None,
    data_frequency: str = 'daily',
    asset_class: Optional[str] = None,
    custom_params: Optional[Dict[str, Any]] = None,
    validate_calendar: bool = False
) -> Tuple[pd.DataFrame, Any]:
    """
    Run a backtest for a strategy.

    This is the main entry point for backtest execution. It orchestrates:
    1. Strategy loading and parameter validation
    2. Pre-flight checks (calendar alignment, symbol validation, date ranges)
    3. Backtest execution via Zipline
    4. Results return

    Args:
        strategy_name: Name of strategy (e.g., 'spy_sma_cross')
        start_date: Start date string (YYYY-MM-DD) or None for default
        end_date: End date string or None for today
        capital_base: Starting capital or None for default
        bundle: Bundle name or None for auto-detect
        data_frequency: 'daily' or 'minute'
        asset_class: Optional asset class hint for strategy location
        custom_params: Optional parameter overrides for optimization (merged with parameters.yaml)
        validate_calendar: If True, raise error on calendar mismatch (v1.1.0 feature)

    Returns:
        Tuple[pd.DataFrame, Any]: Performance DataFrame and trading calendar

    Raises:
        FileNotFoundError: If strategy not found
        ImportError: If strategy module can't be loaded
        ValueError: If dates, bundle, or calendar alignment invalid
    """
    try:
        from zipline import run_algorithm
    except ImportError:
        raise ImportError(
            "zipline-reloaded not installed. "
            "Install with: pip install zipline-reloaded"
        )

    # === STEP 1: LOAD STRATEGY AND PARAMETERS ===
    strategy_module = _load_strategy_module(strategy_name, asset_class)

    # Load and validate strategy parameters
    try:
        params = load_strategy_params(strategy_name, asset_class)

        # Apply custom parameter overrides if provided (for optimization)
        if custom_params:
            params = _deep_merge_params(params, custom_params)

        is_valid, errors = validate_strategy_params(params, strategy_name)
        if not is_valid:
            error_msg = f"Invalid parameters for strategy '{strategy_name}':\n" + "\n".join(f"  - {e}" for e in errors)
            raise ValueError(error_msg)
    except FileNotFoundError:
        # Parameters file doesn't exist - strategy might load params differently
        params = {}

    # === STEP 2: PREPARE CONFIGURATION ===
    config = _prepare_backtest_config(
        strategy_name, start_date, end_date, capital_base, bundle, data_frequency, asset_class
    )

    # === STEP 3: PRE-FLIGHT VALIDATIONS ===
    # Warmup validation
    if params:
        _validate_warmup_period(
            config.start_date,
            config.end_date,
            params,
            strategy_name
        )

    # Symbol validation (ensures strategy symbols exist in bundle)
    validate_strategy_symbols(strategy_name, config.bundle, config.asset_class)

    # Register custom calendars before getting trading calendar
    if config.asset_class:
        calendar_name = get_calendar_for_asset_class(config.asset_class)
        if calendar_name:
            register_custom_calendars(calendars=[calendar_name])

    # Get trading calendar
    trading_calendar = get_trading_calendar(config.bundle, config.asset_class)

    # Validate calendar consistency
    validate_calendar_consistency(config.bundle, trading_calendar)

    # Validate bundle and get timestamps
    start_ts, end_ts = validate_bundle_date_range(
        config.bundle, config.start_date, config.end_date, config.data_frequency, trading_calendar
    )

    # Ensure dates are properly normalized (timezone-naive UTC)
    assert start_ts.tz is None, "Start date must be timezone-naive"
    assert end_ts.tz is None, "End date must be timezone-naive"

    # v1.1.0: Validate session alignment using SessionManager
    validate_session_alignment(config.bundle, start_ts, end_ts, validate_calendar)

    # === STEP 4: EXECUTE BACKTEST ===
    perf, trading_calendar = execute_zipline_backtest(
        strategy_module=strategy_module,
        start_ts=start_ts,
        end_ts=end_ts,
        capital_base=config.capital_base,
        bundle=config.bundle,
        data_frequency=config.data_frequency,
        trading_calendar=trading_calendar,
        strategy_name=strategy_name,
        asset_class=config.asset_class,
        params=params if params else None
    )

    return perf, trading_calendar
