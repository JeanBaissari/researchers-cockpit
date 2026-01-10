"""
Column mapping for OHLCV data validation.

Provides case-insensitive column name resolution for various data sources.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict

import pandas as pd

from .core import REQUIRED_OHLCV_COLUMNS, COLUMN_ALIASES


@dataclass(frozen=True)
class ColumnMapping:
    """
    Immutable mapping of canonical column names to actual DataFrame columns.
    
    Provides a clean interface for accessing OHLCV columns regardless of
    their actual naming convention in the source data.
    """
    open: Optional[str] = None
    high: Optional[str] = None
    low: Optional[str] = None
    close: Optional[str] = None
    volume: Optional[str] = None

    def get(self, canonical: str) -> Optional[str]:
        """Get actual column name for canonical name."""
        return getattr(self, canonical, None)

    def has_all_required(self) -> bool:
        """Check if all required OHLCV columns are mapped."""
        return all([self.open, self.high, self.low, self.close, self.volume])

    def missing_columns(self) -> List[str]:
        """Get list of missing required columns."""
        return [col for col in REQUIRED_OHLCV_COLUMNS if self.get(col) is None]

    def to_dict(self) -> Dict[str, Optional[str]]:
        """Convert to dictionary."""
        return {
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'volume': self.volume
        }

    @property
    def price_columns(self) -> List[str]:
        """Get list of mapped price column names."""
        return [
            col for col in [self.open, self.high, self.low, self.close]
            if col is not None
        ]

    @property
    def all_columns(self) -> List[str]:
        """Get list of all mapped column names."""
        return [
            col for col in [self.open, self.high, self.low, self.close, self.volume]
            if col is not None
        ]


def build_column_mapping(df: pd.DataFrame) -> ColumnMapping:
    """
    Build a case-insensitive mapping from canonical column names to actual column names.
    
    Supports various common column name formats:
    - lowercase: open, high, low, close, volume
    - uppercase: OPEN, HIGH, LOW, CLOSE, VOLUME
    - titlecase: Open, High, Low, Close, Volume
    - abbreviated: O, H, L, C, V (uppercase only)
    
    Args:
        df: DataFrame to analyze
        
    Returns:
        ColumnMapping with actual column names
        
    Example:
        >>> df = pd.DataFrame({'Open': [1], 'HIGH': [2], 'low': [0.5], 'Close': [1.5], 'Vol': [100]})
        >>> mapping = build_column_mapping(df)
        >>> mapping.open  # Returns 'Open'
    """
    df_columns = set(df.columns)
    mapping: Dict[str, Optional[str]] = {}

    for canonical, aliases in COLUMN_ALIASES.items():
        mapping[canonical] = None
        for alias in aliases:
            if alias in df_columns:
                mapping[canonical] = alias
                break

    return ColumnMapping(**mapping)





