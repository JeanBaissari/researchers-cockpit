"""
Zipline writer interface for CSV bundles.

Handles writing minute and daily bars to Zipline bundle storage,
including aggregation from minute to daily data.
"""

import logging
from typing import Iterator, Tuple, List

import pandas as pd

from ...calendars.sessions import SessionManager
from ...utils import aggregate_ohlcv
from ...data.filters import consolidate_forex_sunday_to_friday, filter_to_calendar_sessions, apply_gap_filling

logger = logging.getLogger(__name__)


def write_minute_and_daily_bars(
    minute_data: List[Tuple[int, pd.DataFrame]],
    symbols: List[str],
    session_mgr: SessionManager,
    asset_db_writer,
    minute_bar_writer,
    daily_bar_writer,
    adjustment_writer,
    show_progress: bool = False
):
    """
    Write both minute and daily bars to Zipline bundle.

    For minute data, aggregates to daily and applies FOREX-specific
    filters (Sunday consolidation, gap filling) to daily bars.

    Args:
        minute_data: List of (sid, DataFrame) tuples with minute bars
        symbols: List of symbols
        session_mgr: SessionManager for calendar operations
        asset_db_writer: Zipline asset database writer
        minute_bar_writer: Zipline minute bar writer
        daily_bar_writer: Zipline daily bar writer
        adjustment_writer: Zipline adjustment writer
        show_progress: Whether to print progress messages
    """
    from .ingestion import create_asset_metadata

    # Write asset metadata
    asset_metadata = create_asset_metadata(
        symbols,
        {sid: df for sid, df in minute_data},
        session_mgr.calendar_name
    )
    asset_db_writer.write(equities=asset_metadata)

    # Write minute bars
    if show_progress:
        print(f"  Writing {len(minute_data)} symbol(s) to minute bar writer...")
    minute_bar_writer.write(iter(minute_data), show_progress=show_progress)

    # Aggregate to daily and write
    if show_progress:
        print("  Aggregating minute data to daily bars...")

    def daily_data_gen():
        """Generate aggregated daily data from minute data."""
        for sid, minute_df in minute_data:
            try:
                daily_df = aggregate_ohlcv(minute_df, 'daily')
                if daily_df.empty:
                    logger.warning(f"No daily data after aggregating minute data for SID {sid}")
                    continue

                # Ensure UTC timezone and normalize
                if daily_df.index.tz is not None:
                    daily_df.index = daily_df.index.tz_convert('UTC').normalize()
                else:
                    daily_df.index = daily_df.index.tz_localize('UTC').normalize()

                # Apply FOREX-specific filters to aggregated daily data
                if 'FOREX' in session_mgr.calendar_name.upper():
                    daily_df = consolidate_forex_sunday_to_friday(
                        daily_df, session_mgr.calendar, show_progress, sid
                    )
                    if daily_df.empty:
                        continue

                    daily_df = filter_to_calendar_sessions(
                        daily_df, session_mgr.calendar, show_progress, sid
                    )
                    if daily_df.empty:
                        continue

                # Gap filling for FOREX and CRYPTO
                if 'FOREX' in session_mgr.calendar_name.upper() or 'CRYPTO' in session_mgr.calendar_name.upper():
                    daily_df = apply_gap_filling(
                        daily_df, session_mgr.calendar,
                        session_mgr.calendar_name, show_progress, sid
                    )
                    if daily_df.empty:
                        continue

                yield sid, daily_df
            except Exception as e:
                logger.exception(f"Failed to aggregate daily data for SID {sid}: {e}")
                continue

    daily_bar_writer.write(daily_data_gen(), show_progress=show_progress)

    # Write adjustments (empty for CSV data)
    adjustment_writer.write(splits=None, dividends=None, mergers=None)

    if show_progress:
        print("  ✓ Both minute and daily bars written successfully")


def write_daily_bars(
    daily_data: List[Tuple[int, pd.DataFrame]],
    symbols: List[str],
    calendar_name: str,
    asset_db_writer,
    daily_bar_writer,
    adjustment_writer,
    show_progress: bool = False
):
    """
    Write daily bars to Zipline bundle.

    Args:
        daily_data: List of (sid, DataFrame) tuples with daily bars
        symbols: List of symbols
        calendar_name: Calendar name
        asset_db_writer: Zipline asset database writer
        daily_bar_writer: Zipline daily bar writer
        adjustment_writer: Zipline adjustment writer
        show_progress: Whether to print progress messages
    """
    from .ingestion import create_asset_metadata

    # Write asset metadata
    asset_metadata = create_asset_metadata(
        symbols,
        {sid: df for sid, df in daily_data},
        calendar_name
    )
    asset_db_writer.write(equities=asset_metadata)

    # Write daily bars
    daily_bar_writer.write(iter(daily_data), show_progress=show_progress)

    # Write adjustments (empty for CSV data)
    adjustment_writer.write(splits=None, dividends=None, mergers=None)
