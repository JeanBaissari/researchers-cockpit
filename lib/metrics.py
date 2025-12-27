"""
Enhanced metrics calculation module for The Researcher's Cockpit.

Provides comprehensive performance metrics using Empyrical library and custom
trade-level analysis.
"""

# Standard library imports
from pathlib import Path
from typing import Optional, Dict, List, Any

# Third-party imports
import numpy as np
import pandas as pd

try:
    import empyrical as ep
    EMPYRICAL_AVAILABLE = True
except ImportError:
    EMPYRICAL_AVAILABLE = False


def calculate_metrics(
    returns: pd.Series,
    transactions: Optional[pd.DataFrame] = None,
    risk_free_rate: float = 0.04,
    trading_days_per_year: int = 252
) -> Dict[str, float]:
    """
    Calculate comprehensive performance metrics from returns.
    
    Uses Empyrical library for financial metrics when available, falls back
    to manual calculations otherwise.
    
    Args:
        returns: Series of daily returns (timezone-naive index)
        transactions: Optional DataFrame of transactions for trade-level metrics
        risk_free_rate: Annual risk-free rate (default: 0.04)
        trading_days_per_year: Trading days per year (default: 252)
        
    Returns:
        Dictionary of calculated metrics
    """
    returns = returns.dropna()
    
    if len(returns) == 0:
        return _empty_metrics()
    
    metrics = {}
    
    # Basic return metrics
    total_return = float((1 + returns).prod() - 1)
    metrics['total_return'] = total_return
    
    # Annualized return
    n_days = len(returns)
    if n_days > 0:
        annual_return = float((1 + total_return) ** (trading_days_per_year / n_days) - 1)
        metrics['annual_return'] = annual_return
    else:
        metrics['annual_return'] = 0.0
    
    # Volatility (annualized)
    volatility = float(returns.std() * np.sqrt(trading_days_per_year))
    metrics['annual_volatility'] = volatility
    
    # Sharpe ratio
    if EMPYRICAL_AVAILABLE:
        sharpe = float(ep.sharpe_ratio(returns, risk_free=risk_free_rate, period='daily'))
    else:
        if volatility > 0:
            sharpe = float(np.sqrt(trading_days_per_year) * (returns.mean() - risk_free_rate / trading_days_per_year) / volatility)
        else:
            sharpe = 0.0
    metrics['sharpe'] = sharpe
    
    # Sortino ratio
    if EMPYRICAL_AVAILABLE:
        sortino = float(ep.sortino_ratio(returns, required_return=risk_free_rate, period='daily'))
    else:
        downside_returns = returns[returns < 0]
        if len(downside_returns) > 0:
            downside_std = downside_returns.std() * np.sqrt(trading_days_per_year)
            if downside_std > 0:
                sortino = float(np.sqrt(trading_days_per_year) * (returns.mean() - risk_free_rate / trading_days_per_year) / downside_std)
            else:
                sortino = 0.0
        else:
            sortino = 0.0
    metrics['sortino'] = sortino
    
    # Maximum drawdown
    if EMPYRICAL_AVAILABLE:
        max_dd = float(ep.max_drawdown(returns))
    else:
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        max_dd = float(drawdown.min())
    metrics['max_drawdown'] = max_dd
    
    # Calmar ratio (annual return / max drawdown)
    if abs(max_dd) > 1e-10:
        calmar = float(annual_return / abs(max_dd))
    else:
        calmar = 0.0
    metrics['calmar'] = calmar
    
    # Additional metrics from Empyrical if available
    if EMPYRICAL_AVAILABLE:
        try:
            metrics['alpha'] = float(ep.alpha(returns, returns, risk_free=risk_free_rate, period='daily'))
            metrics['beta'] = float(ep.beta(returns, returns, risk_free=risk_free_rate))
        except:
            metrics['alpha'] = 0.0
            metrics['beta'] = 1.0
        
        try:
            metrics['omega'] = float(ep.omega_ratio(returns, risk_free=risk_free_rate, required_return=risk_free_rate))
        except:
            metrics['omega'] = 0.0
        
        try:
            metrics['tail_ratio'] = float(ep.tail_ratio(returns))
        except:
            metrics['tail_ratio'] = 0.0
        
        try:
            metrics['max_drawdown_duration'] = float(ep.max_drawdown_duration(returns).total_seconds() / (60 * 60 * 24)) # Convert to days
        except:
            metrics['max_drawdown_duration'] = 0.0

        try:
            metrics['recovery_time'] = float(_calculate_recovery_time(returns).total_seconds() / (60 * 60 * 24))
        except:
            metrics['recovery_time'] = 0.0
    
    # Trade-level metrics if transactions provided
    if transactions is not None and len(transactions) > 0:
        trade_metrics = calculate_trade_metrics(transactions)
        metrics.update(trade_metrics)
    
    return metrics


def calculate_trade_metrics(transactions: pd.DataFrame) -> Dict[str, float]:
    """
    Calculate trade-level metrics from transactions DataFrame.
    
    Args:
        transactions: DataFrame with columns: date, sid, amount, price, commission
        
    Returns:
        Dictionary of trade-level metrics
    """
    if len(transactions) == 0:
        return {
            'trade_count': 0,
            'win_rate': 0.0,
            'profit_factor': 0.0,
            'avg_trade_return': 0.0,
            'avg_win': 0.0,
            'avg_loss': 0.0,
            'max_win': 0.0,
            'max_loss': 0.0,
            'max_consecutive_losses': 0,
            'avg_trade_duration': 0.0,
            'trades_per_month': 0.0,
        }
    
    # Group transactions into trades (pairs of buy/sell)
    trades = _extract_trades(transactions)
    
    if len(trades) == 0:
        return {
            'trade_count': 0,
            'win_rate': 0.0,
            'profit_factor': 0.0,
            'avg_trade_return': 0.0,
            'avg_win': 0.0,
            'avg_loss': 0.0,
            'max_win': 0.0,
            'max_loss': 0.0,
            'max_consecutive_losses': 0,
            'avg_trade_duration': 0.0,
            'trades_per_month': 0.0,
        }
    
    # Calculate trade returns
    trade_returns = []
    trade_durations = []
    
    for trade in trades:
        if trade['entry_price'] > 0 and trade['exit_price'] > 0:
            # Calculate return
            if trade['direction'] == 'long':
                trade_return = (trade['exit_price'] - trade['entry_price']) / trade['entry_price']
            else:  # short
                trade_return = (trade['entry_price'] - trade['exit_price']) / trade['entry_price']
            
            trade_returns.append(trade_return)
            
            # Calculate duration
            duration = (trade['exit_date'] - trade['entry_date']).days
            trade_durations.append(duration)
    
    if len(trade_returns) == 0:
        return {
            'trade_count': 0,
            'win_rate': 0.0,
            'profit_factor': 0.0,
            'avg_trade_return': 0.0,
            'avg_win': 0.0,
            'avg_loss': 0.0,
            'max_win': 0.0,
            'max_loss': 0.0,
            'max_consecutive_losses': 0,
            'avg_trade_duration': 0.0,
            'trades_per_month': 0.0,
        }
    
    trade_returns = np.array(trade_returns)
    
    # Win rate
    wins = trade_returns > 0
    win_rate = float(np.mean(wins)) if len(wins) > 0 else 0.0
    
    # Profit factor
    gross_profit = trade_returns[trade_returns > 0].sum()
    gross_loss = abs(trade_returns[trade_returns < 0].sum())
    profit_factor = float(gross_profit / gross_loss) if gross_loss > 0 else 0.0
    
    # Average trade return
    avg_trade_return = float(np.mean(trade_returns))
    
    # Average win/loss
    avg_win = float(np.mean(trade_returns[trade_returns > 0])) if np.any(trade_returns > 0) else 0.0
    avg_loss = float(np.mean(trade_returns[trade_returns < 0])) if np.any(trade_returns < 0) else 0.0
    
    # Max win/loss
    max_win = float(np.max(trade_returns)) if len(trade_returns) > 0 else 0.0
    max_loss = float(np.min(trade_returns)) if len(trade_returns) > 0 else 0.0
    
    # Max consecutive losses
    max_consecutive_losses = _calculate_max_consecutive_losses(trade_returns)
    
    # Average trade duration
    avg_trade_duration = float(np.mean(trade_durations)) if len(trade_durations) > 0 else 0.0
    
    # Trades per month (approximate)
    if len(trades) > 0:
        first_trade_date = trades[0]['entry_date']
        last_trade_date = trades[-1]['exit_date']
        total_days = (last_trade_date - first_trade_date).days
        if total_days > 0:
            trades_per_month = float(len(trades) * 30 / total_days)
        else:
            trades_per_month = 0.0
    else:
        trades_per_month = 0.0
    
    return {
        'trade_count': len(trades),
        'win_rate': win_rate,
        'profit_factor': profit_factor,
        'avg_trade_return': avg_trade_return,
        'avg_win': avg_win,
        'avg_loss': avg_loss,
        'max_win': max_win,
        'max_loss': max_loss,
        'max_consecutive_losses': max_consecutive_losses,
        'avg_trade_duration': avg_trade_duration,
        'trades_per_month': trades_per_month,
    }


def _extract_trades(transactions: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Extract individual trades from transactions DataFrame.
    
    Assumes transactions are ordered by date and groups buy/sell pairs.
    """
    trades = []
    current_position = None
    
    for idx, row in transactions.iterrows():
        amount = row['amount']
        price = row['price']
        date = pd.Timestamp(idx) if isinstance(idx, pd.Timestamp) else pd.Timestamp(row.get('date', idx))
        
        if current_position is None:
            # Starting a new position
            if amount > 0:  # Buy
                current_position = {
                    'entry_date': date,
                    'entry_price': price,
                    'entry_amount': amount,
                    'direction': 'long',
                }
            elif amount < 0:  # Short
                current_position = {
                    'entry_date': date,
                    'entry_price': price,
                    'entry_amount': abs(amount),
                    'direction': 'short',
                }
        else:
            # Closing or modifying position
            if ((current_position['direction'] == 'long' and amount < 0) or 
               (current_position['direction'] == 'short' and amount > 0)):
                # Closing position
                current_position['exit_date'] = date
                current_position['exit_price'] = price
                trades.append(current_position)
                current_position = None
            else:
                # Adding to position (pyramiding) - treat as new entry
                current_position = {
                    'entry_date': date,
                    'entry_price': price,
                    'entry_amount': abs(amount),
                    'direction': 'long' if amount > 0 else 'short',
                }
    
    return trades


def _calculate_max_consecutive_losses(trade_returns: np.ndarray) -> int:
    """Calculate maximum consecutive losses."""
    if len(trade_returns) == 0:
        return 0
    
    max_consecutive = 0
    current_consecutive = 0
    
    for ret in trade_returns:
        if ret < 0:
            current_consecutive += 1
            max_consecutive = max(max_consecutive, current_consecutive)
        else:
            current_consecutive = 0
    
    return int(max_consecutive)


def calculate_rolling_metrics(
    returns: pd.Series,
    window: int = 63,
    risk_free_rate: float = 0.04
) -> pd.DataFrame:
    """
    Calculate rolling metrics over a specified window.
    
    Args:
        returns: Series of daily returns
        window: Rolling window size in days (default: 63 = ~3 months)
        risk_free_rate: Annual risk-free rate
        
    Returns:
        DataFrame with rolling metrics columns
    """
    returns = returns.dropna()
    
    if len(returns) < window:
        return pd.DataFrame()
    
    rolling_data = []
    
    for i in range(window, len(returns) + 1):
        window_returns = returns.iloc[i-window:i]
        
        if len(window_returns) == 0:
            continue
        
        # Calculate metrics for this window
        window_metrics = calculate_metrics(window_returns, risk_free_rate=risk_free_rate)
        
        rolling_data.append({
            'date': returns.index[i-1],
            'rolling_sharpe': window_metrics.get('sharpe', 0.0),
            'rolling_sortino': window_metrics.get('sortino', 0.0),
            'rolling_return': window_metrics.get('annual_return', 0.0),
            'rolling_volatility': window_metrics.get('annual_volatility', 0.0),
            'rolling_max_dd': window_metrics.get('max_drawdown', 0.0),
        })
    
    return pd.DataFrame(rolling_data).set_index('date')


def compare_strategies(strategy_names: List[str], results_base: Optional[Path] = None) -> pd.DataFrame:
    """
    Compare multiple strategies by loading their latest metrics.
    
    Args:
        strategy_names: List of strategy names to compare
        results_base: Base path to results directory (default: project_root/results)
        
    Returns:
        DataFrame with strategy comparison metrics
    """
    from .utils import get_project_root
    
    if results_base is None:
        results_base = get_project_root() / 'results'
    
    comparison_data = []
    
    for strategy_name in strategy_names:
        latest_dir = results_base / strategy_name / 'latest'
        metrics_file = latest_dir / 'metrics.json'
        
        if not metrics_file.exists():
            continue
        
        import json
        with open(metrics_file) as f:
            metrics = json.load(f)
        
        comparison_data.append({
            'strategy': strategy_name,
            'sharpe': metrics.get('sharpe', 0.0),
            'sortino': metrics.get('sortino', 0.0),
            'annual_return': metrics.get('annual_return', 0.0),
            'max_drawdown': metrics.get('max_drawdown', 0.0),
            'calmar': metrics.get('calmar', 0.0),
            'win_rate': metrics.get('win_rate', 0.0),
            'trade_count': metrics.get('trade_count', 0),
        })
    
    return pd.DataFrame(comparison_data)


def _calculate_recovery_time(returns: pd.Series) -> pd.Timedelta:
    """
    Calculate the recovery time from the start of the maximum drawdown to new equity high.

    Args:
        returns: Series of daily returns.

    Returns:
        pd.Timedelta: The recovery time.
    """
    if len(returns) == 0:
        return pd.Timedelta(seconds=0)

    # Calculate cumulative returns
    cumulative_returns = (1 + returns).cumprod()
    
    # Calculate the running maximum
    running_max = cumulative_returns.cummax()
    
    # Calculate drawdowns
    drawdown = (cumulative_returns - running_max) / running_max
    
    # Find the maximum drawdown (most negative value in the drawdown series)
    max_dd_value = drawdown.min()
    
    if max_dd_value == 0:
        return pd.Timedelta(seconds=0) # No drawdown, no recovery needed

    # Find the index of the start and end of the max drawdown
    # The start of the max drawdown is the last peak before the lowest trough
    # The end of the max drawdown is the lowest trough itself
    end_of_max_dd_idx = drawdown.idxmin()
    start_of_max_dd_idx = cumulative_returns[:end_of_max_dd_idx].idxmax()

    # Find the next time the equity curve makes a new high after the max drawdown start
    # We need to find the first point after start_of_max_dd_idx where cumulative_returns >= running_max at start_of_max_dd_idx
    recovery_idx = cumulative_returns[cumulative_returns.index > end_of_max_dd_idx]
    
    # Find the first index where the cumulative returns recover to or exceed the peak before the drawdown
    recovered_date = recovery_idx[recovery_idx >= cumulative_returns[start_of_max_dd_idx]].first_valid_index()

    if recovered_date is None:
        return pd.Timedelta(seconds=0)  # Has not recovered yet
    
    return recovered_date - start_of_max_dd_idx


def _empty_metrics() -> Dict[str, float]:
    """Return empty metrics dictionary."""
    return {
        'total_return': 0.0,
        'annual_return': 0.0,
        'annual_volatility': 0.0,
        'sharpe': 0.0,
        'sortino': 0.0,
        'max_drawdown': 0.0,
        'calmar': 0.0,
        'alpha': 0.0,
        'beta': 1.0,
        'omega': 0.0,
        'tail_ratio': 0.0,
        'max_drawdown_duration': 0.0,
        'recovery_time': 0.0,
        'trade_count': 0,
        'win_rate': 0.0,
        'profit_factor': 0.0,
        'avg_trade_return': 0.0,
        'avg_win': 0.0,
        'avg_loss': 0.0,
        'max_win': 0.0,
        'max_loss': 0.0,
        'max_consecutive_losses': 0,
        'avg_trade_duration': 0.0,
        'trades_per_month': 0.0,
    }

