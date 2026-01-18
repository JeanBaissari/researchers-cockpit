"""
Yahoo Finance bundle registration for The Researcher's Cockpit.

Handles bundle registration with Zipline, metadata management, and writer coordination.
Extracted from yahoo_bundle.py as part of v1.0.11 refactoring.
"""

import logging
from pathlib import Path
from typing import List, Optional

import pandas as pd
from zipline.utils.calendar_utils import get_calendar

from ..timeframes import get_timeframe_info, get_minutes_per_day, validate_timeframe_date_range
from ..registry import unregister_bundle, register_bundle_metadata, add_registered_bundle
from .fetcher import fetch_yahoo_data
from .processor import process_yahoo_data, aggregate_to_daily
from ...data.filters import (
    consolidate_forex_sunday_to_friday,
    filter_to_calendar_sessions,
    apply_gap_filling,
)

logger = logging.getLogger(__name__)


def register_yahoo_bundle(
    bundle_name: str,
    symbols: List[str],
    calendar_name: str = 'XNYS',
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    data_frequency: str = 'daily',
    timeframe: str = 'daily',
    force: bool = False
):
    """
    Register a Yahoo Finance bundle with multi-timeframe support.

    Args:
        bundle_name: Name for the bundle
        symbols: List of symbols to ingest
        calendar_name: Trading calendar name
        start_date: Start date for data (YYYY-MM-DD)
        end_date: End date for data (YYYY-MM-DD)
        data_frequency: Zipline data frequency ('daily' or 'minute')
        timeframe: Actual timeframe for yfinance ('1m', '5m', '15m', '1h', '4h', 'daily', etc.')
        force: If True, unregister and re-register even if already registered

    Note:
        For 4h timeframe, this fetches 1h data from yfinance and aggregates to 4h,
        since yfinance does not natively support 4h intervals.
    """
    from zipline.data.bundles import register, bundles

    # Check if already registered
    if bundle_name in bundles:
        if force:
            unregister_bundle(bundle_name)
        else:
            return

    # Validate and adjust date range
    adjusted_start_date, adjusted_end_date, warning = validate_timeframe_date_range(
        timeframe, start_date, end_date
    )
    if warning:
        logger.warning(warning)
        print(warning)

    # Get timeframe info
    tf_info = get_timeframe_info(timeframe.lower())
    yf_interval = tf_info['yf_interval']
    requires_aggregation = tf_info['requires_aggregation']
    aggregation_target = tf_info['aggregation_target']

    # Capture closure variables
    closure_start_date = adjusted_start_date
    closure_end_date = adjusted_end_date
    closure_data_frequency = data_frequency
    closure_timeframe = timeframe
    closure_yf_interval = yf_interval
    closure_calendar_name = calendar_name
    closure_requires_aggregation = requires_aggregation
    closure_aggregation_target = aggregation_target

    def make_yahoo_ingest(symbols_list):
        mpd = get_minutes_per_day(closure_calendar_name)

        @register(bundle_name, calendar_name=closure_calendar_name, minutes_per_day=mpd)
        def yahoo_ingest(environ, asset_db_writer, minute_bar_writer,
                         daily_bar_writer, adjustment_writer, calendar,
                         start_session, end_session, cache, show_progress, timestamp):
            """Yahoo Finance bundle ingest function."""
            calendar_obj = get_calendar(closure_calendar_name)

            # Convert sessions to UTC midnight
            def to_utc_midnight(ts):
                if ts is None:
                    return None
                if hasattr(ts, 'tz') and ts.tz is not None:
                    ts = ts.tz_convert('UTC')
                return pd.Timestamp(ts.date(), tz='UTC')

            start_date_utc = to_utc_midnight(start_session)
            end_date_utc = to_utc_midnight(end_session)

            # Create asset metadata
            n_symbols = len(symbols_list)
            equities_data = {
                'symbol': symbols_list,
                'asset_name': symbols_list,
                'start_date': [start_date_utc] * n_symbols,
                'end_date': [end_date_utc] * n_symbols,
                'exchange': ['NYSE' if closure_calendar_name == 'XNYS' else ('NASDAQ' if closure_calendar_name == 'XNAS' else 'NYSE')] * n_symbols,
                'country_code': ['US'] * n_symbols,
            }
            equities_df = pd.DataFrame(equities_data, index=pd.Index(range(n_symbols), name='sid'))
            asset_db_writer.write(equities=equities_df)

            if show_progress:
                print(f"Fetching {closure_timeframe} data for {len(symbols_list)} symbols from Yahoo Finance...")
                if closure_data_frequency == 'minute':
                    print(f"  Using minute bar writer (yfinance interval: {closure_yf_interval})")
                if closure_requires_aggregation:
                    print(f"  Note: Will aggregate {closure_yf_interval} data to {closure_aggregation_target}")

            # Data generator
            def data_gen():
                successful_fetches = 0

                for sid, symbol in enumerate(symbols_list):
                    try:
                        # Fetch data
                        hist = fetch_yahoo_data(
                            symbol,
                            closure_start_date,
                            closure_end_date,
                            closure_yf_interval,
                            show_progress
                        )

                        # Process data
                        bars_df = process_yahoo_data(
                            hist,
                            closure_data_frequency,
                            calendar_obj,
                            closure_calendar_name,
                            closure_start_date,
                            closure_end_date,
                            closure_requires_aggregation,
                            closure_aggregation_target,
                            symbol,
                            show_progress
                        )

                        successful_fetches += 1
                        yield sid, bars_df

                    except Exception as e:
                        print(f"Error fetching {closure_timeframe} data for {symbol}: {e}")
                        logger.exception(f"Error fetching {closure_timeframe} data for {symbol}")
                        continue

                if successful_fetches == 0:
                    raise RuntimeError(
                        f"No data was successfully fetched for any symbol. "
                        f"Symbols attempted: {symbols_list}. "
                        f"Check that symbols are valid and date range has data."
                    )

            if closure_data_frequency == 'minute':
                # Collect minute data
                if show_progress:
                    print("  Collecting minute data for aggregation...")
                all_minute_data = list(data_gen())

                if not all_minute_data:
                    raise RuntimeError("No minute data was collected. Check symbol validity and date range.")

                # Write minute bars
                if show_progress:
                    print(f"  Writing {len(all_minute_data)} symbol(s) to minute bar writer...")
                minute_bar_writer.write(iter(all_minute_data), show_progress=show_progress)

                # Aggregate to daily
                if show_progress:
                    print("  Aggregating minute data to daily bars...")

                def daily_data_gen():
                    for sid, minute_df in all_minute_data:
                        try:
                            daily_df = aggregate_to_daily(minute_df)

                            if daily_df.empty:
                                print(f"  Warning: No daily data after aggregating minute data for SID {sid}")
                                continue

                            # Ensure UTC and normalize
                            if daily_df.index.tz is None:
                                daily_df.index = daily_df.index.tz_localize('UTC')
                            elif str(daily_df.index.tz) != 'UTC':
                                daily_df.index = daily_df.index.tz_convert('UTC')
                            daily_df.index = daily_df.index.normalize()

                            # FOREX Sunday consolidation
                            if 'FOREX' in closure_calendar_name.upper():
                                daily_df = consolidate_forex_sunday_to_friday(daily_df, calendar_obj, show_progress, sid)
                                if daily_df.empty:
                                    continue

                            # Calendar session filtering
                            if 'FOREX' in closure_calendar_name.upper():
                                daily_df = filter_to_calendar_sessions(daily_df, calendar_obj, show_progress, sid)
                                if daily_df.empty:
                                    continue

                            # Gap filling
                            if 'FOREX' in closure_calendar_name.upper() or 'CRYPTO' in closure_calendar_name.upper():
                                daily_df = apply_gap_filling(daily_df, calendar_obj, closure_calendar_name, show_progress, sid)
                                if daily_df.empty:
                                    continue

                            yield sid, daily_df
                        except Exception as agg_err:
                            print(f"  Warning: Failed to aggregate daily data for SID {sid}: {agg_err}")
                            logger.exception(f"Failed to aggregate daily data for SID {sid}")
                            continue

                daily_bar_writer.write(daily_data_gen(), show_progress=show_progress)

                if show_progress:
                    print("  ✓ Both minute and daily bars written successfully")
            else:
                daily_bar_writer.write(data_gen(), show_progress=show_progress)

            # Write empty adjustments
            adjustment_writer.write(splits=None, dividends=None, mergers=None)

        return yahoo_ingest

    make_yahoo_ingest(symbols)
    add_registered_bundle(bundle_name)

    # Persist metadata
    register_bundle_metadata(
        bundle_name=bundle_name,
        symbols=symbols,
        calendar_name=calendar_name,
        start_date=start_date,
        end_date=end_date,
        data_frequency=data_frequency,
        timeframe=timeframe
    )
