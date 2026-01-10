"""
Schema Validator.

Validates DataFrame schemas against expected specifications.
"""

from typing import Optional, List, Dict, Set

import numpy as np
import pandas as pd

from .core import ValidationResult, ValidationSeverity


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





