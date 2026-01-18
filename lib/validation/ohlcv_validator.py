"""
OHLCV Validator Module (extracted from data_validator.py)

Provides focused validation functions for OHLCV data.
"""

import pandas as pd
from .core import ValidationResult
from .column_mapping import ColumnMapping
from .utils import safe_divide

def check_required_columns(df: pd.DataFrame, col_map: ColumnMapping, required_cols) -> ValidationResult:
    """Check that required OHLCV columns exist (case-insensitive)."""
    missing = col_map.missing_columns()
    result = ValidationResult()
    if missing:
        result.add_check(
            'required_columns',
            False,
            f"Missing required columns: {missing}. Expected columns (case-insensitive): {list(required_cols)}",
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

# TODO: Implement validate_numeric_values, check_for_duplicates, validate_price_order
# Extract logic from data_validator.py as per the refactor plan.
