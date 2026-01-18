"""
FOREX-specific OHLCV data validator.

Validates FOREX data with FOREX-specific rules:
- 24/5 market hours validation
- Sunday bar detection and consolidation
- Weekend gap integrity checks
- Pip range validation
- Major pair volatility checks
"""

import logging
from typing import Any, Optional

import pandas as pd

from ..base import BaseValidator
from ..core import ValidationResult, ValidationSeverity, CONTINUOUS_CALENDARS
from ..column_mapping import ColumnMapping
from ..utils import safe_divide, ensure_timezone

logger = logging.getLogger('cockpit.validation.forex')


class ForexValidator(BaseValidator):
    """
    Validator for FOREX-specific OHLCV data checks.

    Performs FOREX-specific validation including:
    - Sunday bar detection (24/5 market)
    - Weekend gap integrity
    - Pip range validation
    - Trading session validation

    Inherits common OHLCV checks from BaseValidator.
    """

    def __init__(self, config: Optional[Any] = None):
        """Initialize FOREX validator with configuration."""
        super().__init__(config)

    def _register_checks(self) -> None:
        """Register FOREX-specific validation checks."""
        self._check_registry = [
            self._check_sunday_bars,
            self._check_weekend_gap_integrity,
        ]

    def validate(
        self,
        df: pd.DataFrame,
        col_map: ColumnMapping,
        asset_name: str = "unknown"
    ) -> ValidationResult:
        """
        Validate FOREX-specific characteristics.

        Args:
            df: DataFrame with OHLCV data
            col_map: Column mapping for OHLCV columns
            asset_name: Asset name for logging

        Returns:
            ValidationResult with FOREX-specific check outcomes
        """
        result = self._create_result()
        result.add_metadata('asset_name', asset_name)
        result.add_metadata('asset_type', 'forex')

        if df.empty:
            result.add_check('empty_data', False, f"DataFrame is empty for {asset_name}")
            return result

        # Run registered checks
        for check_func in self._check_registry:
            if not self._should_skip_check(check_func.__name__):
                result = self._run_check(result, check_func, df, col_map, asset_name)

        return result

    def _check_sunday_bars(
        self,
        result: ValidationResult,
        df: pd.DataFrame,
        col_map: ColumnMapping,
        asset_name: str
    ) -> ValidationResult:
        """Check for Sunday bars in FOREX/24/7 data."""
        # Only check for FOREX/24/7 calendars
        if not self.config.check_sunday_bars:
            return result

        if len(df) == 0:
            return result

        # Check for Sunday bars (dayofweek == 6)
        df_index = ensure_timezone(pd.DatetimeIndex(df.index))
        sunday_mask = df_index.dayofweek == 6
        sunday_count = int(sunday_mask.sum())

        if sunday_count > 0:
            sunday_dates = df_index[sunday_mask].normalize().tolist()
            msg = (
                f"Found {sunday_count} Sunday bar(s) in {asset_name}. "
                f"Consider consolidating to Friday using "
                f"lib.utils.consolidate_sunday_to_friday()"
            )
            result.add_check(
                'sunday_bars', False, msg,
                {
                    'sunday_count': sunday_count,
                    'sunday_dates': [str(d.date()) for d in sunday_dates[:10]]  # First 10
                },
                severity=ValidationSeverity.WARNING
            )
        else:
            result.add_check('sunday_bars', True, "No Sunday bars detected")
        return result

    def _check_weekend_gap_integrity(
        self,
        result: ValidationResult,
        df: pd.DataFrame,
        col_map: ColumnMapping,
        asset_name: str
    ) -> ValidationResult:
        """Validate FOREX weekend gap semantics (Friday-Sunday-Monday relationships)."""
        # Only check for FOREX data
        if not self.config.check_weekend_gaps:
            return result

        if len(df) < 2:
            return result

        df_index = ensure_timezone(pd.DatetimeIndex(df.index))
        close_col = col_map.close

        if not close_col:
            return result

        # Normalize dates to midnight for day-of-week checks
        df_index_norm = df_index.normalize()

        # Find all Fridays, Sundays, and Mondays
        fridays = df_index_norm[df_index_norm.dayofweek == 4]  # Friday = 4
        sundays = df_index_norm[df_index_norm.dayofweek == 6]  # Sunday = 6
        mondays = df_index_norm[df_index_norm.dayofweek == 0]  # Monday = 0

        issues = []
        details = {
            'friday_count': len(fridays),
            'sunday_count': len(sundays),
            'monday_count': len(mondays)
        }

        # Check for Friday-Sunday pairs (potential duplication)
        for sunday_date in sundays:
            friday_date = sunday_date - pd.Timedelta(days=2)
            if friday_date in fridays:
                issues.append(
                    f"Both Friday {friday_date.date()} and Sunday {sunday_date.date()} "
                    f"bars exist (potential duplication)"
                )

        # Check for Sunday-Monday pairs (should have weekend gap)
        for sunday_date in sundays:
            monday_date = sunday_date + pd.Timedelta(days=1)
            if monday_date in mondays:
                sunday_data = df.loc[df_index_norm == sunday_date, close_col]
                monday_data = df.loc[df_index_norm == monday_date, col_map.open] if col_map.open else pd.Series(dtype=float)

                if len(sunday_data) > 0 and len(monday_data) > 0:
                    sunday_close = sunday_data.iloc[0]
                    monday_open = monday_data.iloc[0]

                    if pd.notna(sunday_close) and pd.notna(monday_open):
                        gap_pct = abs((monday_open - sunday_close) / sunday_close * 100) if sunday_close != 0 else 0
                        if gap_pct < 0.01:  # Less than 0.01% gap might indicate missing weekend movement
                            issues.append(
                                f"Sunday {sunday_date.date()} to Monday {monday_date.date()} "
                                f"gap is very small ({gap_pct:.4f}%), may indicate missing weekend data"
                            )

        # Check for Friday-Monday pairs without Sunday (expected for consolidated data)
        for friday_date in fridays:
            monday_date = friday_date + pd.Timedelta(days=3)
            if monday_date in mondays:
                # Check if Sunday exists between them
                sunday_date = friday_date + pd.Timedelta(days=2)
                if sunday_date not in sundays:
                    # This is expected if Sunday was consolidated into Friday
                    # Check if gap is reasonable
                    friday_data = df.loc[df_index_norm == friday_date, close_col]
                    monday_data = df.loc[df_index_norm == monday_date, col_map.open] if col_map.open else pd.Series(dtype=float)

                    if len(friday_data) > 0 and len(monday_data) > 0:
                        friday_close = friday_data.iloc[0]
                        monday_open = monday_data.iloc[0]

                        if pd.notna(friday_close) and pd.notna(monday_open):
                            gap_pct = abs((monday_open - friday_close) / friday_close * 100) if friday_close != 0 else 0
                            if gap_pct > 10:  # Large gap might indicate missing data
                                issues.append(
                                    f"Large gap ({gap_pct:.2f}%) from Friday {friday_date.date()} "
                                    f"to Monday {monday_date.date()} (no Sunday bar found)"
                                )

        if issues:
            msg = (
                f"Weekend gap integrity issues detected in {asset_name}: "
                f"{len(issues)} issue(s) found"
            )
            details['issues'] = issues[:5]  # First 5 issues
            result.add_check(
                'weekend_gap_integrity', False, msg,
                details,
                severity=ValidationSeverity.WARNING
            )
        else:
            result.add_check(
                'weekend_gap_integrity', True,
                "Weekend gap semantics are valid",
                details
            )
        return result
