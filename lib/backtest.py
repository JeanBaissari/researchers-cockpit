"""
Backtest execution module for The Researcher's Cockpit.

Provides functions to run Zipline backtests and save results in standardized format.
"""

# Standard library imports
import sys
import json
import importlib.util
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Callable, Tuple
from dataclasses import dataclass

# Third-party imports
import numpy as np
import pandas as pd

# Local imports
from .config import load_settings, load_strategy_params, get_default_bundle, validate_strategy_params, get_warmup_days
from .utils import (
    get_project_root,
    get_strategy_path,
    timestamp_dir,
    update_symlink,
    save_yaml,
    ensure_dir,
    check_and_fix_symlinks,
    normalize_to_utc,
)
from .extension import (
    register_custom_calendars,
    get_calendar_for_asset_class,
)

# Module-level logger
logger = logging.getLogger(__name__)


@dataclass
class StrategyModule:
    """Container for strategy functions."""
    initialize: Callable
    handle_data: Optional[Callable] = None
    analyze: Optional[Callable] = None
    before_trading_start: Optional[Callable] = None


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


def _load_strategy_module(strategy_name: str, asset_class: Optional[str] = None) -> StrategyModule:
    """
    Load strategy module and extract required functions.
    
    Args:
        strategy_name: Name of strategy
        asset_class: Optional asset class hint
        
    Returns:
        StrategyModule: Container with strategy functions
        
    Raises:
        FileNotFoundError: If strategy file not found
        ImportError: If module can't be loaded
        ValueError: If required functions missing
    """
    strategy_path = get_strategy_path(strategy_name, asset_class)
    strategy_file = strategy_path / 'strategy.py'
    
    if not strategy_file.exists():
        raise FileNotFoundError(
            f"Strategy file not found: {strategy_file}. "
            f"Expected: strategies/{asset_class}/{strategy_name}/strategy.py"
        )
    
    # Load strategy module
    spec = importlib.util.spec_from_file_location(
        f"strategy_{strategy_name}",
        strategy_file
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Failed to create module spec for {strategy_file}")
    
    # Add project root to path for lib imports
    project_root = get_project_root()
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    strategy_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(strategy_module)
    
    # Extract strategy functions
    initialize_func = getattr(strategy_module, 'initialize', None)
    if initialize_func is None:
        raise ValueError(
            f"Strategy {strategy_name} must have an 'initialize' function"
        )
    
    return StrategyModule(
        initialize=initialize_func,
        handle_data=getattr(strategy_module, 'handle_data', None),
        analyze=getattr(strategy_module, 'analyze', None),
        before_trading_start=getattr(strategy_module, 'before_trading_start', None)
    )


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

    from .data_loader import load_bundle

    # Parse dates - Zipline expects timezone-naive UTC timestamps
    start_ts = normalize_to_utc(start_date)
    end_ts = normalize_to_utc(end_date)

    
    # If using yahoo bundle, ensure it's registered
    if bundle.startswith('yahoo_'):
        from .data_loader import _register_yahoo_bundle
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
        
    Returns:
        Trading calendar object
        
    Raises:
        ValueError: If calendar can't be extracted
    """
    from .data_loader import load_bundle
    
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
    asset_class: Optional[str] = None
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

    # Register custom calendars before getting trading calendar
    if config.asset_class:
        calendar_name = get_calendar_for_asset_class(config.asset_class)
        if calendar_name:
            register_custom_calendars(calendars=[calendar_name])
    
    # Get trading calendar
    trading_calendar = _get_trading_calendar(config.bundle, config.asset_class)

    # Validate bundle and get timestamps
    start_ts, end_ts = _validate_bundle_date_range(
        config.bundle, config.start_date, config.end_date, config.data_frequency, trading_calendar
    )
    
    # Ensure dates are properly normalized (timezone-naive UTC)
    assert start_ts.tz is None, "Start date must be timezone-naive"
    assert end_ts.tz is None, "End date must be timezone-naive"
    
    # Run backtest with bundle's calendar
    # Create empty benchmark returns Series to avoid Zipline trying to fetch benchmark data
    benchmark_freq = 'T' if config.data_frequency == 'minute' else 'D'
    empty_benchmark = pd.Series(dtype=float, index=pd.DatetimeIndex([], freq=benchmark_freq))
    
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


def _normalize_performance_dataframe(perf: pd.DataFrame) -> pd.DataFrame:
    """Normalize performance DataFrame index to timezone-naive UTC."""
    perf_normalized = perf.copy()
    if perf_normalized.index.tz is not None:
        perf_normalized.index = perf_normalized.index.tz_convert('UTC').tz_localize(None)
    return perf_normalized


def _extract_positions_dataframe(perf: pd.DataFrame) -> pd.DataFrame:
    """
    Extract and flatten positions into proper DataFrame.
    
    Args:
        perf: Performance DataFrame
        
    Returns:
        pd.DataFrame: Positions DataFrame
    """
    if 'positions' not in perf.columns:
        return pd.DataFrame(columns=['sid', 'amount', 'cost_basis', 'last_sale_price'])
    
    positions_list = []
    for date, positions in perf['positions'].items():
        if positions and len(positions) > 0:
            for pos in positions:
                # Convert Asset objects to strings for CSV compatibility
                sid_str = str(pos.get('sid', ''))
                positions_list.append({
                    'date': date,
                    'sid': sid_str,
                    'amount': pos.get('amount', 0),
                    'cost_basis': pos.get('cost_basis', 0.0),
                    'last_sale_price': pos.get('last_sale_price', 0.0),
                })
    
    if positions_list:
        positions_df = pd.DataFrame(positions_list)
        positions_df.set_index('date', inplace=True)
        return positions_df
    else:
        return pd.DataFrame(columns=['sid', 'amount', 'cost_basis', 'last_sale_price'])


def _extract_transactions_dataframe(perf: pd.DataFrame) -> pd.DataFrame:
    """
    Extract and flatten transactions into proper DataFrame.
    
    Args:
        perf: Performance DataFrame
        
    Returns:
        pd.DataFrame: Transactions DataFrame
    """
    if 'transactions' not in perf.columns:
        return pd.DataFrame(columns=['sid', 'amount', 'price', 'commission', 'order_id'])
    
    transactions_list = []
    for date, transactions_for_date in perf['transactions'].items():
        if transactions_for_date and len(transactions_for_date) > 0:
            for txn in transactions_for_date:
                # Convert Asset objects to strings for CSV compatibility
                sid_str = str(txn.get('sid', ''))
                transactions_list.append({
                    'date': date,
                    'sid': sid_str,
                    'amount': txn.get('amount', 0),
                    'price': txn.get('price', 0.0),
                    'commission': txn.get('commission', 0.0) if txn.get('commission') is not None else 0.0,
                    'order_id': txn.get('order_id', ''),
                })
    
    if transactions_list:
        transactions_df = pd.DataFrame(transactions_list)
        transactions_df.set_index('date', inplace=True)
        return transactions_df
    else:
        return pd.DataFrame(columns=['sid', 'amount', 'price', 'commission', 'order_id'])


def _calculate_and_save_metrics(
    perf: pd.DataFrame,
    transactions_df: pd.DataFrame,
    result_dir: Path,
    trading_calendar: Any
) -> Dict[str, Any]:
    """
    Calculate enhanced metrics and save to JSON.
    """
    from .metrics import calculate_metrics
    from .config import load_settings
    
    settings = load_settings()
    risk_free_rate = settings.get('metrics', {}).get('risk_free_rate', 0.04)

    # Determine trading_days_per_year dynamically based on the calendar
    if trading_calendar and hasattr(trading_calendar, 'name'):
        calendar_name = trading_calendar.name.upper()
        if 'CRYPTO' in calendar_name:
            # Crypto markets are generally 365 days a year
            trading_days_per_year = 365
        elif 'FOREX' in calendar_name:
            # Forex markets are generally 260 days (5 days/week * 52 weeks)
            trading_days_per_year = 260
        else:
            # Default for equity-like calendars
            trading_days_per_year = settings.get('metrics', {}).get('trading_days_per_year', 252)
    else:
        # Fallback if no calendar or name is available
        trading_days_per_year = settings.get('metrics', {}).get('trading_days_per_year', 252)

    logger.info(f"Using trading_days_per_year: {trading_days_per_year} for metrics calculation.")
    
    metrics = {}
    if 'returns' in perf.columns:
        returns = perf['returns'].dropna()
        
        # Use enhanced metrics calculation
        metrics = calculate_metrics(
            returns,
            transactions=transactions_df if len(transactions_df) > 0 else None,
            risk_free_rate=risk_free_rate,
            trading_days_per_year=trading_days_per_year
        )
    
    # Portfolio value (add to metrics if available)
    if 'portfolio_value' in perf.columns:
        metrics['final_portfolio_value'] = float(perf['portfolio_value'].iloc[-1])
        metrics['initial_portfolio_value'] = float(perf['portfolio_value'].iloc[0])
    
    # Save metrics JSON
    with open(result_dir / 'metrics.json', 'w') as f:
        json.dump(metrics, f, indent=2)
    
    return metrics


def _verify_data_integrity(
    perf: pd.DataFrame,
    transactions_df: pd.DataFrame,
    metrics: Dict[str, Any]
) -> None:
    """
    Run optional data integrity checks.
    
    Args:
        perf: Performance DataFrame
        transactions_df: Transactions DataFrame
        metrics: Calculated metrics
    """
    try:
        from .data_integrity import (
            verify_metrics_calculation,
            verify_returns_calculation,
            verify_positions_match_transactions
        )
        
        # Verify metrics
        if 'returns' in perf.columns:
            returns = perf['returns'].dropna()
            is_valid, discrepancies = verify_metrics_calculation(
                metrics,
                returns,
                transactions_df if len(transactions_df) > 0 else None
            )
            if not is_valid:
                logger.warning(f"Metrics verification found discrepancies: {discrepancies}")
            
            # Verify returns calculation
            if len(transactions_df) > 0:
                is_valid, error = verify_returns_calculation(returns, transactions_df)
                if not is_valid:
                    logger.warning(f"Returns verification failed: {error}")
        
        # Verify positions match transactions
        if 'positions' in perf.columns and len(transactions_df) > 0:
            positions_df = perf[['positions']].copy()
            is_valid, error = verify_positions_match_transactions(positions_df, transactions_df)
            if not is_valid:
                logger.warning(f"Positions verification failed: {error}")
    except ImportError:
        # Data integrity module not available, skip
        pass
    except Exception as e:
        logger.warning(f"Data integrity check failed: {e}")


def _generate_plots(
    perf: pd.DataFrame,
    transactions_df: pd.DataFrame,
    result_dir: Path,
    strategy_name: str,
    trading_calendar: Any
) -> None:
    """
    Generate all plots for backtest results.
    
    Args:
        perf: Performance DataFrame
        transactions_df: Transactions DataFrame
        result_dir: Directory to save plots
        strategy_name: Name of strategy
    """
    try:
        from .plots import plot_all
        
        returns = perf['returns'].dropna() if 'returns' in perf.columns else pd.Series()
        portfolio_value = perf['portfolio_value'] if 'portfolio_value' in perf.columns else None
        
        plot_all(
            returns=returns,
            save_dir=result_dir,
            portfolio_value=portfolio_value,
            transactions=transactions_df if len(transactions_df) > 0 else None,
            strategy_name=strategy_name
        )
    except ImportError:
        # Fallback to basic equity curve if plots module not available
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            
            if 'portfolio_value' in perf.columns:
                plt.figure(figsize=(12, 6))
                plt.plot(perf.index, perf['portfolio_value'])
                plt.title(f'{strategy_name} - Equity Curve')
                plt.xlabel('Date')
                plt.ylabel('Portfolio Value ($)')
                plt.grid(True, alpha=0.3)
                plt.tight_layout()
                plt.savefig(result_dir / 'equity_curve.png', dpi=150)
                plt.close()
        except ImportError:
            # Matplotlib not available, skip plot
            pass


def save_results(
    strategy_name: str,
    perf: pd.DataFrame,
    params: Dict[str, Any],
    trading_calendar: Any,
    result_type: str = 'backtest',
    verify_integrity: bool = False
) -> Path:
    """
    Save backtest results to timestamped directory.
    
    Creates:
    - results/{strategy}/{result_type}_{timestamp}/
      - returns.csv
      - positions.csv
      - transactions.csv
      - metrics.json (basic)
      - parameters_used.yaml
      - equity_curve.png (if matplotlib available)
    
    Updates:
    - results/{strategy}/latest -> new directory
    
    Args:
        strategy_name: Name of strategy
        perf: Performance DataFrame from Zipline
        params: Strategy parameters dictionary
        result_type: Type of result ('backtest', 'optimization', etc.)
        verify_integrity: If True, run data integrity checks (default: False)
        
    Returns:
        Path: Path to created results directory
    """
    root = get_project_root()
    results_base = root / 'results' / strategy_name
    ensure_dir(results_base)
    
    # Create timestamped directory
    result_dir = timestamp_dir(results_base, result_type)
    
    # Normalize DataFrame index to timezone-naive
    perf_normalized = _normalize_performance_dataframe(perf)
    
    # Save returns CSV
    if 'returns' in perf_normalized.columns:
        returns_df = pd.DataFrame({'returns': perf_normalized['returns']})
        returns_df.to_csv(result_dir / 'returns.csv', date_format='%Y-%m-%d')
    
    # Extract and save positions
    positions_df = _extract_positions_dataframe(perf_normalized)
    positions_df.to_csv(result_dir / 'positions.csv', date_format='%Y-%m-%d', index_label='date')
    
    # Extract and save transactions
    transactions_df = _extract_transactions_dataframe(perf_normalized)
    transactions_df.to_csv(result_dir / 'transactions.csv', date_format='%Y-%m-%d', index_label='date')
    
    # Calculate and save metrics
    metrics = _calculate_and_save_metrics(perf_normalized, transactions_df, result_dir, trading_calendar)
    
    # Optional data integrity verification
    if verify_integrity:
        _verify_data_integrity(perf_normalized, transactions_df, metrics)
    
    # Save parameters used
    save_yaml(params, result_dir / 'parameters_used.yaml')
    
    # Generate plots
    _generate_plots(perf_normalized, transactions_df, result_dir, strategy_name, trading_calendar)
    
    # Check and fix any broken symlinks before updating
    try:
        asset_class = None
        try:
            strategy_path = get_strategy_path(strategy_name)
            asset_class = strategy_path.parent.name
            if asset_class not in ['crypto', 'forex', 'equities']:
                asset_class = None
        except FileNotFoundError:
            pass
        
        fixed_links = check_and_fix_symlinks(strategy_name, asset_class)
        if fixed_links:
            logger.info(f"Fixed {len(fixed_links)} broken symlink(s): {fixed_links}")
    except Exception as e:
        logger.warning(f"Symlink check failed: {e}")
    
    # Update latest symlink
    latest_link = results_base / 'latest'
    update_symlink(result_dir, latest_link)
    
    return result_dir
