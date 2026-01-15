"""
Validation configuration.

Provides the ValidationConfig dataclass for configuring validation behavior.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, Literal

import pandas as pd

from .core import (
    INTRADAY_TIMEFRAMES,
    TIMEFRAME_INTERVALS,
    DEFAULT_GAP_TOLERANCE_DAYS,
    DEFAULT_GAP_TOLERANCE_BARS,
    DEFAULT_OUTLIER_THRESHOLD_SIGMA,
    DEFAULT_STALE_THRESHOLD_DAYS,
    DEFAULT_ZERO_VOLUME_THRESHOLD_PCT,
    DEFAULT_PRICE_JUMP_THRESHOLD_PCT,
    DEFAULT_VOLUME_SPIKE_THRESHOLD_SIGMA,
    DEFAULT_MIN_ROWS_DAILY,
    DEFAULT_MIN_ROWS_INTRADAY,
    ValidationSeverity,
)


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















