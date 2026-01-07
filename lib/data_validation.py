"""
Data validation module for The Researcher's Cockpit.

Provides multi-layer validation for OHLCV data:
- Pre-ingestion source validation
- Ingestion-time bundle creation checks
- Pre-backtest bundle verification
- Post-backtest results validation

Architecture:
    - ValidationSeverity: Enum for validation severity levels
    - ValidationCheck: Individual check result container
    - ValidationResult: Aggregated validation results with merge support
    - BaseValidator: Abstract base for all validators (DRY pattern)
    - DataValidator: OHLCV data validation
    - BundleValidator: Bundle integrity validation
    - BacktestValidator: Backtest results validation
    - SchemaValidator: DataFrame schema validation
    - CompositeValidator: Pipeline multiple validators together

Design Principles:
    - Single Responsibility: Each validator handles one concern
    - Open/Closed: Easy to extend with new checks
    - Dependency Inversion: Validators depend on abstractions
    - DRY: Common logic in base class and utilities
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import (
    List, Tuple, Optional, Dict, Any, Union, Callable,
    TypeVar, Set, FrozenSet, Literal
)
import json
import hashlib

import numpy as np
import pandas as pd

logger = logging.getLogger('cockpit.validation')

# Type aliases for clarity
T = TypeVar('T')
CheckFunc = Callable[['ValidationResult', pd.DataFrame, 'ColumnMapping', str], 'ValidationResult']


# =============================================================================
# Constants and Configuration
# =============================================================================

# Timeframe categories for validation logic
INTRADAY_TIMEFRAMES: FrozenSet[str] = frozenset({
    '1m', '2m', '5m', '15m', '30m', '1h', '60m', '90m'
})
DAILY_TIMEFRAMES: FrozenSet[str] = frozenset({
    '1d', 'daily', '1wk', 'weekly', '1mo', 'monthly'
})
ALL_TIMEFRAMES: FrozenSet[str] = INTRADAY_TIMEFRAMES | DAILY_TIMEFRAMES

# Expected column names (lowercase canonical form)
REQUIRED_OHLCV_COLUMNS: FrozenSet[str] = frozenset([
    'open', 'high', 'low', 'close', 'volume'
])
OPTIONAL_OHLCV_COLUMNS: FrozenSet[str] = frozenset([
    'adj_close', 'dividends', 'splits', 'vwap'
])

# Validation thresholds (sensible defaults)
DEFAULT_GAP_TOLERANCE_DAYS: int = 3
DEFAULT_GAP_TOLERANCE_BARS: int = 10
DEFAULT_OUTLIER_THRESHOLD_SIGMA: float = 5.0
DEFAULT_STALE_THRESHOLD_DAYS: int = 7
DEFAULT_ZERO_VOLUME_THRESHOLD_PCT: float = 10.0
DEFAULT_PRICE_JUMP_THRESHOLD_PCT: float = 50.0
DEFAULT_VOLUME_SPIKE_THRESHOLD_SIGMA: float = 5.0
DEFAULT_MIN_ROWS_DAILY: int = 20
DEFAULT_MIN_ROWS_INTRADAY: int = 100

# 24/7 calendar identifiers
CONTINUOUS_CALENDARS: FrozenSet[str] = frozenset({
    '24/7', 'FOREX', '24_7', 'CRYPTO', 'always_open'
})

# Timeframe to interval mapping
TIMEFRAME_INTERVALS: Dict[str, pd.Timedelta] = {
    '1m': pd.Timedelta(minutes=1),
    '2m': pd.Timedelta(minutes=2),
    '5m': pd.Timedelta(minutes=5),
    '15m': pd.Timedelta(minutes=15),
    '30m': pd.Timedelta(minutes=30),
    '1h': pd.Timedelta(hours=1),
    '60m': pd.Timedelta(hours=1),
    '90m': pd.Timedelta(minutes=90),
    '1d': pd.Timedelta(days=1),
    'daily': pd.Timedelta(days=1),
    '1wk': pd.Timedelta(weeks=1),
    'weekly': pd.Timedelta(weeks=1),
    '1mo': pd.Timedelta(days=30),
    'monthly': pd.Timedelta(days=30),
}

# Column aliases for case-insensitive matching
COLUMN_ALIASES: Dict[str, List[str]] = {
    'open': ['open', 'Open', 'OPEN', 'o', 'O'],
    'high': ['high', 'High', 'HIGH', 'h', 'H'],
    'low': ['low', 'Low', 'LOW', 'l', 'L'],
    'close': [
        'close', 'Close', 'CLOSE', 'c', 'C',
        'adj_close', 'Adj_Close', 'adj close', 'Adj Close'
    ],
    'volume': ['volume', 'Volume', 'VOLUME', 'vol', 'Vol', 'VOL', 'v', 'V'],
}


# =============================================================================
# Enums
# =============================================================================

class ValidationSeverity(str, Enum):
    """Enumeration of validation severity levels."""
    ERROR = 'error'
    WARNING = 'warning'
    INFO = 'info'

    def __str__(self) -> str:
        return self.value

    @property
    def is_blocking(self) -> bool:
        """Check if this severity should block validation."""
        return self == ValidationSeverity.ERROR


class ValidationStatus(str, Enum):
    """Enumeration of validation statuses."""
    PASSED = 'passed'
    FAILED = 'failed'
    SKIPPED = 'skipped'

    def __str__(self) -> str:
        return self.value


# =============================================================================
# Data Classes
# =============================================================================

@dataclass(frozen=True)
class ColumnMapping:
    """
    Immutable mapping of canonical column names to actual DataFrame columns.
    
    Provides a clean interface for accessing OHLCV columns regardless of
    their actual naming convention in the source data.
    """
    open: Optional[str] = None
    high: Optional[str] = None
    low: Optional[str] = None
    close: Optional[str] = None
    volume: Optional[str] = None

    def get(self, canonical: str) -> Optional[str]:
        """Get actual column name for canonical name."""
        return getattr(self, canonical, None)

    def has_all_required(self) -> bool:
        """Check if all required OHLCV columns are mapped."""
        return all([self.open, self.high, self.low, self.close, self.volume])

    def missing_columns(self) -> List[str]:
        """Get list of missing required columns."""
        return [col for col in REQUIRED_OHLCV_COLUMNS if self.get(col) is None]

    def to_dict(self) -> Dict[str, Optional[str]]:
        """Convert to dictionary."""
        return {
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'volume': self.volume
        }

    @property
    def price_columns(self) -> List[str]:
        """Get list of mapped price column names."""
        return [
            col for col in [self.open, self.high, self.low, self.close]
            if col is not None
        ]

    @property
    def all_columns(self) -> List[str]:
        """Get list of all mapped column names."""
        return [
            col for col in [self.open, self.high, self.low, self.close, self.volume]
            if col is not None
        ]


@dataclass
class ValidationCheck:
    """
    Individual validation check result.
    
    Encapsulates the outcome of a single validation check including
    pass/fail status, severity, message, and additional details.
    """
    name: str
    passed: bool
    severity: ValidationSeverity = ValidationSeverity.ERROR
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    @property
    def status(self) -> ValidationStatus:
        """Get validation status."""
        return ValidationStatus.PASSED if self.passed else ValidationStatus.FAILED

    @property
    def is_error(self) -> bool:
        """Check if this is a failed error-severity check."""
        return not self.passed and self.severity == ValidationSeverity.ERROR

    @property
    def is_warning(self) -> bool:
        """Check if this is a failed warning-severity check."""
        return not self.passed and self.severity == ValidationSeverity.WARNING

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'name': self.name,
            'passed': self.passed,
            'status': str(self.status),
            'severity': str(self.severity),
            'message': self.message,
            'details': self.details,
            'timestamp': self.timestamp.isoformat() + 'Z'
        }


@dataclass
class ValidationResult:
    """
    Container for aggregated validation results.
    
    Supports:
    - Adding individual checks with severity levels
    - Merging multiple results
    - Generating summaries
    - JSON serialization
    - Method chaining for fluent API
    
    Example:
        >>> result = ValidationResult()
        >>> result.add_check('test', True, 'All good')
        >>> result.add_warning('Minor issue detected')
        >>> print(result.summary())
    """
    passed: bool = True
    checks: List[ValidationCheck] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    info: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    _start_time: datetime = field(default_factory=datetime.utcnow)

    def add_check(
        self,
        name: str,
        passed: bool,
        message: str = "",
        details: Optional[Dict[str, Any]] = None,
        severity: ValidationSeverity = ValidationSeverity.ERROR
    ) -> 'ValidationResult':
        """
        Add a validation check result.
        
        Args:
            name: Check identifier
            passed: Whether check passed
            message: Human-readable message
            details: Additional details dictionary
            severity: Severity level for failures
            
        Returns:
            Self for method chaining
        """
        check = ValidationCheck(
            name=name,
            passed=passed,
            message=message,
            details=details or {},
            severity=severity
        )
        self.checks.append(check)

        if not passed:
            formatted_msg = f"{name}: {message}" if message else name
            if severity == ValidationSeverity.ERROR:
                self.passed = False
                self.errors.append(formatted_msg)
            elif severity == ValidationSeverity.WARNING:
                self.warnings.append(formatted_msg)
            else:
                self.info.append(formatted_msg)

        return self

    def add_warning(self, message: str) -> 'ValidationResult':
        """Add a warning message (non-fatal)."""
        self.warnings.append(message)
        return self

    def add_info(self, message: str) -> 'ValidationResult':
        """Add an informational message."""
        self.info.append(message)
        return self

    def add_error(self, message: str) -> 'ValidationResult':
        """Add an error message and mark validation as failed."""
        self.errors.append(message)
        self.passed = False
        return self

    def add_metadata(self, key: str, value: Any) -> 'ValidationResult':
        """Add metadata to the result."""
        self.metadata[key] = value
        return self

    def merge(self, other: 'ValidationResult') -> 'ValidationResult':
        """
        Merge another ValidationResult into this one.
        
        Args:
            other: ValidationResult to merge
            
        Returns:
            Self for method chaining
        """
        self.passed = self.passed and other.passed
        self.checks.extend(other.checks)
        self.warnings.extend(other.warnings)
        self.errors.extend(other.errors)
        self.info.extend(other.info)
        self.metadata.update(other.metadata)
        return self

    def get_checks_by_status(self, passed: bool) -> List[ValidationCheck]:
        """Get checks filtered by pass/fail status."""
        return [c for c in self.checks if c.passed == passed]

    @property
    def failed_checks(self) -> List[ValidationCheck]:
        """Get list of failed checks."""
        return self.get_checks_by_status(False)

    @property
    def passed_checks(self) -> List[ValidationCheck]:
        """Get list of passed checks."""
        return self.get_checks_by_status(True)

    @property
    def error_checks(self) -> List[ValidationCheck]:
        """Get failed checks with ERROR severity."""
        return [c for c in self.checks if c.is_error]

    @property
    def warning_checks(self) -> List[ValidationCheck]:
        """Get failed checks with WARNING severity."""
        return [c for c in self.checks if c.is_warning]

    @property
    def duration_ms(self) -> float:
        """Get validation duration in milliseconds."""
        return (datetime.utcnow() - self._start_time).total_seconds() * 1000

    @property
    def check_count(self) -> int:
        """Get total number of checks."""
        return len(self.checks)

    @property
    def pass_rate(self) -> float:
        """Get percentage of checks that passed."""
        if not self.checks:
            return 100.0
        return (len(self.passed_checks) / len(self.checks)) * 100

    def summary(self, max_errors: int = 5) -> str:
        """
        Generate a human-readable summary.
        
        Args:
            max_errors: Maximum number of errors to display
            
        Returns:
            Formatted summary string
        """
        total = len(self.checks)
        passed = len(self.passed_checks)
        failed = len(self.failed_checks)

        status = "PASSED" if self.passed else "FAILED"
        lines = [
            f"Validation {status}: {passed}/{total} checks passed ({self.pass_rate:.1f}%)",
            f"  Duration: {self.duration_ms:.1f}ms",
            f"  Errors: {len(self.errors)}",
            f"  Warnings: {len(self.warnings)}",
        ]

        if self.errors:
            lines.append("  Error details:")
            for error in self.errors[:max_errors]:
                lines.append(f"    - {error}")
            if len(self.errors) > max_errors:
                lines.append(f"    ... and {len(self.errors) - max_errors} more")

        if self.warnings:
            lines.append("  Warning details:")
            for warning in self.warnings[:max_errors]:
                lines.append(f"    - {warning}")
            if len(self.warnings) > max_errors:
                lines.append(f"    ... and {len(self.warnings) - max_errors} more")

        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'passed': self.passed,
            'status': str(ValidationStatus.PASSED if self.passed else ValidationStatus.FAILED),
            'checks': [c.to_dict() for c in self.checks],
            'warnings': self.warnings,
            'errors': self.errors,
            'info': self.info,
            'metadata': self.metadata,
            'summary': {
                'total_checks': len(self.checks),
                'passed_checks': len(self.passed_checks),
                'failed_checks': len(self.failed_checks),
                'error_count': len(self.errors),
                'warning_count': len(self.warnings),
                'pass_rate': self.pass_rate,
                'duration_ms': self.duration_ms
            },
            'validated_at': datetime.utcnow().isoformat() + 'Z'
        }

    def __bool__(self) -> bool:
        """Allow using result directly in boolean context."""
        return self.passed

    def __repr__(self) -> str:
        """String representation."""
        status = "PASSED" if self.passed else "FAILED"
        return f"ValidationResult({status}, checks={len(self.checks)}, errors={len(self.errors)})"


# =============================================================================
# Configuration
# =============================================================================

@dataclass
class ValidationConfig:
    """
    Configuration container for validation settings.
    
    Centralizes all validation thresholds and flags for consistent behavior.
    Supports factory methods for common configurations.
    
    Attributes:
        check_gaps: Whether to check for data gaps
        gap_tolerance_days: Max consecutive missing days (daily data)
        gap_tolerance_bars: Max consecutive missing bars (intraday)
        check_outliers: Whether to check for price outliers
        outlier_threshold_sigma: Standard deviations for outlier detection
        check_negative_values: Whether to check for negative prices/volumes
        check_future_dates: Whether to check for future dates
        check_stale_data: Whether to check for stale data
        stale_threshold_days: Days before data is considered stale
        check_zero_volume: Whether to check for zero volume bars
        zero_volume_threshold_pct: Max percentage of zero volume bars
        check_price_jumps: Whether to check for large price jumps
        price_jump_threshold_pct: Percentage threshold for price jumps
        check_sorted_index: Whether to verify index is sorted
        min_rows_daily: Minimum rows for daily data
        min_rows_intraday: Minimum rows for intraday data
        strict_mode: If True, warnings become errors
        timeframe: Data timeframe for context-aware validation
        asset_type: Asset type ('equity', 'forex', 'crypto') for context-aware validation
        calendar_name: Calendar name (e.g., 'XNYS', '24/7', 'FOREX') for context-aware validation
        check_sunday_bars: Whether to check for Sunday bars in FOREX/24/7 data
        check_weekend_gaps: Whether to check weekend gap integrity for FOREX data
    """
    # Gap checking
    check_gaps: bool = True
    gap_tolerance_days: int = DEFAULT_GAP_TOLERANCE_DAYS
    gap_tolerance_bars: int = DEFAULT_GAP_TOLERANCE_BARS

    # Outlier detection
    check_outliers: bool = True
    outlier_threshold_sigma: float = DEFAULT_OUTLIER_THRESHOLD_SIGMA

    # Value checks
    check_negative_values: bool = True
    check_future_dates: bool = True

    # Stale data detection
    check_stale_data: bool = True
    stale_threshold_days: int = DEFAULT_STALE_THRESHOLD_DAYS

    # Volume checks
    check_zero_volume: bool = True
    zero_volume_threshold_pct: float = DEFAULT_ZERO_VOLUME_THRESHOLD_PCT
    check_volume_spikes: bool = True
    volume_spike_threshold_sigma: float = DEFAULT_VOLUME_SPIKE_THRESHOLD_SIGMA

    # Price jump detection
    check_price_jumps: bool = True
    price_jump_threshold_pct: float = DEFAULT_PRICE_JUMP_THRESHOLD_PCT

    # Adjustment detection
    check_adjustments: bool = True

    # Index checks
    check_sorted_index: bool = True

    # Data sufficiency
    min_rows_daily: int = DEFAULT_MIN_ROWS_DAILY
    min_rows_intraday: int = DEFAULT_MIN_ROWS_INTRADAY

    # Mode
    strict_mode: bool = False
    suggest_fixes: bool = False

    # Context
    timeframe: Optional[str] = None
    asset_type: Optional[Literal['equity', 'forex', 'crypto']] = None
    calendar_name: Optional[str] = None

    # FOREX-specific checks
    check_sunday_bars: bool = True
    check_weekend_gaps: bool = True

    def __post_init__(self) -> None:
        """Normalize timeframe after initialization."""
        if self.timeframe:
            self.timeframe = self.timeframe.lower()

    @property
    def is_intraday(self) -> Optional[bool]:
        """Check if configured timeframe is intraday."""
        if not self.timeframe:
            return None
        return self.timeframe in INTRADAY_TIMEFRAMES

    @property
    def expected_interval(self) -> Optional[pd.Timedelta]:
        """Get expected time interval for configured timeframe."""
        if not self.timeframe:
            return None
        return TIMEFRAME_INTERVALS.get(self.timeframe)

    @property
    def min_rows(self) -> int:
        """Get minimum rows based on timeframe type."""
        if self.is_intraday:
            return self.min_rows_intraday
        return self.min_rows_daily

    def get_severity(
        self,
        default: ValidationSeverity = ValidationSeverity.WARNING
    ) -> ValidationSeverity:
        """Get severity based on strict mode."""
        return ValidationSeverity.ERROR if self.strict_mode else default

    @classmethod
    def default(cls, timeframe: Optional[str] = None) -> 'ValidationConfig':
        """Create default validation config."""
        return cls(timeframe=timeframe)

    @classmethod
    def strict(cls, timeframe: Optional[str] = None) -> 'ValidationConfig':
        """Create strict validation config."""
        return cls(strict_mode=True, timeframe=timeframe)

    @classmethod
    def lenient(cls, timeframe: Optional[str] = None) -> 'ValidationConfig':
        """Create lenient validation config with relaxed thresholds."""
        return cls(
            check_outliers=False,
            check_stale_data=False,
            check_price_jumps=False,
            check_zero_volume=False,
            gap_tolerance_days=10,
            gap_tolerance_bars=50,
            timeframe=timeframe
        )

    @classmethod
    def minimal(cls, timeframe: Optional[str] = None) -> 'ValidationConfig':
        """Create minimal config that only checks essential data integrity."""
        return cls(
            check_gaps=False,
            check_outliers=False,
            check_stale_data=False,
            check_zero_volume=False,
            check_price_jumps=False,
            timeframe=timeframe
        )

    @classmethod
    def for_equity(cls, timeframe: Optional[str] = None) -> 'ValidationConfig':
        """
        Create validation config optimized for equity data.
        
        Profile:
        - Enables all standard checks
        - Expects zero volume on holidays (handled by calendar checks)
        - Enables price jump detection (for split detection)
        """
        return cls(
            timeframe=timeframe,
            asset_type='equity',
            check_zero_volume=True,
            check_price_jumps=True,
            check_sunday_bars=False,  # Not relevant for equity
            check_weekend_gaps=False  # Not relevant for equity
        )

    @classmethod
    def for_forex(cls, timeframe: Optional[str] = None) -> 'ValidationConfig':
        """
        Create validation config optimized for FOREX data.
        
        Profile:
        - Enables Sunday bar detection
        - Enables weekend gap integrity checks
        - Disables volume validation (unreliable for FOREX)
        """
        return cls(
            timeframe=timeframe,
            asset_type='forex',
            check_zero_volume=False,  # Volume unreliable for FOREX
            check_sunday_bars=True,
            check_weekend_gaps=True
        )

    @classmethod
    def for_crypto(cls, timeframe: Optional[str] = None) -> 'ValidationConfig':
        """
        Create validation config optimized for crypto data.
        
        Profile:
        - Enables 24/7 continuity checks
        - No session gaps expected
        - Standard validation otherwise
        """
        return cls(
            timeframe=timeframe,
            asset_type='crypto',
            check_gaps=True,  # Should be continuous
            check_sunday_bars=False,  # 24/7 markets don't have Sunday bars
            check_weekend_gaps=False  # No weekends in 24/7 markets
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'check_gaps': self.check_gaps,
            'gap_tolerance_days': self.gap_tolerance_days,
            'gap_tolerance_bars': self.gap_tolerance_bars,
            'check_outliers': self.check_outliers,
            'outlier_threshold_sigma': self.outlier_threshold_sigma,
            'check_negative_values': self.check_negative_values,
            'check_future_dates': self.check_future_dates,
            'check_stale_data': self.check_stale_data,
            'stale_threshold_days': self.stale_threshold_days,
            'check_zero_volume': self.check_zero_volume,
            'zero_volume_threshold_pct': self.zero_volume_threshold_pct,
            'check_volume_spikes': self.check_volume_spikes,
            'volume_spike_threshold_sigma': self.volume_spike_threshold_sigma,
            'check_price_jumps': self.check_price_jumps,
            'price_jump_threshold_pct': self.price_jump_threshold_pct,
            'check_adjustments': self.check_adjustments,
            'check_sorted_index': self.check_sorted_index,
            'min_rows_daily': self.min_rows_daily,
            'min_rows_intraday': self.min_rows_intraday,
            'strict_mode': self.strict_mode,
            'timeframe': self.timeframe,
            'asset_type': self.asset_type,
            'calendar_name': self.calendar_name,
            'check_sunday_bars': self.check_sunday_bars,
            'check_weekend_gaps': self.check_weekend_gaps,
        }


# =============================================================================
# Utility Functions
# =============================================================================

def build_column_mapping(df: pd.DataFrame) -> ColumnMapping:
    """
    Build a case-insensitive mapping from canonical column names to actual column names.
    
    Supports various common column name formats:
    - lowercase: open, high, low, close, volume
    - uppercase: OPEN, HIGH, LOW, CLOSE, VOLUME
    - titlecase: Open, High, Low, Close, Volume
    - abbreviated: O, H, L, C, V (uppercase only)
    
    Args:
        df: DataFrame to analyze
        
    Returns:
        ColumnMapping with actual column names
        
    Example:
        >>> df = pd.DataFrame({'Open': [1], 'HIGH': [2], 'low': [0.5], 'Close': [1.5], 'Vol': [100]})
        >>> mapping = build_column_mapping(df)
        >>> mapping.open  # Returns 'Open'
    """
    df_columns = set(df.columns)
    mapping: Dict[str, Optional[str]] = {}

    for canonical, aliases in COLUMN_ALIASES.items():
        mapping[canonical] = None
        for alias in aliases:
            if alias in df_columns:
                mapping[canonical] = alias
                break

    return ColumnMapping(**mapping)


def normalize_dataframe_index(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure DataFrame has a proper DatetimeIndex.
    
    Args:
        df: DataFrame to normalize
        
    Returns:
        DataFrame with DatetimeIndex
        
    Raises:
        ValueError: If index cannot be converted to DatetimeIndex
    """
    if isinstance(df.index, pd.DatetimeIndex):
        return df

    try:
        df = df.copy()
        df.index = pd.to_datetime(df.index)
        return df
    except Exception as e:
        raise ValueError(f"Could not convert index to DatetimeIndex: {e}") from e


def ensure_timezone(
    index: pd.DatetimeIndex,
    tz: str = 'UTC'
) -> pd.DatetimeIndex:
    """
    Ensure DatetimeIndex has a consistent timezone.
    
    Args:
        index: DatetimeIndex to normalize
        tz: Target timezone (default: UTC)
        
    Returns:
        Timezone-aware DatetimeIndex
    """
    if index.tz is None:
        return index.tz_localize(tz)
    return index.tz_convert(tz)


def compute_dataframe_hash(df: pd.DataFrame) -> str:
    """
    Compute a hash of DataFrame contents for integrity checking.
    
    Uses SHA256 for strong collision resistance.
    
    Args:
        df: DataFrame to hash
        
    Returns:
        SHA256 hash string (64 characters)
    """
    hash_values = pd.util.hash_pandas_object(df, index=True)
    combined = hashlib.sha256(hash_values.values.tobytes())
    return combined.hexdigest()


def parse_timeframe(timeframe: Optional[str]) -> Optional[pd.Timedelta]:
    """
    Parse timeframe string to Timedelta.
    
    Args:
        timeframe: Timeframe string (e.g., '1m', '1h', '1d')
        
    Returns:
        Corresponding Timedelta or None if unknown
    """
    if not timeframe:
        return None
    return TIMEFRAME_INTERVALS.get(timeframe.lower())


def is_intraday_timeframe(timeframe: Optional[str]) -> Optional[bool]:
    """
    Check if timeframe is intraday.
    
    Args:
        timeframe: Timeframe string
        
    Returns:
        True if intraday, False if daily+, None if unknown
    """
    if not timeframe:
        return None
    return timeframe.lower() in INTRADAY_TIMEFRAMES


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safely divide two numbers, returning default if denominator is zero.
    
    Args:
        numerator: The numerator
        denominator: The denominator
        default: Value to return if denominator is zero
        
    Returns:
        Result of division or default
    """
    if denominator == 0:
        return default
    return numerator / denominator


def calculate_z_scores(series: pd.Series) -> pd.Series:
    """
    Calculate z-scores for a series.
    
    Args:
        series: Input series (typically returns)
        
    Returns:
        Series of absolute z-scores
    """
    mean_val = series.mean()
    std_val = series.std()
    
    if std_val == 0 or pd.isna(std_val):
        return pd.Series(0, index=series.index)
    
    return ((series - mean_val) / std_val).abs()


# =============================================================================
# Base Validator (Abstract)
# =============================================================================

class BaseValidator(ABC):
    """
    Abstract base class for all validators.
    
    Provides common functionality and enforces consistent interface.
    Implements the Template Method pattern for validation workflow.
    
    Subclasses must implement:
    - _register_checks(): Register validation check methods
    - validate(): Perform validation and return results
    
    Attributes:
        config: ValidationConfig for this validator
    """

    def __init__(self, config: Optional[ValidationConfig] = None):
        """
        Initialize validator with configuration.
        
        Args:
            config: Validation configuration (uses defaults if None)
        """
        self.config = config or ValidationConfig()
        self._check_registry: List[Callable] = []
        self._register_checks()

    @abstractmethod
    def _register_checks(self) -> None:
        """Register validation checks. Must be overridden in subclasses."""
        pass

    @abstractmethod
    def validate(self, *args, **kwargs) -> ValidationResult:
        """Perform validation. Must be overridden in subclasses."""
        pass

    def _create_result(self) -> ValidationResult:
        """Create a new ValidationResult with common metadata."""
        result = ValidationResult()
        result.add_metadata('validator', self.__class__.__name__)
        result.add_metadata('config', {
            'strict_mode': self.config.strict_mode,
            'timeframe': self.config.timeframe
        })
        result.add_metadata('timestamp', datetime.utcnow().isoformat() + 'Z')
        result.add_metadata('timezone', 'UTC')
        result.add_metadata('timezone_aware', True)
        return result

    def _run_check(
        self,
        result: ValidationResult,
        check_func: Callable[..., ValidationResult],
        *args,
        **kwargs
    ) -> ValidationResult:
        """
        Run a single check with error handling.
        
        Catches any exceptions and logs them as warnings rather than
        failing the entire validation process.
        
        Args:
            result: ValidationResult to update
            check_func: Check function to run
            *args, **kwargs: Arguments for check function
            
        Returns:
            Updated ValidationResult
        """
        try:
            return check_func(result, *args, **kwargs)
        except Exception as e:
            check_name = check_func.__name__.replace('_check_', '')
            error_msg = f"Check '{check_name}' failed with error: {str(e)}"
            result.add_warning(error_msg)
            logger.warning(f"Validation check {check_name} raised exception: {e}", exc_info=True)
            return result

    def _should_skip_check(self, check_name: str) -> bool:
        """
        Determine if a check should be skipped based on configuration.
        
        Args:
            check_name: Name of the check function
            
        Returns:
            True if check should be skipped
        """
        config_map = {
            '_check_no_negative_values': self.config.check_negative_values,
            '_check_no_future_dates': self.config.check_future_dates,
            '_check_zero_volume': self.config.check_zero_volume,
            '_check_price_jumps': self.config.check_price_jumps,
            '_check_stale_data': self.config.check_stale_data,
            '_check_price_outliers': self.config.check_outliers,
            '_check_sorted_index': self.config.check_sorted_index,
            '_check_sunday_bars': self.config.check_sunday_bars,
            '_check_weekend_gap_integrity': self.config.check_weekend_gaps,
            '_check_volume_spikes': self.config.check_volume_spikes,
            '_check_potential_splits': self.config.check_adjustments,
        }
        
        # Skip volume checks for FOREX (volume is unreliable)
        if check_name == '_check_zero_volume' and self.config.asset_type == 'forex':
            return True
        
        return not config_map.get(check_name, True)


# =============================================================================
# OHLCV Data Validator
# =============================================================================

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
            self._check_sunday_bars,
            self._check_weekend_gap_integrity,
            self._check_data_sufficiency,
            self._check_price_outliers,
            self._check_volume_spikes,
            self._check_potential_splits,
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
                from .utils import consolidate_sunday_to_friday
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
            if len(df) < 2:
                result.add_check(
                    'intraday_continuity', True,
                    "Insufficient data for gap check"
                )
                return result

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


# =============================================================================
# Bundle Validator
# =============================================================================

class BundleValidator(BaseValidator):
    """
    Validates existing data bundles for integrity and consistency.
    
    Checks performed:
    - Bundle existence
    - Metadata file validity
    - Asset file presence
    - Data integrity
    
    Example:
        >>> validator = BundleValidator(bundle_path_resolver=lambda name: Path(f'bundles/{name}'))
        >>> result = validator.validate('my_bundle')
        >>> print(result.summary())
    """

    def __init__(
        self,
        config: Optional[ValidationConfig] = None,
        bundle_path_resolver: Optional[Callable[[str], Optional[Path]]] = None
    ):
        """
        Initialize bundle validator.
        
        Args:
            config: ValidationConfig object (uses default if None)
            bundle_path_resolver: Optional callable that takes bundle_name and returns Path.
                If None, attempts to use get_bundle_path from data_loader with lazy import.
                Falls back to None if data_loader is unavailable (graceful degradation).
        """
        super().__init__(config)
        if bundle_path_resolver is None:
            # Lazy import to avoid circular dependency
            try:
                from .data_loader import get_bundle_path
                self.bundle_path_resolver = get_bundle_path
            except ImportError:
                self.bundle_path_resolver = None
        else:
            self.bundle_path_resolver = bundle_path_resolver

    def _register_checks(self) -> None:
        """Register bundle validation checks."""
        self._check_registry = [
            self._check_bundle_exists,
            self._check_bundle_metadata,
            self._check_bundle_assets,
        ]

    def validate(
        self,
        bundle_name: str,
        bundle_path: Optional[Path] = None
    ) -> ValidationResult:
        """
        Validate an existing bundle.

        Args:
            bundle_name: Name of the bundle
            bundle_path: Optional path to bundle directory

        Returns:
            ValidationResult
        """
        result = self._create_result()
        result.add_metadata('bundle_name', bundle_name)

        # Resolve bundle path using dependency injection
        if bundle_path is None:
            if self.bundle_path_resolver is not None:
                try:
                    bundle_path = self.bundle_path_resolver(bundle_name)
                except Exception as e:
                    result.add_warning(f"Error resolving bundle path with resolver: {e}")
                    bundle_path = None
            else:
                result.add_warning(
                    "No bundle_path provided and no bundle_path_resolver configured. "
                    "Please provide bundle_path or configure bundle_path_resolver in BundleValidator.__init__"
                )

        # Check bundle existence
        if not bundle_path or not bundle_path.exists():
            result.add_check(
                'bundle_exists', False,
                f"Bundle path does not exist: {bundle_path}"
            )
            return result

        result.add_check(
            'bundle_exists', True,
            f"Bundle '{bundle_name}' exists at {bundle_path}"
        )
        result.add_metadata('bundle_path', str(bundle_path))

        # Run remaining checks
        result = self._run_check(result, self._check_bundle_metadata, bundle_path)
        result = self._run_check(result, self._check_bundle_assets, bundle_path)

        return result

    def _check_bundle_exists(
        self,
        result: ValidationResult,
        bundle_path: Path
    ) -> ValidationResult:
        """Check bundle directory exists (handled in validate_bundle)."""
        return result

    def _check_bundle_metadata(
        self,
        result: ValidationResult,
        bundle_path: Path
    ) -> ValidationResult:
        """Check bundle metadata file exists and is valid."""
        metadata_path = bundle_path / 'metadata.json'

        if not metadata_path.exists():
            result.add_check(
                'bundle_metadata', False,
                f"Metadata file missing: {metadata_path}",
                severity=ValidationSeverity.WARNING
            )
            return result

        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)

            required_fields = ['created_at', 'assets']
            missing_fields = [f for f in required_fields if f not in metadata]

            if missing_fields:
                result.add_check(
                    'bundle_metadata', False,
                    f"Missing metadata fields: {missing_fields}",
                    {'missing_fields': missing_fields},
                    severity=ValidationSeverity.WARNING
                )
            else:
                result.add_check(
                    'bundle_metadata', True,
                    "Metadata is valid",
                    {'metadata_keys': list(metadata.keys())}
                )
                result.add_metadata('bundle_metadata', metadata)

        except json.JSONDecodeError as e:
            result.add_check('bundle_metadata', False, f"Invalid JSON: {e}")
        except Exception as e:
            result.add_check('bundle_metadata', False, f"Error reading metadata: {e}")

        return result

    def _check_bundle_assets(
        self,
        result: ValidationResult,
        bundle_path: Path
    ) -> ValidationResult:
        """Check that bundle assets exist and are valid."""
        data_path = bundle_path / 'data'

        if not data_path.exists():
            # Try alternate locations
            alternate_paths = [bundle_path / 'assets', bundle_path]
            for alt_path in alternate_paths:
                if alt_path.exists():
                    data_path = alt_path
                    break
            else:
                result.add_check('bundle_assets', False, f"Data directory missing: {data_path}")
                return result

        # Find asset files
        asset_files = (
            list(data_path.glob('*.parquet')) +
            list(data_path.glob('*.csv')) +
            list(data_path.glob('*.h5'))
        )

        if len(asset_files) == 0:
            result.add_check('bundle_assets', False, "No asset files found in bundle")
            return result

        result.add_check(
            'bundle_assets', True,
            f"Found {len(asset_files)} asset files",
            {
                'asset_count': len(asset_files),
                'file_formats': list(set(f.suffix for f in asset_files))
            }
        )
        result.add_metadata('asset_count', len(asset_files))
        result.add_metadata('asset_files', [f.name for f in asset_files])

        return result


# =============================================================================
# Backtest Validator
# =============================================================================

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


# =============================================================================
# Schema Validator
# =============================================================================

class SchemaValidator:
    """
    Validates DataFrame schemas against expected specifications.
    
    Useful for ensuring data conforms to expected structure before processing.
    
    Example:
        >>> schema = SchemaValidator(
        ...     required_columns=['open', 'high', 'low', 'close', 'volume'],
        ...     column_types={'volume': np.integer},
        ...     index_type=pd.DatetimeIndex
        ... )
        >>> result = schema.validate(df)
    """

    def __init__(
        self,
        required_columns: Optional[List[str]] = None,
        optional_columns: Optional[List[str]] = None,
        column_types: Optional[Dict[str, type]] = None,
        index_type: Optional[type] = None,
        allow_extra_columns: bool = True
    ):
        """
        Initialize schema validator.
        
        Args:
            required_columns: Columns that must be present
            optional_columns: Columns that may be present
            column_types: Expected numpy dtypes for columns
            index_type: Expected index type (e.g., pd.DatetimeIndex)
            allow_extra_columns: Whether to allow columns not in schema
        """
        self.required_columns: Set[str] = set(required_columns or [])
        self.optional_columns: Set[str] = set(optional_columns or [])
        self.column_types: Dict[str, type] = column_types or {}
        self.index_type = index_type
        self.allow_extra_columns = allow_extra_columns

    def validate(self, df: pd.DataFrame) -> ValidationResult:
        """
        Validate DataFrame against schema.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            ValidationResult
        """
        result = ValidationResult()
        result.add_metadata('validator', 'SchemaValidator')
        result.add_metadata('row_count', len(df))
        result.add_metadata('column_count', len(df.columns))

        # Check required columns
        df_cols = set(df.columns)
        missing = self.required_columns - df_cols

        if missing:
            result.add_check(
                'required_columns', False,
                f"Missing required columns: {sorted(missing)}",
                {'missing_columns': sorted(missing)}
            )
        else:
            result.add_check(
                'required_columns', True,
                "All required columns present",
                {'required_columns': sorted(self.required_columns)}
            )

        # Check for unexpected columns
        if not self.allow_extra_columns:
            all_expected = self.required_columns | self.optional_columns
            unexpected = df_cols - all_expected

            if unexpected:
                result.add_check(
                    'no_unexpected_columns', False,
                    f"Unexpected columns: {sorted(unexpected)}",
                    {'unexpected_columns': sorted(unexpected)},
                    severity=ValidationSeverity.WARNING
                )
            else:
                result.add_check('no_unexpected_columns', True, "No unexpected columns")

        # Check column types
        for col, expected_type in self.column_types.items():
            if col in df.columns:
                actual_type = df[col].dtype
                if not np.issubdtype(actual_type, expected_type):
                    result.add_check(
                        f'column_type_{col}', False,
                        f"Column '{col}' has type {actual_type}, expected {expected_type}",
                        {'column': col, 'actual_type': str(actual_type), 'expected_type': str(expected_type)},
                        severity=ValidationSeverity.WARNING
                    )
                else:
                    result.add_check(
                        f'column_type_{col}', True,
                        f"Column '{col}' has correct type"
                    )

        # Check index type
        if self.index_type is not None:
            if not isinstance(df.index, self.index_type):
                result.add_check(
                    'index_type', False,
                    f"Index has type {type(df.index).__name__}, expected {self.index_type.__name__}",
                    {'actual_type': type(df.index).__name__, 'expected_type': self.index_type.__name__}
                )
            else:
                result.add_check('index_type', True, "Index type is correct")

        return result


# =============================================================================
# Composite Validator
# =============================================================================

class CompositeValidator:
    """
    Combines multiple validators for comprehensive validation.
    
    Implements the Composite pattern to run validation pipelines.
    
    Example:
        >>> composite = CompositeValidator([
        ...     DataValidator(timeframe='1d'),
        ...     SchemaValidator(required_columns=['open', 'close'])
        ... ])
        >>> result = composite.validate(df)
    """

    def __init__(self, validators: Optional[List[BaseValidator]] = None):
        """
        Initialize composite validator.
        
        Args:
            validators: List of validators to run
        """
        self.validators: List[BaseValidator] = validators or []

    def add_validator(self, validator: BaseValidator) -> 'CompositeValidator':
        """
        Add a validator to the pipeline.
        
        Args:
            validator: Validator to add
            
        Returns:
            Self for method chaining
        """
        self.validators.append(validator)
        return self

    def validate(self, *args, **kwargs) -> ValidationResult:
        """
        Run all validators and merge results.
        
        Args:
            *args, **kwargs: Arguments passed to each validator
            
        Returns:
            Merged ValidationResult
        """
        result = ValidationResult()
        result.add_metadata('validator', 'CompositeValidator')
        result.add_metadata('validator_count', len(self.validators))

        for i, validator in enumerate(self.validators):
            try:
                validator_name = validator.__class__.__name__
                validator_result = validator.validate(*args, **kwargs)
                result.merge(validator_result)
                result.add_info(f"Completed {validator_name} ({i + 1}/{len(self.validators)})")
            except Exception as e:
                error_msg = f"Validator {validator.__class__.__name__} failed: {e}"
                result.add_warning(error_msg)
                logger.warning(f"Composite validation error: {e}", exc_info=True)

        return result


# =============================================================================
# Public API - Convenience Functions
# =============================================================================

def validate_before_ingest(
    df: pd.DataFrame,
    asset_name: str = "unknown",
    timeframe: Optional[str] = None,
    calendar: Optional[Any] = None,
    calendar_name: Optional[str] = None,
    asset_type: Optional[Literal['equity', 'forex', 'crypto']] = None,
    strict_mode: bool = False,
    suggest_fixes: bool = False,
    config: Optional[ValidationConfig] = None
) -> ValidationResult:
    """
    Validate data before ingestion into a bundle.

    This is the main entry point for pre-ingestion validation.

    Args:
        df: DataFrame with OHLCV data
        asset_name: Asset name for logging
        timeframe: Data timeframe (e.g., '1m', '1h', '1d')
        calendar: Optional trading calendar
        calendar_name: Calendar name for context-aware validation
        asset_type: Asset type ('equity', 'forex', 'crypto') for context-aware validation
        strict_mode: If True, warnings become errors
        suggest_fixes: If True, add fix suggestions to result metadata
        config: Optional ValidationConfig (overrides other params)

    Returns:
        ValidationResult with all check outcomes
        
    Example:
        >>> result = validate_before_ingest(df, asset_name='AAPL', timeframe='1d')
        >>> if not result:
        ...     raise ValueError(result.summary())
    """
    if config is None:
        config = ValidationConfig(
            timeframe=timeframe,
            strict_mode=strict_mode,
            asset_type=asset_type,
            calendar_name=calendar_name,
            suggest_fixes=suggest_fixes
        )
    else:
        # Update config with provided values if not already set
        if asset_type is not None:
            config.asset_type = asset_type
        if calendar_name is not None:
            config.calendar_name = calendar_name
        if suggest_fixes:
            config.suggest_fixes = suggest_fixes

    validator = DataValidator(config=config)
    return validator.validate(
        df=df,
        calendar=calendar,
        asset_name=asset_name,
        calendar_name=calendar_name,
        asset_type=asset_type,
        suggest_fixes=suggest_fixes
    )


def validate_bundle(
    bundle_name: str,
    bundle_path: Optional[Path] = None,
    config: Optional[ValidationConfig] = None
) -> ValidationResult:
    """
    Validate an existing bundle.

    Args:
        bundle_name: Name of the bundle to validate
        bundle_path: Optional path to bundle directory. If None, uses default resolver
            from data_loader.get_bundle_path (with graceful degradation if unavailable)
        config: Optional ValidationConfig

    Returns:
        ValidationResult
    """
    # BundleValidator will use get_bundle_path as default resolver if bundle_path_resolver is None
    validator = BundleValidator(config=config)
    return validator.validate(bundle_name, bundle_path)


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


# =============================================================================
# Report I/O Functions
# =============================================================================

def save_validation_report(
    result: ValidationResult,
    output_path: Union[str, Path],
    include_summary: bool = True,
    pretty_print: bool = True
) -> None:
    """
    Save validation report to JSON file.

    Args:
        result: ValidationResult to save
        output_path: Path for output file
        include_summary: Whether to include human-readable summary
        pretty_print: Whether to format JSON with indentation
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    report = result.to_dict()

    if include_summary:
        report['human_summary'] = result.summary()

    indent = 2 if pretty_print else None

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=indent, default=str)

    logger.info(f"Saved validation report to {output_path}")


def load_validation_report(report_path: Union[str, Path]) -> ValidationResult:
    """
    Load a validation report from JSON file.

    Args:
        report_path: Path to the report file

    Returns:
        ValidationResult reconstructed from the file
        
    Raises:
        FileNotFoundError: If the report file does not exist
        json.JSONDecodeError: If the file contains invalid JSON
        ValueError: If the report structure is invalid
    """
    report_path = Path(report_path)
    
    if not report_path.exists():
        raise FileNotFoundError(f"Validation report not found: {report_path}")

    try:
        with open(report_path, 'r') as f:
            report_data = json.load(f)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Invalid JSON in validation report: {e}", e.doc, e.pos) from e
    except Exception as e:
        raise ValueError(f"Error reading validation report: {e}") from e

    # Reconstruct ValidationResult
    result = ValidationResult()
    result.passed = report_data.get('passed', True)
    
    # Reconstruct checks
    checks_data = report_data.get('checks', [])
    for check_data in checks_data:
        check = ValidationCheck(
            name=check_data.get('name', 'unknown'),
            passed=check_data.get('passed', False),
            severity=ValidationSeverity(check_data.get('severity', 'error')),
            message=check_data.get('message', ''),
            details=check_data.get('details', {}),
            timestamp=datetime.fromisoformat(check_data.get('timestamp', datetime.utcnow().isoformat()).replace('Z', '+00:00'))
        )
        result.checks.append(check)
    
    # Reconstruct lists
    result.warnings = report_data.get('warnings', [])
    result.errors = report_data.get('errors', [])
    result.info = report_data.get('info', [])
    result.metadata = report_data.get('metadata', {})
    
    # Restore start time if available (for duration calculation)
    validated_at = report_data.get('validated_at')
    if validated_at:
        try:
            result._start_time = datetime.fromisoformat(validated_at.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            # If we can't parse it, use current time (duration will be inaccurate)
            pass
    
    return result
