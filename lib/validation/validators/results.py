"""
Backtest results validation and verification functions.

Validates backtest outputs and verifies metric calculations:
- validate_backtest_results(): Full backtest results validation
- verify_metrics_calculation(): Metric sanity checks
- verify_returns_calculation(): Returns data quality checks
- verify_positions_match_transactions(): Position-transaction consistency
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from ..core import ValidationResult
from ..config import ValidationConfig
from ..backtest_validator import BacktestValidator

logger = logging.getLogger('cockpit.validation')


def validate_backtest_results(
    results: Dict[str, Any],
    returns: Optional[pd.Series] = None,
    transactions: Optional[pd.DataFrame] = None,
    positions: Optional[pd.DataFrame] = None,
    config: Optional[ValidationConfig] = None
) -> ValidationResult:
    """
    Validate backtest results.

    Args:
        results: Backtest results dictionary
        returns: Optional returns series
        transactions: Optional transactions DataFrame
        positions: Optional positions DataFrame
        config: Optional ValidationConfig

    Returns:
        ValidationResult
    """
    validator = BacktestValidator(config=config)
    return validator.validate(results, returns, transactions, positions)


def verify_metrics_calculation(
    metrics: Dict[str, Any],
    returns: pd.Series,
    transactions: Optional[pd.DataFrame] = None
) -> Tuple[bool, List[str]]:
    """
    Verify that calculated metrics are within valid ranges.

    Args:
        metrics: Calculated metrics dictionary
        returns: Returns series used for calculation
        transactions: Optional transactions DataFrame

    Returns:
        Tuple of (is_valid, list of discrepancies)
    """
    discrepancies: List[str] = []

    # Sharpe ratio bounds
    sharpe = metrics.get('sharpe', metrics.get('sharpe_ratio'))
    if sharpe is not None and not -10 <= sharpe <= 10:
        discrepancies.append(f"Sharpe ratio {sharpe} outside expected range [-10, 10]")

    # Sortino ratio bounds
    sortino = metrics.get('sortino', metrics.get('sortino_ratio'))
    if sortino is not None and not -10 <= sortino <= 10:
        discrepancies.append(f"Sortino ratio {sortino} outside expected range [-10, 10]")

    # Max drawdown sign
    max_dd = metrics.get('max_drawdown')
    if max_dd is not None and max_dd > 0:
        discrepancies.append(f"Max drawdown {max_dd} should be <= 0")

    # Total return consistency
    if 'total_return' in metrics and len(returns) > 0:
        calculated = (1 + returns).prod() - 1
        reported = metrics['total_return']
        if abs(calculated - reported) > 0.001:
            discrepancies.append(
                f"Total return mismatch: calculated={calculated:.4f}, "
                f"reported={reported:.4f}"
            )

    # Win rate bounds
    win_rate = metrics.get('win_rate')
    if win_rate is not None and not 0 <= win_rate <= 1:
        discrepancies.append(f"Win rate {win_rate} should be between 0 and 1")

    return len(discrepancies) == 0, discrepancies


def verify_returns_calculation(
    returns: pd.Series,
    transactions: pd.DataFrame
) -> Tuple[bool, Optional[str]]:
    """
    Verify returns are consistent with transactions.

    Args:
        returns: Returns series
        transactions: Transactions DataFrame

    Returns:
        Tuple of (is_valid, error_message)
    """
    if returns.empty:
        return True, None

    # Check for extreme returns
    extreme = returns[returns.abs() > 0.5]
    if len(extreme) > 0:
        return False, f"Found {len(extreme)} extreme daily returns (>50%)"

    # Check for NaN values
    nan_count = returns.isna().sum()
    if nan_count > 0:
        return False, f"Found {nan_count} NaN values in returns"

    # Check for infinite values
    inf_count = np.isinf(returns).sum()
    if inf_count > 0:
        return False, f"Found {inf_count} infinite values in returns"

    return True, None


def verify_positions_match_transactions(
    positions_df: pd.DataFrame,
    transactions_df: pd.DataFrame
) -> Tuple[bool, Optional[str]]:
    """
    Verify that positions are consistent with transactions.

    Args:
        positions_df: Positions DataFrame
        transactions_df: Transactions DataFrame

    Returns:
        Tuple of (is_valid, error_message)
    """
    if transactions_df.empty:
        return True, None

    # Check transaction columns
    expected_cols = ['amount', 'price']
    missing_cols = [c for c in expected_cols if c not in transactions_df.columns]
    if missing_cols:
        return False, f"Missing transaction columns: {missing_cols}"

    # Check for negative prices
    if 'price' in transactions_df.columns:
        neg_prices = (transactions_df['price'] < 0).sum()
        if neg_prices > 0:
            return False, f"Found {neg_prices} transactions with negative prices"

    return True, None
