"""
OHLCV Data Validator - Orchestrator Pattern.

Coordinates validation across common OHLCV checks and asset-specific validators.
Delegates asset-specific validation to specialized validators (EquityValidator,
ForexValidator, CryptoValidator).
"""

import logging
from typing import Optional, Any, Tuple, Literal

import numpy as np
import pandas as pd

from .core import (
    ValidationResult,
    ValidationSeverity,
    REQUIRED_OHLCV_COLUMNS,
    CONTINUOUS_CALENDARS,
)
from .config import ValidationConfig
from .column_mapping import ColumnMapping, build_column_mapping
from .base import BaseValidator
from .utils import (
    normalize_dataframe_index,
    ensure_timezone,
    compute_dataframe_hash,
    safe_divide,
    calculate_z_scores,
)
from .validators import (
    EquityValidator,
    ForexValidator,
    CryptoValidator,
    add_fix_suggestions_to_result,
)

logger = logging.getLogger('cockpit.validation')


class DataValidator(BaseValidator):
    """
    Orchestrator for OHLCV data validation.

    Performs common OHLCV validation and delegates asset-specific checks
    to specialized validators based on asset type.

    Architecture:
        - Common checks: Runs on all asset types
        - Asset-specific checks: Delegated to EquityValidator, ForexValidator, CryptoValidator
        - Result merging: Combines common and asset-specific validation results

    Usage:
        >>> config = ValidationConfig.strict(timeframe='1d', asset_type='equity')
        >>> validator = DataValidator(config=config)
        >>> result = validator.validate(df, asset_name='AAPL')
        >>> if not result:
        ...     print(result.summary())
    """

    def __init__(self, config: Optional[ValidationConfig] = None):
        """Initialize validator with configuration."""
        if config is None:
            config = ValidationConfig()
        super().__init__(config)
        self._asset_validators = {}

    def _register_checks(self) -> None:
        """Register common validation checks (non-asset-specific)."""
        self._check_registry = [
            self._check_required_columns,
            self._check_no_nulls,
            self._check_ohlc_consistency,
            self._check_no_negative_values,
            self._check_no_future_dates,
            self._check_no_duplicate_dates,
            self._check_sorted_index,
            self._check_zero_volume,
            self._check_stale_data,
            self._check_data_sufficiency,
            self._check_price_outliers,
        ]

    def _get_asset_validator(self, asset_type: str) -> Optional[BaseValidator]:
        """Get or create asset-specific validator."""
        if asset_type not in self._asset_validators:
            validators = {
                'equity': EquityValidator,
                'forex': ForexValidator,
                'crypto': CryptoValidator,
            }
            validator_class = validators.get(asset_type)
            if validator_class:
                self._asset_validators[asset_type] = validator_class(config=self.config)
        return self._asset_validators.get(asset_type)

    def validate(
        self,
        df: pd.DataFrame,
        calendar: Optional[Any] = None,
        asset_name: str = "unknown",
        calendar_name: Optional[str] = None,
        asset_type: Optional[Literal['equity', 'forex', 'crypto']] = None,
        suggest_fixes: Optional[bool] = None
    ) -> ValidationResult:
        """
        Validate OHLCV DataFrame with common and asset-specific checks.

        Args:
            df: DataFrame with OHLCV columns (case-insensitive matching)
            calendar: Optional trading calendar for gap detection
            asset_name: Asset name for logging
            calendar_name: Calendar name (e.g., 'XNYS', '24/7')
            asset_type: Asset type ('equity', 'forex', 'crypto') for context-aware validation
            suggest_fixes: If True, add fix suggestions to result metadata (overrides config)

        Returns:
            ValidationResult with all check outcomes
        """
        # Update config with provided values
        if asset_type is not None:
            self.config.asset_type = asset_type
        if calendar_name is not None:
            self.config.calendar_name = calendar_name
        if suggest_fixes is not None:
            self.config.suggest_fixes = suggest_fixes

        result = self._create_result()

        # Add metadata
        result.add_metadata('asset_name', asset_name)
        result.add_metadata('timeframe', self.config.timeframe)
        result.add_metadata('calendar_name', self.config.calendar_name)
        result.add_metadata('asset_type', self.config.asset_type)
        result.add_metadata('row_count', len(df))

        # Handle empty DataFrame
        if df.empty:
            result.add_check('empty_data', False, f"DataFrame is empty for {asset_name}")
            return result

        # Normalize index
        try:
            df = normalize_dataframe_index(df)
        except ValueError as e:
            result.add_check('valid_index', False, str(e))
            return result

        result.add_check('valid_index', True, "Index is valid DatetimeIndex")

        # Add date range metadata
        result.add_metadata('date_range_start', str(df.index.min()))
        result.add_metadata('date_range_end', str(df.index.max()))
        result.add_metadata('data_hash', compute_dataframe_hash(df))

        # Build column mapping
        col_map = build_column_mapping(df)

        # Run common checks
        result = self._run_common_checks(df, col_map, asset_name, result)

        # Run gap/continuity checks if calendar provided
        if self.config.check_gaps and not result.get_check('required_columns') or result.get_check('required_columns').passed:
            result = self._run_continuity_checks(df, calendar, result, asset_name, calendar_name)

        # Run asset-specific validation
        if self.config.asset_type:
            asset_validator = self._get_asset_validator(self.config.asset_type)
            if asset_validator:
                asset_result = asset_validator.validate(df, col_map, asset_name)
                result = result.merge(asset_result)

        # Generate fix suggestions if enabled
        if self.config.suggest_fixes:
            result = add_fix_suggestions_to_result(result, df, asset_name)

        return result

    def _run_common_checks(
        self,
        df: pd.DataFrame,
        col_map: ColumnMapping,
        asset_name: str,
        result: ValidationResult
    ) -> ValidationResult:
        """Run all common (non-asset-specific) validation checks."""
        # Run required columns check first (blocking if fails)
        result = self._run_check(result, self._check_required_columns, df, col_map, asset_name)
        if not result.passed:
            return result

        # Run remaining common checks
        for check_func in self._check_registry[1:]:
            if not self._should_skip_check(check_func.__name__):
                result = self._run_check(result, check_func, df, col_map, asset_name)

        return result

    # =========================================================================
    # Common Check Methods (apply to all asset types)
    # =========================================================================

    def _check_required_columns(
        self,
        result: ValidationResult,
        df: pd.DataFrame,
        col_map: ColumnMapping,
        asset_name: str
    ) -> ValidationResult:
        """Check that required OHLCV columns exist (case-insensitive)."""
        missing = col_map.missing_columns()

        if missing:
            result.add_check(
                'required_columns',
                False,
                f"Missing required columns: {missing}. "
                f"Expected columns (case-insensitive): {list(REQUIRED_OHLCV_COLUMNS)}",
                {'missing_columns': missing}
            )
        else:
            result.add_check(
                'required_columns',
                True,
                "All required columns present",
                {'column_mapping': col_map.to_dict()}
            )
        return result

    def _check_no_nulls(
        self,
        result: ValidationResult,
        df: pd.DataFrame,
        col_map: ColumnMapping,
        asset_name: str
    ) -> ValidationResult:
        """Check for null values in OHLCV columns."""
        actual_cols = col_map.all_columns

        # Check for all-NaN columns
        for col in actual_cols:
            if df[col].isna().all():
                result.add_error(
                    f"Column '{col}' in {asset_name} is entirely NaN. "
                    f"All values are missing. Check data source."
                )

        null_counts = df[actual_cols].isnull().sum()
        total_nulls = null_counts.sum()

        if total_nulls > 0:
            null_details = {
                col: int(count)
                for col, count in null_counts.items()
                if count > 0
            }
            null_pct = safe_divide(total_nulls, len(df) * len(actual_cols)) * 100

            # Find sample dates with null values
            null_dates = []
            for col in actual_cols:
                if null_counts[col] > 0:
                    col_null_mask = df[col].isnull()
                    col_null_dates = df.index[col_null_mask][:3]
                    null_dates.extend([str(d) for d in col_null_dates])
                    if len(null_dates) >= 3:
                        break

            msg = (
                f"Found {total_nulls} null values ({null_pct:.2f}%) in {asset_name}. "
                f"Use df.fillna(method='ffill') or df.interpolate() to forward-fill, "
                f"or df.dropna() to remove rows with nulls."
            )
            result.add_check(
                'no_nulls', False, msg,
                {
                    'null_counts': null_details,
                    'null_pct': null_pct,
                    'sample_dates': null_dates[:3]
                }
            )
        else:
            result.add_check('no_nulls', True, "No null values found")
        return result

    def _check_ohlc_consistency(
        self,
        result: ValidationResult,
        df: pd.DataFrame,
        col_map: ColumnMapping,
        asset_name: str
    ) -> ValidationResult:
        """Check OHLC price relationships are valid."""
        o, h, l, c = col_map.open, col_map.high, col_map.low, col_map.close

        if not all([o, h, l, c]):
            return result

        # Check for non-numeric OHLCV values
        for col_name, col_key in [('open', o), ('high', h), ('low', l), ('close', c)]:
            if col_key and not pd.api.types.is_numeric_dtype(df[col_key]):
                result.add_error(
                    f"Column '{col_key}' ({col_name}) in {asset_name} is not numeric. "
                    f"OHLCV columns must be numeric. Found dtype: {df[col_key].dtype}"
                )
                return result

        # High >= Low, High >= Open/Close, Low <= Open/Close
        high_low_violations = int((df[h] < df[l]).sum())
        high_violations = int(((df[h] < df[o]) | (df[h] < df[c])).sum())
        low_violations = int(((df[l] > df[o]) | (df[l] > df[c])).sum())
        total_violations = high_low_violations + high_violations + low_violations

        if total_violations > 0:
            violation_pct = safe_divide(total_violations, len(df)) * 100
            violation_mask = (df[h] < df[l]) | (df[h] < df[o]) | (df[h] < df[c]) | (df[l] > df[o]) | (df[l] > df[c])
            violation_dates = df.index[violation_mask][:3].tolist()

            msg = (
                f"Found {total_violations} OHLC consistency violations ({violation_pct:.2f}%) in {asset_name}. "
                f"OHLC relationships must satisfy: High >= Low, High >= Open/Close, Low <= Open/Close. "
                f"Review data source for errors or use df.clip() to constrain values."
            )
            result.add_check(
                'ohlc_consistency', False, msg,
                {
                    'high_low_violations': high_low_violations,
                    'high_violations': high_violations,
                    'low_violations': low_violations,
                    'total_violations': total_violations,
                    'violation_pct': violation_pct,
                    'sample_dates': [str(d) for d in violation_dates]
                }
            )
        else:
            result.add_check('ohlc_consistency', True, "OHLC prices are consistent")
        return result

    def _check_no_negative_values(
        self,
        result: ValidationResult,
        df: pd.DataFrame,
        col_map: ColumnMapping,
        asset_name: str
    ) -> ValidationResult:
        """Check for negative prices or volumes."""
        price_cols = col_map.price_columns
        volume_col = col_map.volume

        negative_prices = sum(int((df[col] < 0).sum()) for col in price_cols)
        negative_volumes = int((df[volume_col] < 0).sum()) if volume_col else 0
        total_negatives = negative_prices + negative_volumes

        if total_negatives > 0:
            # Find sample dates with negative values
            negative_dates = []
            for col in price_cols:
                if (df[col] < 0).any():
                    neg_mask = df[col] < 0
                    neg_dates = df.index[neg_mask][:2]
                    negative_dates.extend([f"{str(d)} ({col})" for d in neg_dates])
            if volume_col and (df[volume_col] < 0).any():
                vol_neg_mask = df[volume_col] < 0
                vol_neg_dates = df.index[vol_neg_mask][:2]
                negative_dates.extend([f"{str(d)} (volume)" for d in vol_neg_dates])

            msg = (
                f"Found {total_negatives} negative values in {asset_name}. "
                f"Prices and volumes must be non-negative. Use df[df < 0] = 0 or "
                f"df.clip(lower=0) to fix negative values."
            )
            result.add_check(
                'no_negative_values', False, msg,
                {
                    'negative_prices': negative_prices,
                    'negative_volumes': negative_volumes,
                    'sample_dates': negative_dates[:3]
                }
            )
        else:
            result.add_check('no_negative_values', True, "No negative values found")
        return result

    def _check_no_future_dates(
        self,
        result: ValidationResult,
        df: pd.DataFrame,
        col_map: ColumnMapping,
        asset_name: str
    ) -> ValidationResult:
        """Check for dates in the future."""
        today = pd.Timestamp.now(tz='UTC').normalize()
        index = ensure_timezone(pd.DatetimeIndex(df.index))
        future_dates = int((index > today).sum())

        if future_dates > 0:
            future_date_list = index[index > today][:3].tolist()
            msg = (
                f"Found {future_dates} future date(s) in {asset_name}. "
                f"Data should not contain dates beyond today. "
                f"Use df[df.index <= pd.Timestamp.now(tz='UTC')] to filter out future dates."
            )
            result.add_check(
                'no_future_dates', False, msg,
                {
                    'future_date_count': future_dates,
                    'sample_dates': [str(d.date()) for d in future_date_list]
                }
            )
        else:
            result.add_check('no_future_dates', True, "No future dates found")
        return result

    def _check_no_duplicate_dates(
        self,
        result: ValidationResult,
        df: pd.DataFrame,
        col_map: ColumnMapping,
        asset_name: str
    ) -> ValidationResult:
        """Check for duplicate dates in index."""
        duplicates = int(df.index.duplicated().sum())

        if duplicates > 0:
            dup_pct = safe_divide(duplicates, len(df)) * 100
            dup_mask = df.index.duplicated(keep=False)
            dup_dates = df.index[dup_mask].unique()[:3].tolist()

            msg = (
                f"Found {duplicates} duplicate dates ({dup_pct:.2f}%) in {asset_name}. "
                f"Each date should appear only once. Use df[~df.index.duplicated(keep='first')] "
                f"to keep first occurrence, or df.groupby(df.index).last() to aggregate duplicates."
            )
            result.add_check(
                'no_duplicate_dates', False, msg,
                {
                    'duplicate_count': duplicates,
                    'duplicate_pct': dup_pct,
                    'sample_dates': [str(d) for d in dup_dates]
                }
            )
        else:
            result.add_check('no_duplicate_dates', True, "No duplicate dates found")
        return result

    def _check_sorted_index(
        self,
        result: ValidationResult,
        df: pd.DataFrame,
        col_map: ColumnMapping,
        asset_name: str
    ) -> ValidationResult:
        """Check that index is sorted in ascending order."""
        is_ascending = df.index.is_monotonic_increasing
        is_descending = df.index.is_monotonic_decreasing

        if not is_ascending:
            sample_issues = []
            if len(df) >= 2:
                for i in range(min(3, len(df) - 1)):
                    if df.index[i] > df.index[i + 1]:
                        sample_issues.append(f"{df.index[i]} > {df.index[i + 1]}")

            if is_descending:
                msg = f"Index is sorted descending for {asset_name}, should be ascending. Use df.sort_index() to fix."
            else:
                msg = f"Index is not sorted for {asset_name}. Use df.sort_index() to sort in ascending order."

            result.add_check(
                'sorted_index', False, msg,
                {
                    'is_ascending': is_ascending,
                    'is_descending': is_descending,
                    'sample_issues': sample_issues
                },
                severity=self.config.get_severity()
            )
        else:
            result.add_check('sorted_index', True, "Index is sorted ascending")
        return result

    def _check_zero_volume(
        self,
        result: ValidationResult,
        df: pd.DataFrame,
        col_map: ColumnMapping,
        asset_name: str
    ) -> ValidationResult:
        """Check for excessive zero volume bars."""
        volume_col = col_map.volume

        if not volume_col:
            return result

        zero_count = int((df[volume_col] == 0).sum())
        zero_pct = safe_divide(zero_count, len(df)) * 100

        if zero_pct > self.config.zero_volume_threshold_pct:
            zero_vol_mask = df[volume_col] == 0
            zero_vol_dates = df.index[zero_vol_mask][:3].tolist()

            msg = (
                f"Found {zero_count} ({zero_pct:.1f}%) zero volume bars in {asset_name}. "
                f"High zero volume may indicate data quality issues or market closures. "
                f"Review data source or filter using df[df['{volume_col}'] > 0]."
            )
            result.add_check(
                'zero_volume', False, msg,
                {
                    'zero_volume_count': zero_count,
                    'zero_volume_pct': zero_pct,
                    'sample_dates': [str(d) for d in zero_vol_dates]
                },
                severity=self.config.get_severity()
            )
        else:
            result.add_check(
                'zero_volume', True,
                f"Zero volume bars within tolerance ({zero_pct:.1f}%)",
                {'zero_volume_count': zero_count, 'zero_volume_pct': zero_pct}
            )
        return result

    def _check_stale_data(
        self,
        result: ValidationResult,
        df: pd.DataFrame,
        col_map: ColumnMapping,
        asset_name: str
    ) -> ValidationResult:
        """Check if data is stale (too old)."""
        if len(df) == 0:
            return result

        df_index = ensure_timezone(pd.DatetimeIndex(df.index))
        last_date = df_index.max()
        now = pd.Timestamp.now(tz='UTC')
        days_since = (now - last_date).days

        if days_since > self.config.stale_threshold_days:
            msg = (
                f"Data for {asset_name} is {days_since} days old (last: {last_date.date()}). "
                f"Data may be stale. Update data source or check if data feed is still active."
            )
            result.add_check(
                'stale_data', False, msg,
                {
                    'days_since_last': days_since,
                    'last_date': str(last_date.date()),
                    'threshold_days': self.config.stale_threshold_days
                },
                severity=ValidationSeverity.WARNING
            )
        else:
            result.add_check(
                'stale_data', True,
                f"Data is current (last: {last_date.date()})",
                {'days_since_last': days_since}
            )
        return result

    def _check_data_sufficiency(
        self,
        result: ValidationResult,
        df: pd.DataFrame,
        col_map: ColumnMapping,
        asset_name: str
    ) -> ValidationResult:
        """Check that there's sufficient data for meaningful analysis."""
        min_required = self.config.min_rows
        row_count = len(df)

        if row_count < min_required:
            msg = (
                f"Insufficient data for {asset_name}: {row_count} rows (minimum: {min_required}). "
                f"More data is needed for meaningful analysis. Check data source date range or "
                f"adjust min_rows_daily/min_rows_intraday in ValidationConfig if appropriate."
            )
            result.add_check(
                'data_sufficiency', False, msg,
                {
                    'row_count': row_count,
                    'minimum_required': min_required,
                    'timeframe': self.config.timeframe
                },
                severity=ValidationSeverity.WARNING
            )
        else:
            result.add_check(
                'data_sufficiency', True,
                f"Sufficient data ({row_count} rows)",
                {'row_count': row_count, 'minimum_required': min_required}
            )
        return result

    def _check_price_outliers(
        self,
        result: ValidationResult,
        df: pd.DataFrame,
        col_map: ColumnMapping,
        asset_name: str
    ) -> ValidationResult:
        """Check for price outliers using z-score analysis."""
        close_col = col_map.close

        if not close_col or len(df) < 3:
            return result

        returns = df[close_col].pct_change().dropna()

        if len(returns) < 2:
            return result

        z_scores = calculate_z_scores(returns)
        threshold = self.config.outlier_threshold_sigma
        outliers = int((z_scores > threshold).sum())

        if outliers > 0:
            outlier_pct = safe_divide(outliers, len(returns)) * 100
            outlier_mask = z_scores > threshold
            outlier_dates = z_scores[outlier_mask].index[:3].tolist()
            outlier_z_values = [float(z_scores[d]) for d in outlier_dates]

            msg = (
                f"Found {outliers} price outliers (>{threshold} sigma) in {asset_name}. "
                f"Outliers may indicate data errors or significant market events. "
                f"Review these dates for accuracy."
            )

            if self.config.strict_mode:
                result.add_check(
                    'price_outliers', False, msg,
                    {
                        'outlier_count': outliers,
                        'outlier_pct': outlier_pct,
                        'sample_dates': [str(d) for d in outlier_dates],
                        'sample_z_scores': outlier_z_values
                    }
                )
            else:
                result.add_warning(msg)
                result.add_check(
                    'price_outliers', True,
                    "Outliers found but within tolerance",
                    {
                        'outlier_count': outliers,
                        'outlier_pct': outlier_pct,
                        'sample_dates': [str(d) for d in outlier_dates]
                    }
                )
        else:
            result.add_check('price_outliers', True, "No significant price outliers")
        return result

    def _run_continuity_checks(
        self,
        df: pd.DataFrame,
        calendar: Optional[Any],
        result: ValidationResult,
        asset_name: str,
        calendar_name: Optional[str]
    ) -> ValidationResult:
        """Run date/bar continuity checks based on available calendar."""
        if calendar is not None:
            return self._run_check(
                result,
                self._check_date_continuity,
                df, calendar, asset_name, calendar_name
            )
        elif self.config.is_intraday:
            return self._run_check(
                result,
                self._check_intraday_continuity,
                df, asset_name
            )
        return result

    def _is_continuous_calendar(
        self,
        calendar: Optional[Any],
        calendar_name: Optional[str]
    ) -> bool:
        """Detect 24/7 calendars using calendar properties or name matching."""
        # Check calendar object properties
        if calendar is not None:
            if hasattr(calendar, 'weekmask'):
                weekmask = calendar.weekmask
                if isinstance(weekmask, str):
                    all_days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
                    if all(day in weekmask for day in all_days):
                        return True

            if hasattr(calendar, 'name'):
                cal_name = str(calendar.name).upper()
                if cal_name in CONTINUOUS_CALENDARS:
                    return True

            if hasattr(calendar, 'session_length'):
                try:
                    session_length = calendar.session_length
                    if hasattr(session_length, 'total_seconds'):
                        hours = session_length.total_seconds() / 3600
                        if hours >= 23.0:
                            return True
                except (AttributeError, TypeError):
                    pass

        # Fallback to string matching
        if calendar_name:
            return calendar_name.upper() in CONTINUOUS_CALENDARS

        return False

    def _check_date_continuity(
        self,
        result: ValidationResult,
        df: pd.DataFrame,
        calendar: Any,
        asset_name: str,
        calendar_name: Optional[str] = None
    ) -> ValidationResult:
        """Check for missing dates according to trading calendar."""
        try:
            df_index = ensure_timezone(pd.DatetimeIndex(df.index))
            start_date = df_index.min()
            end_date = df_index.max()

            # For intraday data, use different logic
            if self.config.is_intraday:
                return self._check_intraday_calendar_continuity(
                    result, df, calendar, asset_name, calendar_name
                )

            # Daily data: check sessions
            sessions = calendar.sessions_in_range(start_date, end_date)

            if len(sessions) == 0:
                result.add_check(
                    'date_continuity', True,
                    "No sessions in date range",
                    severity=ValidationSeverity.INFO
                )
                return result

            # Normalize for comparison
            sessions_norm = ensure_timezone(pd.DatetimeIndex(sessions).normalize())
            df_dates_norm = df_index.normalize()
            missing = set(sessions_norm) - set(df_dates_norm)

            if missing:
                missing_count = len(missing)
                missing_pct = safe_divide(missing_count, len(sessions)) * 100
                msg = f"Found {missing_count} missing calendar dates ({missing_pct:.1f}%) in {asset_name}"

                if missing_count > self.config.gap_tolerance_days:
                    missing_dates_list = sorted(list(missing))[:5]
                    msg_with_guidance = (
                        f"{msg} Missing dates may indicate data gaps or market closures. "
                        f"Review data source or use gap filling techniques if appropriate."
                    )

                    if self.config.strict_mode:
                        result.add_check(
                            'date_continuity', False, msg_with_guidance,
                            {
                                'missing_count': missing_count,
                                'missing_pct': missing_pct,
                                'sample_missing_dates': [str(d.date()) for d in missing_dates_list]
                            }
                        )
                    else:
                        result.add_warning(msg_with_guidance)
                        result.add_check(
                            'date_continuity', True,
                            "Gaps within tolerance",
                            {
                                'missing_count': missing_count,
                                'missing_pct': missing_pct,
                                'sample_missing_dates': [str(d.date()) for d in missing_dates_list]
                            }
                        )
                else:
                    result.add_check(
                        'date_continuity', True,
                        f"Minor gaps ({missing_count} days)",
                        {'missing_count': missing_count}
                    )
            else:
                result.add_check('date_continuity', True, "No missing calendar dates")

        except Exception as e:
            result.add_warning(f"Could not check date continuity: {e}")

        return result

    def _check_intraday_calendar_continuity(
        self,
        result: ValidationResult,
        df: pd.DataFrame,
        calendar: Any,
        asset_name: str,
        calendar_name: Optional[str] = None
    ) -> ValidationResult:
        """Check intraday data continuity with calendar awareness."""
        try:
            df_index = ensure_timezone(pd.DatetimeIndex(df.index))
            start_date = df_index.min()
            end_date = df_index.max()

            sessions = calendar.sessions_in_range(
                start_date.normalize(),
                end_date.normalize()
            )

            if len(sessions) == 0:
                result.add_check('date_continuity', True, "No sessions in range")
                return result

            # For 24/7 calendars, skip session-based checks
            if self._is_continuous_calendar(calendar=calendar, calendar_name=calendar_name):
                return self._check_intraday_continuity(result, df, asset_name)

            # Check session coverage
            sessions_with_data = 0
            sessions_missing = 0

            for session in sessions:
                session_start = session.normalize()
                session_end = session_start + pd.Timedelta(days=1)
                session_data = df_index[(df_index >= session_start) & (df_index < session_end)]
                if len(session_data) > 0:
                    sessions_with_data += 1
                else:
                    sessions_missing += 1

            if sessions_missing > self.config.gap_tolerance_days:
                coverage_pct = safe_divide(sessions_with_data, len(sessions)) * 100
                msg = f"Missing data for {sessions_missing} trading sessions in {asset_name}"

                if self.config.strict_mode:
                    result.add_check(
                        'date_continuity', False, msg,
                        {
                            'sessions_missing': sessions_missing,
                            'sessions_with_data': sessions_with_data,
                            'coverage_pct': coverage_pct
                        }
                    )
                else:
                    result.add_warning(msg)
                    result.add_check(
                        'date_continuity', True,
                        "Session gaps within tolerance",
                        {'sessions_missing': sessions_missing, 'coverage_pct': coverage_pct}
                    )
            else:
                result.add_check(
                    'date_continuity', True,
                    f"Data present for {sessions_with_data} sessions",
                    {'sessions_with_data': sessions_with_data}
                )

        except Exception as e:
            result.add_warning(f"Could not check intraday calendar continuity: {e}")

        return result

    def _check_intraday_continuity(
        self,
        result: ValidationResult,
        df: pd.DataFrame,
        asset_name: str
    ) -> ValidationResult:
        """Check intraday data for excessive gaps between bars."""
        if len(df) < 2:
            result.add_check(
                'intraday_continuity', True,
                "Insufficient data for continuity check (need at least 2 rows)"
            )
            return result

        try:
            time_diffs = pd.Series(df.index).diff().dropna()

            if len(time_diffs) == 0:
                return result

            expected_interval = self.config.expected_interval
            if expected_interval is None:
                result.add_warning(
                    f"Unknown timeframe '{self.config.timeframe}', skipping continuity check"
                )
                return result

            # Allow for 3x expected interval (market closures)
            gap_threshold = expected_interval * 3
            large_gaps = int((time_diffs > gap_threshold).sum())
            gap_pct = safe_divide(large_gaps, len(time_diffs)) * 100

            if large_gaps > self.config.gap_tolerance_bars:
                msg = f"Found {large_gaps} large gaps ({gap_pct:.1f}%) in intraday data for {asset_name}"

                if self.config.strict_mode:
                    result.add_check(
                        'intraday_continuity', False, msg,
                        {'large_gaps': large_gaps, 'gap_pct': gap_pct}
                    )
                else:
                    result.add_warning(msg)
                    result.add_check(
                        'intraday_continuity', True,
                        "Gaps within tolerance",
                        {'large_gaps': large_gaps, 'gap_pct': gap_pct}
                    )
            else:
                result.add_check(
                    'intraday_continuity', True,
                    f"Intraday continuity OK ({large_gaps} gaps)",
                    {'large_gaps': large_gaps}
                )

        except Exception as e:
            result.add_warning(f"Could not check intraday continuity: {e}")

        return result
