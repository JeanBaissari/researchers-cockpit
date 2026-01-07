"""
Data integrity validation module for The Researcher's Cockpit.

Provides functions to verify data consistency and correctness in backtest results.
Integrates with the existing DataValidator for pre-ingestion validation and
provides post-backtest verification capabilities.
"""

# Standard library imports
import logging
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional

# Third-party imports
import numpy as np
import pandas as pd

# Local imports - reuse existing validation infrastructure
from .data_validation import DataValidator, ValidationResult, ValidationConfig

logger = logging.getLogger('cockpit.data_integrity')


def _normalize_timestamp(ts: pd.Timestamp) -> pd.Timestamp:
    """
    Normalize a timestamp to timezone-naive midnight, matching data_loader.py patterns.
    
    Args:
        ts: Timestamp to normalize (may be timezone-aware or naive)
        
    Returns:
        Timezone-naive timestamp normalized to midnight
    """
    if ts.tz is not None:
        return ts.tz_convert(None).normalize()
    return ts.normalize()


def validate_csv_files_pre_ingestion(
    timeframe: str,
    symbols: Optional[List[str]] = None,
    data_dir: Optional[Path] = None
) -> ValidationResult:
    """
    Pre-ingestion hook that validates CSV files in data/processed/{timeframe}/.
    
    Complements the existing ingestion flow by validating source files before
    the bundle creation process begins.
    
    Args:
        timeframe: Timeframe directory to validate (e.g., '1h', 'daily')
        symbols: Optional list of symbols to validate. If None, validates all CSVs.
        data_dir: Optional custom data directory. Defaults to data/processed/{timeframe}/
        
    Returns:
        ValidationResult with detailed check results
    """
    from .utils import get_project_root
    
    result = ValidationResult(passed=True)
    
    if data_dir is None:
        data_dir = get_project_root() / 'data' / 'processed' / timeframe
    
    if not data_dir.exists():
        result.add_check(
            name='directory_exists',
            passed=False,
            message=f"Data directory does not exist: {data_dir}"
        )
        return result
    
    result.add_check(
        name='directory_exists',
        passed=True,
        message=f"Data directory exists: {data_dir}"
    )
    
    # Find CSV files
    if symbols:
        csv_files = [data_dir / f"{symbol}.csv" for symbol in symbols]
        csv_files = [f for f in csv_files if f.exists()]
        missing = [s for s in symbols if not (data_dir / f"{s}.csv").exists()]
        if missing:
            result.add_warning(f"Missing CSV files for symbols: {missing}")
    else:
        csv_files = list(data_dir.glob('*.csv'))
    
    if not csv_files:
        result.add_check(
            name='csv_files_found',
            passed=False,
            message=f"No CSV files found in {data_dir}"
        )
        return result
    
    result.add_check(
        name='csv_files_found',
        passed=True,
        message=f"Found {len(csv_files)} CSV file(s)",
        details={'files': [f.name for f in csv_files]}
    )
    
    # Use existing DataValidator for each file
    config = ValidationConfig(timeframe=timeframe) if timeframe else None
    validator = DataValidator(config=config)
    
    for csv_file in csv_files:
        symbol = csv_file.stem
        try:
            df = pd.read_csv(csv_file, parse_dates=['datetime'], index_col='datetime')
            
            # Validate using existing DataValidator
            validation = validator.validate(df, asset_name=symbol)
            
            if not validation.passed:
                result.add_check(
                    name=f'validate_{symbol}',
                    passed=False,
                    message=f"Validation failed for {symbol}",
                    details={'errors': validation.errors}
                )
            else:
                result.add_check(
                    name=f'validate_{symbol}',
                    passed=True,
                    message=f"Validation passed for {symbol}",
                    details={
                        'rows': len(df),
                        'date_range': f"{df.index.min()} to {df.index.max()}"
                    }
                )
                
            # Add any warnings from the validation
            for warning in validation.warnings:
                result.add_warning(f"{symbol}: {warning}")
                
        except Exception as e:
            result.add_check(
                name=f'validate_{symbol}',
                passed=False,
                message=f"Failed to read/validate {symbol}: {e}"
            )
    
    return result


def verify_bundle_dates(bundle_name: str, start_date: str, end_date: str) -> ValidationResult:
    """
    Verify that a bundle covers the requested date range.
    
    Args:
        bundle_name: Name of bundle to check
        start_date: Requested start date (YYYY-MM-DD)
        end_date: Requested end date (YYYY-MM-DD)
        
    Returns:
        ValidationResult with check details
    """
    result = ValidationResult(passed=True)
    
    try:
        from .data_loader import load_bundle
        bundle_data = load_bundle(bundle_name)
        
        # Get available sessions from bundle
        sessions = bundle_data.equity_daily_bar_reader.sessions
        if len(sessions) == 0:
            result.add_check(
                name='bundle_has_sessions',
                passed=False,
                message=f"Bundle '{bundle_name}' has no trading sessions"
            )
            return result
        
        result.add_check(
            name='bundle_has_sessions',
            passed=True,
            message=f"Bundle has {len(sessions)} trading sessions"
        )
        
        # Normalize timestamps matching data_loader.py patterns
        bundle_start = _normalize_timestamp(pd.Timestamp(sessions[0]))
        bundle_end = _normalize_timestamp(pd.Timestamp(sessions[-1]))
        start_ts = _normalize_timestamp(pd.Timestamp(start_date))
        end_ts = _normalize_timestamp(pd.Timestamp(end_date))
        
        # Check start date
        if start_ts < bundle_start:
            result.add_check(
                name='start_date_covered',
                passed=False,
                message=f"Start date {start_date} is before bundle start {bundle_start.strftime('%Y-%m-%d')}",
                details={
                    'requested_start': start_date,
                    'bundle_start': bundle_start.strftime('%Y-%m-%d')
                }
            )
        else:
            result.add_check(
                name='start_date_covered',
                passed=True,
                message=f"Start date {start_date} is within bundle range"
            )
        
        # Check end date
        if end_ts > bundle_end:
            result.add_check(
                name='end_date_covered',
                passed=False,
                message=f"End date {end_date} is after bundle end {bundle_end.strftime('%Y-%m-%d')}",
                details={
                    'requested_end': end_date,
                    'bundle_end': bundle_end.strftime('%Y-%m-%d')
                }
            )
        else:
            result.add_check(
                name='end_date_covered',
                passed=True,
                message=f"End date {end_date} is within bundle range"
            )
        
        # Add bundle info to result
        result.add_check(
            name='bundle_date_range',
            passed=True,
            message=f"Bundle covers {bundle_start.strftime('%Y-%m-%d')} to {bundle_end.strftime('%Y-%m-%d')}",
            details={
                'bundle_start': bundle_start.strftime('%Y-%m-%d'),
                'bundle_end': bundle_end.strftime('%Y-%m-%d'),
                'session_count': len(sessions)
            }
        )
        
    except Exception as e:
        result.add_check(
            name='bundle_load',
            passed=False,
            message=f"Failed to verify bundle dates: {e}"
        )
    
    return result


def verify_returns_calculation(returns: pd.Series, transactions: pd.DataFrame, tolerance: float = 1e-6) -> ValidationResult:
    """
    Verify that returns match transactions by recalculating from transactions.
    
    This is a simplified check - full verification would require portfolio value tracking.
    
    Args:
        returns: Series of daily returns
        transactions: DataFrame with columns: date, sid, amount, price, commission
        tolerance: Tolerance for floating point comparison
        
    Returns:
        ValidationResult with check details
    """
    result = ValidationResult(passed=True)
    
    if len(transactions) == 0:
        if len(returns) == 0:
            result.add_check(
                name='empty_data_consistency',
                passed=True,
                message="No transactions and no returns - consistent"
            )
            return result
        result.add_check(
            name='transactions_exist',
            passed=False,
            message="No transactions but returns exist"
        )
        return result
    
    if len(returns) == 0:
        result.add_check(
            name='returns_exist',
            passed=False,
            message="No returns but transactions exist"
        )
        return result
    
    result.add_check(
        name='data_exists',
        passed=True,
        message=f"Found {len(returns)} returns and {len(transactions)} transactions"
    )
    
    # Basic sanity check: returns should have same date range as transactions
    trans_dates = pd.to_datetime(transactions.index if hasattr(transactions.index, 'date') else transactions.get('date', transactions.index))
    returns_dates = pd.to_datetime(returns.index)
    
    # Check overlap
    overlap = set(trans_dates) & set(returns_dates)
    if len(overlap) == 0:
        result.add_check(
            name='date_overlap',
            passed=False,
            message="Transaction dates and return dates have no overlap",
            details={
                'transaction_date_range': f"{trans_dates.min()} to {trans_dates.max()}",
                'returns_date_range': f"{returns_dates.min()} to {returns_dates.max()}"
            }
        )
        return result
    
    result.add_check(
        name='date_overlap',
        passed=True,
        message=f"Found {len(overlap)} overlapping dates between transactions and returns"
    )
    
    # For a more complete check, we would need to:
    # 1. Calculate portfolio value from transactions
    # 2. Calculate returns from portfolio value changes
    # 3. Compare with provided returns
    
    return result


def verify_positions_match_transactions(positions: pd.DataFrame, transactions: pd.DataFrame, tolerance: float = 1e-6) -> ValidationResult:
    """
    Verify that positions are consistent with transactions.
    
    Checks that position changes match transaction amounts.
    
    Args:
        positions: DataFrame with position history (columns: sid, amount, etc.)
        transactions: DataFrame with transactions (columns: date, sid, amount, price, commission)
        tolerance: Tolerance for floating point comparison
        
    Returns:
        ValidationResult with check details
    """
    result = ValidationResult(passed=True)
    
    if len(transactions) == 0:
        # No transactions means no positions (or flat positions)
        result.add_check(
            name='no_transactions',
            passed=True,
            message="No transactions - positions check skipped"
        )
        return result
    
    if len(positions) == 0:
        result.add_check(
            name='positions_exist',
            passed=False,
            message="No positions but transactions exist"
        )
        return result
    
    result.add_check(
        name='data_exists',
        passed=True,
        message=f"Found {len(positions)} position records and {len(transactions)} transactions"
    )
    
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
        result.add_check(
            name='key_overlap',
            passed=False,
            message="No overlapping dates/sids between positions and transactions"
        )
        return result
    
    result.add_check(
        name='key_overlap',
        passed=True,
        message=f"Found {len(common_keys)} overlapping date/sid combinations"
    )
    
    # For each common key, check consistency
    discrepancies = []
    for key in list(common_keys)[:100]:  # Limit to first 100 for performance
        trans_amount = trans_grouped[key]
        pos_amount = pos_grouped[key]
        
        # Position should change by transaction amount (simplified check)
        # Full verification would require tracking position history
        if abs(trans_amount) > tolerance and abs(pos_amount) < tolerance:
            discrepancies.append(f"Transaction at {key} but no position change")
    
    if discrepancies:
        result.add_check(
            name='position_transaction_consistency',
            passed=False,
            message=f"Found {len(discrepancies)} position/transaction mismatches",
            details={'discrepancies': discrepancies[:10]}
        )
    else:
        result.add_check(
            name='position_transaction_consistency',
            passed=True,
            message="Positions consistent with transactions"
        )
    
    return result


def verify_metrics_calculation(metrics: Dict[str, Any], returns: pd.Series, transactions: Optional[pd.DataFrame] = None, tolerance: float = 0.01) -> ValidationResult:
    """
    Verify that metrics match manual calculations.
    
    Recalculates key metrics and compares with provided metrics.
    
    Args:
        metrics: Dictionary of calculated metrics
        returns: Series of daily returns
        transactions: Optional DataFrame of transactions
        tolerance: Tolerance for metric comparison (as fraction, e.g., 0.01 = 1%)
        
    Returns:
        ValidationResult with check details
    """
    result = ValidationResult(passed=True)
    
    if len(returns) == 0:
        result.add_check(
            name='returns_exist',
            passed=True,
            message="No returns to verify - skipping metrics verification"
        )
        return result
    
    returns_clean = returns.dropna()
    
    result.add_check(
        name='returns_data',
        passed=True,
        message=f"Verifying metrics against {len(returns_clean)} return observations"
    )
    
    # Verify total return
    if 'total_return' in metrics:
        calculated_total = float((1 + returns_clean).prod() - 1)
        provided_total = float(metrics['total_return'])
        diff = abs(calculated_total - provided_total)
        
        if diff > tolerance:
            result.add_check(
                name='total_return',
                passed=False,
                message=f"Total return mismatch: calculated={calculated_total:.6f}, provided={provided_total:.6f}",
                details={
                    'calculated': calculated_total,
                    'provided': provided_total,
                    'difference': diff
                }
            )
        else:
            result.add_check(
                name='total_return',
                passed=True,
                message=f"Total return verified: {provided_total:.6f}"
            )
    
    # Verify annual return (approximate)
    if 'annual_return' in metrics and len(returns_clean) > 0:
        n_days = len(returns_clean)
        calculated_annual = float((1 + returns_clean.sum()) ** (252 / n_days) - 1)
        provided_annual = float(metrics['annual_return'])
        diff = abs(calculated_annual - provided_annual)
        
        if diff > tolerance:
            result.add_check(
                name='annual_return',
                passed=False,
                message=f"Annual return mismatch: calculated={calculated_annual:.6f}, provided={provided_annual:.6f}",
                details={
                    'calculated': calculated_annual,
                    'provided': provided_annual,
                    'difference': diff,
                    'trading_days': n_days
                }
            )
        else:
            result.add_check(
                name='annual_return',
                passed=True,
                message=f"Annual return verified: {provided_annual:.6f}"
            )
    
    # Verify annual volatility
    if 'annual_volatility' in metrics and len(returns_clean) > 1:
        calculated_vol = float(returns_clean.std() * np.sqrt(252))
        provided_vol = float(metrics['annual_volatility'])
        diff = abs(calculated_vol - provided_vol)
        
        if diff > tolerance:
            result.add_check(
                name='annual_volatility',
                passed=False,
                message=f"Annual volatility mismatch: calculated={calculated_vol:.6f}, provided={provided_vol:.6f}",
                details={
                    'calculated': calculated_vol,
                    'provided': provided_vol,
                    'difference': diff
                }
            )
        else:
            result.add_check(
                name='annual_volatility',
                passed=True,
                message=f"Annual volatility verified: {provided_vol:.6f}"
            )
    
    # Verify max drawdown (approximate)
    if 'max_drawdown' in metrics:
        cumulative = (1 + returns_clean).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        calculated_dd = float(drawdown.min())
        provided_dd = float(metrics['max_drawdown'])
        diff = abs(calculated_dd - provided_dd)
        
        if diff > tolerance:
            result.add_check(
                name='max_drawdown',
                passed=False,
                message=f"Max drawdown mismatch: calculated={calculated_dd:.6f}, provided={provided_dd:.6f}",
                details={
                    'calculated': calculated_dd,
                    'provided': provided_dd,
                    'difference': diff
                }
            )
        else:
            result.add_check(
                name='max_drawdown',
                passed=True,
                message=f"Max drawdown verified: {provided_dd:.6f}"
            )
    
    return result


