"""
Data validation package for The Researcher's Cockpit.

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
    - DataValidator: OHLCV data validation (orchestrator)
    - Asset-specific validators: EquityValidator, ForexValidator, CryptoValidator
    - BundleValidator: Bundle integrity validation
    - BacktestValidator: Backtest results validation
    - SchemaValidator: DataFrame schema validation
    - CompositeValidator: Pipeline multiple validators together

Design Principles:
    - Single Responsibility: Each validator handles one concern
    - Open/Closed: Easy to extend with new checks
    - Dependency Inversion: Validators depend on abstractions
    - DRY: Common logic in base class and utilities

Usage:
    >>> from lib.validation import DataValidator, ValidationConfig, ValidationResult
    >>> config = ValidationConfig.strict(timeframe='1d')
    >>> validator = DataValidator(config=config)
    >>> result = validator.validate(df, asset_name='AAPL')
    >>> if not result:
    ...     print(result.summary())
"""

# Core types and constants
from .core import (
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
)

# Configuration
from .config import ValidationConfig

# Column mapping
from .column_mapping import ColumnMapping, build_column_mapping

# Base validator
from .base import BaseValidator

# Core validators
from .data_validator import DataValidator
from .bundle_validator import BundleValidator
from .backtest_validator import BacktestValidator
from .schema_validator import SchemaValidator
from .composite import CompositeValidator

# Asset-specific validators
from .validators import (
    EquityValidator,
    ForexValidator,
    CryptoValidator,
    format_validation_report,
    generate_fix_suggestions,
    add_fix_suggestions_to_result,
)

# Utility functions
from .utils import (
    normalize_dataframe_index,
    ensure_timezone,
    compute_dataframe_hash,
    parse_timeframe,
    is_intraday_timeframe,
    safe_divide,
    calculate_z_scores,
)

# Public API - Convenience functions
from .api import (
    validate_before_ingest,
    validate_bundle,
    validate_backtest_results,
    verify_metrics_calculation,
    verify_returns_calculation,
    verify_positions_match_transactions,
    verify_bundle_dates,
    validate_csv_files_pre_ingestion,
    save_validation_report,
    load_validation_report,
)

# =============================================================================
# Public API Exports
# =============================================================================

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
    # Core validators
    'DataValidator',
    'BundleValidator',
    'BacktestValidator',
    'SchemaValidator',
    'CompositeValidator',
    # Asset-specific validators
    'EquityValidator',
    'ForexValidator',
    'CryptoValidator',
    'format_validation_report',
    'generate_fix_suggestions',
    'add_fix_suggestions_to_result',
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
    # Data integrity functions
    'verify_bundle_dates',
    'validate_csv_files_pre_ingestion',
    # Report I/O
    'save_validation_report',
    'load_validation_report',
]
