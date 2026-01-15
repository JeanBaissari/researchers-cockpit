"""
Trade-level metrics calculation for The Researcher's Cockpit.

Provides trade extraction and trade-level performance metrics from transactions.

v1.0.4 Fixes Applied:
- Added input validation for transaction data
- Added NaN/Inf sanitization for all output values
- Improved error handling for malformed data

v1.0.7 Fixes Applied:
- Fixed profit factor to return MAX_PROFIT_FACTOR when profits but no losses
- Fixed trade extraction to handle pyramiding with weighted average entry price
- Added as_percentages parameter to calculate_trade_metrics()
"""

# Standard library imports
from typing import Dict, List, Any

# Third-party imports
import numpy as np
import pandas as pd

# Local imports
from .core import (
    _sanitize_value,
    _convert_to_percentages,
    MAX_PROFIT_FACTOR,
)


def calculate_trade_metrics(
    transactions: pd.DataFrame,
    as_percentages: bool = False
) -> Dict[str, float]:
    """
    Calculate trade-level metrics from transactions DataFrame.
    
    v1.0.4 Fixes:
    - Added input validation
    - Added NaN/Inf sanitization for all output values
    - Improved error handling
    
    v1.0.7 Fixes:
    - Added as_percentages parameter for API consistency
    - Fixed profit factor to return MAX_PROFIT_FACTOR when profits but no losses
    
    Args:
        transactions: DataFrame with columns: date, sid, amount, price, commission
        as_percentages: If True, convert decimal metrics to percentages (default: False)
        
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
    
    # v1.0.7: Fixed profit factor edge case
    gross_profit = trade_returns[trade_returns > 0].sum()
    gross_loss = abs(trade_returns[trade_returns < 0].sum())
    if gross_loss > 1e-10:
        profit_factor = _sanitize_value(float(gross_profit / gross_loss))
    elif gross_profit > 0:
        # v1.0.7: Profits but no losses - cap at MAX_PROFIT_FACTOR
        profit_factor = MAX_PROFIT_FACTOR
    else:
        # No profits and no losses
        profit_factor = 0.0
    
    # Average trade return
    avg_trade_return = _sanitize_value(float(np.mean(trade_returns)))
    
    # Average win/loss
    winning_trades = trade_returns[trade_returns > 0]
    losing_trades = trade_returns[trade_returns < 0]
    avg_win = _sanitize_value(float(np.mean(winning_trades))) if len(winning_trades) > 0 else 0.0
    avg_loss = _sanitize_value(float(np.mean(losing_trades))) if len(losing_trades) > 0 else 0.0
    
    # Max win/loss
    # v1.0.7: Use only winning/losing trades for max calculations (not all trades)
    max_win = _sanitize_value(float(np.max(winning_trades))) if len(winning_trades) > 0 else 0.0
    max_loss = _sanitize_value(float(np.min(losing_trades))) if len(losing_trades) > 0 else 0.0
    
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
    
    result = {
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
    
    # v1.0.7: Convert to percentages if requested
    if as_percentages:
        return _convert_to_percentages(result)
    return result


def _extract_trades(transactions: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Extract individual trades from transactions DataFrame.
    
    v1.0.7: Enhanced to handle pyramiding with weighted average entry price.
    Tracks cumulative position and creates trade record only on full position close.
    Handles partial closes proportionally.
    
    v1.0.4 Fixes:
    - Added validation for transaction data
    - Improved error handling for malformed data
    """
    trades = []
    
    # v1.0.7: Track cumulative position with weighted average entry
    current_position = {
        'quantity': 0.0,
        'weighted_avg_price': 0.0,
        'total_cost': 0.0,
        'entry_date': None,
        'direction': None,
    }
    
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
            
            # v1.0.7: Determine if this is opening, adding to, or closing position
            if current_position['quantity'] == 0:
                # Starting a new position
                current_position = {
                    'quantity': abs(amount),
                    'weighted_avg_price': price,
                    'total_cost': abs(amount) * price,
                    'entry_date': date,
                    'direction': 'long' if amount > 0 else 'short',
                }
            elif (current_position['direction'] == 'long' and amount > 0) or \
                 (current_position['direction'] == 'short' and amount < 0):
                # v1.0.7: Adding to position (pyramiding) - update weighted average
                new_quantity = current_position['quantity'] + abs(amount)
                new_total_cost = current_position['total_cost'] + abs(amount) * price
                current_position['weighted_avg_price'] = new_total_cost / new_quantity
                current_position['quantity'] = new_quantity
                current_position['total_cost'] = new_total_cost
            else:
                # Closing or reducing position
                close_quantity = abs(amount)
                
                if close_quantity >= current_position['quantity']:
                    # v1.0.7: Full close - create trade record
                    trades.append({
                        'entry_date': current_position['entry_date'],
                        'entry_price': current_position['weighted_avg_price'],
                        'entry_amount': current_position['quantity'],
                        'exit_date': date,
                        'exit_price': price,
                        'direction': current_position['direction'],
                    })
                    
                    # Check if there's excess that starts a new position
                    excess = close_quantity - current_position['quantity']
                    if excess > 1e-10:
                        # Start new position in opposite direction
                        current_position = {
                            'quantity': excess,
                            'weighted_avg_price': price,
                            'total_cost': excess * price,
                            'entry_date': date,
                            'direction': 'short' if current_position['direction'] == 'long' else 'long',
                        }
                    else:
                        # Reset position
                        current_position = {
                            'quantity': 0.0,
                            'weighted_avg_price': 0.0,
                            'total_cost': 0.0,
                            'entry_date': None,
                            'direction': None,
                        }
                else:
                    # v1.0.7: Partial close - create proportional trade record
                    trades.append({
                        'entry_date': current_position['entry_date'],
                        'entry_price': current_position['weighted_avg_price'],
                        'entry_amount': close_quantity,
                        'exit_date': date,
                        'exit_price': price,
                        'direction': current_position['direction'],
                    })
                    
                    # Reduce position (weighted avg price stays the same)
                    current_position['quantity'] -= close_quantity
                    current_position['total_cost'] = current_position['quantity'] * current_position['weighted_avg_price']
                    
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















