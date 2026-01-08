"""
Data validation module for The Researcher's Cockpit.

DEPRECATED: This module has been refactored into lib/validation/ package.
This file is maintained for backward compatibility.
Please update imports to use lib.validation instead.

Migration:
    # Old import:
    from lib.data_validation import DataValidator, ValidationConfig, ValidationResult
    
    # New import:
    from lib.validation import DataValidator, ValidationConfig, ValidationResult
"""

import warnings

# Issue deprecation warning
warnings.warn(
    "lib.data_validation is deprecated. Use lib.validation instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export all public API from new location
from .validation import (
    # Constants
    INTRADAY_TIMEFRAMES,
    DAILY_TIMEFRAMES,
    ALL_TIMEFRAMES,
    REQUIRED_OHLCV_COLUMNS,
    OPTIONAL_OHLCV_COLUMNS,
    DEFAULT_GAP_TOLERANCE_DAYS,
    DEFAULT_GAP_TOLERANCE_BARS,
    DEFAULT_OUTLIER_THRESHOLD_SIGMA,
    DEFAULT_STALE_THRESHOLD_DAYS,
    DEFAULT_ZERO_VOLUME_THRESHOLD_PCT,
    DEFAULT_PRICE_JUMP_THRESHOLD_PCT,
    DEFAULT_VOLUME_SPIKE_THRESHOLD_SIGMA,
    DEFAULT_MIN_ROWS_DAILY,
    DEFAULT_MIN_ROWS_INTRADAY,
    CONTINUOUS_CALENDARS,
    TIMEFRAME_INTERVALS,
    COLUMN_ALIASES,
    # Enums
    ValidationSeverity,
    ValidationStatus,
    # Data classes
    ValidationCheck,
    ValidationResult,
    # Configuration
    ValidationConfig,
    # Column mapping
    ColumnMapping,
    build_column_mapping,
    # Base validator
    BaseValidator,
    # Validators
    DataValidator,
    BundleValidator,
    BacktestValidator,
    SchemaValidator,
    CompositeValidator,
    # Utility functions
    normalize_dataframe_index,
    ensure_timezone,
    compute_dataframe_hash,
    parse_timeframe,
    is_intraday_timeframe,
    safe_divide,
    calculate_z_scores,
    # Convenience functions
    validate_before_ingest,
    validate_bundle,
    validate_backtest_results,
    verify_metrics_calculation,
    verify_returns_calculation,
    verify_positions_match_transactions,
    # Report I/O
    save_validation_report,
    load_validation_report,
)

# Type alias for backward compatibility
CheckFunc = None  # This type was internal, keeping None for compatibility

__all__ = [
    # Constants
    'INTRADAY_TIMEFRAMES',
    'DAILY_TIMEFRAMES',
    'ALL_TIMEFRAMES',
    'REQUIRED_OHLCV_COLUMNS',
    'OPTIONAL_OHLCV_COLUMNS',
    'DEFAULT_GAP_TOLERANCE_DAYS',
    'DEFAULT_GAP_TOLERANCE_BARS',
    'DEFAULT_OUTLIER_THRESHOLD_SIGMA',
    'DEFAULT_STALE_THRESHOLD_DAYS',
    'DEFAULT_ZERO_VOLUME_THRESHOLD_PCT',
    'DEFAULT_PRICE_JUMP_THRESHOLD_PCT',
    'DEFAULT_VOLUME_SPIKE_THRESHOLD_SIGMA',
    'DEFAULT_MIN_ROWS_DAILY',
    'DEFAULT_MIN_ROWS_INTRADAY',
    'CONTINUOUS_CALENDARS',
    'TIMEFRAME_INTERVALS',
    'COLUMN_ALIASES',
    # Enums
    'ValidationSeverity',
    'ValidationStatus',
    # Data classes
    'ValidationCheck',
    'ValidationResult',
    # Configuration
    'ValidationConfig',
    # Column mapping
    'ColumnMapping',
    'build_column_mapping',
    # Base validator
    'BaseValidator',
    # Validators
    'DataValidator',
    'BundleValidator',
    'BacktestValidator',
    'SchemaValidator',
    'CompositeValidator',
    # Utility functions
    'normalize_dataframe_index',
    'ensure_timezone',
    'compute_dataframe_hash',
    'parse_timeframe',
    'is_intraday_timeframe',
    'safe_divide',
    'calculate_z_scores',
    # Convenience functions
    'validate_before_ingest',
    'validate_bundle',
    'validate_backtest_results',
    'verify_metrics_calculation',
    'verify_returns_calculation',
    'verify_positions_match_transactions',
    # Report I/O
    'save_validation_report',
    'load_validation_report',
]
