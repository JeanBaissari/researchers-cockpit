"""
Data integrity validation module for The Researcher's Cockpit.

DEPRECATED: This module has been merged into lib/validation/ package.
Please update imports to use lib.validation instead.

Migration:
    # Old import:
    from lib.data_integrity import verify_bundle_dates, validate_csv_files_pre_ingestion
    
    # New import:
    from lib.validation import verify_bundle_dates, validate_csv_files_pre_ingestion
"""

import warnings

# Issue deprecation warning
warnings.warn(
    "lib.data_integrity is deprecated and has been merged into lib.validation. "
    "Use lib.validation instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export all public API from new location
from .validation import (
    ValidationResult,
    ValidationConfig,
    DataValidator,
    verify_bundle_dates,
    validate_csv_files_pre_ingestion,
    verify_returns_calculation,
    verify_positions_match_transactions,
    verify_metrics_calculation,
)

__all__ = [
    'ValidationResult',
    'ValidationConfig',
    'DataValidator',
    'verify_bundle_dates',
    'validate_csv_files_pre_ingestion',
    'verify_returns_calculation',
    'verify_positions_match_transactions',
    'verify_metrics_calculation',
]
