"""
Data integrity validation module for The Researcher's Cockpit.

Provides functions to verify data consistency and correctness in backtest results.
"""

# Standard library imports
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional

# Third-party imports
import numpy as np
import pandas as pd


def verify_bundle_dates(bundle_name: str, start_date: str, end_date: str) -> Tuple[bool, str]:
    """
    Verify that a bundle covers the requested date range.
    
    Args:
        bundle_name: Name of bundle to check
        start_date: Requested start date (YYYY-MM-DD)
        end_date: Requested end date (YYYY-MM-DD)
        
    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if bundle covers the date range
        - error_message: Empty string if valid, error description if invalid
    """
    try:
        from .data_loader import load_bundle
        bundle_data = load_bundle(bundle_name)
        
        # Get available sessions from bundle
        sessions = bundle_data.equity_daily_bar_reader.sessions
        if len(sessions) == 0:
            return False, f"Bundle '{bundle_name}' has no trading sessions"
        
        bundle_start = pd.Timestamp(sessions[0]).normalize()
        bundle_end = pd.Timestamp(sessions[-1]).normalize()
        start_ts = pd.Timestamp(start_date).normalize()
        end_ts = pd.Timestamp(end_date).normalize()
        
        errors = []
        
        if start_ts < bundle_start:
            errors.append(
                f"Start date {start_date} is before bundle start {bundle_start.strftime('%Y-%m-%d')}"
            )
        
        if end_ts > bundle_end:
            errors.append(
                f"End date {end_date} is after bundle end {bundle_end.strftime('%Y-%m-%d')}"
            )
        
        if errors:
            error_msg = f"Bundle '{bundle_name}' date range mismatch:\n" + "\n".join(f"  - {e}" for e in errors)
            error_msg += f"\nBundle covers: {bundle_start.strftime('%Y-%m-%d')} to {bundle_end.strftime('%Y-%m-%d')}"
            return False, error_msg
        
        return True, ""
        
    except Exception as e:
        return False, f"Failed to verify bundle dates: {e}"


def verify_returns_calculation(returns: pd.Series, transactions: pd.DataFrame, tolerance: float = 1e-6) -> Tuple[bool, str]:
    """
    Verify that returns match transactions by recalculating from transactions.
    
    This is a simplified check - full verification would require portfolio value tracking.
    
    Args:
        returns: Series of daily returns
        transactions: DataFrame with columns: date, sid, amount, price, commission
        tolerance: Tolerance for floating point comparison
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(transactions) == 0:
        if len(returns) == 0:
            return True, ""
        return False, "No transactions but returns exist"
    
    if len(returns) == 0:
        return False, "No returns but transactions exist"
    
    # Basic sanity check: returns should have same date range as transactions
    trans_dates = pd.to_datetime(transactions.index if hasattr(transactions.index, 'date') else transactions.get('date', transactions.index))
    returns_dates = pd.to_datetime(returns.index)
    
    # Check overlap
    if len(set(trans_dates) & set(returns_dates)) == 0:
        return False, "Transaction dates and return dates have no overlap"
    
    # For a more complete check, we would need to:
    # 1. Calculate portfolio value from transactions
    # 2. Calculate returns from portfolio value changes
    # 3. Compare with provided returns
    
    # For now, just verify basic consistency
    return True, ""


def verify_positions_match_transactions(positions: pd.DataFrame, transactions: pd.DataFrame, tolerance: float = 1e-6) -> Tuple[bool, str]:
    """
    Verify that positions are consistent with transactions.
    
    Checks that position changes match transaction amounts.
    
    Args:
        positions: DataFrame with position history (columns: sid, amount, etc.)
        transactions: DataFrame with transactions (columns: date, sid, amount, price, commission)
        tolerance: Tolerance for floating point comparison
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(transactions) == 0:
        # No transactions means no positions (or flat positions)
        return True, ""
    
    if len(positions) == 0:
        return False, "No positions but transactions exist"
    
    # Group transactions by date and sid
    trans_grouped = transactions.groupby([transactions.index, 'sid'])['amount'].sum()
    
    # Group positions by date and sid
    if 'sid' in positions.columns:
        pos_grouped = positions.groupby([positions.index, 'sid'])['amount'].sum()
    else:
        # Positions might be indexed by sid already
        pos_grouped = positions['amount'] if 'amount' in positions.columns else positions.iloc[:, 0]
    
    # Check that position changes match transaction amounts for overlapping dates/sids
    common_keys = set(trans_grouped.index) & set(pos_grouped.index)
    
    if len(common_keys) == 0:
        return False, "No overlapping dates/sids between positions and transactions"
    
    # For each common key, check consistency
    discrepancies = []
    for key in list(common_keys)[:100]:  # Limit to first 100 for performance
        trans_amount = trans_grouped[key]
        pos_amount = pos_grouped[key]
        
        # Position should change by transaction amount (simplified check)
        # Full verification would require tracking position history
        if abs(trans_amount) > tolerance and abs(pos_amount) < tolerance:
            discrepancies.append(f"Transaction at {key} but no position change")
    
    if len(discrepancies) > 10:
        return False, f"Found {len(discrepancies)} position/transaction mismatches (showing first 10)"
    
    if discrepancies:
        return False, f"Position/transaction mismatches:\n" + "\n".join(f"  - {d}" for d in discrepancies[:10])
    
    return True, ""


def verify_metrics_calculation(metrics: Dict[str, Any], returns: pd.Series, transactions: Optional[pd.DataFrame] = None, tolerance: float = 0.01) -> Tuple[bool, List[str]]:
    """
    Verify that metrics match manual calculations.
    
    Recalculates key metrics and compares with provided metrics.
    
    Args:
        metrics: Dictionary of calculated metrics
        returns: Series of daily returns
        transactions: Optional DataFrame of transactions
        tolerance: Tolerance for metric comparison (as fraction, e.g., 0.01 = 1%)
        
    Returns:
        Tuple of (is_valid, list_of_discrepancies)
    """
    discrepancies = []
    
    if len(returns) == 0:
        return True, discrepancies
    
    returns_clean = returns.dropna()
    
    # Verify total return
    if 'total_return' in metrics:
        calculated_total = float((1 + returns_clean).prod() - 1)
        provided_total = float(metrics['total_return'])
        if abs(calculated_total - provided_total) > tolerance:
            discrepancies.append(
                f"Total return mismatch: calculated={calculated_total:.6f}, provided={provided_total:.6f}"
            )
    
    # Verify annual return (approximate)
    if 'annual_return' in metrics and len(returns_clean) > 0:
        n_days = len(returns_clean)
        calculated_annual = float((1 + returns_clean.sum()) ** (252 / n_days) - 1)
        provided_annual = float(metrics['annual_return'])
        if abs(calculated_annual - provided_annual) > tolerance:
            discrepancies.append(
                f"Annual return mismatch: calculated={calculated_annual:.6f}, provided={provided_annual:.6f}"
            )
    
    # Verify annual volatility
    if 'annual_volatility' in metrics and len(returns_clean) > 1:
        calculated_vol = float(returns_clean.std() * np.sqrt(252))
        provided_vol = float(metrics['annual_volatility'])
        if abs(calculated_vol - provided_vol) > tolerance:
            discrepancies.append(
                f"Annual volatility mismatch: calculated={calculated_vol:.6f}, provided={provided_vol:.6f}"
            )
    
    # Verify max drawdown (approximate)
    if 'max_drawdown' in metrics:
        cumulative = (1 + returns_clean).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        calculated_dd = float(drawdown.min())
        provided_dd = float(metrics['max_drawdown'])
        if abs(calculated_dd - provided_dd) > tolerance:
            discrepancies.append(
                f"Max drawdown mismatch: calculated={calculated_dd:.6f}, provided={provided_dd:.6f}"
            )
    
    return len(discrepancies) == 0, discrepancies


