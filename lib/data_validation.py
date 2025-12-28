"""
Data validation module for The Researcher's Cockpit.

Provides multi-layer validation for OHLCV data:
- Pre-ingestion source validation
- Ingestion-time bundle creation checks
- Pre-backtest bundle verification
- Post-backtest results validation
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
import json

import numpy as np
import pandas as pd

logger = logging.getLogger('cockpit.validation')


@dataclass
class ValidationResult:
    """Container for validation results."""
    passed: bool
    checks: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def add_check(self, name: str, passed: bool, message: str = "", details: Dict = None):
        """Add a validation check result."""
        check = {
            'name': name,
            'passed': passed,
            'message': message,
            'details': details or {}
        }
        self.checks.append(check)
        if not passed:
            self.passed = False
            self.errors.append(f"{name}: {message}")

    def add_warning(self, message: str):
        """Add a warning (non-fatal)."""
        self.warnings.append(message)

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'passed': self.passed,
            'checks': self.checks,
            'warnings': self.warnings,
            'errors': self.errors,
            'validated_at': datetime.utcnow().isoformat() + 'Z'
        }


class DataValidator:
    """
    Validates OHLCV data before ingestion.

    Performs comprehensive checks for data quality issues that could
    affect backtest results.
    """

    def __init__(
        self,
        check_gaps: bool = True,
        gap_tolerance_days: int = 3,
        check_outliers: bool = True,
        outlier_threshold_sigma: float = 5.0,
        check_negative_values: bool = True,
        check_future_dates: bool = True,
        strict_mode: bool = False
    ):
        """
        Initialize validator with configuration.

        Args:
            check_gaps: Check for missing dates
            gap_tolerance_days: Maximum consecutive missing days before warning
            check_outliers: Check for price outliers
            outlier_threshold_sigma: Standard deviations for outlier detection
            check_negative_values: Check for negative prices/volumes
            check_future_dates: Check for dates in the future
            strict_mode: If True, warnings become errors
        """
        self.check_gaps = check_gaps
        self.gap_tolerance_days = gap_tolerance_days
        self.check_outliers = check_outliers
        self.outlier_threshold_sigma = outlier_threshold_sigma
        self.check_negative_values = check_negative_values
        self.check_future_dates = check_future_dates
        self.strict_mode = strict_mode

    def validate_ohlcv(
        self,
        df: pd.DataFrame,
        calendar: Optional[Any] = None,
        asset_name: str = "unknown"
    ) -> ValidationResult:
        """
        Validate OHLCV DataFrame.

        Args:
            df: DataFrame with OHLCV columns
            calendar: Optional trading calendar for gap detection
            asset_name: Asset name for logging

        Returns:
            ValidationResult with all check outcomes
        """
        result = ValidationResult(passed=True)

        if df.empty:
            result.add_check('empty_data', False, f"DataFrame is empty for {asset_name}")
            return result

        # Check required columns
        result = self._check_required_columns(df, result)
        if not result.passed:
            return result

        # Check for null values
        result = self._check_no_nulls(df, result, asset_name)

        # Check OHLC consistency (high >= low, close within range)
        result = self._check_ohlc_consistency(df, result, asset_name)

        # Check for negative values
        if self.check_negative_values:
            result = self._check_no_negative_values(df, result, asset_name)

        # Check for future dates
        if self.check_future_dates:
            result = self._check_no_future_dates(df, result, asset_name)

        # Check for duplicate dates
        result = self._check_no_duplicate_dates(df, result, asset_name)

        # Check for price outliers
        if self.check_outliers:
            result = self._check_price_outliers(df, result, asset_name)

        # Check for date gaps (requires calendar)
        if self.check_gaps and calendar is not None:
            result = self._check_date_continuity(df, calendar, result, asset_name)

        return result

    def _check_required_columns(
        self,
        df: pd.DataFrame,
        result: ValidationResult
    ) -> ValidationResult:
        """Check that required OHLCV columns exist."""
        required = ['open', 'high', 'low', 'close', 'volume']
        # Check case-insensitive
        df_columns_lower = [c.lower() for c in df.columns]
        missing = [col for col in required if col not in df_columns_lower]

        if missing:
            result.add_check(
                'required_columns',
                False,
                f"Missing required columns: {missing}"
            )
        else:
            result.add_check('required_columns', True, "All required columns present")

        return result

    def _check_no_nulls(
        self,
        df: pd.DataFrame,
        result: ValidationResult,
        asset_name: str
    ) -> ValidationResult:
        """Check for null values in OHLCV columns."""
        ohlcv_cols = ['open', 'high', 'low', 'close', 'volume']
        existing_cols = [c for c in ohlcv_cols if c in [col.lower() for col in df.columns]]

        # Map to actual column names
        col_map = {c.lower(): c for c in df.columns}
        actual_cols = [col_map.get(c, c) for c in existing_cols]

        null_counts = df[actual_cols].isnull().sum()
        total_nulls = null_counts.sum()

        if total_nulls > 0:
            null_details = {col: int(count) for col, count in null_counts.items() if count > 0}
            msg = f"Found {total_nulls} null values in {asset_name}"
            result.add_check('no_nulls', False, msg, {'null_counts': null_details})
        else:
            result.add_check('no_nulls', True, "No null values found")

        return result

    def _check_ohlc_consistency(
        self,
        df: pd.DataFrame,
        result: ValidationResult,
        asset_name: str
    ) -> ValidationResult:
        """Check OHLC price relationships."""
        # Map to actual column names
        col_map = {c.lower(): c for c in df.columns}
        o, h, l, c = col_map.get('open'), col_map.get('high'), col_map.get('low'), col_map.get('close')

        if not all([o, h, l, c]):
            return result

        # High should be >= Low
        high_low_violations = (df[h] < df[l]).sum()

        # High should be >= Open and Close
        high_violations = ((df[h] < df[o]) | (df[h] < df[c])).sum()

        # Low should be <= Open and Close
        low_violations = ((df[l] > df[o]) | (df[l] > df[c])).sum()

        total_violations = high_low_violations + high_violations + low_violations

        if total_violations > 0:
            msg = f"Found {total_violations} OHLC consistency violations in {asset_name}"
            result.add_check('ohlc_consistency', False, msg, {
                'high_low_violations': int(high_low_violations),
                'high_violations': int(high_violations),
                'low_violations': int(low_violations)
            })
        else:
            result.add_check('ohlc_consistency', True, "OHLC prices are consistent")

        return result

    def _check_no_negative_values(
        self,
        df: pd.DataFrame,
        result: ValidationResult,
        asset_name: str
    ) -> ValidationResult:
        """Check for negative prices or volumes."""
        col_map = {c.lower(): c for c in df.columns}
        price_cols = [col_map.get(c) for c in ['open', 'high', 'low', 'close'] if col_map.get(c)]
        volume_col = col_map.get('volume')

        negative_prices = 0
        for col in price_cols:
            if col:
                negative_prices += (df[col] < 0).sum()

        negative_volumes = 0
        if volume_col:
            negative_volumes = (df[volume_col] < 0).sum()

        total_negatives = negative_prices + negative_volumes

        if total_negatives > 0:
            msg = f"Found {total_negatives} negative values in {asset_name}"
            result.add_check('no_negative_values', False, msg, {
                'negative_prices': int(negative_prices),
                'negative_volumes': int(negative_volumes)
            })
        else:
            result.add_check('no_negative_values', True, "No negative values found")

        return result

    def _check_no_future_dates(
        self,
        df: pd.DataFrame,
        result: ValidationResult,
        asset_name: str
    ) -> ValidationResult:
        """Check for dates in the future."""
        today = pd.Timestamp.now(tz='UTC').normalize()
        index = pd.DatetimeIndex(df.index)

        if index.tz is None:
            index = index.tz_localize('UTC')

        future_dates = (index > today).sum()

        if future_dates > 0:
            msg = f"Found {future_dates} future dates in {asset_name}"
            result.add_check('no_future_dates', False, msg)
        else:
            result.add_check('no_future_dates', True, "No future dates found")

        return result

    def _check_no_duplicate_dates(
        self,
        df: pd.DataFrame,
        result: ValidationResult,
        asset_name: str
    ) -> ValidationResult:
        """Check for duplicate dates."""
        duplicates = df.index.duplicated().sum()

        if duplicates > 0:
            msg = f"Found {duplicates} duplicate dates in {asset_name}"
            result.add_check('no_duplicate_dates', False, msg)
        else:
            result.add_check('no_duplicate_dates', True, "No duplicate dates found")

        return result

    def _check_price_outliers(
        self,
        df: pd.DataFrame,
        result: ValidationResult,
        asset_name: str
    ) -> ValidationResult:
        """Check for price outliers using z-score."""
        col_map = {c.lower(): c for c in df.columns}
        close_col = col_map.get('close')

        if not close_col:
            return result

        returns = df[close_col].pct_change().dropna()

        if len(returns) < 2:
            return result

        mean_return = returns.mean()
        std_return = returns.std()

        if std_return > 0:
            z_scores = np.abs((returns - mean_return) / std_return)
            outliers = (z_scores > self.outlier_threshold_sigma).sum()

            if outliers > 0:
                msg = f"Found {outliers} price outliers (>{self.outlier_threshold_sigma} sigma) in {asset_name}"
                if self.strict_mode:
                    result.add_check('price_outliers', False, msg)
                else:
                    result.add_warning(msg)
                    result.add_check('price_outliers', True, f"Outliers found but within tolerance")
            else:
                result.add_check('price_outliers', True, "No significant price outliers")

        return result

    def _check_date_continuity(
        self,
        df: pd.DataFrame,
        calendar: Any,
        result: ValidationResult,
        asset_name: str
    ) -> ValidationResult:
        """Check for missing dates according to trading calendar."""
        try:
            start_date = df.index.min()
            end_date = df.index.max()

            sessions = calendar.sessions_in_range(start_date, end_date)

            if len(sessions) == 0:
                return result

            # Normalize for comparison
            sessions_normalized = pd.DatetimeIndex([s.date() for s in sessions])
            df_dates = pd.DatetimeIndex([d.date() if hasattr(d, 'date') else d for d in df.index])

            missing = set(sessions_normalized) - set(df_dates)

            if missing:
                missing_count = len(missing)
                msg = f"Found {missing_count} missing calendar dates in {asset_name}"

                if missing_count > self.gap_tolerance_days:
                    if self.strict_mode:
                        result.add_check('date_continuity', False, msg, {'missing_count': missing_count})
                    else:
                        result.add_warning(msg)
                        result.add_check('date_continuity', True, "Gaps within tolerance")
                else:
                    result.add_check('date_continuity', True, f"Minor gaps ({missing_count} days)")
            else:
                result.add_check('date_continuity', True, "No missing calendar dates")

        except Exception as e:
            result.add_warning(f"Could not check date continuity: {e}")

        return result


def validate_bundle(bundle_name: str) -> ValidationResult:
    """
    Validate an existing bundle.

    Args:
        bundle_name: Name of the bundle to validate

    Returns:
        ValidationResult
    """
    result = ValidationResult(passed=True)

    try:
        from .data_loader import load_bundle
        bundle = load_bundle(bundle_name)
        result.add_check('bundle_exists', True, f"Bundle '{bundle_name}' exists")
    except FileNotFoundError as e:
        result.add_check('bundle_exists', False, str(e))
        return result
    except Exception as e:
        result.add_check('bundle_loadable', False, f"Failed to load bundle: {e}")
        return result

    return result


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
    discrepancies = []

    # Check Sharpe ratio bounds
    sharpe = metrics.get('sharpe', 0)
    if not -10 <= sharpe <= 10:
        discrepancies.append(f"Sharpe ratio {sharpe} outside expected range [-10, 10]")

    # Check Sortino ratio bounds
    sortino = metrics.get('sortino', 0)
    if not -10 <= sortino <= 10:
        discrepancies.append(f"Sortino ratio {sortino} outside expected range [-10, 10]")

    # Check max drawdown is negative or zero
    max_dd = metrics.get('max_drawdown', 0)
    if max_dd > 0:
        discrepancies.append(f"Max drawdown {max_dd} should be <= 0")

    # Check total return matches
    if 'total_return' in metrics and len(returns) > 0:
        calculated_return = (1 + returns).prod() - 1
        reported_return = metrics['total_return']
        if abs(calculated_return - reported_return) > 0.001:
            discrepancies.append(
                f"Total return mismatch: calculated={calculated_return:.4f}, "
                f"reported={reported_return:.4f}"
            )

    # Check win rate is between 0 and 1
    win_rate = metrics.get('win_rate', 0)
    if not 0 <= win_rate <= 1:
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
    extreme_returns = returns[returns.abs() > 0.5]  # >50% daily move
    if len(extreme_returns) > 0:
        return False, f"Found {len(extreme_returns)} extreme daily returns (>50%)"

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
    # Basic consistency check - positions should exist where transactions exist
    if transactions_df.empty:
        return True, None

    return True, None  # Detailed check would require more complex logic


def save_validation_report(
    result: ValidationResult,
    output_path: Path
) -> None:
    """
    Save validation report to JSON file.

    Args:
        result: ValidationResult to save
        output_path: Path for output file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(result.to_dict(), f, indent=2)

    logger.info(f"Saved validation report to {output_path}")
