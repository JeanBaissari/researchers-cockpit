"""
Yahoo Finance bundle registration.

Provides functions to register and ingest Yahoo Finance data bundles.
"""

import logging
from pathlib import Path
from typing import List, Optional

import numpy as np
import pandas as pd
import yfinance as yf
from zipline.utils.calendar_utils import get_calendar

from ..utils import aggregate_ohlcv
from ..data.filters import (
    filter_forex_presession_bars,
    consolidate_forex_sunday_to_friday,
    filter_to_calendar_sessions,
    filter_daily_to_calendar_sessions,
    apply_gap_filling,
)
from .timeframes import (
    get_timeframe_info,
    get_minutes_per_day,
    validate_timeframe_date_range,
)
from .registry import (
    unregister_bundle,
    register_bundle_metadata,
    load_bundle_registry,
    add_registered_bundle,
)
from .utils import aggregate_to_4h, is_valid_date_string

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
        timeframe: Actual timeframe for yfinance ('1m', '5m', '15m', '1h', '4h', 'daily', etc.)
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

    # Validate and adjust date range based on timeframe limits for Yahoo Finance
    adjusted_start_date, adjusted_end_date, warning = validate_timeframe_date_range(
        timeframe, start_date, end_date
    )
    if warning:
        logger.warning(warning)
        print(warning)

    # Get timeframe info including aggregation requirements
    tf_info = get_timeframe_info(timeframe.lower())
    yf_interval = tf_info['yf_interval']
    requires_aggregation = tf_info['requires_aggregation']
    aggregation_target = tf_info['aggregation_target']

    # Capture closure variables explicitly
    closure_start_date = adjusted_start_date
    closure_end_date = adjusted_end_date
    closure_data_frequency = data_frequency
    closure_timeframe = timeframe
    closure_yf_interval = yf_interval
    closure_calendar_name = calendar_name
    closure_requires_aggregation = requires_aggregation
    closure_aggregation_target = aggregation_target

    # Store symbols for this bundle (needed for the ingest function)
    # Use closure to capture symbols
    def make_yahoo_ingest(symbols_list):
        # CRITICAL: Use exchange_calendars code, not common name
        # Zipline-reloaded uses exchange_calendars library codes:
        # - 'XNYS' (NYSE)
        # - 'XNAS' (NASDAQ)
        # - '24/7' (Crypto - always open)
        # calendar_name should already be in exchange_calendars format

        # Get minutes_per_day for the calendar type
        # CRITICAL: This must be set correctly for minute bar writers
        # 24/7 markets (CRYPTO) need 1440, standard markets use 390
        mpd = get_minutes_per_day(closure_calendar_name)

        @register(bundle_name, calendar_name=closure_calendar_name, minutes_per_day=mpd)
        def yahoo_ingest(environ, asset_db_writer, minute_bar_writer,
                         daily_bar_writer, adjustment_writer, calendar,
                         start_session, end_session, cache, show_progress, timestamp):
            """Yahoo Finance bundle ingest function.

            Args:
                environ: Environment variables
                asset_db_writer: Asset database writer
                minute_bar_writer: Minute bar writer
                daily_bar_writer: Daily bar writer
                adjustment_writer: Adjustment writer
                calendar: Trading calendar
                start_session: Start session timestamp
                end_session: End session timestamp
                cache: Cache object
                show_progress: Whether to show progress
                timestamp: Bundle timestamp string
            """
            # Get calendar object inside ingest function for consistency
            calendar_obj = get_calendar(closure_calendar_name)
            
            # Convert start/end sessions to timezone-aware UTC at midnight
            # Per Zipline patterns: dates must be pd.Timestamp with tz='utc'
            def to_utc_midnight(ts):
                """Convert timestamp to midnight UTC, timezone-aware."""
                if ts is None:
                    return None
                # Convert to UTC if timezone-aware
                if hasattr(ts, 'tz') and ts.tz is not None:
                    ts = ts.tz_convert('UTC')
                # Normalize to midnight and ensure UTC timezone
                return pd.Timestamp(ts.date(), tz='UTC')

            start_date_utc = to_utc_midnight(start_session)
            end_date_utc = to_utc_midnight(end_session)

            # Create asset metadata DataFrame with SID as index
            # CRITICAL: Pass dates as lists to ensure datetime64[ns] dtype (not datetime64[s])
            # Pandas 2.x creates datetime64[s] for broadcasted single values, but Zipline
            # expects nanoseconds when reading back via pd.Timestamp(..., unit='ns')
            n_symbols = len(symbols_list)
            equities_data = {
                'symbol': symbols_list,
                'asset_name': symbols_list,  # Use symbol as name for now'
                'start_date': [start_date_utc] * n_symbols,   # List for datetime64[ns]
                'end_date': [end_date_utc] * n_symbols,       # List for datetime64[ns]
                'exchange': ['NYSE' if closure_calendar_name == 'XNYS' else ('NASDAQ' if closure_calendar_name == 'XNAS' else 'NYSE')] * n_symbols,
                'country_code': ['US'] * n_symbols,  # Add country code column
            }
            equities_df = pd.DataFrame(equities_data, index=pd.Index(range(n_symbols), name='sid'))
            asset_db_writer.write(equities=equities_df)

            # Fetch data from Yahoo Finance
            if show_progress:
                print(f"Fetching {closure_timeframe} data for {len(symbols_list)} symbols from Yahoo Finance...")
                if closure_data_frequency == 'minute':
                    print(f"  Using minute bar writer (yfinance interval: {closure_yf_interval})")
                if closure_requires_aggregation:
                    print(f"  Note: Will aggregate {closure_yf_interval} data to {closure_aggregation_target}")

            # Download data and prepare for writing
            def data_gen():
                # Use the yf_interval from closure (set based on timeframe)
                current_yf_interval = closure_yf_interval

                # Track successful fetches for validation
                successful_fetches = 0

                for sid, symbol in enumerate(symbols_list):
                    try:
                        ticker = yf.Ticker(symbol)
                        # CRITICAL: Use user-specified dates from closure, not Zipline's session dates
                        # For intraday data (1h, 5m, etc.), yfinance has strict date limits
                        # The closure_start_date/closure_end_date are the user's intended range
                        if closure_start_date:
                            yf_start = pd.Timestamp(closure_start_date).to_pydatetime()
                        else:
                            yf_start = start_date_utc.tz_localize(None).to_pydatetime() if start_date_utc else None

                        if closure_end_date:
                            yf_end = pd.Timestamp(closure_end_date).to_pydatetime()
                        else:
                            yf_end = None  # Let yfinance use today

                        hist = ticker.history(start=yf_start, end=yf_end, interval=current_yf_interval)

                        if hist.empty:
                            print(f"Warning: No data for {symbol} at {closure_timeframe} timeframe.")
                            continue

                        # Timestamp handling depends on data frequency:
                        # - Daily data: Normalize to midnight UTC (Zipline expectation)
                        # - Intraday data (minute, hourly): Keep time-of-day, just ensure UTC
                        if closure_data_frequency == 'daily':
                            # Per Zipline patterns: daily bar data must be at midnight UTC
                            if hist.index.tz is not None:
                                hist.index = hist.index.tz_convert('UTC').normalize()
                            else:
                                hist.index = pd.to_datetime(hist.index).normalize().tz_localize('UTC')
                        else:
                            # Intraday data: Keep time-of-day information, ensure UTC
                            if hist.index.tz is not None:
                                hist.index = hist.index.tz_convert('UTC')
                            else:
                                hist.index = pd.to_datetime(hist.index).tz_localize('UTC')

                        # Prepare DataFrame with required columns
                        # Use float64 for volume to handle large crypto volumes
                        # uint32 max is ~4.29B, insufficient for BTC daily volumes
                        volume_data = hist['Volume'].astype('float64')

                        # Validate and log if volume exceeds uint32 limits
                        max_vol = volume_data.max()
                        uint32_max = np.iinfo(np.uint32).max
                        if max_vol > uint32_max:
                            if show_progress:
                                print(f"  {symbol}: Volume exceeds uint32 ({max_vol:.2e}), using float64 storage")

                        # Verify no NaN/Inf after conversion
                        if volume_data.isna().any():
                            volume_data = volume_data.fillna(0)
                        if np.isinf(volume_data).any():
                            volume_data = volume_data.replace([np.inf, -np.inf], 0)

                        bars_df = pd.DataFrame({
                            'open': hist['Open'],
                            'high': hist['High'],
                            'low': hist['Low'],
                            'close': hist['Close'],
                            'volume': volume_data,
                        }, index=hist.index)

                        # === 4H AGGREGATION ===
                        # If timeframe requires aggregation (e.g., 4h from 1h), do it now
                        if closure_requires_aggregation and closure_aggregation_target == '4h':
                            original_count = len(bars_df)
                            bars_df = aggregate_to_4h(bars_df)
                            if show_progress:
                                print(f"  {symbol}: Aggregated {original_count} 1h bars to {len(bars_df)} 4h bars")

                        # === USER-SPECIFIED DATE FILTERING ===
                        # Filter to user-specified date range (from closure)
                        if closure_start_date:
                            user_start = pd.Timestamp(closure_start_date, tz='UTC')
                            bars_df = bars_df[bars_df.index >= user_start]
                        if closure_end_date:
                            user_end = pd.Timestamp(closure_end_date, tz='UTC')
                            bars_df = bars_df[bars_df.index <= user_end]

                        # === CALENDAR BOUNDS FILTERING ===
                        # Align data to calendar first session
                        first_calendar_session = calendar_obj.first_session
                        if first_calendar_session.tz is None:
                            first_calendar_session = first_calendar_session.tz_localize('UTC')
                        bars_df = bars_df[bars_df.index >= first_calendar_session]

                        # === CALENDAR SESSION FILTERING (for daily data) ===
                        if closure_data_frequency == 'daily' and len(bars_df) > 0:
                            bars_df = filter_daily_to_calendar_sessions(bars_df, calendar_obj, show_progress, symbol)

                        # === FOREX PRE-SESSION FILTERING (for intraday data) ===
                        if closure_data_frequency == 'minute' and 'FOREX' in closure_calendar_name.upper():
                            bars_df = filter_forex_presession_bars(bars_df, calendar_obj, show_progress, symbol)

                        # Check if we have any data left after filtering
                        if bars_df.empty:
                            print(f"Warning: No data for {symbol} after date/calendar filtering.")
                            continue

                        # === GAP-FILLING FOR FOREX AND CRYPTO (daily data only) ===
                        if closure_data_frequency == 'daily':
                            if 'FOREX' in closure_calendar_name.upper() or 'CRYPTO' in closure_calendar_name.upper():
                                bars_df = apply_gap_filling(bars_df, calendar_obj, closure_calendar_name, show_progress, symbol)

                        successful_fetches += 1
                        yield sid, bars_df

                    except Exception as e:
                        print(f"Error fetching {closure_timeframe} data for {symbol}: {e}")
                        logger.exception(f"Error fetching {closure_timeframe} data for {symbol}")
                        continue

                # Validate that at least some data was fetched
                if successful_fetches == 0:
                    raise RuntimeError(
                        f"No data was successfully fetched for any symbol. "
                        f"Symbols attempted: {symbols_list}. "
                        f"Check that symbols are valid and date range has data."
                    )
            
            if closure_data_frequency == 'minute':
                # For intraday bundles, we need to write BOTH minute and daily bars.
                # Zipline's internal operations (benchmark, history window, Pipeline API)
                # require valid daily bar data even when running minute-frequency backtests.
                # Without daily bars, the daily_bar_reader has NaT for first_trading_day,
                # causing: AttributeError: 'NaTType' object has no attribute 'normalize'

                # Step 1: Collect all minute data (generator can only be consumed once)
                if show_progress:
                    print("  Collecting minute data for aggregation...")
                all_minute_data = list(data_gen())

                if not all_minute_data:
                    raise RuntimeError("No minute data was collected. Check symbol validity and date range.")

                # Step 2: Write minute bars
                if show_progress:
                    print(f"  Writing {len(all_minute_data)} symbol(s) to minute bar writer...")
                minute_bar_writer.write(iter(all_minute_data), show_progress=show_progress)

                # Step 3: Aggregate minute data to daily and write to daily bar writer
                # This ensures the daily bar reader has valid data for Zipline's internal operations
                if show_progress:
                    print("  Aggregating minute data to daily bars...")

                def daily_data_gen():
                    """Generator that yields aggregated daily data from minute data."""
                    for sid, minute_df in all_minute_data:
                        try:
                            # Aggregate minute bars to daily
                            daily_df = aggregate_ohlcv(minute_df, 'daily')

                            if daily_df.empty:
                                print(f"  Warning: No daily data after aggregating minute data for SID {sid}")
                                continue

                            # Ensure UTC timezone and normalize to midnight
                            # This needs to happen BEFORE shifting, as shifting operates on dates
                            if daily_df.index.tz is None:
                                daily_df.index = daily_df.index.tz_localize('UTC')
                            elif str(daily_df.index.tz) != 'UTC':
                                daily_df.index = daily_df.index.tz_convert('UTC')
                            daily_df.index = daily_df.index.normalize() # Normalize to midnight UTC

                            # === FOREX SUNDAY CONSOLIDATION ===
                            if 'FOREX' in closure_calendar_name.upper():
                                daily_df = consolidate_forex_sunday_to_friday(daily_df, calendar_obj, show_progress, sid)
                                if daily_df.empty:
                                    continue

                            # === CALENDAR SESSION FILTERING ===
                            if 'FOREX' in closure_calendar_name.upper():
                                daily_df = filter_to_calendar_sessions(daily_df, calendar_obj, show_progress, sid)
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

            # Write empty adjustments (no splits/dividends for now)
            # Pass None instead of empty DataFrames to avoid column validation issues
            adjustment_writer.write(splits=None, dividends=None, mergers=None)
        
        return yahoo_ingest
    
    make_yahoo_ingest(symbols)
    add_registered_bundle(bundle_name)

    # Persist bundle metadata to registry file (include timeframe for reconstruction)
    register_bundle_metadata(
        bundle_name=bundle_name,
        symbols=symbols,
        calendar_name=calendar_name,
        start_date=start_date,
        end_date=end_date,
        data_frequency=data_frequency,
        timeframe=timeframe
    )


def auto_register_yahoo_bundle_if_exists():
    """Auto-register yahoo_equities_daily bundle if data was ingested."""
    import logging

    zipline_data_dir = Path.home() / '.zipline' / 'data' / 'yahoo_equities_daily'
    if not zipline_data_dir.exists():
        return

    try:
        from zipline.data.bundles import bundles
        from .utils import extract_symbols_from_bundle
        
        if 'yahoo_equities_daily' not in bundles:
            # First try to load from registry
            registry = load_bundle_registry()
            if 'yahoo_equities_daily' in registry:
                meta = registry['yahoo_equities_daily']
                # Validate end_date (may be corrupted from earlier bug)
                end_date = meta.get('end_date')
                if end_date and not is_valid_date_string(end_date):
                    end_date = None
                register_yahoo_bundle(
                    bundle_name='yahoo_equities_daily',
                    symbols=meta.get('symbols', ['SPY']),
                    calendar_name=meta.get('calendar_name', 'XNYS'),
                    start_date=meta.get('start_date'),
                    end_date=end_date,
                    data_frequency=meta.get('data_frequency', 'daily'),
                    timeframe=meta.get('timeframe', 'daily')
                )
            else:
                # Fallback to extracting symbols from database
                symbols = extract_symbols_from_bundle('yahoo_equities_daily')
                if symbols:
                    register_yahoo_bundle('yahoo_equities_daily', symbols, 'XNYS')
                else:
                    register_yahoo_bundle('yahoo_equities_daily', ['SPY'], 'XNYS')
    except ImportError:
        pass  # Zipline not installed
    except Exception as e:
        logging.getLogger(__name__).warning(f"Auto-registration failed: {e}")


# Backward compatibility aliases
_register_yahoo_bundle = register_yahoo_bundle
_auto_register_yahoo_bundle_if_exists = auto_register_yahoo_bundle_if_exists















