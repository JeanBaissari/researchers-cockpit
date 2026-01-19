"""
CSV bundle ingestion with SessionManager integration.

This module implements Phase 2 of the v1.1.0 calendar alignment plan,
integrating SessionManager for consistent session definitions across
bundle ingestion and backtest execution.
"""

import logging
from pathlib import Path
from typing import List, Optional, Iterator, Tuple

import pandas as pd
from zipline.utils.calendar_utils import get_calendar

from ...calendars.sessions import SessionManager
from ...paths import get_project_root
from ...data.aggregation import aggregate_ohlcv
from ...validation import DataValidator, ValidationConfig
from ..timeframes import get_timeframe_info, get_minutes_per_day
from ..registry import register_bundle_metadata, add_registered_bundle, unregister_bundle
from .parser import normalize_csv_columns, parse_csv_filename

logger = logging.getLogger(__name__)


def load_and_process_csv(
    csv_file: Path,
    symbol: str,
    timeframe: str,
    asset_class: str,
    session_mgr: SessionManager,
    user_start_date: Optional[pd.Timestamp],
    user_end_date: Optional[pd.Timestamp],
    show_progress: bool = False
) -> pd.DataFrame:
    """
    Load CSV file and apply session filters using SessionManager.

    Args:
        csv_file: Path to CSV file
        symbol: Asset symbol
        timeframe: Data timeframe (1m, 1h, daily, etc.)
        asset_class: Asset class (forex, crypto, equity)
        session_mgr: SessionManager for calendar and filtering
        user_start_date: User-specified start date (overrides filename)
        user_end_date: User-specified end date (overrides filename)
        show_progress: Whether to print progress messages

    Returns:
        Processed DataFrame with calendar-aligned sessions

    Raises:
        ValueError: If CSV validation fails
        FileNotFoundError: If CSV file doesn't exist
    """
    # Parse dates from filename
    file_start_date, file_end_date = parse_csv_filename(
        csv_file.name, symbol, timeframe
    )

    # Read CSV
    df = pd.read_csv(csv_file, parse_dates=[0], index_col=0)

    if df.empty:
        raise ValueError(f"Empty data for {symbol} from {csv_file}")

    # Normalize column names
    df = normalize_csv_columns(df)

    # Convert index to UTC
    df.index = pd.to_datetime(df.index, utc=True)

    # Data validation
    asset_type_map = {
        'equities': 'equity',
        'equity': 'equity',
        'forex': 'forex',
        'crypto': 'crypto',
        'cryptocurrencies': 'crypto'
    }
    asset_type = asset_type_map.get(asset_class.lower())

    config = ValidationConfig(
        timeframe=timeframe,
        asset_type=asset_type,
        calendar_name=session_mgr.calendar_name
    )
    validator = DataValidator(config=config)

    if show_progress:
        print(f"  Validating data for {symbol}...")

    validation_result = validator.validate(
        df, asset_name=symbol, asset_type=asset_type,
        calendar_name=session_mgr.calendar_name
    )

    if not validation_result.passed:
        error_summary = "; ".join([
            f"{check.details.get('field', check.name)}: {check.message}"
            for check in validation_result.error_checks[:5]
        ])
        raise ValueError(f"Data validation failed for {symbol}: {error_summary}")

    if show_progress:
        print(f"  ✓ Data validation passed for {symbol}")

    # Date filtering
    effective_start = user_start_date or file_start_date
    effective_end = user_end_date or file_end_date

    if effective_start:
        df = df[df.index >= effective_start]
    if effective_end:
        df = df[df.index <= effective_end]

    # Calendar bounds filtering
    first_calendar_session = session_mgr.calendar.first_session
    if first_calendar_session.tz is None:
        first_calendar_session = first_calendar_session.tz_localize('UTC')
    df = df[df.index >= first_calendar_session]

    # Apply session filters via SessionManager (SINGLE SOURCE OF TRUTH)
    if show_progress:
        print(f"  Applying session filters for {symbol}...")

    df = session_mgr.apply_filters(
        df,
        show_progress=show_progress,
        symbol=symbol
    )

    return df


def create_asset_metadata(
    symbols: List[str],
    data_dict: dict,
    calendar_name: str
) -> pd.DataFrame:
    """
    Create asset metadata DataFrame from symbol data.

    Args:
        symbols: List of symbols
        data_dict: Dict mapping sid -> DataFrame
        calendar_name: Calendar name

    Returns:
        Assets DataFrame with metadata
    """
    asset_data_list = []
    for sid, df in data_dict.items():
        symbol = symbols[sid]
        first_trade = df.index.min().normalize()
        last_trade = df.index.max().normalize()
        asset_data_list.append({
            'sid': sid,
            'symbol': symbol,
            'asset_name': symbol,
            'start_date': first_trade,
            'end_date': last_trade,
            'exchange': calendar_name,
            'country_code': 'XX',
        })
    return pd.DataFrame(asset_data_list).set_index('sid')
