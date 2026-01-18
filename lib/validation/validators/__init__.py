"""
Asset-specific validators for OHLCV data.

Provides specialized validators for different asset classes:
- EquityValidator: Stock-specific validation (splits, dividends)
- ForexValidator: FOREX-specific validation (24/5 market, weekend gaps)
- CryptoValidator: Cryptocurrency-specific validation (24/7 market, flash crashes)
- Reporting utilities for formatting validation results
"""

from .equity import EquityValidator
from .forex import ForexValidator
from .crypto import CryptoValidator
from .reporting import (
    format_validation_report,
    generate_fix_suggestions,
    add_fix_suggestions_to_result,
)

__all__ = [
    'EquityValidator',
    'ForexValidator',
    'CryptoValidator',
    'format_validation_report',
    'generate_fix_suggestions',
    'add_fix_suggestions_to_result',
]
