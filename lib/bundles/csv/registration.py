"""
CSV bundle registration orchestration.

Main entry point for registering CSV bundles with Zipline.
Coordinates CSV loading, session management, and Zipline writer operations.
"""

import logging
from pathlib import Path
from typing import List, Optional

import pandas as pd
from zipline.utils.calendar_utils import get_calendar

from ...calendars.sessions import SessionManager
from ...utils import get_project_root
from ..timeframes import get_timeframe_info, get_minutes_per_day
from ..registry import register_bundle_metadata, add_registered_bundle, unregister_bundle
from .ingestion import load_and_process_csv
from .writer import write_minute_and_daily_bars, write_daily_bars

logger = logging.getLogger(__name__)


def register_csv_bundle(
    bundle_name: str,
    symbols: List[str],
    calendar_name: str,
    timeframe: str,
    asset_class: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    force: bool = False
):
    """
    Register a local CSV data bundle for ingestion using SessionManager.

    This function implements Phase 2 of the v1.1.0 calendar alignment plan,
    using SessionManager to ensure consistent session definitions between
    bundle ingestion and backtest execution.

    CSV files are expected in:
    data/processed/{timeframe}/{symbol}_{timeframe}_*.csv

    Args:
        bundle_name: Name for the bundle
        symbols: List of symbols to ingest
        calendar_name: Trading calendar name (FOREX, CRYPTO, NYSE, etc.)
        timeframe: Data timeframe (1m, 5m, 1h, daily, etc.)
        asset_class: Asset class (forex, crypto, equity)
        start_date: Optional start date (overrides filename dates)
        end_date: Optional end date (overrides filename dates)
        force: If True, re-ingest even if bundle exists

    Raises:
        FileNotFoundError: If CSV directory or files not found
        RuntimeError: If no data was successfully loaded
    """
    from zipline.data.bundles import register, bundles

    if bundle_name in bundles:
        if force:
            unregister_bundle(bundle_name)
        else:
            logger.info(f"Bundle {bundle_name} already registered. Use --force to re-ingest.")
            return

    # Closure variables
    closure_start_date = start_date
    closure_end_date = end_date
    closure_timeframe = timeframe
    closure_calendar_name = calendar_name
    closure_asset_class = asset_class

    def make_csv_ingest(symbols_list):
        mpd = get_minutes_per_day(closure_calendar_name)

        @register(bundle_name, calendar_name=closure_calendar_name, minutes_per_day=mpd)
        def csv_ingest(environ, asset_db_writer, minute_bar_writer,
                       daily_bar_writer, adjustment_writer, calendar,
                       start_session, end_session, cache, show_progress, timestamp):
            """CSV bundle ingest function with SessionManager integration."""

            # Create SessionManager for this asset class (SINGLE SOURCE OF TRUTH)
            session_mgr = SessionManager.for_asset_class(closure_asset_class)

            if show_progress:
                print(f"✓ SessionManager initialized ({session_mgr.strategy.__class__.__name__})")
                print(f"Ingesting {closure_timeframe} data for {len(symbols_list)} symbols from CSVs...")

            # Parse user-specified dates
            user_start = pd.Timestamp(closure_start_date, tz='UTC').normalize() if closure_start_date else None
            user_end = pd.Timestamp(closure_end_date, tz='UTC').normalize() if closure_end_date else None

            # Get expected sessions for validation
            if user_start and user_end:
                expected_sessions = session_mgr.get_sessions(user_start, user_end)
                if show_progress:
                    print(f"✓ Calendar expects {len(expected_sessions)} sessions")

            # Get Zipline data frequency
            tf_info = get_timeframe_info(closure_timeframe)
            data_frequency = tf_info['data_frequency']

            # Load all CSV data
            local_data_path = get_project_root() / 'data' / 'processed' / closure_timeframe
            if not local_data_path.is_dir():
                raise FileNotFoundError(f"CSV data directory not found: {local_data_path}")

            all_data = []
            for sid, symbol in enumerate(symbols_list):
                try:
                    # Find CSV file
                    file_pattern = f"{symbol}_{closure_timeframe}_*.csv"
                    matching_files = list(local_data_path.glob(file_pattern))

                    if not matching_files:
                        logger.warning(f"No CSV file found for {symbol} with pattern '{file_pattern}'")
                        continue

                    csv_file = matching_files[0]

                    # Load and process CSV with SessionManager
                    df = load_and_process_csv(
                        csv_file=csv_file,
                        symbol=symbol,
                        timeframe=closure_timeframe,
                        asset_class=closure_asset_class,
                        session_mgr=session_mgr,
                        user_start_date=user_start,
                        user_end_date=user_end,
                        show_progress=show_progress
                    )

                    if not df.empty:
                        all_data.append((sid, df))
                    else:
                        logger.warning(f"No data for {symbol} after filtering")

                except Exception as e:
                    logger.exception(f"Error processing CSV for {symbol}: {e}")
                    if show_progress:
                        print(f"  Error: {symbol}: {e}")
                    continue

            if not all_data:
                raise RuntimeError(
                    f"No CSV data was successfully loaded. "
                    f"Symbols attempted: {symbols_list}. "
                    f"Check data/processed/{closure_timeframe}/"
                )

            # Write data to Zipline bundle
            if data_frequency == 'minute':
                write_minute_and_daily_bars(
                    minute_data=all_data,
                    symbols=symbols_list,
                    session_mgr=session_mgr,
                    asset_db_writer=asset_db_writer,
                    minute_bar_writer=minute_bar_writer,
                    daily_bar_writer=daily_bar_writer,
                    adjustment_writer=adjustment_writer,
                    show_progress=show_progress
                )
            else:
                write_daily_bars(
                    daily_data=all_data,
                    symbols=symbols_list,
                    calendar_name=closure_calendar_name,
                    asset_db_writer=asset_db_writer,
                    daily_bar_writer=daily_bar_writer,
                    adjustment_writer=adjustment_writer,
                    show_progress=show_progress
                )

        return csv_ingest

    make_csv_ingest(symbols)
    add_registered_bundle(bundle_name)

    register_bundle_metadata(
        bundle_name=bundle_name,
        symbols=symbols,
        calendar_name=calendar_name,
        start_date=start_date,
        end_date=end_date,
        data_frequency=get_timeframe_info(timeframe)['data_frequency'],
        timeframe=timeframe
    )

    if force:
        logger.info(f"Bundle {bundle_name} re-registered successfully")
    else:
        logger.info(f"Bundle {bundle_name} registered successfully")
