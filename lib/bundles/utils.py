"""
Utility functions for bundle management.

Provides helper functions for data aggregation, date validation,
and symbol extraction from bundles.
"""

import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List

import pandas as pd

logger = logging.getLogger(__name__)


def is_valid_date_string(date_str: str) -> bool:
    """
    Check if a string is a valid YYYY-MM-DD date.

    Args:
        date_str: String to validate

    Returns:
        True if valid date format, False otherwise
    """
    if not date_str or not isinstance(date_str, str):
        return False
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def aggregate_to_4h(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate 1-hour OHLCV data to 4-hour bars.

    yfinance does not natively support 4h intervals. This function takes
    1h data and aggregates it to 4h bars using standard OHLCV aggregation rules.

    Args:
        df: DataFrame with 1h OHLCV data (columns: open, high, low, close, volume)
            Index must be a DatetimeIndex

    Returns:
        DataFrame with 4h OHLCV data
    """
    if df.empty:
        return df

    # Ensure we have the required columns
    required_cols = ["open", "high", "low", "close", "volume"]
    missing = set(required_cols) - set(df.columns)
    if missing:
        raise ValueError(f"DataFrame missing required columns for 4h aggregation: {missing}")

    # Resample to 4h using standard OHLCV aggregation
    agg_rules = {
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "volume": "sum",
    }

    # Use label='left' to label bars by their start time
    result = df.resample("4h", label="left", closed="left").agg(agg_rules)

    # Drop any rows where all values are NaN (incomplete periods)
    result = result.dropna(how="all")

    return result


def extract_symbols_from_bundle(bundle_name: str) -> List[str]:
    """
    Extract symbol list from an existing bundle's SQLite asset database.

    Args:
        bundle_name: Name of the bundle

    Returns:
        List of symbols, or empty list if extraction fails
    """
    bundle_data_path = Path.home() / ".zipline" / "data" / bundle_name
    if not bundle_data_path.exists():
        return []

    # Find the most recent ingestion directory
    ingestion_dirs = sorted(bundle_data_path.glob("*"), reverse=True)
    for ingestion_dir in ingestion_dirs:
        asset_db_path = ingestion_dir / "assets-8.sqlite"
        if not asset_db_path.exists():
            # Try older versions
            for version in range(7, 0, -1):
                asset_db_path = ingestion_dir / f"assets-{version}.sqlite"
                if asset_db_path.exists():
                    break

        if asset_db_path.exists():
            try:
                conn = sqlite3.connect(str(asset_db_path))
                cursor = conn.cursor()
                cursor.execute("SELECT symbol FROM equity_symbol_mappings")
                symbols = [row[0] for row in cursor.fetchall()]
                conn.close()
                if symbols:
                    return list(set(symbols))  # Remove duplicates
            except (sqlite3.Error, Exception) as e:
                logger.warning(f"Failed to extract symbols from {asset_db_path}: {e}")
                continue

    return []


def validate_bundle_exists(bundle_name: str, check_filesystem: bool = False) -> bool:
    """
    Validate that a bundle exists in Zipline's registry.

    v1.12.0+: Uses Zipline's bundles dict directly (NO WRAPPERS).

    Args:
        bundle_name: Name of the bundle to validate
        check_filesystem: If True, also verify bundle data directory exists

    Returns:
        True if bundle exists, False otherwise

    Example:
        >>> from lib.bundles.utils import validate_bundle_exists
        >>> if validate_bundle_exists('eurusd_1m'):
        ...     print("Bundle exists")
        >>> if validate_bundle_exists('missing_bundle', check_filesystem=True):
        ...     print("Bundle exists in registry and filesystem")
    """
    from zipline.data.bundles import bundles
    from .initialization import ensure_bundles_initialized

    # Ensure bundles are initialized
    ensure_bundles_initialized()

    # Check if bundle is registered in Zipline's registry
    if bundle_name not in bundles:
        logger.debug(f"Bundle '{bundle_name}' not found in Zipline registry")
        return False

    # Optional filesystem check
    if check_filesystem:
        bundle_data_path = Path.home() / ".zipline" / "data" / bundle_name
        if not bundle_data_path.exists():
            logger.debug(
                f"Bundle '{bundle_name}' registered but data directory not found: {bundle_data_path}"
            )
            return False

    logger.debug(f"Bundle '{bundle_name}' validated successfully")
    return True


def ensure_bundle_registered(
    bundle_name: str,
    raise_on_missing: bool = True,
    exception_type: type = FileNotFoundError,
    log_on_missing: bool = False,
    log_level: int = logging.WARNING,
    source_hint: str = "<SOURCE>",
    symbols_hint: str = "<SYMBOLS>",
    start_date_hint: str | None = None,
    end_date_hint: str | None = None,
) -> bool:
    """
    Ensure a bundle is registered in Zipline's registry, raising helpful error if missing.

    This function centralizes bundle existence checking and error messaging
    to avoid duplication across access.py, preprocessing.py, and validation modules.

    v1.12.0+: Uses Zipline's bundles dict directly (NO WRAPPERS).

    Args:
        bundle_name: Name of the bundle to check
        raise_on_missing: If True, raise exception when bundle is missing; if False, return False
        exception_type: Exception type to raise (default: FileNotFoundError)
        log_on_missing: If True and raise_on_missing is False, log the full error message.
            Useful for "warn-only" validation paths to avoid duplicating error text.
        log_level: Logging level to use when log_on_missing is True.
        source_hint: Source hint for the suggested ingestion command (default placeholder).
        symbols_hint: Symbols hint for the suggested ingestion command (default placeholder).
        start_date_hint: Optional start date hint for the suggested ingestion command.
        end_date_hint: Optional end date hint for the suggested ingestion command.

    Returns:
        True if bundle exists, False if missing and raise_on_missing=False

    Raises:
        FileNotFoundError (or exception_type): If bundle not found and raise_on_missing=True

    Example:
        >>> from lib.bundles.utils import ensure_bundle_registered
        >>> ensure_bundle_registered('eurusd_1m')  # Raises if missing
        >>> if ensure_bundle_registered('missing', raise_on_missing=False):
        ...     print("Bundle exists")
    """
    from zipline.data.bundles import bundles
    from .initialization import ensure_bundles_initialized

    # Ensure bundles are initialized
    ensure_bundles_initialized()

    # Check if bundle is registered
    if bundle_name not in bundles:
        from .errors import format_bundle_not_found_message, format_ingest_command

        ingest_cmd = format_ingest_command(
            bundle_name=bundle_name,
            source=source_hint,
            symbols=symbols_hint,
            start_date=start_date_hint,
            end_date=end_date_hint,
        )
        error_msg = format_bundle_not_found_message(
            bundle_name=bundle_name,
            available_bundles=bundles.keys(),
            ingest_command=ingest_cmd,
        )

        if raise_on_missing:
            raise exception_type(error_msg)

        if log_on_missing:
            logger.log(log_level, error_msg)
        else:
            logger.debug(f"Bundle '{bundle_name}' not found in Zipline registry")
        return False

    return True


def get_bundle_session_date_range(bundle_data: object) -> tuple[pd.Timestamp, pd.Timestamp] | None:
    """
    Extract the covered session date range from a loaded Zipline bundle object.

    This helper exists to keep bundle date-range validation DRY across:
    - Backtest preprocessing (`lib/backtest/preprocessing.py`)
    - Validation checks (`lib/validation/validators/bundle.py`)

    It does NOT wrap Zipline APIs; it simply reads the standard attributes
    exposed by Zipline's bundle data object.

    Args:
        bundle_data: The object returned by `zipline.data.bundles.load()`.

    Returns:
        A tuple of (bundle_start, bundle_end) as timezone-naive, normalized (midnight) timestamps,
        or None if the bundle does not expose sessions in the expected location.
    """
    try:
        sessions = bundle_data.equity_daily_bar_reader.sessions
    except AttributeError:
        return None

    if sessions is None or len(sessions) == 0:
        return None

    start = pd.Timestamp(sessions[0])
    end = pd.Timestamp(sessions[-1])

    # Normalize to timezone-naive midnight for consistent comparisons/messages
    if start.tz is not None:
        start = start.tz_convert(None)
    if end.tz is not None:
        end = end.tz_convert(None)

    return start.normalize(), end.normalize()
