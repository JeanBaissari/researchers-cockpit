"""
OHLCV Data Validator.

Validates OHLCV data before ingestion into bundles.
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

logger = logging.getLogger('cockpit.validation')


class DataValidator(BaseValidator):
    """
    Validates OHLCV data before ingestion.

    Performs comprehensive checks for data quality issues that could
    affect backtest results.
    
    Checks performed:
    1. Required columns presence (case-insensitive matching)
    2. Null value detection
    3. OHLC price relationship consistency
    4. Negative value detection
    5. Future date detection
    6. Duplicate date detection
    7. Index sorting verification
    8. Zero volume detection
    9. Price jump detection
    10. Stale data detection
    11. Data sufficiency
    12. Price outlier detection
    13. Date/bar continuity (with optional calendar)
    
    Column Name Handling:
        The validator supports multiple column name formats:
        - lowercase: open, high, low, close, volume
        - uppercase: OPEN, HIGH, LOW, CLOSE, VOLUME
        - titlecase: Open, High, Low, Close, Volume
        - abbreviated: O, H, L, C, V
        
    Example:
        >>> config = ValidationConfig.strict(timeframe='1d')
        >>> validator = DataValidator(config=config)
        >>> result = validator.validate(df, asset_name='AAPL')
        >>> if not result:
        ...     print(result.summary())
    """

    def __init__(
        self,
        config: Optional[ValidationConfig] = None
    ):
        """
        Initialize validator with configuration.

        Args:
            config: ValidationConfig object (uses default if None)
        """
        if config is None:
            config = ValidationConfig()
        super().__init__(config)

    def _register_checks(self) -> None:
        """Register all validation checks in execution order."""
        self._check_registry = [
            self._check_required_columns,
            self._check_no_nulls,
            self._check_ohlc_consistency,
            self._check_no_negative_values,
            self._check_no_future_dates,
            self._check_no_duplicate_dates,
            self._check_sorted_index,
            self._check_zero_volume,
            self._check_price_jumps,
            self._check_stale_data,
            self._check_data_sufficiency,
            self._check_price_outliers,
            self._check_volume_spikes,
            self._check_potential_splits,
            self._check_sunday_bars,
            self._check_weekend_gap_integrity,
        ]

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
        Validate OHLCV DataFrame.

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
        # Update config with provided values if not already set
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
            result.add_check(
                'empty_data', False,
                f"DataFrame is empty for {asset_name}"
            )
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

        # Run required columns check first (blocking if fails)
        result = self._run_check(result, self._check_required_columns, df, col_map, asset_name)
        if not result.passed:
            return result

        # Run all registered checks (skip required_columns, already run)
        for check_func in self._check_registry[1:]:
            if not self._should_skip_check(check_func.__name__):
                result = self._run_check(result, check_func, df, col_map, asset_name)

        # Run gap/continuity checks
        if self.config.check_gaps:
            result = self._run_continuity_checks(df, calendar, result, asset_name, calendar_name)

        # Generate fix suggestions if enabled
        if self.config.suggest_fixes:
            result = self._add_fix_suggestions(result, df, asset_name)

        return result

    def validate_and_report(
        self,
        df: pd.DataFrame,
        calendar: Optional[Any] = None,
        asset_name: str = "unknown",
        calendar_name: Optional[str] = None,
        asset_type: Optional[Literal['equity', 'forex', 'crypto']] = None,
        suggest_fixes: Optional[bool] = None
    ) -> Tuple[ValidationResult, pd.DataFrame]:
        """
        Validate OHLCV DataFrame and return result with optional fix suggestions.
        
        This method is designed for validation chaining workflows where you may
        want to validate, check results, and potentially apply fixes in a pipeline.
        
        Args:
            df: DataFrame with OHLCV columns (case-insensitive matching)
            calendar: Optional trading calendar for gap detection
            asset_name: Asset name for logging
            calendar_name: Calendar name (e.g., 'XNYS', '24/7')
            asset_type: Asset type ('equity', 'forex', 'crypto') for context-aware validation
            suggest_fixes: If True, add fix suggestions to result metadata (overrides config)
            
        Returns:
            Tuple of (ValidationResult, pd.DataFrame):
            - ValidationResult with all check outcomes and optional fix suggestions
            - Original DataFrame (unchanged, for chaining)
            
        Example:
            >>> validator = DataValidator(config=ValidationConfig(suggest_fixes=True))
            >>> result, df = validator.validate_and_report(df, asset_name='AAPL')
            >>> if not result.passed:
            ...     fixes = result.metadata.get('suggested_fixes', [])
            ...     for fix in fixes:
            ...         print(f"Suggested: {fix['description']}")
        """
        result = self.validate(
            df=df,
            calendar=calendar,
            asset_name=asset_name,
            calendar_name=calendar_name,
            asset_type=asset_type,
            suggest_fixes=suggest_fixes
        )
        return result, df

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
        """
        Detect 24/7 calendars using calendar properties, fallback to string matching.
        
        Checks calendar properties first (if available), then falls back to
        checking calendar_name against CONTINUOUS_CALENDARS set.
        
        Args:
            calendar: Calendar object (may have properties like weekmask, session_length)
            calendar_name: Calendar name string (e.g., 'CRYPTO', 'FOREX', '24/7')
            
        Returns:
            True if calendar is continuous/24/7, False otherwise
        """
        # First, try to detect using calendar object properties
        if calendar is not None:
            # Check if calendar has weekmask that includes all days (24/7)
            if hasattr(calendar, 'weekmask'):
                weekmask = calendar.weekmask
                # Check if all 7 days are included (continuous trading)
                if isinstance(weekmask, str):
                    # Check if all weekdays are present
                    all_days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
                    if all(day in weekmask for day in all_days):
                        return True
            
            # Check if calendar has a name attribute that matches continuous calendars
            if hasattr(calendar, 'name'):
                cal_name = str(calendar.name).upper()
                if cal_name in CONTINUOUS_CALENDARS:
                    return True
            
            # Check session length - if it's close to 24 hours, likely continuous
            # This is a heuristic: if session is > 23 hours, consider it continuous
            if hasattr(calendar, 'session_length'):
                try:
                    session_length = calendar.session_length
                    if hasattr(session_length, 'total_seconds'):
                        hours = session_length.total_seconds() / 3600
                        if hours >= 23.0:
                            return True
                except (AttributeError, TypeError):
                    pass
        
        # Fallback to string matching on calendar_name
        if calendar_name:
            return calendar_name.upper() in CONTINUOUS_CALENDARS
        
        return False

    def _add_fix_suggestions(
        self,
        result: ValidationResult,
        df: pd.DataFrame,
        asset_name: str
    ) -> ValidationResult:
        """
        Add fix suggestions to validation result based on detected issues.
        
        Uses lazy imports to avoid circular dependencies with lib.utils.
        
        Args:
            result: ValidationResult to add suggestions to
            df: DataFrame that was validated
            asset_name: Asset name for context
            
        Returns:
            ValidationResult with suggested fixes added to metadata
        """
        fixes = []
        
        # Check for Sunday bars issue
        sunday_bars_check = result.get_check('sunday_bars')
        if sunday_bars_check and not sunday_bars_check.passed:
            try:
                # Lazy import to avoid circular dependency
                from ..utils import consolidate_sunday_to_friday
                fixes.append({
                    'issue': 'sunday_bars',
                    'function': 'lib.utils.consolidate_sunday_to_friday',
                    'description': 'Consolidate Sunday bars into Friday to preserve weekend gap semantics',
                    'usage': f'df_fixed = consolidate_sunday_to_friday(df)',
                    'module': 'lib.utils'
                })
            except ImportError:
                logger.warning("Could not import consolidate_sunday_to_friday for fix suggestion")
        
        # Check for null values issue
        no_nulls_check = result.get_check('no_nulls')
        if no_nulls_check and not no_nulls_check.passed:
            fixes.append({
                'issue': 'no_nulls',
                'function': 'pandas.DataFrame.fillna',
                'description': 'Fill null values using forward fill or interpolation',
                'usage': "df_fixed = df.fillna(method='ffill')  # or df.interpolate()",
                'module': 'pandas'
            })
            fixes.append({
                'issue': 'no_nulls',
                'function': 'pandas.DataFrame.dropna',
                'description': 'Drop rows with null values if they are not critical',
                'usage': 'df_fixed = df.dropna()',
                'module': 'pandas'
            })
        
        # Check for unsorted index issue
        sorted_index_check = result.get_check('sorted_index')
        if sorted_index_check and not sorted_index_check.passed:
            fixes.append({
                'issue': 'sorted_index',
                'function': 'pandas.DataFrame.sort_index',
                'description': 'Sort DataFrame index in ascending order',
                'usage': 'df_fixed = df.sort_index()',
                'module': 'pandas'
            })
        
        # Check for duplicate dates issue
        duplicate_dates_check = result.get_check('duplicate_dates')
        if duplicate_dates_check and not duplicate_dates_check.passed:
            fixes.append({
                'issue': 'duplicate_dates',
                'function': 'pandas.DataFrame.drop_duplicates',
                'description': 'Remove duplicate index entries, keeping the first occurrence',
                'usage': 'df_fixed = df[~df.index.duplicated(keep="first")]',
                'module': 'pandas'
            })
        
        # Check for negative values issue
        negative_values_check = result.get_check('no_negative_values')
        if negative_values_check and not negative_values_check.passed:
            fixes.append({
                'issue': 'no_negative_values',
                'function': 'Data cleaning',
                'description': 'Review and correct negative OHLCV values - may indicate data corruption',
                'usage': 'df_fixed = df[df[["open", "high", "low", "close", "volume"]] >= 0]',
                'module': 'manual_review'
            })
        
        # Add fixes to result metadata if any were found
        if fixes:
            result.add_metadata('suggested_fixes', fixes)
            logger.debug(f"Added {len(fixes)} fix suggestions for {asset_name}")
        
        return result

    # =========================================================================
    # Individual Check Methods
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

        # Edge case: Check for all-NaN columns
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
                    col_null_dates = df.index[col_null_mask][:3]  # First 3 dates
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

        # Edge case: Check for non-numeric OHLCV values
        for col_name, col_key in [('open', o), ('high', h), ('low', l), ('close', c)]:
            if col_key and not pd.api.types.is_numeric_dtype(df[col_key]):
                result.add_error(
                    f"Column '{col_key}' ({col_name}) in {asset_name} is not numeric. "
                    f"OHLCV columns must be numeric. Found dtype: {df[col_key].dtype}"
                )
                return result

        # High >= Low
        high_low_violations = int((df[h] < df[l]).sum())

        # High >= Open and Close
        high_violations = int(((df[h] < df[o]) | (df[h] < df[c])).sum())

        # Low <= Open and Close
        low_violations = int(((df[l] > df[o]) | (df[l] > df[c])).sum())

        total_violations = high_low_violations + high_violations + low_violations

        if total_violations > 0:
            violation_pct = safe_divide(total_violations, len(df)) * 100
            
            # Find sample dates with violations
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
            # Find sample duplicate dates
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
            # Find sample unsorted pairs
            sample_issues = []
            if len(df) >= 2:
                for i in range(min(3, len(df) - 1)):
                    if df.index[i] > df.index[i + 1]:
                        sample_issues.append(f"{df.index[i]} > {df.index[i + 1]}")
            
            if is_descending:
                msg = (
                    f"Index is sorted descending for {asset_name}, should be ascending. "
                    f"Use df.sort_index() to fix."
                )
            else:
                msg = (
                    f"Index is not sorted for {asset_name}. "
                    f"Use df.sort_index() to sort in ascending order."
                )

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
            # Find sample dates with zero volume
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

    def _check_price_jumps(
        self,
        result: ValidationResult,
        df: pd.DataFrame,
        col_map: ColumnMapping,
        asset_name: str
    ) -> ValidationResult:
        """Check for sudden large price jumps."""
        close_col = col_map.close

        if not close_col:
            return result

        # Edge case: Single-row DataFrame
        if len(df) < 2:
            result.add_check(
                'price_jumps', True,
                "Insufficient data for price jump check (need at least 2 rows)"
            )
            return result

        pct_changes = df[close_col].pct_change().abs() * 100
        threshold = self.config.price_jump_threshold_pct
        large_jumps = pct_changes[pct_changes > threshold]

        if len(large_jumps) > 0:
            jump_pct = safe_divide(len(large_jumps), len(df)) * 100
            jump_dates_list = large_jumps.index[:5].tolist()
            jump_values = [f"{pct:.2f}%" for pct in large_jumps[:5].values]
            
            msg = (
                f"Found {len(large_jumps)} price jumps >{threshold}% in {asset_name}. "
                f"Large price jumps may indicate data errors, splits, or significant events. "
                f"Review these dates for data quality issues or verify if splits/adjustments are needed."
            )
            result.add_check(
                'price_jumps', False, msg,
                {
                    'jump_count': len(large_jumps),
                    'jump_pct': jump_pct,
                    'max_jump_pct': float(pct_changes.max()),
                    'jump_dates': [str(d) for d in jump_dates_list],
                    'jump_values': jump_values
                },
                severity=self.config.get_severity()
            )
        else:
            result.add_check('price_jumps', True, "No excessive price jumps detected")
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

        # Use ensure_timezone() helper for consistent timezone handling
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

    def _check_sunday_bars(
        self,
        result: ValidationResult,
        df: pd.DataFrame,
        col_map: ColumnMapping,
        asset_name: str
    ) -> ValidationResult:
        """Check for Sunday bars in FOREX/24/7 data."""
        # Only check for FOREX/24/7 calendars or forex asset_type
        if not self.config.check_sunday_bars:
            return result

        # Check if this is FOREX or 24/7 data
        is_forex = self.config.asset_type == 'forex'
        is_continuous = self._is_continuous_calendar(
            calendar=None,  # Calendar not available in this method
            calendar_name=self.config.calendar_name
        )

        if not (is_forex or is_continuous):
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

        if self.config.asset_type != 'forex':
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

        if not close_col:
            return result

        # Edge case: Single-row or insufficient data
        if len(df) < 3:
            result.add_check(
                'price_outliers', True,
                "Insufficient data for outlier check (need at least 3 rows)"
            )
            return result

        returns = df[close_col].pct_change().dropna()

        if len(returns) < 2:
            result.add_check(
                'price_outliers', True,
                "Insufficient data for outlier check (need at least 2 returns)"
            )
            return result

        z_scores = calculate_z_scores(returns)
        threshold = self.config.outlier_threshold_sigma
        outliers = int((z_scores > threshold).sum())

        if outliers > 0:
            outlier_pct = safe_divide(outliers, len(returns)) * 100
            # Find sample outlier dates
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

    def _check_volume_spikes(
        self,
        result: ValidationResult,
        df: pd.DataFrame,
        col_map: ColumnMapping,
        asset_name: str
    ) -> ValidationResult:
        """Check for volume spikes using z-score analysis."""
        volume_col = col_map.volume

        if not volume_col:
            return result

        # Edge case: Single-row or insufficient data
        if len(df) < 3:
            result.add_check(
                'volume_spikes', True,
                "Insufficient data for volume spike check (need at least 3 rows)"
            )
            return result

        # Skip volume checks for FOREX assets (volume is unreliable)
        if self.config.asset_type == 'forex':
            result.add_check(
                'volume_spikes', True,
                "Volume spike check skipped for FOREX data (volume unreliable)"
            )
            return result

        # Calculate z-scores for volume
        volume_series = df[volume_col]
        z_scores = calculate_z_scores(volume_series)
        threshold = self.config.volume_spike_threshold_sigma
        spikes = int((z_scores > threshold).sum())

        if spikes > 0:
            spike_pct = safe_divide(spikes, len(df)) * 100
            spike_dates = z_scores[z_scores > threshold].index
            max_spike_z = float(z_scores.max())
            
            msg = (
                f"Found {spikes} volume spikes (>{threshold} sigma) in {asset_name}. "
                f"Consider investigating these dates for data quality issues or significant events."
            )
            
            result.add_check(
                'volume_spikes', False, msg,
                {
                    'spike_count': spikes,
                    'spike_pct': spike_pct,
                    'max_spike_z': max_spike_z,
                    'spike_dates': [str(d) for d in spike_dates[:5].tolist()]
                },
                severity=ValidationSeverity.WARNING
            )
        else:
            result.add_check('volume_spikes', True, "No significant volume spikes detected")
        return result

    def _check_potential_splits(
        self,
        result: ValidationResult,
        df: pd.DataFrame,
        col_map: ColumnMapping,
        asset_name: str
    ) -> ValidationResult:
        """
        Detect potential unadjusted stock splits via price drops and volume spikes.
        
        Checks for common split ratios (2:1, 3:1, 4:1) and reverse splits (1:2, 1:3)
        by detecting price movements that match split patterns, cross-referenced with
        volume spikes on the same day.
        """
        close_col = col_map.close
        volume_col = col_map.volume

        if not close_col:
            return result

        # Edge case: Single-row DataFrame
        if len(df) < 2:
            result.add_check(
                'potential_splits', True,
                "Insufficient data for split detection (need at least 2 rows)"
            )
            return result

        # Only check for equity assets
        if self.config.asset_type != 'equity':
            result.add_check(
                'potential_splits', True,
                f"Split detection skipped for {self.config.asset_type or 'unknown'} asset type"
            )
            return result

        # Common split ratios: 2:1 (50% drop), 3:1 (66.7% drop), 4:1 (75% drop)
        # Also check 3:2 (33% drop) and 5:4 (25% drop) as mentioned in plan
        # Reverse splits: 1:2 (100% increase), 1:3 (200% increase)
        split_ratios = [
            (0.25, 0.28, "5:4"),      # 25% drop ±3% tolerance
            (0.33, 0.36, "3:2"),      # 33% drop ±3% tolerance
            (0.50, 0.55, "2:1"),      # 50% drop ±5% tolerance
            (0.667, 0.70, "3:1"),     # 66.7% drop ±3.3% tolerance
            (0.75, 0.78, "4:1"),      # 75% drop ±3% tolerance
            (1.00, 1.10, "1:2 reverse"),  # 100% increase ±10% tolerance
            (2.00, 2.20, "1:3 reverse"),  # 200% increase ±20% tolerance
        ]

        # Calculate price changes
        price_changes = df[close_col].pct_change().dropna()
        
        if len(price_changes) < 1:
            return result

        # Pre-calculate volume z-scores once for efficiency
        volume_z_scores = None
        volume_spike_threshold = self.config.volume_spike_threshold_sigma
        if volume_col and len(df[volume_col]) >= 3:
            try:
                volume_z_scores = calculate_z_scores(df[volume_col])
            except Exception:
                # If volume z-score calculation fails, continue without volume check
                volume_z_scores = None

        potential_splits = []
        
        for date, pct_change in price_changes.items():
            # Check for downward price drops (forward splits)
            if pct_change < 0:
                abs_change = abs(pct_change)
                for min_ratio, max_ratio, ratio_name in split_ratios[:5]:  # Forward splits only
                    if min_ratio <= abs_change <= max_ratio:
                        # Check if there's a volume spike on the same day
                        volume_z = None
                        has_volume_spike = False
                        
                        if volume_z_scores is not None and date in volume_z_scores.index:
                            volume_z = float(volume_z_scores[date])
                            has_volume_spike = volume_z > volume_spike_threshold
                        
                        # Flag if price drop matches split pattern (with or without volume spike)
                        # Volume spike strengthens the signal but isn't required
                        if has_volume_spike or volume_z_scores is None:
                            potential_splits.append({
                                'date': str(date),
                                'price_change_pct': float(pct_change * 100),
                                'split_ratio': ratio_name,
                                'volume_z_score': volume_z,
                                'has_volume_spike': has_volume_spike
                            })
                        break
            
            # Check for upward price jumps (reverse splits)
            elif pct_change > 0:
                for min_ratio, max_ratio, ratio_name in split_ratios[5:]:  # Reverse splits only
                    if min_ratio <= pct_change <= max_ratio:
                        volume_z = None
                        has_volume_spike = False
                        
                        if volume_z_scores is not None and date in volume_z_scores.index:
                            volume_z = float(volume_z_scores[date])
                            has_volume_spike = volume_z > volume_spike_threshold
                        
                        if has_volume_spike or volume_z_scores is None:
                            potential_splits.append({
                                'date': str(date),
                                'price_change_pct': float(pct_change * 100),
                                'split_ratio': ratio_name,
                                'volume_z_score': volume_z,
                                'has_volume_spike': has_volume_spike
                            })
                        break

        if potential_splits:
            msg = (
                f"Found {len(potential_splits)} potential unadjusted split(s) in {asset_name}. "
                f"Consider using adjusted close data or verifying split adjustments. "
                f"Sample dates: {', '.join([s['date'] for s in potential_splits[:3]])}"
            )
            
            result.add_check(
                'potential_splits', False, msg,
                {
                    'potential_split_count': len(potential_splits),
                    'potential_splits': potential_splits[:10]  # Limit to first 10
                },
                severity=ValidationSeverity.WARNING
            )
        else:
            result.add_check('potential_splits', True, "No potential unadjusted splits detected")
        return result

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
                    missing_dates_list = sorted(list(missing))[:5]  # First 5 missing dates
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
        # Edge case: Single-row DataFrame
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















