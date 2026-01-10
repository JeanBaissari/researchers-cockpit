"""
Results handling module for The Researcher's Cockpit.

Provides functions to save backtest results in standardized format.
"""

import json
import logging
import math
from pathlib import Path
from typing import Dict, Any

import numpy as np
import pandas as pd

from ..utils import (
    get_project_root,
    get_strategy_path,
    timestamp_dir,
    update_symlink,
    save_yaml,
    ensure_dir,
    check_and_fix_symlinks,
)

from .verification import _verify_data_integrity


# Module-level logger
logger = logging.getLogger(__name__)


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


def _sanitize_for_json(obj: Any) -> Any:
    """
    Recursively sanitize values for JSON serialization.

    v1.0.7: Ensures no NaN/Inf values escape to JSON output, which would
    produce invalid strict JSON (Python's json.dump outputs 'NaN' literal).

    Args:
        obj: Any value to sanitize

    Returns:
        Sanitized value safe for JSON serialization
    """
    if isinstance(obj, dict):
        return {k: _sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_sanitize_for_json(item) for item in obj]
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return 0.0
        return obj
    elif isinstance(obj, np.floating):
        if np.isnan(obj) or np.isinf(obj):
            return 0.0
        return float(obj)
    elif isinstance(obj, np.integer):
        return int(obj)
    return obj


def _calculate_and_save_metrics(
    perf: pd.DataFrame,
    transactions_df: pd.DataFrame,
    result_dir: Path,
    trading_calendar: Any
) -> Dict[str, Any]:
    """
    Calculate enhanced metrics and save to JSON.
    """
    from ..metrics import calculate_metrics
    from ..config import load_settings
    
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
    # v1.0.7: Sanitize metrics to ensure valid strict JSON (no NaN/Inf)
    with open(result_dir / 'metrics.json', 'w') as f:
        json.dump(_sanitize_for_json(metrics), f, indent=2)
    
    return metrics


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
        trading_calendar: Trading calendar object
    """
    try:
        from ..plots import plot_all
        
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
        trading_calendar: Trading calendar object
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





