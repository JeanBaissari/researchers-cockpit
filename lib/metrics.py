"""
Enhanced metrics calculation module for The Researcher's Cockpit.

Provides comprehensive performance metrics using empyrical-reloaded library and custom
trade-level analysis.

v1.0.4 Fixes Applied:
- Fixed Sharpe ratio calculation to handle edge cases (zero volatility, insufficient data)
- Fixed Sortino ratio calculation with proper downside deviation threshold
- Added NaN/Inf handling throughout all metric calculations
- Fixed recovery time calculation to handle edge cases properly
- Added input validation for all public functions
- Improved error handling with graceful degradation
"""

# Standard library imports
from pathlib import Path
from typing import Optional, Dict, List, Any, Union

# Third-party imports
import numpy as np
import pandas as pd

try:
    import empyrical as ep
    EMPYRICAL_AVAILABLE = True
except ImportError:
    EMPYRICAL_AVAILABLE = False


def _sanitize_value(value: float, default: float = 0.0) -> float:
    """
    Sanitize a numeric value by replacing NaN/Inf with a default.
    
    v1.0.4: Added to ensure all returned metrics are valid floats.
    
    Args:
        value: The value to sanitize
        default: The default value to use if value is NaN or Inf
        
    Returns:
        Sanitized float value
    """
    if value is None or np.isnan(value) or np.isinf(value):
        return default
    return float(value)


def _validate_returns(returns: pd.Series) -> pd.Series:
    """
    Validate and clean a returns series.
    
    v1.0.4: Added comprehensive input validation.
    
    Args:
        returns: Series of returns to validate
        
    Returns:
        Cleaned returns series with NaN values removed
        
    Raises:
        ValueError: If returns is not a valid pandas Series
    """
    if returns is None:
        raise ValueError("Returns series cannot be None")
    
    if not isinstance(returns, pd.Series):
        raise ValueError(f"Returns must be a pandas Series, got {type(returns)}")
    
    # Drop NaN values and convert to float
    cleaned = returns.dropna().astype(float)
    
    # v1.0.4: Replace any infinite values with NaN and then drop
    cleaned = cleaned.replace([np.inf, -np.inf], np.nan).dropna()
    
    return cleaned


def calculate_metrics(
    returns: pd.Series,
    transactions: Optional[pd.DataFrame] = None,
    benchmark_returns: Optional[pd.Series] = None,
    risk_free_rate: float = 0.04,
    trading_days_per_year: int = 252
) -> Dict[str, float]:
    """
    Calculate comprehensive performance metrics from returns.
    
    Uses empyrical-reloaded library for financial metrics when available, falls back
    to manual calculations otherwise.
    
    v1.0.4 Fixes:
    - Added input validation for all parameters
    - Fixed Sharpe ratio edge cases (zero volatility, insufficient data)
    - Fixed Sortino ratio with proper downside deviation calculation
    - Added NaN/Inf sanitization for all output values
    - Improved error handling with graceful degradation
    
    Args:
        returns: Series of daily returns (timezone-naive index)
        transactions: Optional DataFrame of transactions for trade-level metrics
        benchmark_returns: Optional Series of benchmark daily returns for alpha/beta
        risk_free_rate: Annual risk-free rate (default: 0.04)
        trading_days_per_year: Trading days per year (default: 252)
        
    Returns:
        Dictionary of calculated metrics (all values guaranteed to be valid floats)
        
    Raises:
        ValueError: If returns is not a valid pandas Series
    """
    # v1.0.4: Validate inputs
    returns = _validate_returns(returns)
    
    if len(returns) == 0:
        return _empty_metrics()
    
    # v1.0.4: Validate risk_free_rate and trading_days_per_year
    if not isinstance(risk_free_rate, (int, float)) or np.isnan(risk_free_rate):
        risk_free_rate = 0.04
    if not isinstance(trading_days_per_year, int) or trading_days_per_year <= 0:
        trading_days_per_year = 252
    
    metrics = {}
    
    # Convert annual risk-free rate to daily
    daily_risk_free_rate = risk_free_rate / trading_days_per_year
    
    # Basic return metrics
    total_return = float((1 + returns).prod() - 1)
    metrics['total_return'] = _sanitize_value(total_return)
    
    # Annualized return
    n_days = len(returns)
    if n_days > 0:
        # v1.0.4: Handle edge case where total_return is -100% (would cause negative base for power)
        if total_return <= -1.0:
            annual_return = -1.0  # Complete loss
        else:
            annual_return = float((1 + total_return) ** (trading_days_per_year / n_days) - 1)
        metrics['annual_return'] = _sanitize_value(annual_return)
    else:
        metrics['annual_return'] = 0.0
    
    annual_return = metrics['annual_return']  # Use sanitized value for subsequent calculations
    
    # Volatility (annualized)
    # v1.0.4: Handle edge case where std is zero or NaN
    daily_volatility = float(returns.std())
    if np.isnan(daily_volatility) or daily_volatility < 0:
        daily_volatility = 0.0
    volatility = daily_volatility * np.sqrt(trading_days_per_year)
    metrics['annual_volatility'] = _sanitize_value(volatility)
    
    # v1.0.4: Fixed Sharpe ratio calculation with proper edge case handling
    # Sharpe ratio requires sufficient data and non-zero volatility
    MIN_PERIODS_FOR_SHARPE = 20  # v1.0.4: Minimum periods for reliable Sharpe calculation
    
    if n_days < MIN_PERIODS_FOR_SHARPE:
        # v1.0.4: Not enough data for reliable Sharpe ratio
        sharpe = 0.0
    elif volatility < 1e-10:
        # v1.0.4: Zero volatility edge case - if returns positive, infinite Sharpe (cap at 0)
        # We return 0 because zero volatility with positive returns is unrealistic
        sharpe = 0.0
    elif EMPYRICAL_AVAILABLE:
        try:
            # empyrical-reloaded expects annualized risk-free rate and handles conversion internally
            sharpe = float(ep.sharpe_ratio(
                returns, 
                risk_free=risk_free_rate, 
                period='daily', 
                annualization=trading_days_per_year
            ))
            sharpe = _sanitize_value(sharpe)
        except Exception:
            # v1.0.4: Fallback to manual calculation on empyrical error
            excess_return = annual_return - risk_free_rate
            sharpe = _sanitize_value(excess_return / volatility)
    else:
        # Manual calculation: (annualized_return - risk_free_rate) / annualized_volatility
        excess_return = annual_return - risk_free_rate
        sharpe = _sanitize_value(excess_return / volatility)
    metrics['sharpe'] = sharpe
    
    # v1.0.4: Fixed Sortino ratio calculation with proper downside deviation
    # The threshold for downside deviation should be the target return (often 0 or risk-free rate)
    if n_days < MIN_PERIODS_FOR_SHARPE:
        # v1.0.4: Not enough data for reliable Sortino ratio
        sortino = 0.0
    elif EMPYRICAL_AVAILABLE:
        try:
            # empyrical-reloaded expects annualized required return
            sortino = float(ep.sortino_ratio(
                returns, 
                required_return=risk_free_rate, 
                period='daily', 
                annualization=trading_days_per_year
            ))
            sortino = _sanitize_value(sortino)
        except Exception:
            # v1.0.4: Fallback to manual calculation
            sortino = _calculate_sortino_manual(
                returns, daily_risk_free_rate, annual_return, 
                risk_free_rate, trading_days_per_year
            )
    else:
        # v1.0.4: Manual Sortino calculation with corrected downside deviation
        sortino = _calculate_sortino_manual(
            returns, daily_risk_free_rate, annual_return, 
            risk_free_rate, trading_days_per_year
        )
    metrics['sortino'] = sortino
    
    # Maximum drawdown
    if EMPYRICAL_AVAILABLE:
        try:
            max_dd = float(ep.max_drawdown(returns))
            max_dd = _sanitize_value(max_dd)
        except Exception:
            max_dd = _calculate_max_drawdown_manual(returns)
    else:
        max_dd = _calculate_max_drawdown_manual(returns)
    metrics['max_drawdown'] = max_dd
    
    # Calmar ratio (annual return / max drawdown)
    # v1.0.4: Handle edge case where max_dd is zero or very small
    if abs(max_dd) > 1e-10:
        calmar = _sanitize_value(annual_return / abs(max_dd))
    else:
        calmar = 0.0
    metrics['calmar'] = calmar
    
    # Additional metrics from empyrical-reloaded if available
    if EMPYRICAL_AVAILABLE:
        # Alpha and Beta require benchmark returns
        if benchmark_returns is not None and len(benchmark_returns) > 0:
            try:
                # v1.0.4: Validate benchmark returns
                benchmark_returns = _validate_returns(benchmark_returns)
                
                # Align returns and benchmark
                aligned_returns, aligned_benchmark = returns.align(benchmark_returns, join='inner')
                aligned_returns = aligned_returns.dropna()
                aligned_benchmark = aligned_benchmark.dropna()
                
                if len(aligned_returns) >= MIN_PERIODS_FOR_SHARPE and len(aligned_benchmark) >= MIN_PERIODS_FOR_SHARPE:
                    alpha = float(ep.alpha(
                        aligned_returns, 
                        aligned_benchmark, 
                        risk_free=risk_free_rate, 
                        period='daily', 
                        annualization=trading_days_per_year
                    ))
                    beta = float(ep.beta(aligned_returns, aligned_benchmark))
                    metrics['alpha'] = _sanitize_value(alpha)
                    metrics['beta'] = _sanitize_value(beta, default=1.0)
                else:
                    metrics['alpha'] = 0.0
                    metrics['beta'] = 1.0
            except Exception:
                metrics['alpha'] = 0.0
                metrics['beta'] = 1.0
        else:
            # Without benchmark, alpha is 0 and beta is undefined (set to 1)
            metrics['alpha'] = 0.0
            metrics['beta'] = 1.0
        
        # Omega ratio
        try:
            omega = float(ep.omega_ratio(
                returns, 
                risk_free=risk_free_rate, 
                required_return=0.0, 
                annualization=trading_days_per_year
            ))
            metrics['omega'] = _sanitize_value(omega)
        except Exception:
            metrics['omega'] = 0.0
        
        # Tail ratio
        try:
            tail_ratio = float(ep.tail_ratio(returns))
            metrics['tail_ratio'] = _sanitize_value(tail_ratio)
        except Exception:
            metrics['tail_ratio'] = 0.0
        
        # Maximum drawdown duration
        try:
            max_dd_duration = ep.max_drawdown_duration(returns)
            if max_dd_duration is not None:
                # v1.0.4: Handle case where duration is a timedelta
                if isinstance(max_dd_duration, pd.Timedelta):
                    metrics['max_drawdown_duration'] = _sanitize_value(
                        max_dd_duration.total_seconds() / (60 * 60 * 24)
                    )
                else:
                    metrics['max_drawdown_duration'] = _sanitize_value(float(max_dd_duration))
            else:
                metrics['max_drawdown_duration'] = 0.0
        except Exception:
            metrics['max_drawdown_duration'] = 0.0

        # Recovery time
        try:
            recovery_time = _calculate_recovery_time(returns)
            if recovery_time is not None:
                metrics['recovery_time'] = _sanitize_value(
                    recovery_time.total_seconds() / (60 * 60 * 24)
                )
            else:
                metrics['recovery_time'] = 0.0
        except Exception:
            metrics['recovery_time'] = 0.0
    else:
        metrics['alpha'] = 0.0
        metrics['beta'] = 1.0
        metrics['omega'] = 0.0
        metrics['tail_ratio'] = 0.0
        metrics['max_drawdown_duration'] = 0.0
        metrics['recovery_time'] = 0.0
    
    # Trade-level metrics if transactions provided
    if transactions is not None:
        if len(transactions) > 0:
            try:
                trade_metrics = calculate_trade_metrics(transactions)
                metrics.update(trade_metrics)
            except Exception:
                # v1.0.4: If trade metrics fail, add empty trade metrics
                metrics.update({
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
                })
        else:
            # v1.0.6: Empty transactions DataFrame - still include trade_count: 0
            metrics['trade_count'] = 0

    return metrics


def _calculate_sortino_manual(
    returns: pd.Series,
    daily_risk_free_rate: float,
    annual_return: float,
    risk_free_rate: float,
    trading_days_per_year: int
) -> float:
    """
    Calculate Sortino ratio manually with proper downside deviation.
    
    v1.0.4: Extracted and fixed Sortino calculation.
    
    The downside deviation should use returns below the target (risk-free rate),
    not just negative returns.
    
    Args:
        returns: Daily returns series
        daily_risk_free_rate: Daily risk-free rate
        annual_return: Annualized return
        risk_free_rate: Annual risk-free rate
        trading_days_per_year: Trading days per year
        
    Returns:
        Sortino ratio as float
    """
    # v1.0.4: Calculate downside deviation using returns below target
    # Target is the daily risk-free rate
    excess_returns = returns - daily_risk_free_rate
    downside_returns = excess_returns[excess_returns < 0]
    
    if len(downside_returns) == 0:
        # v1.0.4: No downside returns means all returns beat the target
        # Return 0 as we can't calculate a meaningful ratio
        return 0.0
    
    # v1.0.4: Downside deviation is the std of returns below target
    # Using squared deviations from zero (since we already subtracted target)
    downside_std = float(np.sqrt(np.mean(downside_returns ** 2)))
    annualized_downside_std = downside_std * np.sqrt(trading_days_per_year)
    
    if annualized_downside_std < 1e-10:
        return 0.0
    
    excess_annual_return = annual_return - risk_free_rate
    sortino = _sanitize_value(excess_annual_return / annualized_downside_std)
    
    return sortino


def _calculate_max_drawdown_manual(returns: pd.Series) -> float:
    """
    Calculate maximum drawdown manually.
    
    v1.0.4: Extracted for reuse and added error handling.
    
    Args:
        returns: Daily returns series
        
    Returns:
        Maximum drawdown as a negative float (or 0 if no drawdown)
    """
    if len(returns) == 0:
        return 0.0
    
    try:
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        max_dd = float(drawdown.min())
        return _sanitize_value(max_dd)
    except Exception:
        return 0.0


def calculate_trade_metrics(transactions: pd.DataFrame) -> Dict[str, float]:
    """
    Calculate trade-level metrics from transactions DataFrame.
    
    v1.0.4 Fixes:
    - Added input validation
    - Added NaN/Inf sanitization for all output values
    - Improved error handling
    
    Args:
        transactions: DataFrame with columns: date, sid, amount, price, commission
        
    Returns:
        Dictionary of trade-level metrics (all values guaranteed to be valid)
    """
    empty_trade_metrics = {
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
    
    # v1.0.4: Input validation
    if transactions is None or not isinstance(transactions, pd.DataFrame):
        return empty_trade_metrics
    
    if len(transactions) == 0:
        return empty_trade_metrics
    
    # Group transactions into trades (pairs of buy/sell)
    try:
        trades = _extract_trades(transactions)
    except Exception:
        return empty_trade_metrics
    
    if len(trades) == 0:
        return empty_trade_metrics
    
    # Calculate trade returns
    trade_returns = []
    trade_durations = []
    
    for trade in trades:
        try:
            entry_price = trade.get('entry_price', 0)
            exit_price = trade.get('exit_price', 0)
            
            # v1.0.4: Validate prices
            if entry_price is None or exit_price is None:
                continue
            if np.isnan(entry_price) or np.isnan(exit_price):
                continue
            if entry_price <= 0 or exit_price <= 0:
                continue
            
            # Calculate return
            if trade.get('direction') == 'long':
                trade_return = (exit_price - entry_price) / entry_price
            else:  # short
                trade_return = (entry_price - exit_price) / entry_price
            
            # v1.0.4: Validate trade return
            if not np.isnan(trade_return) and not np.isinf(trade_return):
                trade_returns.append(trade_return)
            
            # Calculate duration
            entry_date = trade.get('entry_date')
            exit_date = trade.get('exit_date')
            if entry_date is not None and exit_date is not None:
                duration = (exit_date - entry_date).days
                if duration >= 0:
                    trade_durations.append(duration)
        except Exception:
            continue
    
    if len(trade_returns) == 0:
        return empty_trade_metrics
    
    trade_returns = np.array(trade_returns)
    
    # Win rate
    wins = trade_returns > 0
    win_rate = _sanitize_value(float(np.mean(wins))) if len(wins) > 0 else 0.0
    
    # Profit factor
    gross_profit = trade_returns[trade_returns > 0].sum()
    gross_loss = abs(trade_returns[trade_returns < 0].sum())
    if gross_loss > 1e-10:
        profit_factor = _sanitize_value(float(gross_profit / gross_loss))
    else:
        # v1.0.4: If no losses, profit factor is undefined - use 0 or cap it
        profit_factor = 0.0 if gross_profit == 0 else 0.0  # Could also use a large number
    
    # Average trade return
    avg_trade_return = _sanitize_value(float(np.mean(trade_returns)))
    
    # Average win/loss
    winning_trades = trade_returns[trade_returns > 0]
    losing_trades = trade_returns[trade_returns < 0]
    avg_win = _sanitize_value(float(np.mean(winning_trades))) if len(winning_trades) > 0 else 0.0
    avg_loss = _sanitize_value(float(np.mean(losing_trades))) if len(losing_trades) > 0 else 0.0
    
    # Max win/loss
    max_win = _sanitize_value(float(np.max(trade_returns))) if len(trade_returns) > 0 else 0.0
    max_loss = _sanitize_value(float(np.min(trade_returns))) if len(trade_returns) > 0 else 0.0
    
    # Max consecutive losses
    max_consecutive_losses = _calculate_max_consecutive_losses(trade_returns)
    
    # Average trade duration
    avg_trade_duration = _sanitize_value(float(np.mean(trade_durations))) if len(trade_durations) > 0 else 0.0
    
    # Trades per month (approximate)
    trades_per_month = 0.0
    if len(trades) > 0:
        try:
            first_trade_date = trades[0].get('entry_date')
            last_trade_date = trades[-1].get('exit_date')
            if first_trade_date is not None and last_trade_date is not None:
                total_days = (last_trade_date - first_trade_date).days
                if total_days > 0:
                    trades_per_month = _sanitize_value(float(len(trades) * 30 / total_days))
        except Exception:
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
    
    v1.0.4 Fixes:
    - Added validation for transaction data
    - Improved error handling for malformed data
    """
    trades = []
    current_position = None
    
    for idx, row in transactions.iterrows():
        try:
            # v1.0.4: Safely extract values with validation
            amount = row.get('amount', 0) if isinstance(row, dict) else row['amount']
            price = row.get('price', 0) if isinstance(row, dict) else row['price']
            
            # v1.0.4: Validate amount and price
            if amount is None or price is None:
                continue
            if np.isnan(amount) or np.isnan(price):
                continue
            if amount == 0:
                continue
            
            # Determine date
            if isinstance(idx, pd.Timestamp):
                date = idx
            else:
                date_val = row.get('date', idx) if isinstance(row, dict) else row.get('date', idx)
                date = pd.Timestamp(date_val) if date_val is not None else pd.Timestamp(idx)
            
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
        except Exception:
            # v1.0.4: Skip malformed transactions
            continue
    
    return trades


def _calculate_max_consecutive_losses(trade_returns: np.ndarray) -> int:
    """
    Calculate maximum consecutive losses.
    
    v1.0.4: Added input validation.
    """
    if trade_returns is None or len(trade_returns) == 0:
        return 0
    
    max_consecutive = 0
    current_consecutive = 0
    
    for ret in trade_returns:
        if np.isnan(ret):
            continue
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
    
    v1.0.4 Fixes:
    - Added input validation
    - Added error handling for edge cases
    
    Args:
        returns: Series of daily returns
        window: Rolling window size in days (default: 63 = ~3 months)
        risk_free_rate: Annual risk-free rate
        
    Returns:
        DataFrame with rolling metrics columns
    """
    # v1.0.4: Input validation
    try:
        returns = _validate_returns(returns)
    except ValueError:
        return pd.DataFrame()
    
    if len(returns) < window:
        return pd.DataFrame()
    
    # v1.0.4: Validate window
    if not isinstance(window, int) or window <= 0:
        window = 63
    
    rolling_data = []
    
    for i in range(window, len(returns) + 1):
        try:
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
        except Exception:
            # v1.0.4: Skip windows that fail
            continue
    
    if len(rolling_data) == 0:
        return pd.DataFrame()
    
    return pd.DataFrame(rolling_data).set_index('date')


def compare_strategies(strategy_names: List[str], results_base: Optional[Path] = None) -> pd.DataFrame:
    """
    Compare multiple strategies by loading their latest metrics.
    
    v1.0.4 Fixes:
    - Added input validation
    - Improved error handling for missing files
    
    Args:
        strategy_names: List of strategy names to compare
        results_base: Base path to results directory (default: project_root/results)
        
    Returns:
        DataFrame with strategy comparison metrics
    """
    from .utils import get_project_root
    
    # v1.0.4: Input validation
    if strategy_names is None or not isinstance(strategy_names, list):
        return pd.DataFrame()
    
    if results_base is None:
        try:
            results_base = get_project_root() / 'results'
        except Exception:
            return pd.DataFrame()
    
    comparison_data = []
    
    for strategy_name in strategy_names:
        try:
            if not isinstance(strategy_name, str):
                continue
                
            latest_dir = results_base / strategy_name / 'latest'
            metrics_file = latest_dir / 'metrics.json'
            
            if not metrics_file.exists():
                continue
            
            import json
            with open(metrics_file) as f:
                metrics = json.load(f)
            
            comparison_data.append({
                'strategy': strategy_name,
                'sharpe': _sanitize_value(metrics.get('sharpe', 0.0)),
                'sortino': _sanitize_value(metrics.get('sortino', 0.0)),
                'annual_return': _sanitize_value(metrics.get('annual_return', 0.0)),
                'max_drawdown': _sanitize_value(metrics.get('max_drawdown', 0.0)),
                'calmar': _sanitize_value(metrics.get('calmar', 0.0)),
                'win_rate': _sanitize_value(metrics.get('win_rate', 0.0)),
                'trade_count': int(metrics.get('trade_count', 0)),
            })
        except Exception:
            # v1.0.4: Skip strategies that fail to load
            continue
    
    return pd.DataFrame(comparison_data)


def _calculate_recovery_time(returns: pd.Series) -> Optional[pd.Timedelta]:
    """
    Calculate the recovery time from the start of the maximum drawdown to new equity high.

    v1.0.4 Fixes:
    - Added input validation
    - Fixed edge case handling for empty returns
    - Fixed edge case when drawdown starts at first data point
    - Added proper handling for when recovery hasn't occurred

    Args:
        returns: Series of daily returns.

    Returns:
        pd.Timedelta: The recovery time, or None if not yet recovered.
    """
    # v1.0.4: Input validation
    if returns is None or len(returns) == 0:
        return pd.Timedelta(seconds=0)

    try:
        # v1.0.4: Validate returns has a proper datetime index
        if not isinstance(returns.index, pd.DatetimeIndex):
            # Try to convert index to datetime
            try:
                returns.index = pd.to_datetime(returns.index)
            except Exception:
                return pd.Timedelta(seconds=0)
        
        # Calculate cumulative returns
        cumulative_returns = (1 + returns).cumprod()
        
        # v1.0.4: Check for valid cumulative returns
        if cumulative_returns.isna().all() or len(cumulative_returns) == 0:
            return pd.Timedelta(seconds=0)
        
        # Calculate the running maximum
        running_max = cumulative_returns.cummax()
        
        # Calculate drawdowns
        # v1.0.4: Handle division by zero
        with np.errstate(divide='ignore', invalid='ignore'):
            drawdown = (cumulative_returns - running_max) / running_max
            drawdown = drawdown.replace([np.inf, -np.inf], 0).fillna(0)
        
        # Find the maximum drawdown (most negative value in the drawdown series)
        max_dd_value = drawdown.min()
        
        # v1.0.4: If no drawdown, no recovery needed
        if max_dd_value >= 0 or np.isnan(max_dd_value):
            return pd.Timedelta(seconds=0)

        # Find the index of the start and end of the max drawdown
        # The end of the max drawdown is the lowest trough itself
        end_of_max_dd_idx = drawdown.idxmin()
        
        # The start of the max drawdown is the last peak before the lowest trough
        cumulative_before_trough = cumulative_returns[:end_of_max_dd_idx]
        
        # v1.0.4: Handle edge case where trough is at the beginning
        if len(cumulative_before_trough) == 0:
            return pd.Timedelta(seconds=0)
        
        start_of_max_dd_idx = cumulative_before_trough.idxmax()

        # Find the next time the equity curve makes a new high after the max drawdown trough
        recovery_candidates = cumulative_returns[cumulative_returns.index > end_of_max_dd_idx]
        
        if len(recovery_candidates) == 0:
            return None  # Has not recovered yet
        
        # Find the first index where the cumulative returns recover to or exceed the peak before the drawdown
        peak_value = cumulative_returns[start_of_max_dd_idx]
        
        # v1.0.4: Handle NaN peak value
        if np.isnan(peak_value):
            return pd.Timedelta(seconds=0)
        
        recovered_mask = recovery_candidates >= peak_value
        
        if not recovered_mask.any():
            return None  # Has not recovered yet
        
        recovered_date = recovery_candidates[recovered_mask].index[0]
        
        return recovered_date - start_of_max_dd_idx
        
    except Exception:
        # v1.0.4: Return 0 on any unexpected error
        return pd.Timedelta(seconds=0)


def _empty_metrics() -> Dict[str, float]:
    """
    Return empty metrics dictionary.
    
    v1.0.4: All values are guaranteed to be valid (no NaN/Inf).
    """
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
