"""
CSV parsing and normalization utilities.

Handles CSV file reading, column normalization, and filename parsing
for date range extraction.
"""

import logging
import re
from pathlib import Path
from typing import Tuple, Optional

import pandas as pd

logger = logging.getLogger(__name__)


def normalize_csv_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize CSV column names to lowercase standard format.

    Handles various column naming conventions:
    - Title case: Open, High, Low, Close, Volume
    - Uppercase: OPEN, HIGH, LOW, CLOSE, VOLUME
    - Mixed case: open, HIGH, Close, etc.
    - With prefixes: Adj Close, Adj_Close, adjusted_close

    Args:
        df: DataFrame with potentially non-standard column names

    Returns:
        DataFrame with normalized lowercase column names

    Raises:
        ValueError: If required OHLCV columns cannot be identified
    """
    column_mapping = {}

    # Define patterns for each required column
    column_patterns = {
        'open': [r'^open$', r'^o$'],
        'high': [r'^high$', r'^h$'],
        'low': [r'^low$', r'^l$'],
        'close': [r'^close$', r'^c$', r'^adj[_\s]?close$', r'^adjusted[_\s]?close$'],
        'volume': [r'^volume$', r'^vol$', r'^v$'],
    }

    found_columns = {}

    for target_name, patterns in column_patterns.items():
        for col in df.columns:
            col_lower = str(col).lower().strip()
            for pattern in patterns:
                if re.match(pattern, col_lower):
                    if target_name not in found_columns:
                        found_columns[target_name] = col
                        column_mapping[col] = target_name
                    break
            if target_name in found_columns:
                break

    # Check for missing required columns
    required = {'open', 'high', 'low', 'close', 'volume'}
    missing = required - set(found_columns.keys())

    if missing:
        raise ValueError(
            f"CSV missing required columns: {missing}. "
            f"Found columns: {list(df.columns)}. "
            f"Expected: open, high, low, close, volume (case-insensitive)"
        )

    # Rename and keep only required columns
    df = df.rename(columns=column_mapping)
    df = df[['open', 'high', 'low', 'close', 'volume']]

    return df


def parse_csv_filename(
    filename: str,
    symbol: str,
    timeframe: str
) -> Tuple[Optional[pd.Timestamp], Optional[pd.Timestamp]]:
    """
    Parse CSV filename to extract date range using flexible regex patterns.

    Supports multiple filename formats:
    - EURUSD_1h_20200102-050000_20250717-030000_ready.csv
    - EURUSD_1h_20200102_20250717_ready.csv
    - EURUSD_1h_2020-01-02_2025-07-17.csv
    - EURUSD_1h.csv (no dates in filename)

    Args:
        filename: CSV filename (without path)
        symbol: Expected symbol name
        timeframe: Expected timeframe

    Returns:
        Tuple of (start_date: pd.Timestamp or None, end_date: pd.Timestamp or None)
    """
    stem = Path(filename).stem

    # Pattern 1: SYMBOL_TIMEFRAME_YYYYMMDD-HHMMSS_YYYYMMDD-HHMMSS_suffix
    pattern1 = re.compile(
        rf'^{re.escape(symbol)}_{re.escape(timeframe)}_'
        r'(\d{8})(?:-\d{6})?_'
        r'(\d{8})(?:-\d{6})?'
        r'(?:_\w+)?$'
    )

    # Pattern 2: SYMBOL_TIMEFRAME_YYYY-MM-DD_YYYY-MM-DD
    pattern2 = re.compile(
        rf'^{re.escape(symbol)}_{re.escape(timeframe)}_'
        r'(\d{4}-\d{2}-\d{2})_'
        r'(\d{4}-\d{2}-\d{2})'
        r'(?:_\w+)?$'
    )

    # Pattern 3: SYMBOL_TIMEFRAME_YYYYMMDD_YYYYMMDD
    pattern3 = re.compile(
        rf'^{re.escape(symbol)}_{re.escape(timeframe)}_'
        r'(\d{8})_'
        r'(\d{8})'
        r'(?:_\w+)?$'
    )

    for pattern in [pattern1, pattern2, pattern3]:
        match = pattern.match(stem)
        if match:
            start_str, end_str = match.groups()

            try:
                if '-' in start_str:
                    start_date = pd.Timestamp(start_str, tz='UTC')
                    end_date = pd.Timestamp(end_str, tz='UTC')
                else:
                    start_date = pd.Timestamp(
                        f"{start_str[:4]}-{start_str[4:6]}-{start_str[6:8]}",
                        tz='UTC'
                    )
                    end_date = pd.Timestamp(
                        f"{end_str[:4]}-{end_str[4:6]}-{end_str[6:8]}",
                        tz='UTC'
                    )

                # Normalize to beginning/end of day
                start_date = start_date.normalize()
                end_date = end_date.normalize() + pd.Timedelta(days=1, seconds=-1)

                return start_date, end_date
            except Exception as e:
                logger.warning(f"Failed to parse dates from filename {filename}: {e}")
                continue

    logger.info(f"Could not parse dates from filename {filename}. Using full file range.")
    return None, None
