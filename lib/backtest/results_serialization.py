"""
Results serialization module for The Researcher's Cockpit.

Handles CSV and JSON serialization of backtest results:
- Returns, positions, and transactions CSV files
- Metrics JSON file
- Parameters YAML file
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any

import numpy as np
import pandas as pd

from ..utils import save_yaml
from ..metrics import calculate_metrics
from lib.data.sanitization import sanitize_for_json
from ..config import load_settings

# Module-level logger
logger = logging.getLogger(__name__)


def normalize_performance_dataframe(perf: pd.DataFrame) -> pd.DataFrame:
    """Normalize performance DataFrame index to timezone-naive UTC."""
    perf_normalized = perf.copy()
    if perf_normalized.index.tz is not None:
        perf_normalized.index = perf_normalized.index.tz_convert('UTC').tz_localize(None)
    return perf_normalized


def extract_positions_dataframe(perf: pd.DataFrame) -> pd.DataFrame:
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


def extract_transactions_dataframe(perf: pd.DataFrame) -> pd.DataFrame:
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


# Import sanitization utility
from lib.data.sanitization import sanitize_for_json


def save_returns_csv(perf: pd.DataFrame, result_dir: Path) -> None:
    """Save returns to CSV file."""
    if 'returns' in perf.columns:
        returns_df = pd.DataFrame({'returns': perf['returns']})
        returns_df.to_csv(result_dir / 'returns.csv', date_format='%Y-%m-%d')


def save_positions_csv(positions_df: pd.DataFrame, result_dir: Path) -> None:
    """Save positions to CSV file."""
    positions_df.to_csv(result_dir / 'positions.csv', date_format='%Y-%m-%d', index_label='date')


def save_transactions_csv(transactions_df: pd.DataFrame, result_dir: Path) -> None:
    """Save transactions to CSV file."""
    transactions_df.to_csv(result_dir / 'transactions.csv', date_format='%Y-%m-%d', index_label='date')


def calculate_portfolio_value_from_transactions(
    perf: pd.DataFrame,
    transactions_df: pd.DataFrame,
    positions_df: pd.DataFrame,
    initial_capital: float
) -> pd.Series:
    """
    Calculate portfolio_value from transactions and positions when metrics_set='none'.
    
    v1.11.0: Reconstructs portfolio_value by:
    1. Tracking cash balance from transactions
    2. Calculating position values from positions DataFrame
    3. Portfolio_value = cash + sum(position_values)
    
    Args:
        perf: Performance DataFrame
        transactions_df: Transactions DataFrame
        positions_df: Positions DataFrame
        initial_capital: Starting capital
        
    Returns:
        pd.Series: Portfolio value over time (indexed by date)
    """
    if len(transactions_df) == 0 and len(positions_df) == 0:
        # No transactions or positions - return constant portfolio value
        if len(perf) > 0:
            return pd.Series(initial_capital, index=perf.index)
        return pd.Series(dtype=float)
    
    # Get all unique dates from perf index
    dates = perf.index.sort_values()
    portfolio_values = pd.Series(index=dates, dtype=float)
    
    # Track cash balance over time (initialize with starting capital)
    cash_balance = initial_capital
    
    # Group transactions by date for efficient processing
    if len(transactions_df) > 0:
        transactions_by_date = transactions_df.groupby(transactions_df.index.date)
    else:
        transactions_by_date = {}
    
    # Group positions by date for efficient processing
    if len(positions_df) > 0:
        positions_by_date = positions_df.groupby(positions_df.index.date)
    else:
        positions_by_date = {}
    
    # Process each date chronologically
    for date in dates:
        date_only = date.date() if hasattr(date, 'date') else pd.Timestamp(date).date()
        
        # Process transactions for this date
        if date_only in transactions_by_date.groups:
            date_transactions = transactions_by_date.get_group(date_only)
            for _, txn in date_transactions.iterrows():
                amount = float(txn.get('amount', 0))
                price = float(txn.get('price', 0.0))
                commission = float(txn.get('commission', 0.0)) if pd.notna(txn.get('commission')) else 0.0
                
                # Update cash: buy reduces cash, sell increases cash
                if amount > 0:  # Buy
                    cash_balance -= (amount * price + commission)
                elif amount < 0:  # Sell
                    cash_balance += (abs(amount) * price - commission)
        
        # Calculate position values for this date
        position_value = 0.0
        if date_only in positions_by_date.groups:
            date_positions = positions_by_date.get_group(date_only)
            for _, pos in date_positions.iterrows():
                amount = float(pos.get('amount', 0))
                last_sale_price = float(pos.get('last_sale_price', 0.0)) if pd.notna(pos.get('last_sale_price')) else 0.0
                if last_sale_price > 0:
                    position_value += amount * last_sale_price
                else:
                    # Fallback to cost_basis if last_sale_price not available
                    cost_basis = float(pos.get('cost_basis', 0.0)) if pd.notna(pos.get('cost_basis')) else 0.0
                    if cost_basis > 0 and amount > 0:
                        position_value += cost_basis
        
        # Portfolio value = cash + positions
        portfolio_values[date] = cash_balance + position_value
    
    # Forward fill any missing values (use pandas 2.0+ compatible method)
    if hasattr(portfolio_values, 'ffill'):
        portfolio_values = portfolio_values.ffill().fillna(initial_capital)
    else:
        # Fallback for older pandas
        portfolio_values = portfolio_values.fillna(method='ffill').fillna(initial_capital)
    
    return portfolio_values


def calculate_and_save_metrics(
    perf: pd.DataFrame,
    transactions_df: pd.DataFrame,
    result_dir: Path,
    trading_calendar: Any,
    initial_capital: float = None
) -> Dict[str, Any]:
    """
    Calculate enhanced metrics and save to JSON.
    
    Args:
        perf: Performance DataFrame
        transactions_df: Transactions DataFrame
        result_dir: Directory to save metrics
        trading_calendar: Trading calendar object
        initial_capital: Starting capital (for portfolio_value reconstruction)
        
    Returns:
        Dict[str, Any]: Calculated metrics
    """
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
    # v1.11.0: Handle case where returns column is missing (when metrics_set='none')
    # Calculate returns from portfolio_value if available, or reconstruct portfolio_value from transactions
    returns = None
    portfolio_value = None
    
    if 'returns' in perf.columns:
        returns = perf['returns'].dropna()
        portfolio_value = perf['portfolio_value'] if 'portfolio_value' in perf.columns else None
    elif 'portfolio_value' in perf.columns:
        # Calculate returns from portfolio_value
        portfolio_value = perf['portfolio_value']
        pv = portfolio_value.dropna()
        if len(pv) > 1:
            returns = pv.pct_change().dropna()
            logger.info("Calculated returns from portfolio_value (metrics_set='none' was used)")
        else:
            logger.warning("Insufficient portfolio_value data to calculate returns")
            returns = pd.Series(dtype=float)
    else:
        # v1.11.0 Option B: Reconstruct portfolio_value from transactions and positions
        logger.info("Reconstructing portfolio_value from transactions and positions (metrics_set='none' was used)")
        positions_df = extract_positions_dataframe(perf)
        
        # Get initial capital from perf if available, or use default
        if initial_capital is None:
            # Try to get from perf if it has capital_base column
            if 'capital_base' in perf.columns:
                initial_capital = float(perf['capital_base'].iloc[0])
            else:
                # Default to 100000 if not available
                initial_capital = 100000.0
                logger.warning(f"Initial capital not provided, using default: {initial_capital}")
        
        portfolio_value = calculate_portfolio_value_from_transactions(
            perf, transactions_df, positions_df, initial_capital
        )
        
        if len(portfolio_value) > 1:
            returns = portfolio_value.pct_change().dropna()
            logger.info(f"Reconstructed portfolio_value and calculated returns from {len(portfolio_value)} data points")
        else:
            logger.warning("Could not reconstruct portfolio_value from transactions")
            returns = pd.Series(dtype=float)
    
    if returns is not None and len(returns) > 0:
        # Use enhanced metrics calculation
        metrics = calculate_metrics(
            returns,
            transactions=transactions_df if len(transactions_df) > 0 else None,
            risk_free_rate=risk_free_rate,
            trading_days_per_year=trading_days_per_year
        )
    else:
        logger.warning("No returns data available for metrics calculation")
        metrics = {}
    
    # Portfolio value (add to metrics if available)
    if portfolio_value is not None and len(portfolio_value) > 0:
        metrics['final_portfolio_value'] = float(portfolio_value.iloc[-1])
        metrics['initial_portfolio_value'] = float(portfolio_value.iloc[0])
        # v1.11.0: Add reconstructed portfolio_value and returns to perf DataFrame for plotting
        if 'portfolio_value' not in perf.columns:
            perf['portfolio_value'] = portfolio_value.reindex(perf.index, method='ffill').fillna(initial_capital if initial_capital else 100000.0)
        if 'returns' not in perf.columns and returns is not None and len(returns) > 0:
            perf['returns'] = returns.reindex(perf.index)
    elif 'portfolio_value' in perf.columns:
        metrics['final_portfolio_value'] = float(perf['portfolio_value'].iloc[-1])
        metrics['initial_portfolio_value'] = float(perf['portfolio_value'].iloc[0])
    
    # Save metrics JSON
    # v1.0.7: Sanitize metrics to ensure valid strict JSON (no NaN/Inf)
    with open(result_dir / 'metrics.json', 'w') as f:
        json.dump(sanitize_for_json(metrics), f, indent=2)
    
    return metrics


def save_parameters_yaml(params: Dict[str, Any], result_dir: Path) -> None:
    """Save parameters to YAML file."""
    save_yaml(params, result_dir / 'parameters_used.yaml')


def generate_plots(
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
