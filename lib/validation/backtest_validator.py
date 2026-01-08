"""
Backtest Validator.

Validates backtest results for consistency and accuracy.
"""

import logging
from typing import Optional, Dict, Any

import numpy as np
import pandas as pd

from .core import ValidationResult, ValidationSeverity
from .config import ValidationConfig
from .base import BaseValidator

logger = logging.getLogger('cockpit.validation')


class BacktestValidator(BaseValidator):
    """
    Validates backtest results for consistency and accuracy.
    
    Checks performed:
    - Metric range validation
    - Return calculation verification
    - Position/transaction consistency
    
    Example:
        >>> validator = BacktestValidator()
        >>> result = validator.validate(backtest_results, returns=returns_series)
        >>> if result.warnings:
        ...     print("Warnings:", result.warnings)
    """

    def _register_checks(self) -> None:
        """Register backtest validation checks."""
        self._check_registry = [
            self._check_metric_ranges,
            self._check_return_consistency,
            self._check_position_consistency,
        ]

    def validate(
        self,
        results: Dict[str, Any],
        returns: Optional[pd.Series] = None,
        transactions: Optional[pd.DataFrame] = None,
        positions: Optional[pd.DataFrame] = None
    ) -> ValidationResult:
        """
        Validate backtest results for consistency.

        Args:
            results: Backtest results dictionary
            returns: Optional returns series
            transactions: Optional transactions DataFrame
            positions: Optional positions DataFrame

        Returns:
            ValidationResult
        """
        result = self._create_result()
        result.add_metadata('result_keys', list(results.keys()))

        # Validate metrics
        metrics = results.get('metrics', results)
        result = self._run_check(result, self._check_metrics, metrics, returns)

        # Validate returns if provided
        if returns is not None:
            result = self._run_check(result, self._check_returns, returns, transactions)

        # Validate positions/transactions if both provided
        if positions is not None and transactions is not None:
            result = self._run_check(
                result, self._check_positions_transactions,
                positions, transactions
            )

        return result

    def _check_metric_ranges(
        self,
        result: ValidationResult,
        metrics: Dict[str, Any],
        returns: Optional[pd.Series]
    ) -> ValidationResult:
        """Wrapper for _check_metrics."""
        return self._check_metrics(result, metrics, returns)

    def _check_return_consistency(
        self,
        result: ValidationResult,
        returns: pd.Series,
        transactions: Optional[pd.DataFrame]
    ) -> ValidationResult:
        """Wrapper for _check_returns."""
        return self._check_returns(result, returns, transactions)

    def _check_position_consistency(
        self,
        result: ValidationResult,
        positions: pd.DataFrame,
        transactions: pd.DataFrame
    ) -> ValidationResult:
        """Wrapper for _check_positions_transactions."""
        return self._check_positions_transactions(result, positions, transactions)

    def _check_metrics(
        self,
        result: ValidationResult,
        metrics: Dict[str, Any],
        returns: Optional[pd.Series]
    ) -> ValidationResult:
        """Validate calculated metrics are within valid ranges."""

        # Sharpe ratio bounds [-10, 10]
        sharpe = metrics.get('sharpe', metrics.get('sharpe_ratio'))
        if sharpe is not None:
            if not -10 <= sharpe <= 10:
                result.add_check(
                    'sharpe_range', False,
                    f"Sharpe ratio {sharpe:.4f} outside expected range [-10, 10]",
                    {'sharpe': sharpe},
                    severity=ValidationSeverity.WARNING
                )
            else:
                result.add_check(
                    'sharpe_range', True,
                    "Sharpe ratio within expected range",
                    {'sharpe': sharpe}
                )

        # Sortino ratio bounds [-10, 10]
        sortino = metrics.get('sortino', metrics.get('sortino_ratio'))
        if sortino is not None:
            if not -10 <= sortino <= 10:
                result.add_check(
                    'sortino_range', False,
                    f"Sortino ratio {sortino:.4f} outside expected range [-10, 10]",
                    {'sortino': sortino},
                    severity=ValidationSeverity.WARNING
                )
            else:
                result.add_check(
                    'sortino_range', True,
                    "Sortino ratio within expected range",
                    {'sortino': sortino}
                )

        # Max drawdown should be <= 0
        max_dd = metrics.get('max_drawdown')
        if max_dd is not None:
            if max_dd > 0:
                result.add_check(
                    'max_drawdown_sign', False,
                    f"Max drawdown {max_dd:.4f} should be <= 0",
                    {'max_drawdown': max_dd}
                )
            else:
                result.add_check(
                    'max_drawdown_sign', True,
                    "Max drawdown has correct sign",
                    {'max_drawdown': max_dd}
                )

        # Verify total return calculation
        if returns is not None and len(returns) > 0:
            calculated = (1 + returns).prod() - 1
            reported = metrics.get('total_return', metrics.get('cumulative_return'))

            if reported is not None:
                discrepancy = abs(calculated - reported)
                if discrepancy > 0.001:
                    result.add_check(
                        'total_return_match', False,
                        f"Total return mismatch: calculated={calculated:.4f}, reported={reported:.4f}",
                        {'calculated': calculated, 'reported': reported, 'discrepancy': discrepancy},
                        severity=ValidationSeverity.WARNING
                    )
                else:
                    result.add_check(
                        'total_return_match', True,
                        "Total return matches calculated value",
                        {'calculated': calculated, 'reported': reported}
                    )

        # Win rate in [0, 1]
        win_rate = metrics.get('win_rate')
        if win_rate is not None:
            if not 0 <= win_rate <= 1:
                result.add_check(
                    'win_rate_range', False,
                    f"Win rate {win_rate:.4f} should be between 0 and 1",
                    {'win_rate': win_rate}
                )
            else:
                result.add_check(
                    'win_rate_range', True,
                    "Win rate within valid range",
                    {'win_rate': win_rate}
                )

        return result

    def _check_returns(
        self,
        result: ValidationResult,
        returns: pd.Series,
        transactions: Optional[pd.DataFrame]
    ) -> ValidationResult:
        """Check returns series."""
        if returns.empty:
            result.add_check('returns_not_empty', False, "Returns series is empty")
            return result

        result.add_check(
            'returns_not_empty', True,
            f"Returns series has {len(returns)} values",
            {'return_count': len(returns)}
        )

        # Check for extreme returns (>50% daily)
        extreme = returns[returns.abs() > 0.5]
        if len(extreme) > 0:
            result.add_check(
                'extreme_returns', False,
                f"Found {len(extreme)} extreme daily returns (>50%)",
                {
                    'count': len(extreme),
                    'max_return': float(returns.max()),
                    'min_return': float(returns.min()),
                    'extreme_dates': [str(d) for d in extreme.index[:5].tolist()]
                },
                severity=ValidationSeverity.WARNING
            )
        else:
            result.add_check(
                'extreme_returns', True,
                "No extreme daily returns"
            )

        # Check for NaN values
        nan_count = int(returns.isna().sum())
        if nan_count > 0:
            result.add_check(
                'returns_no_nan', False,
                f"Found {nan_count} NaN values in returns",
                {'nan_count': nan_count}
            )
        else:
            result.add_check('returns_no_nan', True, "No NaN values in returns")

        # Check for infinite values
        inf_count = int(np.isinf(returns).sum())
        if inf_count > 0:
            result.add_check(
                'returns_no_inf', False,
                f"Found {inf_count} infinite values in returns",
                {'inf_count': inf_count}
            )
        else:
            result.add_check('returns_no_inf', True, "No infinite values in returns")

        return result

    def _check_positions_transactions(
        self,
        result: ValidationResult,
        positions: pd.DataFrame,
        transactions: pd.DataFrame
    ) -> ValidationResult:
        """Check positions are consistent with transactions."""
        if transactions.empty:
            result.add_check('positions_transactions', True, "No transactions to validate")
            return result

        # Check transaction columns
        expected_cols = ['amount', 'price']
        available_cols = [c for c in expected_cols if c in transactions.columns]
        missing_cols = [c for c in expected_cols if c not in transactions.columns]

        if missing_cols:
            result.add_check(
                'transaction_columns', False,
                f"Missing transaction columns: {missing_cols}",
                {'missing_columns': missing_cols, 'available_columns': list(transactions.columns)},
                severity=ValidationSeverity.WARNING
            )
        else:
            result.add_check(
                'transaction_columns', True,
                "Transaction columns present",
                {'columns': available_cols}
            )

        # Check for negative prices
        if 'price' in transactions.columns:
            neg_prices = int((transactions['price'] < 0).sum())
            if neg_prices > 0:
                result.add_check(
                    'transaction_prices', False,
                    f"Found {neg_prices} transactions with negative prices",
                    {'negative_price_count': neg_prices},
                    severity=ValidationSeverity.WARNING
                )
            else:
                result.add_check('transaction_prices', True, "All transaction prices valid")

        return result

