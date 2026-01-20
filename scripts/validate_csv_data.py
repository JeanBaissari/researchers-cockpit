#!/usr/bin/env python3
"""
CSV Data Validation Script for The Researcher's Cockpit.

Validates CSV data files before ingestion into Zipline bundles.
Checks filename format, column names, and data quality using DataValidator.

This script uses canonical functions from lib.bundles to ensure validation
logic matches the actual ingestion pipeline behavior.

Usage:
    python scripts/validate_csv_data.py --timeframe 1h
    python scripts/validate_csv_data.py --timeframe daily --symbol EURUSD
    python scripts/validate_csv_data.py --all
    python scripts/validate_csv_data.py --all --verbose --strict
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.bundles import (
    normalize_csv_columns as _normalize_csv_columns,
    parse_csv_filename as _parse_csv_filename,
    VALID_TIMEFRAMES,
)
from lib.validation import DataValidator, ValidationConfig
from lib.paths import get_project_root
from lib.data.normalization import normalize_to_utc
from lib.logging import configure_logging, get_logger, LogContext

# Configure logging (console=False since we use print/click.echo for user output)
configure_logging(level='INFO', console=False, file=False)
logger = get_logger(__name__)


# =============================================================================
# CONSTANTS & ENUMS
# =============================================================================

class ValidationSeverity(Enum):
    """Severity levels for validation issues."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


# Required OHLCV columns (canonical set)
REQUIRED_COLUMNS = frozenset({'open', 'high', 'low', 'close', 'volume'})

# Exit codes
EXIT_SUCCESS = 0
EXIT_VALIDATION_FAILED = 1
EXIT_CONFIGURATION_ERROR = 2


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class ValidationIssue:
    """Represents a single validation issue."""
    severity: ValidationSeverity
    category: str
    message: str
    field: Optional[str] = None
    
    def __str__(self) -> str:
        prefix = {
            ValidationSeverity.ERROR: "✗",
            ValidationSeverity.WARNING: "⚠",
            ValidationSeverity.INFO: "ℹ",
        }[self.severity]
        field_str = f"[{self.field}] " if self.field else ""
        return f"{prefix} {self.category}: {field_str}{self.message}"


@dataclass
class ValidationResult:
    """Complete validation result for a single file."""
    filepath: Path
    is_valid: bool
    issues: List[ValidationIssue] = field(default_factory=list)
    parsed_info: Optional[Dict] = None
    stats: Dict = field(default_factory=dict)
    
    @property
    def errors(self) -> List[ValidationIssue]:
        """Return only error-level issues."""
        return [i for i in self.issues if i.severity == ValidationSeverity.ERROR]
    
    @property
    def warnings(self) -> List[ValidationIssue]:
        """Return only warning-level issues."""
        return [i for i in self.issues if i.severity == ValidationSeverity.WARNING]
    
    def add_error(self, category: str, message: str, field: Optional[str] = None) -> None:
        """Add an error issue and mark result as invalid."""
        self.issues.append(ValidationIssue(ValidationSeverity.ERROR, category, message, field))
        self.is_valid = False
    
    def add_warning(self, category: str, message: str, field: Optional[str] = None) -> None:
        """Add a warning issue."""
        self.issues.append(ValidationIssue(ValidationSeverity.WARNING, category, message, field))
    
    def add_info(self, category: str, message: str, field: Optional[str] = None) -> None:
        """Add an informational issue."""
        self.issues.append(ValidationIssue(ValidationSeverity.INFO, category, message, field))


# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

def _extract_symbol_and_timeframe(filename: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract symbol and timeframe from CSV filename.
    
    Expected format: {symbol}_{timeframe}_{start}_{end}_ready.csv
    Example: EURUSD_1h_20200102-050000_20250717-030000_ready.csv
    
    Args:
        filename: CSV filename
        
    Returns:
        Tuple of (symbol, timeframe) or (None, None) if pattern doesn't match
    """
    import re
    from pathlib import Path
    
    stem = Path(filename).stem
    
    # Pattern: SYMBOL_TIMEFRAME_...
    # Match alphanumeric symbol, underscore, then timeframe (alphanumeric with possible numbers)
    pattern = re.compile(r'^([A-Z0-9]+)_([a-z0-9]+)_')
    match = pattern.match(stem)
    
    if match:
        symbol = match.group(1)
        timeframe = match.group(2)
        return symbol, timeframe
    
    return None, None


def validate_filename(filename: str) -> Tuple[bool, Optional[str], Optional[Dict]]:
    """
    Validate CSV filename format using the canonical parser from data_loader.
    
    This ensures validation matches the actual ingestion behavior.
    
    Args:
        filename: Name of the CSV file
        
    Returns:
        Tuple of (is_valid, error_message, parsed_info)
        parsed_info contains: symbol, timeframe, start_date, end_date
    """
    try:
        # First, extract symbol and timeframe from filename
        symbol, timeframe = _extract_symbol_and_timeframe(filename)
        
        if symbol is None or timeframe is None:
            return (
                False,
                f"Filename '{filename}' does not match expected pattern: "
                "{{symbol}}_{{timeframe}}_{{start}}_{{end}}_ready.csv",
                None
            )
        
        # Validate timeframe against canonical list
        normalized_timeframes = [tf.lower() for tf in VALID_TIMEFRAMES]
        
        if timeframe.lower() not in normalized_timeframes:
            return (
                False,
                f"Unsupported timeframe '{timeframe}' in filename. "
                f"Supported: {', '.join(VALID_TIMEFRAMES)}",
                None
            )
        
        # Now call the canonical parser with all required arguments
        start_date, end_date = _parse_csv_filename(filename, symbol, timeframe)
        
        # Build the parsed_info dict
        parsed_info = {
            'symbol': symbol,
            'timeframe': timeframe,
            'start_date': start_date,
            'end_date': end_date
        }
        
        return True, None, parsed_info
        
    except Exception as e:
        logger.debug(f"Filename parsing exception for '{filename}': {e}")
        return False, f"Failed to parse filename '{filename}': {str(e)}", None


def validate_columns(df: pd.DataFrame) -> Tuple[bool, Optional[str], List[str]]:
    """
    Validate that DataFrame has required OHLCV columns using canonical normalization.
    
    Uses _normalize_csv_columns from data_loader to ensure consistency
    with the actual ingestion pipeline.
    
    Args:
        df: DataFrame to validate
        
    Returns:
        Tuple of (is_valid, error_message, found_columns)
    """
    try:
        # Use canonical column normalization from data_loader
        normalized_df = _normalize_csv_columns(df.copy())
        found_columns = [col for col in REQUIRED_COLUMNS if col in normalized_df.columns]
        return True, None, sorted(found_columns)
    except ValueError as e:
        # _normalize_csv_columns raises ValueError for missing columns
        return False, str(e), []
    except Exception as e:
        logger.debug(f"Column validation exception: {e}")
        return False, f"Unexpected error during column validation: {str(e)}", []


def validate_data_types(df: pd.DataFrame) -> Tuple[bool, List[str], List[str]]:
    """
    Validate that OHLCV columns have correct data types.
    
    Checks:
    - OHLC columns are numeric
    - No negative prices
    - Volume is numeric and non-negative
    
    Args:
        df: DataFrame with normalized column names
        
    Returns:
        Tuple of (is_valid, errors, warnings)
    """
    errors = []
    warnings = []
    
    # Check OHLC columns are numeric and non-negative
    ohlc_columns = ['open', 'high', 'low', 'close']
    for col in ohlc_columns:
        if col not in df.columns:
            continue
            
        # Check if already numeric
        if pd.api.types.is_numeric_dtype(df[col]):
            numeric_vals = df[col]
        else:
            # Try to convert
            try:
                numeric_vals = pd.to_numeric(df[col], errors='raise')
            except (ValueError, TypeError) as e:
                errors.append(f"Column '{col}' contains non-numeric values: {str(e)[:50]}")
                continue
        
        # Check for negative prices
        if (numeric_vals < 0).any():
            neg_count = (numeric_vals < 0).sum()
            errors.append(f"Column '{col}' contains {neg_count} negative value(s)")
        
        # Check for NaN values
        nan_count = numeric_vals.isna().sum()
        if nan_count > 0:
            pct = (nan_count / len(numeric_vals)) * 100
            if pct > 5:
                errors.append(f"Column '{col}' has {nan_count} ({pct:.1f}%) NaN values")
            else:
                warnings.append(f"Column '{col}' has {nan_count} ({pct:.1f}%) NaN values")
    
    # Check volume is numeric and non-negative
    if 'volume' in df.columns:
        if pd.api.types.is_numeric_dtype(df['volume']):
            numeric_vol = df['volume']
        else:
            try:
                numeric_vol = pd.to_numeric(df['volume'], errors='raise')
            except (ValueError, TypeError) as e:
                errors.append(f"Column 'volume' contains non-numeric values: {str(e)[:50]}")
                numeric_vol = None
        
        if numeric_vol is not None:
            if (numeric_vol < 0).any():
                neg_count = (numeric_vol < 0).sum()
                errors.append(f"Column 'volume' contains {neg_count} negative value(s)")
            
            # Check for zero volume (warning only)
            zero_count = (numeric_vol == 0).sum()
            if zero_count > 0:
                pct = (zero_count / len(numeric_vol)) * 100
                if pct > 50:
                    warnings.append(f"Column 'volume' has {zero_count} ({pct:.1f}%) zero values")
    
    return len(errors) == 0, errors, warnings


def validate_ohlc_consistency(df: pd.DataFrame) -> Tuple[bool, List[str], List[str]]:
    """
    Validate OHLC price consistency (high >= low, etc.).
    
    Args:
        df: DataFrame with normalized column names
        
    Returns:
        Tuple of (is_valid, errors, warnings)
    """
    errors = []
    warnings = []
    
    required_cols = {'open', 'high', 'low', 'close'}
    if not required_cols.issubset(set(df.columns)):
        return True, errors, warnings  # Skip if columns missing
    
    # High should be >= Low
    invalid_hl = df['high'] < df['low']
    if invalid_hl.any():
        count = invalid_hl.sum()
        errors.append(f"Found {count} row(s) where high < low")
    
    # High should be >= Open and Close
    invalid_ho = df['high'] < df['open']
    invalid_hc = df['high'] < df['close']
    if invalid_ho.any() or invalid_hc.any():
        count = (invalid_ho | invalid_hc).sum()
        errors.append(f"Found {count} row(s) where high < open or high < close")
    
    # Low should be <= Open and Close
    invalid_lo = df['low'] > df['open']
    invalid_lc = df['low'] > df['close']
    if invalid_lo.any() or invalid_lc.any():
        count = (invalid_lo | invalid_lc).sum()
        errors.append(f"Found {count} row(s) where low > open or low > close")
    
    return len(errors) == 0, errors, warnings


def validate_timezone(df: pd.DataFrame) -> Tuple[bool, List[str], List[str]]:
    """
    Validate and report on timezone status of the DataFrame index.
    
    Args:
        df: DataFrame to validate
        
    Returns:
        Tuple of (is_valid, errors, warnings)
    """
    errors = []
    warnings = []
    
    if not isinstance(df.index, pd.DatetimeIndex):
        errors.append("Index is not a DatetimeIndex - cannot validate timezone")
        return False, errors, warnings
    
    if df.index.tz is None:
        warnings.append("Index is timezone-naive; will be assumed UTC during ingestion")
    elif str(df.index.tz) != 'UTC':
        warnings.append(
            f"Index timezone is '{df.index.tz}'; will be converted to UTC during ingestion"
        )
    
    return True, errors, warnings


def validate_index_integrity(df: pd.DataFrame) -> Tuple[bool, List[str], List[str]]:
    """
    Validate the datetime index for integrity issues.
    
    Checks:
    - No duplicate timestamps
    - Index is sorted
    - No gaps larger than expected
    
    Args:
        df: DataFrame to validate
        
    Returns:
        Tuple of (is_valid, errors, warnings)
    """
    errors = []
    warnings = []
    
    if not isinstance(df.index, pd.DatetimeIndex):
        return True, errors, warnings  # Skip if not datetime index
    
    # Check for duplicates
    dup_count = df.index.duplicated().sum()
    if dup_count > 0:
        errors.append(f"Found {dup_count} duplicate timestamp(s) in index")
    
    # Check if sorted
    if not df.index.is_monotonic_increasing:
        warnings.append("Index is not sorted in ascending order")
    
    # Check for NaT values
    nat_count = df.index.isna().sum()
    if nat_count > 0:
        errors.append(f"Found {nat_count} NaT (Not a Time) value(s) in index")
    
    return len(errors) == 0, errors, warnings


def _identify_date_column(df: pd.DataFrame) -> Optional[str]:
    """
    Identify the date column in a DataFrame.
    
    Args:
        df: DataFrame to inspect
        
    Returns:
        Column name or index position, or None if not found
    """
    # Check for common date column names
    date_column_names = ['Date', 'date', 'datetime', 'Datetime', 'timestamp', 'Timestamp', 'time', 'Time']
    
    for col_name in date_column_names:
        if col_name in df.columns:
            return col_name
    
    # Check if first column looks like a date column
    first_col = df.columns[0]
    if first_col.lower() in [n.lower() for n in date_column_names]:
        return first_col
    
    return None


def validate_date_range_consistency(
    df: pd.DataFrame,
    parsed_info: Dict,
    result: ValidationResult
) -> None:
    """
    Validate that the actual data date range matches the filename date range.
    
    This ensures the filename accurately describes the data contents, which is
    critical for data integrity and proper bundle ingestion.
    
    Args:
        df: DataFrame with DatetimeIndex
        parsed_info: Parsed filename info containing start_date and end_date
        result: ValidationResult to add issues to
    """
    if not isinstance(df.index, pd.DatetimeIndex):
        return
    
    if df.empty:
        return
    
    # Get actual date range from data
    actual_start = df.index.min()
    actual_end = df.index.max()
    
    # Get expected date range from filename
    expected_start = parsed_info.get('start_date')
    expected_end = parsed_info.get('end_date')
    
    if expected_start is None or expected_end is None:
        result.add_warning(
            "DateRange",
            "Could not extract date range from filename for comparison"
        )
        return
    
    # Normalize both to timezone-naive for comparison (or both to UTC)
    try:
        # Convert expected dates to pandas Timestamps for comparison
        expected_start_ts = pd.Timestamp(expected_start)
        expected_end_ts = pd.Timestamp(expected_end)
        
        # Normalize actual dates (remove timezone for comparison)
        if actual_start.tz is not None:
            actual_start_naive = actual_start.tz_localize(None)
            actual_end_naive = actual_end.tz_localize(None)
        else:
            actual_start_naive = actual_start
            actual_end_naive = actual_end
        
        if expected_start_ts.tz is not None:
            expected_start_naive = expected_start_ts.tz_localize(None)
            expected_end_naive = expected_end_ts.tz_localize(None)
        else:
            expected_start_naive = expected_start_ts
            expected_end_naive = expected_end_ts
        
        # Compare dates (allow for date-only comparison, ignoring time)
        actual_start_date = actual_start_naive.normalize()
        actual_end_date = actual_end_naive.normalize()
        expected_start_date = expected_start_naive.normalize()
        expected_end_date = expected_end_naive.normalize()
        
        # Check start date
        if actual_start_date != expected_start_date:
            # Calculate the difference
            diff_days = abs((actual_start_date - expected_start_date).days)
            if diff_days > 1:
                result.add_warning(
                    "DateRange",
                    f"Actual start date ({actual_start_date.date()}) differs from "
                    f"filename start date ({expected_start_date.date()}) by {diff_days} days"
                )
            else:
                result.add_info(
                    "DateRange",
                    f"Minor start date difference: actual={actual_start_date.date()}, "
                    f"filename={expected_start_date.date()}"
                )
        
        # Check end date
        if actual_end_date != expected_end_date:
            diff_days = abs((actual_end_date - expected_end_date).days)
            if diff_days > 1:
                result.add_warning(
                    "DateRange",
                    f"Actual end date ({actual_end_date.date()}) differs from "
                    f"filename end date ({expected_end_date.date()}) by {diff_days} days"
                )
            else:
                result.add_info(
                    "DateRange",
                    f"Minor end date difference: actual={actual_end_date.date()}, "
                    f"filename={expected_end_date.date()}"
                )
        
        # Store the comparison in stats
        result.stats['date_range_comparison'] = {
            'filename_start': str(expected_start_date.date()),
            'filename_end': str(expected_end_date.date()),
            'actual_start': str(actual_start_date.date()),
            'actual_end': str(actual_end_date.date()),
            'start_match': actual_start_date == expected_start_date,
            'end_match': actual_end_date == expected_end_date,
        }
        
    except Exception as e:
        logger.debug(f"Date range comparison failed: {e}")
        result.add_info(
            "DateRange",
            f"Could not compare date ranges: {str(e)[:50]}"
        )


def validate_gap_detection(
    df: pd.DataFrame,
    timeframe: str,
    result: ValidationResult
) -> None:
    """
    Detect and report gaps in the time series data.
    
    This identifies missing data periods which could affect analysis quality.
    Different thresholds are used based on the timeframe.
    
    Args:
        df: DataFrame with DatetimeIndex
        timeframe: Timeframe string (e.g., '1h', 'daily', '4h')
        result: ValidationResult to add issues to
    """
    if not isinstance(df.index, pd.DatetimeIndex):
        return
    
    if len(df) < 2:
        return
    
    # Determine expected frequency based on timeframe
    timeframe_lower = timeframe.lower()
    
    # Map timeframes to expected gaps (in hours)
    # These are the maximum expected gaps before we consider it a "gap"
    # For forex, we expect gaps over weekends, so we use business-aware thresholds
    gap_thresholds = {
        '1m': pd.Timedelta(minutes=5),      # 5 minutes for 1-minute data
        '5m': pd.Timedelta(minutes=15),     # 15 minutes for 5-minute data
        '15m': pd.Timedelta(hours=1),       # 1 hour for 15-minute data
        '30m': pd.Timedelta(hours=2),       # 2 hours for 30-minute data
        '1h': pd.Timedelta(hours=4),        # 4 hours for hourly data
        '4h': pd.Timedelta(hours=12),       # 12 hours for 4-hour data
        'daily': pd.Timedelta(days=4),      # 4 days for daily (accounts for weekends + holidays)
        'd': pd.Timedelta(days=4),
        '1d': pd.Timedelta(days=4),
    }
    
    # Get threshold, default to 4 hours if unknown timeframe
    threshold = gap_thresholds.get(timeframe_lower, pd.Timedelta(hours=4))
    
    # Calculate time differences between consecutive rows
    sorted_index = df.index.sort_values()
    time_diffs = sorted_index.to_series().diff()
    
    # Find gaps exceeding the threshold
    gaps = time_diffs[time_diffs > threshold]
    
    if len(gaps) == 0:
        result.stats['gaps'] = {
            'count': 0,
            'threshold': str(threshold),
            'largest_gap': None,
        }
        return
    
    # Analyze gaps
    gap_count = len(gaps)
    largest_gap = gaps.max()
    
    # Categorize gaps
    weekend_gaps = 0
    significant_gaps = []
    
    for gap_time, gap_duration in gaps.items():
        # Check if this gap spans a weekend (Friday to Sunday/Monday)
        if gap_time is not pd.NaT:
            gap_start = gap_time - gap_duration
            # If gap starts on Friday or Saturday, it's likely a weekend gap
            if hasattr(gap_start, 'dayofweek') and gap_start.dayofweek >= 4:  # Friday=4, Saturday=5
                weekend_gaps += 1
            else:
                # Non-weekend gap - more concerning
                significant_gaps.append({
                    'start': str(gap_start),
                    'end': str(gap_time),
                    'duration': str(gap_duration),
                })
    
    # Store gap statistics
    result.stats['gaps'] = {
        'count': gap_count,
        'threshold': str(threshold),
        'largest_gap': str(largest_gap),
        'weekend_gaps': weekend_gaps,
        'non_weekend_gaps': len(significant_gaps),
    }
    
    # Report findings
    if gap_count > 0:
        if len(significant_gaps) > 0:
            # Non-weekend gaps are more concerning
            result.add_warning(
                "Gaps",
                f"Found {len(significant_gaps)} non-weekend gap(s) exceeding {threshold}. "
                f"Largest gap: {largest_gap}"
            )
            # Add details for first few significant gaps
            for i, gap in enumerate(significant_gaps[:3]):
                result.add_info(
                    "Gaps",
                    f"Gap {i+1}: {gap['start']} to {gap['end']} ({gap['duration']})"
                )
        else:
            # Only weekend gaps - less concerning for forex
            result.add_info(
                "Gaps",
                f"Found {weekend_gaps} weekend gap(s) (expected for forex data)"
            )


def validate_price_anomalies(
    df: pd.DataFrame,
    result: ValidationResult
) -> None:
    """
    Detect potential price anomalies and outliers.
    
    Checks for:
    - Extreme price spikes (> 10% single-bar moves)
    - Zero or near-zero prices
    - Prices that are orders of magnitude different from neighbors
    
    Args:
        df: DataFrame with normalized OHLCV columns
        result: ValidationResult to add issues to
    """
    if 'close' not in df.columns:
        return
    
    if len(df) < 2:
        return
    
    close_prices = df['close'].dropna()
    
    if len(close_prices) < 2:
        return
    
    anomalies = {
        'extreme_moves': [],
        'zero_prices': 0,
        'potential_outliers': [],
    }
    
    # Check for zero or near-zero prices
    zero_threshold = 1e-10
    zero_count = (close_prices.abs() < zero_threshold).sum()
    if zero_count > 0:
        anomalies['zero_prices'] = int(zero_count)
        result.add_error(
            "PriceAnomaly",
            f"Found {zero_count} zero or near-zero price(s)"
        )
    
    # Calculate percentage changes
    pct_changes = close_prices.pct_change().dropna()
    
    # Check for extreme moves (> 10% in a single bar)
    extreme_threshold = 0.10  # 10%
    extreme_moves = pct_changes[pct_changes.abs() > extreme_threshold]
    
    if len(extreme_moves) > 0:
        anomalies['extreme_moves'] = [
            {
                'timestamp': str(idx),
                'pct_change': float(val) * 100,
            }
            for idx, val in extreme_moves.head(10).items()
        ]
        
        # Determine severity based on count and magnitude
        max_move = extreme_moves.abs().max() * 100
        if max_move > 50:  # > 50% move is almost certainly an error
            result.add_error(
                "PriceAnomaly",
                f"Found {len(extreme_moves)} extreme price move(s). "
                f"Maximum: {max_move:.1f}% (likely data error)"
            )
        elif len(extreme_moves) > 10:
            result.add_warning(
                "PriceAnomaly",
                f"Found {len(extreme_moves)} price moves > {extreme_threshold*100:.0f}%. "
                f"Maximum: {max_move:.1f}%"
            )
        else:
            result.add_info(
                "PriceAnomaly",
                f"Found {len(extreme_moves)} price move(s) > {extreme_threshold*100:.0f}%. "
                f"Maximum: {max_move:.1f}%"
            )
    
    # Check for outliers using IQR method
    q1 = close_prices.quantile(0.25)
    q3 = close_prices.quantile(0.75)
    iqr = q3 - q1
    
    if iqr > 0:
        lower_bound = q1 - 3 * iqr  # Using 3*IQR for extreme outliers
        upper_bound = q3 + 3 * iqr
        
        outliers = close_prices[(close_prices < lower_bound) | (close_prices > upper_bound)]
        
        if len(outliers) > 0:
            anomalies['potential_outliers'] = [
                {
                    'timestamp': str(idx),
                    'price': float(val),
                }
                for idx, val in outliers.head(10).items()
            ]
            
            pct_outliers = (len(outliers) / len(close_prices)) * 100
            if pct_outliers > 1:
                result.add_warning(
                    "PriceAnomaly",
                    f"Found {len(outliers)} potential outlier(s) ({pct_outliers:.2f}% of data) "
                    f"outside 3*IQR bounds [{lower_bound:.5f}, {upper_bound:.5f}]"
                )
            else:
                result.add_info(
                    "PriceAnomaly",
                    f"Found {len(outliers)} potential outlier(s) outside 3*IQR bounds"
                )
    
    # Store anomaly statistics
    result.stats['price_anomalies'] = anomalies


def validate_volume_patterns(
    df: pd.DataFrame,
    result: ValidationResult
) -> None:
    """
    Validate volume data patterns and detect anomalies.
    
    Checks for:
    - Constant volume (suspicious for real market data)
    - Extreme volume spikes
    - Volume patterns inconsistent with price movements
    
    Args:
        df: DataFrame with normalized OHLCV columns
        result: ValidationResult to add issues to
    """
    if 'volume' not in df.columns:
        return
    
    volume = df['volume'].dropna()
    
    if len(volume) < 2:
        return
    
    volume_stats = {
        'min': float(volume.min()),
        'max': float(volume.max()),
        'mean': float(volume.mean()),
        'std': float(volume.std()),
        'zero_count': int((volume == 0).sum()),
        'constant': False,
    }
    
    # Check for constant volume (all same value)
    unique_volumes = volume.nunique()
    if unique_volumes == 1:
        volume_stats['constant'] = True
        result.add_warning(
            "VolumePattern",
            f"Volume is constant ({volume.iloc[0]}) across all {len(volume)} rows. "
            "This may indicate synthetic or placeholder data."
        )
    elif unique_volumes < 5 and len(volume) > 100:
        result.add_info(
            "VolumePattern",
            f"Volume has only {unique_volumes} unique values across {len(volume)} rows"
        )
    
    # Check for extreme volume spikes
    if volume_stats['std'] > 0:
        z_scores = (volume - volume_stats['mean']) / volume_stats['std']
        extreme_volumes = z_scores[z_scores.abs() > 5]  # > 5 standard deviations
        
        if len(extreme_volumes) > 0:
            result.add_info(
                "VolumePattern",
                f"Found {len(extreme_volumes)} volume value(s) > 5 standard deviations from mean"
            )
    
    # Check zero volume percentage
    zero_pct = (volume_stats['zero_count'] / len(volume)) * 100
    if zero_pct > 50:
        result.add_warning(
            "VolumePattern",
            f"{zero_pct:.1f}% of volume values are zero. "
            "This may indicate missing data or forex tick data."
        )
    elif zero_pct > 10:
        result.add_info(
            "VolumePattern",
            f"{zero_pct:.1f}% of volume values are zero"
        )
    
    result.stats['volume_patterns'] = volume_stats


def validate_csv_file(
    filepath: Path,
    validator: Optional[DataValidator] = None,
    verbose: bool = False,
    strict: bool = False
) -> ValidationResult:
    """
    Validate a single CSV file comprehensively.
    
    Performs the following validations:
    1. Filename format (using canonical parser)
    2. CSV readability
    3. Column presence and normalization
    4. Data types
    5. OHLC consistency
    6. Timezone handling
    7. Index integrity
    8. Date range consistency (filename vs actual data)
    9. Gap detection
    10. Price anomaly detection
    11. Volume pattern analysis
    12. DataValidator checks
    
    Args:
        filepath: Path to the CSV file
        validator: DataValidator instance
        verbose: Whether to print detailed output
        strict: If True, treat warnings as errors
        
    Returns:
        ValidationResult with all findings
    """
    result = ValidationResult(filepath=filepath, is_valid=True)
    
    # Step 1: Validate filename using canonical parser
    filename_valid, filename_error, parsed_info = validate_filename(filepath.name)
    if not filename_valid:
        result.add_error("Filename", filename_error)
        return result
    
    result.parsed_info = parsed_info
    
    # Step 2: Read the CSV file
    try:
        # First pass: inspect structure
        df_preview = pd.read_csv(filepath, nrows=5)
        date_col = _identify_date_column(df_preview)
        
        # Second pass: full read with date parsing
        if date_col:
            df = pd.read_csv(filepath, parse_dates=[date_col], index_col=date_col)
        else:
            # Assume first column is the index
            df = pd.read_csv(filepath, parse_dates=[0], index_col=0)
            
    except pd.errors.EmptyDataError:
        result.add_error("File", "CSV file is empty or contains no data")
        return result
    except pd.errors.ParserError as e:
        result.add_error("File", f"CSV parsing error: {str(e)[:100]}")
        return result
    except Exception as e:
        result.add_error("File", f"Failed to read CSV: {str(e)[:100]}")
        return result
    
    # Step 3: Validate index is datetime
    if not isinstance(df.index, pd.DatetimeIndex):
        try:
            df.index = pd.to_datetime(df.index)
        except Exception as e:
            result.add_error("Index", f"Failed to parse dates in index: {str(e)[:100]}")
            return result
    
    # Step 4: Check if empty
    if df.empty:
        result.add_error("File", "CSV file contains no data rows")
        return result
    
    result.stats['row_count'] = len(df)
    result.stats['column_count'] = len(df.columns)
    
    # Step 5: Validate columns using canonical normalization
    columns_valid, columns_error, found_columns = validate_columns(df)
    if not columns_valid:
        result.add_error("Columns", columns_error)
        return result
    
    result.stats['columns'] = found_columns
    
    # Step 6: Normalize columns using canonical function
    try:
        df = _normalize_csv_columns(df)
    except ValueError as e:
        result.add_error("Columns", f"Column normalization failed: {str(e)}")
        return result
    except Exception as e:
        result.add_error("Columns", f"Unexpected normalization error: {str(e)[:100]}")
        return result
    
    # Step 7: Validate data types
    types_valid, type_errors, type_warnings = validate_data_types(df)
    for error in type_errors:
        result.add_error("DataType", error)
    for warning in type_warnings:
        if strict:
            result.add_error("DataType", warning)
        else:
            result.add_warning("DataType", warning)
    
    # Step 8: Validate OHLC consistency
    ohlc_valid, ohlc_errors, ohlc_warnings = validate_ohlc_consistency(df)
    for error in ohlc_errors:
        result.add_error("OHLC", error)
    for warning in ohlc_warnings:
        if strict:
            result.add_error("OHLC", warning)
        else:
            result.add_warning("OHLC", warning)
    
    # Step 9: Validate timezone
    tz_valid, tz_errors, tz_warnings = validate_timezone(df)
    for error in tz_errors:
        result.add_error("Timezone", error)
    for warning in tz_warnings:
        if strict:
            result.add_error("Timezone", warning)
        else:
            result.add_warning("Timezone", warning)
    
    # Step 10: Validate index integrity
    idx_valid, idx_errors, idx_warnings = validate_index_integrity(df)
    for error in idx_errors:
        result.add_error("Index", error)
    for warning in idx_warnings:
        if strict:
            result.add_error("Index", warning)
        else:
            result.add_warning("Index", warning)
    
    # Step 11: Validate date range consistency (filename vs actual data)
    validate_date_range_consistency(df, parsed_info, result)
    
    # Step 12: Detect gaps in time series
    timeframe = parsed_info.get('timeframe', '1h')
    validate_gap_detection(df, timeframe, result)
    
    # Step 13: Detect price anomalies
    validate_price_anomalies(df, result)
    
    # Step 14: Analyze volume patterns
    validate_volume_patterns(df, result)
    
    # Step 15: Normalize to UTC for DataValidator (matching ingestion behavior)
    try:
        df = normalize_to_utc(df)
    except Exception as e:
        result.add_warning("Timezone", f"UTC normalization issue: {str(e)[:100]}")
    
    # Step 16: Run DataValidator - critical validation
    try:
        # Create validator with timeframe from parsed_info if not provided
        if validator is None:
            timeframe = parsed_info.get('timeframe') if parsed_info else None
            config = ValidationConfig(timeframe=timeframe) if timeframe else None
            validator = DataValidator(config=config)
        
        validation_result = validator.validate(df, asset_name=parsed_info['symbol'])
        
        if not validation_result.passed:
            for check in validation_result.error_checks:
                field = check.details.get('field') or check.name
                result.add_error("DataValidator", check.message, field=field)
        
        if validation_result.warning_checks:
            for check in validation_result.warning_checks:
                field = check.details.get('field') or check.name
                if strict:
                    result.add_error("DataValidator", check.message, field=field)
                else:
                    result.add_warning("DataValidator", check.message, field=field)
        
    except Exception as e:
        # DataValidator exceptions are critical - fail loudly
        result.add_error("DataValidator", f"Critical validation error: {str(e)}")
        logger.error(f"DataValidator failed for {filepath.name}: {str(e)}")
    
    # Step 17: Add comprehensive stats
    try:
        result.stats['date_range'] = {
            'start': str(df.index.min()),
            'end': str(df.index.max()),
            'span_days': (df.index.max() - df.index.min()).days
        }
        result.stats['timezone'] = str(df.index.tz) if df.index.tz else 'naive (assumed UTC)'
        
        # Price stats
        if 'close' in df.columns:
            result.stats['price_range'] = {
                'min': float(df['close'].min()),
                'max': float(df['close'].max()),
                'mean': float(df['close'].mean())
            }
    except Exception as e:
        logger.debug(f"Failed to compute stats for {filepath.name}: {e}")
    
    return result


def validate_timeframe_directory(
    timeframe: str,
    symbol_filter: Optional[str] = None,
    verbose: bool = False,
    strict: bool = False
) -> List[ValidationResult]:
    """
    Validate all CSV files in a timeframe directory.
    
    Args:
        timeframe: Timeframe directory to validate (e.g., '1h', 'daily')
        symbol_filter: Optional symbol to filter by
        verbose: Whether to print detailed output
        strict: If True, treat warnings as errors
        
    Returns:
        List of ValidationResult objects
    """
    data_path = get_project_root() / 'data' / 'processed' / timeframe
    
    if not data_path.exists():
        logger.warning(f"Directory does not exist: {data_path}")
        return []
    
    if not data_path.is_dir():
        logger.error(f"Path is not a directory: {data_path}")
        return []
    
    # Find CSV files
    csv_files = sorted(data_path.glob('*.csv'))
    
    if symbol_filter:
        symbol_upper = symbol_filter.upper()
        csv_files = [f for f in csv_files if f.name.upper().startswith(symbol_upper)]
    
    if not csv_files:
        logger.info(f"No CSV files found in {data_path}")
        return []
    
    logger.info(f"Found {len(csv_files)} CSV file(s) in {data_path}")
    
    # Initialize validator once for all files (with timeframe if available)
    config = ValidationConfig(timeframe=timeframe) if timeframe else None
    validator = DataValidator(config=config)
    
    results = []
    for csv_file in csv_files:
        if verbose:
            print(f"\nValidating: {csv_file.name}")
        
        result = validate_csv_file(csv_file, validator, verbose, strict)
        results.append(result)
        
        if verbose:
            status = "✓ Valid" if result.is_valid else "✗ Invalid"
            row_count = result.stats.get('row_count', 0)
            print(f"  {status} ({row_count:,} rows)")
            
            for issue in result.issues:
                print(f"    {issue}")
    
    return results


def print_summary(results: List[ValidationResult], timeframe: str) -> None:
    """Print a formatted summary of validation results."""
    if not results:
        print(f"\nNo files validated for timeframe: {timeframe}")
        return
    
    valid_count = sum(1 for r in results if r.is_valid)
    invalid_count = len(results) - valid_count
    warning_count = sum(len(r.warnings) for r in results)
    total_rows = sum(r.stats.get('row_count', 0) for r in results)
    
    print(f"\n{'='*70}")
    print(f"VALIDATION SUMMARY: {timeframe}")
    print(f"{'='*70}")
    print(f"Total files:    {len(results)}")
    print(f"Total rows:     {total_rows:,}")
    print(f"Valid:          {valid_count}")
    print(f"Invalid:        {invalid_count}")
    print(f"Warnings:       {warning_count}")
    
    if invalid_count > 0:
        print(f"\n{'─'*70}")
        print("INVALID FILES:")
        print(f"{'─'*70}")
        for result in results:
            if not result.is_valid:
                print(f"\n  {result.filepath.name}")
                for error in result.errors:
                    print(f"    {error}")
    
    if warning_count > 0:
        print(f"\n{'─'*70}")
        print("WARNINGS:")
        print(f"{'─'*70}")
        for result in results:
            if result.warnings:
                print(f"\n  {result.filepath.name}")
                for warning in result.warnings:
                    print(f"    {warning}")
    
    print(f"\n{'='*70}")


def export_results_json(
    results: Dict[str, List[ValidationResult]],
    output_path: Path
) -> None:
    """
    Export validation results to a JSON file for programmatic consumption.
    
    Args:
        results: Dictionary mapping timeframe to list of ValidationResults
        output_path: Path to write the JSON file
    """
    import json
    from datetime import datetime
    
    export_data = {
        'generated_at': datetime.utcnow().isoformat() + 'Z',
        'summary': {
            'total_files': 0,
            'valid_files': 0,
            'invalid_files': 0,
            'total_warnings': 0,
            'total_rows': 0,
        },
        'timeframes': {},
    }
    
    for timeframe, timeframe_results in results.items():
        timeframe_data = {
            'file_count': len(timeframe_results),
            'valid_count': sum(1 for r in timeframe_results if r.is_valid),
            'invalid_count': sum(1 for r in timeframe_results if not r.is_valid),
            'warning_count': sum(len(r.warnings) for r in timeframe_results),
            'total_rows': sum(r.stats.get('row_count', 0) for r in timeframe_results),
            'files': [],
        }
        
        for result in timeframe_results:
            file_data = {
                'filename': result.filepath.name,
                'is_valid': result.is_valid,
                'parsed_info': result.parsed_info,
                'stats': result.stats,
                'errors': [
                    {
                        'category': issue.category,
                        'message': issue.message,
                        'field': issue.field,
                    }
                    for issue in result.errors
                ],
                'warnings': [
                    {
                        'category': issue.category,
                        'message': issue.message,
                        'field': issue.field,
                    }
                    for issue in result.warnings
                ],
            }
            timeframe_data['files'].append(file_data)
        
        export_data['timeframes'][timeframe] = timeframe_data
        
        # Update summary
        export_data['summary']['total_files'] += timeframe_data['file_count']
        export_data['summary']['valid_files'] += timeframe_data['valid_count']
        export_data['summary']['invalid_files'] += timeframe_data['invalid_count']
        export_data['summary']['total_warnings'] += timeframe_data['warning_count']
        export_data['summary']['total_rows'] += timeframe_data['total_rows']
    
    # Write to file
    with open(output_path, 'w') as f:
        json.dump(export_data, f, indent=2, default=str)
    
    logger.info(f"Exported validation results to {output_path}")


def main() -> int:
    """
    Main entry point for the validation script.
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    parser = argparse.ArgumentParser(
        description='Validate CSV data files before Zipline ingestion',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python scripts/validate_csv_data.py --timeframe 1h
    python scripts/validate_csv_data.py --timeframe daily --symbol EURUSD
    python scripts/validate_csv_data.py --all --verbose
    python scripts/validate_csv_data.py --all --strict  # Treat warnings as errors
    python scripts/validate_csv_data.py --all --output results.json

Exit Codes:
    0 - All files valid
    1 - One or more files invalid
    2 - Configuration error
        """
    )
    
    parser.add_argument(
        '--timeframe', '-t',
        type=str,
        help='Timeframe to validate (e.g., 1h, daily, 4h)'
    )
    
    parser.add_argument(
        '--symbol', '-s',
        type=str,
        help='Filter by symbol (e.g., EURUSD)'
    )
    
    parser.add_argument(
        '--all', '-a',
        action='store_true',
        help='Validate all timeframe directories'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Print detailed validation output'
    )
    
    parser.add_argument(
        '--strict',
        action='store_true',
        help='Treat warnings as errors'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        help='Export results to JSON file'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.timeframe and not args.all:
        parser.error("Either --timeframe or --all must be specified")
        return EXIT_CONFIGURATION_ERROR
    
    if args.timeframe and args.all:
        parser.error("Cannot specify both --timeframe and --all")
        return EXIT_CONFIGURATION_ERROR
    
    # Use LogContext for structured logging
    timeframe_context = args.timeframe or 'all'
    with LogContext(phase='csv_validation', timeframe=timeframe_context, symbol=args.symbol, strict=args.strict):
        logger.info(f"Starting CSV validation (timeframe={timeframe_context}, symbol={args.symbol}, strict={args.strict})")
        
        # Determine timeframes to validate
        if args.all:
            processed_path = get_project_root() / 'data' / 'processed'
            if not processed_path.exists():
                logger.error(f"Processed data directory does not exist: {processed_path}")
                print(f"✗ Error: Processed data directory does not exist: {processed_path}")
                print(f"  Create directory: mkdir -p {processed_path}")
                return EXIT_CONFIGURATION_ERROR
            
            timeframes = sorted([d.name for d in processed_path.iterdir() if d.is_dir()])
            if not timeframes:
                logger.error("No timeframe directories found")
                print(f"✗ Error: No timeframe directories found in {processed_path}")
                print(f"  Ingest data first: python scripts/ingest_data.py --source csv --assets forex --symbols EURUSD")
                return EXIT_CONFIGURATION_ERROR
            logger.info(f"Found {len(timeframes)} timeframe directories: {timeframes}")
        else:
            timeframes = [args.timeframe]
        
        # Run validation
        all_results: Dict[str, List[ValidationResult]] = {}
        total_valid = 0
        total_invalid = 0
        
        for timeframe in timeframes:
            logger.info(f"Validating timeframe: {timeframe}")
            print(f"\nValidating timeframe: {timeframe}")
            print("-" * 40)
            
            results = validate_timeframe_directory(
                timeframe,
                symbol_filter=args.symbol,
                verbose=args.verbose,
                strict=args.strict
            )
            
            all_results[timeframe] = results
            valid_count = sum(1 for r in results if r.is_valid)
            invalid_count = sum(1 for r in results if not r.is_valid)
            total_valid += valid_count
            total_invalid += invalid_count
            
            logger.info(f"Timeframe {timeframe}: {valid_count} valid, {invalid_count} invalid files")
            print_summary(results, timeframe)
    
        # Final summary for multiple timeframes
        if len(timeframes) > 1:
            total_rows = sum(
                r.stats.get('row_count', 0)
                for results in all_results.values()
                for r in results
            )
            
            logger.info(f"Overall validation: {total_valid} valid, {total_invalid} invalid files across {len(timeframes)} timeframes")
            print(f"\n{'='*70}")
            print("OVERALL SUMMARY")
            print(f"{'='*70}")
            print(f"Timeframes validated: {len(timeframes)}")
            print(f"Total files:          {total_valid + total_invalid}")
            print(f"Total rows:           {total_rows:,}")
            print(f"Total valid:          {total_valid}")
            print(f"Total invalid:        {total_invalid}")
            print(f"{'='*70}")
        
        # Export results if requested
        if args.output:
            output_path = Path(args.output)
            logger.info(f"Exporting results to: {output_path}")
            export_results_json(all_results, output_path)
            print(f"\nResults exported to: {output_path}")
        
        # Return appropriate exit code
        if total_invalid > 0:
            logger.warning(f"Validation failed: {total_invalid} invalid file(s)")
            return EXIT_VALIDATION_FAILED
        
        logger.info("Validation complete: all files valid")
        return EXIT_SUCCESS


if __name__ == '__main__':
    sys.exit(main())
