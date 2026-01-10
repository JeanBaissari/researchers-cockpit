"""
Core types and constants for validation.

Contains:
- Constants and configuration values
- ValidationSeverity enum
- ValidationStatus enum
- ValidationCheck dataclass
- ValidationResult dataclass
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any, FrozenSet

import pandas as pd

logger = logging.getLogger('cockpit.validation')

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

    def get_check(self, name: str) -> Optional[ValidationCheck]:
        """
        Get a specific check by name.
        
        Args:
            name: Check name to look up
            
        Returns:
            ValidationCheck if found, None otherwise
        """
        for check in self.checks:
            if check.name == name:
                return check
        return None

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





