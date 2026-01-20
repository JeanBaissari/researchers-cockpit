"""
Asset-specific validators and high-level validation API functions.

Provides specialized validators for different asset classes:
- EquityValidator: Stock-specific validation (splits, dividends)
- ForexValidator: FOREX-specific validation (24/5 market, weekend gaps)
- CryptoValidator: Cryptocurrency-specific validation (24/7 market, flash crashes)
- Reporting utilities for formatting validation results

High-level API functions:
- ingest: Pre-ingestion validation functions
- bundle: Bundle validation functions
- results: Backtest results validation and verification
"""

from .equity import EquityValidator
from .forex import ForexValidator
from .crypto import CryptoValidator
from .reporting import (
    format_validation_report,
    generate_fix_suggestions,
    add_fix_suggestions_to_result,
)

# High-level API functions (organized by module)
from . import ingest
from . import bundle
from . import results
from . import reports

__all__ = [
    # Asset-specific validators
    'EquityValidator',
    'ForexValidator',
    'CryptoValidator',
    # Reporting utilities
    'format_validation_report',
    'generate_fix_suggestions',
    'add_fix_suggestions_to_result',
    # API function modules
    'ingest',
    'bundle',
    'results',
    'reports',
]
