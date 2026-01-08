"""
Backtest runner module for The Researcher's Cockpit.

Provides the main run_backtest function and related validation utilities.
"""

import logging
from typing import Optional, Tuple, Any, Dict

import pandas as pd

from ..config import load_strategy_params, validate_strategy_params
from ..utils import normalize_to_utc
from ..extension import register_custom_calendars, get_calendar_for_asset_class

from .strategy import _load_strategy_module
from .config import BacktestConfig, _prepare_backtest_config, _validate_warmup_period


# Module-level logger
logger = logging.getLogger(__name__)


def _deep_merge_params(base: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two parameter dictionaries.
    
    Args:
        base: Base parameters dictionary (from parameters.yaml)
        overrides: Override parameters (from optimization)
        
    Returns:
        Merged dictionary with overrides applied
        
    Example:
        base = {'strategy': {'fast_period': 10, 'slow_period': 30}}
        overrides = {'strategy': {'fast_period': 15}}
        result = {'strategy': {'fast_period': 15, 'slow_period': 30}}
    """
    import copy
    result = copy.deepcopy(base)
    
    for key, value in overrides.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge_params(result[key], value)
        else:
            result[key] = value
    
    return result


def _validate_calendar_consistency(bundle: str, trading_calendar: Any) -> None:
    """
    Validate that the trading calendar used for backtest matches the calendar
    the bundle was ingested with.

    Args:
        bundle: Bundle name
        trading_calendar: Trading calendar object for backtest

    Logs:
        Warning if calendars don't match
    """
    from ..data_loader import _load_bundle_registry

    registry = _load_bundle_registry()
    if bundle not in registry:
        # Bundle not in our registry - might be a built-in bundle
        return

    bundle_calendar_name = registry[bundle].get('calendar_name')
    if not bundle_calendar_name:
        return

    # Get backtest calendar name
    backtest_calendar_name = getattr(trading_calendar, 'name', None)
    if not backtest_calendar_name:
        return

    # Compare calendars (case-insensitive)
    if bundle_calendar_name.upper() != backtest_calendar_name.upper():
        logger.warning(
            f"Calendar mismatch: Bundle '{bundle}' was ingested with calendar "
            f"'{bundle_calendar_name}' but backtest is using '{backtest_calendar_name}'. "
            f"This may cause session misalignment errors."
        )


def validate_strategy_symbols(
    strategy_name: str,
    bundle_name: str,
    asset_class: Optional[str] = None
) -> None:
    """
    Validate that strategy's required symbols exist in the bundle.

    This pre-flight check provides a clear error message instead of cryptic
    Zipline errors when a strategy references symbols not present in the bundle.

    Args:
        strategy_name: Name of the strategy
        bundle_name: Name of the bundle to check against
        asset_class: Optional asset class for strategy lookup

    Raises:
        ValueError: If required symbol is not in the bundle
        FileNotFoundError: If strategy parameters or bundle not found

    Example:
        >>> validate_strategy_symbols('spy_sma_cross', 'yahoo_equities_daily')
        # Raises ValueError if SPY not in bundle
    """
    from ..data_loader import get_bundle_symbols

    # Load strategy parameters
    try:
        params = load_strategy_params(strategy_name, asset_class)
    except FileNotFoundError:
        # Strategy has no parameters.yaml - skip symbol validation
        logger.debug(f"No parameters.yaml for strategy '{strategy_name}', skipping symbol validation")
        return

    # Get required symbol from strategy config
    strategy_config = params.get('strategy', {})
    required_symbol = strategy_config.get('asset_symbol')

    if not required_symbol:
        # No asset_symbol defined - strategy may use multiple symbols or none
        logger.debug(f"No asset_symbol in strategy '{strategy_name}', skipping symbol validation")
        return

    # Get available symbols in bundle
    try:
        available_symbols = get_bundle_symbols(bundle_name)
    except FileNotFoundError as e:
        raise FileNotFoundError(
            f"Bundle '{bundle_name}' not found. {e}"
        ) from e

    # Check if required symbol is available
    if required_symbol not in available_symbols:
        available_str = ', '.join(sorted(available_symbols)) if available_symbols else '(none)'
        raise ValueError(
            f"Strategy '{strategy_name}' requires symbol '{required_symbol}' "
            f"but bundle '{bundle_name}' contains: [{available_str}]. "
            f"Either re-ingest the bundle with the correct symbol:\n"
            f"  python scripts/ingest_data.py --source yahoo --symbols {required_symbol} --bundle-name {bundle_name}\n"
            f"Or update the strategy's parameters.yaml to use an available symbol."
        )

    logger.info(f"Symbol validation passed: '{required_symbol}' found in bundle '{bundle_name}'")


def _validate_bundle_date_range(
    bundle: str,
    start_date: str,
    end_date: str,
    data_frequency: str,
    trading_calendar: Any
) -> Tuple[pd.Timestamp, pd.Timestamp]:
    """
    Validate bundle exists and covers requested date range.
    """
    from ..data_loader import load_bundle

    # Parse dates - Zipline expects timezone-naive UTC timestamps
    start_ts = normalize_to_utc(start_date)
    end_ts = normalize_to_utc(end_date)

    # If using yahoo bundle, ensure it's registered
    if bundle.startswith('yahoo_'):
        from ..data_loader import _register_yahoo_bundle
        if bundle == 'yahoo_equities_daily':
            _register_yahoo_bundle(bundle, ['SPY'], 'XNYS')
    
    # Verify bundle exists and check date range
    try:
        bundle_data = load_bundle(bundle)
        
        # Check if bundle covers requested date range
        try:
            sessions = bundle_data.equity_daily_bar_reader.sessions
            if len(sessions) > 0:
                bundle_start = pd.Timestamp(sessions[0]).normalize()
                bundle_end = pd.Timestamp(sessions[-1]).normalize()

                if start_ts < bundle_start:
                    raise ValueError(
                        f"Requested start date {start_date} is before bundle start date {bundle_start.strftime('%Y-%m-%d')}. "
                        f"Bundle '{bundle}' covers: {bundle_start.strftime('%Y-%m-%d')} to {bundle_end.strftime('%Y-%m-%d')}. "
                        f"Re-ingest data with extended date range: "
                        f"python scripts/ingest_data.py --source yahoo --symbols <SYMBOLS> --start-date {start_date}"
                    )
                
                if end_ts > bundle_end:
                    raise ValueError(
                        f"Requested end date {end_date} is after bundle end date {bundle_end.strftime('%Y-%m-%d')}. "
                        f"Bundle '{bundle}' covers: {bundle_start.strftime('%Y-%m-%d')} to {bundle_end.strftime('%Y-%m-%d')}. "
                        f"Re-ingest data with extended date range: "
                        f"python scripts/ingest_data.py --source yahoo --symbols <SYMBOLS> --end-date {end_date}"
                    )
        except AttributeError:
            # Bundle structure might be different, skip date range check
            pass
            
    except FileNotFoundError as e:
        raise FileNotFoundError(
            f"Bundle '{bundle}' not found. {e}. "
            f"Run: python scripts/ingest_data.py --source yahoo --symbols <SYMBOLS>"
        )
    
    return start_ts, end_ts


def _get_trading_calendar(bundle: str, asset_class: Optional[str] = None):
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
    from ..data_loader import load_bundle
    
    bundle_data = load_bundle(bundle)
    
    # Attempt to get custom calendar based on asset class
    if asset_class:
        custom_calendar_name = get_calendar_for_asset_class(asset_class)
        if custom_calendar_name:
            # Need to re-import Zipline's get_calendar to fetch the registered custom calendar
            # This is a bit indirect, but avoids circular imports with extension.py
            try:
                from zipline.utils.calendar_utils import get_calendar
                calendar = get_calendar(custom_calendar_name)
                logger.info(f"Using custom trading calendar '{custom_calendar_name}' for asset class '{asset_class}'.")
                return calendar
            except Exception as e:
                logger.warning(f"Failed to retrieve custom calendar '{custom_calendar_name}': {e}. Falling back to bundle calendar.")

    # Fallback: Extract calendar from bundle - handle different bundle structures
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


def run_backtest(
    strategy_name: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    capital_base: Optional[float] = None,
    bundle: Optional[str] = None,
    data_frequency: str = 'daily',
    asset_class: Optional[str] = None,
    custom_params: Optional[Dict[str, Any]] = None
) -> Tuple[pd.DataFrame, Any]:
    """
    Run a backtest for a strategy.

    Args:
        strategy_name: Name of strategy (e.g., 'spy_sma_cross')
        start_date: Start date string (YYYY-MM-DD) or None for default
        end_date: End date string or None for today
        capital_base: Starting capital or None for default
        bundle: Bundle name or None for auto-detect
        data_frequency: 'daily' or 'minute'
        asset_class: Optional asset class hint for strategy location
        custom_params: Optional parameter overrides for optimization (merged with parameters.yaml)

    Returns:
        Tuple[pd.DataFrame, Any]: Performance DataFrame and trading calendar

    Raises:
        FileNotFoundError: If strategy not found
        ImportError: If strategy module can't be loaded
        ValueError: If dates or bundle invalid
    """
    try:
        from zipline import run_algorithm
    except ImportError:
        raise ImportError(
            "zipline-reloaded not installed. "
            "Install with: pip install zipline-reloaded"
        )
    
    # Load strategy module
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
        # Parameters file doesn't exist - this is OK, strategy might load params differently
        params = {}

    # Prepare configuration first to resolve default dates
    config = _prepare_backtest_config(
        strategy_name, start_date, end_date, capital_base, bundle, data_frequency, asset_class
    )

    # Pre-flight warmup validation (after config to get resolved dates)
    if params:
        _validate_warmup_period(
            config.start_date,
            config.end_date,
            params,
            strategy_name
        )

    # Pre-flight symbol validation (ensures strategy symbols exist in bundle)
    validate_strategy_symbols(strategy_name, config.bundle, config.asset_class)

    # Register custom calendars before getting trading calendar
    if config.asset_class:
        calendar_name = get_calendar_for_asset_class(config.asset_class)
        if calendar_name:
            register_custom_calendars(calendars=[calendar_name])
    
    # Get trading calendar
    trading_calendar = _get_trading_calendar(config.bundle, config.asset_class)

    # Validate calendar consistency between bundle and backtest
    _validate_calendar_consistency(config.bundle, trading_calendar)

    # Validate bundle and get timestamps
    start_ts, end_ts = _validate_bundle_date_range(
        config.bundle, config.start_date, config.end_date, config.data_frequency, trading_calendar
    )
    
    # Ensure dates are properly normalized (timezone-naive UTC)
    assert start_ts.tz is None, "Start date must be timezone-naive"
    assert end_ts.tz is None, "End date must be timezone-naive"
    
    # Run backtest with bundle's calendar
    # Create empty benchmark returns Series to avoid Zipline trying to fetch benchmark data
    # Note: 'T' is deprecated in pandas 2.x, use 'min' for minute frequency
    benchmark_freq = 'min' if config.data_frequency == 'minute' else 'D'
    empty_benchmark = pd.Series(dtype=float, index=pd.DatetimeIndex([], freq=benchmark_freq))
    
    # Handle custom parameter injection for optimization
    temp_params_file = None
    if params:
        import tempfile
        import yaml
        from ..utils import get_strategy_path
        
        # Create a temporary parameters file with custom params
        # This is the most reliable way to override parameters since the strategy
        # module may cache its parameters at import time
        strategy_path = get_strategy_path(strategy_name, asset_class)
        original_params_file = strategy_path / 'parameters.yaml'
        
        # Create temp file
        fd, temp_params_file = tempfile.mkstemp(suffix='.yaml', prefix='params_')
        with open(temp_params_file, 'w') as f:
            yaml.dump(params, f, default_flow_style=False)
        
        # Temporarily replace the parameters file
        import shutil
        backup_params = strategy_path / 'parameters.yaml.backup'
        if original_params_file.exists():
            shutil.copy2(original_params_file, backup_params)
        shutil.copy2(temp_params_file, original_params_file)
    
    try:
        perf = run_algorithm(
            start=start_ts,
            end=end_ts,
            initialize=strategy_module.initialize,
            handle_data=strategy_module.handle_data,
            analyze=strategy_module.analyze,
            before_trading_start=strategy_module.before_trading_start,
            capital_base=config.capital_base,
            bundle=config.bundle,
            data_frequency=config.data_frequency,
            trading_calendar=trading_calendar,
            benchmark_returns=empty_benchmark,
        )

        return perf, trading_calendar

    except Exception as e:
        raise RuntimeError(f"Backtest execution failed: {e}") from e
    
    finally:
        # Restore original parameters file if we modified it
        if temp_params_file:
            import os
            from ..utils import get_strategy_path
            strategy_path = get_strategy_path(strategy_name, asset_class)
            original_params_file = strategy_path / 'parameters.yaml'
            backup_params = strategy_path / 'parameters.yaml.backup'
            
            if backup_params.exists():
                shutil.copy2(backup_params, original_params_file)
                backup_params.unlink()
            
            # Clean up temp file
            if os.path.exists(temp_params_file):
                os.unlink(temp_params_file)

