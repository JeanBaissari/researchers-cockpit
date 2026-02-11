"""
Validation API - Convenience functions for common validation workflows.

This module provides a unified API by re-exporting functions from specialized validator modules.
These validators COMPLEMENT Zipline-Reloaded's built-in validation:

- validators/ingest.py: Pre-ingestion OHLCV quality validation (before Zipline ingestion)
- validators/bundle.py: Bundle integrity validation (after Zipline ingestion)
- validators/results.py: Backtest results validation (after Zipline backtest)

**Key Distinction:**
- Our validation: Data quality, business rules, statistical checks
- Zipline's validation: Format/structure, data availability, calendar alignment

See docs/validation/validation_architecture.md for complete distinction.

All functions are convenience wrappers that delegate to the appropriate specialized validators.
"""

# Pre-ingestion validation
from .validators.ingest import (
    validate_before_ingest,
    validate_csv_files_pre_ingestion,
)

# Bundle validation
from .validators.bundle import (
    validate_bundle,
    verify_bundle_dates,
)

# Backtest results validation
from .validators.results import (
    validate_backtest_results,
    verify_metrics_calculation,
    verify_returns_calculation,
    verify_positions_match_transactions,
)

# Validation report I/O
from .validators.reports import (
    save_validation_report,
    load_validation_report,
)

__all__ = [
    # Pre-ingestion validation
    "validate_before_ingest",
    "validate_csv_files_pre_ingestion",
    # Bundle validation
    "validate_bundle",
    "verify_bundle_dates",
    # Backtest results validation
    "validate_backtest_results",
    "verify_metrics_calculation",
    "verify_returns_calculation",
    "verify_positions_match_transactions",
    # Report I/O
    "save_validation_report",
    "load_validation_report",
]
