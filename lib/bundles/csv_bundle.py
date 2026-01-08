"""
CSV bundle registration for local data files.

Provides functions to register and ingest local CSV data bundles.
"""

import logging
import re
from pathlib import Path
from typing import List, Optional, Tuple

import pandas as pd
from zipline.utils.calendar_utils import get_calendar

from ..utils import get_project_root, aggregate_ohlcv
from ..validation import DataValidator, ValidationConfig
from ..data.filters import (
    filter_forex_presession_bars,
    consolidate_forex_sunday_to_friday,
    filter_to_calendar_sessions,
    filter_daily_to_calendar_sessions,
    apply_gap_filling,
)
from .timeframes import get_timeframe_info, get_minutes_per_day
from .registry import (
    unregister_bundle,
    register_bundle_metadata,
    add_registered_bundle,
)

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
    # Create a mapping from original to normalized names
    column_mapping = {}
    
    # Define patterns for each required column
    column_patterns = {
        'open': [r'^open$', r'^o$'],
        'high': [r'^high$', r'^h$'],
        'low': [r'^low$', r'^l$'],
        'close': [r'^close$', r'^c$', r'^adj[_\s]?close$', r'^adjusted[_\s]?close$'],
        'volume': [r'^volume$', r'^vol$', r'^v$'],
    }
    
    # Track which columns we've found
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
    
    # Rename columns
    df = df.rename(columns=column_mapping)
    
    # Keep only the required columns (drop any extras like 'Dividends', 'Stock Splits')
    df = df[['open', 'high', 'low', 'close', 'volume']]
    
    return df


def parse_csv_filename(filename: str, symbol: str, timeframe: str) -> Tuple[Optional[pd.Timestamp], Optional[pd.Timestamp]]:
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
    # Remove extension
    stem = Path(filename).stem
    
    # Pattern 1: SYMBOL_TIMEFRAME_YYYYMMDD-HHMMSS_YYYYMMDD-HHMMSS_suffix
    # Example: EURUSD_1h_20200102-050000_20250717-030000_ready
    pattern1 = re.compile(
        rf'^{re.escape(symbol)}_{re.escape(timeframe)}_'
        r'(\d{8})(?:-\d{6})?_'  # Start date with optional time
        r'(\d{8})(?:-\d{6})?'   # End date with optional time
        r'(?:_\w+)?$'           # Optional suffix like _ready
    )
    
    # Pattern 2: SYMBOL_TIMEFRAME_YYYY-MM-DD_YYYY-MM-DD
    # Example: EURUSD_1h_2020-01-02_2025-07-17
    pattern2 = re.compile(
        rf'^{re.escape(symbol)}_{re.escape(timeframe)}_'
        r'(\d{4}-\d{2}-\d{2})_'  # Start date
        r'(\d{4}-\d{2}-\d{2})'   # End date
        r'(?:_\w+)?$'            # Optional suffix
    )
    
    # Pattern 3: SYMBOL_TIMEFRAME_YYYYMMDD_YYYYMMDD
    # Example: EURUSD_1h_20200102_20250717
    pattern3 = re.compile(
        rf'^{re.escape(symbol)}_{re.escape(timeframe)}_'
        r'(\d{8})_'              # Start date
        r'(\d{8})'               # End date
        r'(?:_\w+)?$'            # Optional suffix
    )
    
    # Try each pattern
    for pattern in [pattern1, pattern2, pattern3]:
        match = pattern.match(stem)
        if match:
            start_str, end_str = match.groups()
            
            # Parse dates based on format
            try:
                if '-' in start_str:
                    # YYYY-MM-DD format
                    start_date = pd.Timestamp(start_str, tz='UTC')
                    end_date = pd.Timestamp(end_str, tz='UTC')
                else:
                    # YYYYMMDD format
                    start_date = pd.Timestamp(
                        f"{start_str[:4]}-{start_str[4:6]}-{start_str[6:8]}", 
                        tz='UTC'
                    )
                    end_date = pd.Timestamp(
                        f"{end_str[:4]}-{end_str[4:6]}-{end_str[6:8]}", 
                        tz='UTC'
                    )
                
                # Normalize start to beginning of day, end to end of day
                start_date = start_date.normalize()
                end_date = end_date.normalize() + pd.Timedelta(days=1, seconds=-1)
                
                return start_date, end_date
            except Exception as e:
                logger.warning(f"Failed to parse dates from filename {filename}: {e}")
                continue
    
    # No pattern matched - return None for both dates
    logger.info(f"Could not parse dates from filename {filename}. Using full file range.")
    return None, None


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
    Register a local CSV data bundle for ingestion.
    This function expects CSV files to be located in:
    data/processed/{timeframe}/{symbol}_{timeframe}_{start_date}-{end_date}_ready.csv
    
    Expected CSV columns: Date, Open, High, Low, Close, Volume
    """
    from zipline.data.bundles import register, bundles
    
    if bundle_name in bundles:
        if force:
            unregister_bundle(bundle_name)
        else:
            logger.info(f"Bundle {bundle_name} already registered. Use --force to re-ingest.")
            return

    # Capture closure variables for the ingest function
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
            """CSV bundle ingest function."""
            
            # Get calendar object inside ingest function (consistent with Yahoo pattern)
            calendar_obj = get_calendar(closure_calendar_name)
            
            # Use user-specified start/end dates from closure, converted to UTC
            start_date_utc = pd.Timestamp(closure_start_date, tz='UTC').normalize() if closure_start_date else None
            end_date_utc = pd.Timestamp(closure_end_date, tz='UTC').normalize() if closure_end_date else None

            if show_progress:
                print(f"Ingesting {closure_timeframe} data for {len(symbols_list)} symbols from local CSVs...")

            # Initialize data validator for CSV data quality checks
            # Map asset_class to asset_type for validation
            asset_type_map = {
                'equities': 'equity',
                'equity': 'equity',
                'forex': 'forex',
                'crypto': 'crypto',
                'cryptocurrencies': 'crypto'
            }
            asset_type = asset_type_map.get(closure_asset_class.lower(), None)
            config = ValidationConfig(
                timeframe=closure_timeframe,
                asset_type=asset_type,
                calendar_name=closure_calendar_name
            )
            data_validator = DataValidator(config=config)

            # Get Zipline data frequency from timeframe info
            tf_info = get_timeframe_info(closure_timeframe)
            data_frequency = tf_info['data_frequency']

            def data_gen():
                local_data_path = get_project_root() / 'data' / 'processed' / closure_timeframe
                if not local_data_path.is_dir():
                    raise FileNotFoundError(f"Local CSV data directory not found: {local_data_path}")

                successful_fetches = 0
                for sid, symbol in enumerate(symbols_list):
                    try:
                        # Use glob to find files matching the pattern
                        # e.g., EURUSD_1h_20200102-050000_20250717-030000_ready.csv
                        file_pattern = f"{symbol}_{closure_timeframe}_*.csv"
                        matching_files = list(local_data_path.glob(file_pattern))

                        if not matching_files:
                            print(f"Warning: No CSV file found for {symbol} with pattern '{file_pattern}' in {local_data_path}")
                            continue
                        
                        # Assuming only one matching file for now, or pick the first one
                        csv_file = matching_files[0] 
                        
                        # Parse dates from filename using flexible regex
                        file_start_date, file_end_date = parse_csv_filename(
                            csv_file.name, symbol, closure_timeframe
                        )

                        df = pd.read_csv(
                            csv_file,
                            parse_dates=[0],
                            index_col=0,
                        )
                        
                        if df.empty:
                            print(f"Warning: Empty data for {symbol} from {csv_file}.")
                            continue

                        # === COLUMN NORMALIZATION ===
                        # Normalize column names to lowercase standard format
                        try:
                            df = normalize_csv_columns(df)
                        except ValueError as col_err:
                            print(f"Error: {col_err}")
                            logger.error(f"Column normalization failed for {symbol}: {col_err}")
                            continue

                        # === TIMEZONE CONVERSION (BEFORE VALIDATION) ===
                        # Convert index to UTC DatetimeIndex before validation
                        # This handles timezone-aware strings in CSV files
                        try:
                            df.index = pd.to_datetime(df.index, utc=True)
                        except Exception as tz_err:
                            print(f"  Error: Failed to convert index to UTC for {symbol}: {tz_err}")
                            logger.error(f"Timezone conversion failed for {symbol}: {tz_err}")
                            continue

                        # === DATA VALIDATION HOOK ===
                        # Validate CSV data quality before ingestion
                        if show_progress:
                            print(f"  Validating data for {symbol}...")
                        
                        validation_result = data_validator.validate(
                            df,
                            asset_name=symbol,
                            asset_type=asset_type,
                            calendar_name=closure_calendar_name
                        )
                        
                        if not validation_result.passed:
                            # Log validation errors
                            error_checks = validation_result.error_checks[:5]
                            error_summary = "; ".join([
                                f"{check.details.get('field', check.name)}: {check.message}" 
                                for check in error_checks
                            ])
                            if len(validation_result.error_checks) > 5:
                                error_summary += f" ... and {len(validation_result.error_checks) - 5} more errors"
                            
                            print(f"  Error: Data validation failed for {symbol}: {error_summary}")
                            logger.error(f"CSV data validation failed for {symbol}: {error_summary}")
                            print(f"  Error: Validation failed for {symbol}. Skipping symbol.")
                            continue
                        else:
                            if show_progress:
                                print(f"  ✓ Data validation passed for {symbol}")
                        
                        # Log any warnings even if validation passed
                        if validation_result.warning_checks:
                            warning_summary = "; ".join([
                                check.message for check in validation_result.warning_checks[:3]
                            ])
                            if len(validation_result.warning_checks) > 3:
                                warning_summary += f" ... and {len(validation_result.warning_checks) - 3} more warnings"
                            logger.info(f"Data validation warnings for {symbol}: {warning_summary}")
                        
                        # Determine the effective start and end dates for filtering:
                        # If user provided start_date/end_date, use those. Otherwise, use dates from filename.
                        effective_start_date = pd.Timestamp(closure_start_date, tz='UTC') if closure_start_date else file_start_date
                        effective_end_date = pd.Timestamp(closure_end_date, tz='UTC') if closure_end_date else file_end_date

                        # Apply effective date filtering
                        if effective_start_date is not None:
                            df = df[df.index >= effective_start_date]
                        if effective_end_date is not None:
                            df = df[df.index <= effective_end_date]

                        # === CALENDAR BOUNDS FILTERING ===
                        # Align data to calendar first session
                        first_calendar_session = calendar_obj.first_session
                        if first_calendar_session.tz is None:
                            first_calendar_session = first_calendar_session.tz_localize('UTC')
                        df = df[df.index >= first_calendar_session]

                        # === FOREX PRE-SESSION FILTERING (for intraday data) ===
                        if data_frequency == 'minute' and 'FOREX' in closure_calendar_name.upper():
                            df = filter_forex_presession_bars(df, calendar_obj, show_progress, symbol)

                        # === CALENDAR SESSION FILTERING (for daily data) ===
                        if data_frequency == 'daily' and len(df) > 0:
                            df = filter_daily_to_calendar_sessions(df, calendar_obj, show_progress, symbol)

                        # === GAP-FILLING FOR FOREX AND CRYPTO (daily data only) ===
                        if data_frequency == 'daily':
                            if 'FOREX' in closure_calendar_name.upper() or 'CRYPTO' in closure_calendar_name.upper():
                                df = apply_gap_filling(df, calendar_obj, closure_calendar_name, show_progress, symbol)

                        # Prepare DataFrame with required columns
                        bars_df = pd.DataFrame({
                            'open': df['open'],
                            'high': df['high'],
                            'low': df['low'],
                            'close': df['close'],
                            'volume': df['volume'],
                        }, index=df.index)

                        if bars_df.empty:
                            print(f"Warning: No data for {symbol} after date filtering.")
                            continue

                        successful_fetches += 1
                        yield sid, bars_df

                    except Exception as e:
                        print(f"Error processing CSV data for {symbol}: {e}")
                        logger.exception(f"Error processing CSV data for {symbol}")
                        continue
                
                if successful_fetches == 0:
                    raise RuntimeError(
                        f"No CSV data was successfully loaded for any symbol. "
                        f"Symbols attempted: {symbols_list}. "
                        f"Check that CSV files exist in data/processed/{closure_timeframe}/ and are correctly formatted."
                    )

            if data_frequency == 'minute':
                # For intraday bundles, we need to write BOTH minute and daily bars.
                # Step 1: Collect all minute data (generator can only be consumed once)
                if show_progress:
                    print("  Collecting minute data for aggregation...")
                all_minute_data = list(data_gen())

                if not all_minute_data:
                    raise RuntimeError("No minute data was collected. Check symbol validity and date range.")

                # Step 2: Build asset metadata from collected data
                # This ensures start/end dates are accurate (not NaT)
                asset_data_list = []
                for sid, minute_df in all_minute_data:
                    symbol = symbols_list[sid]
                    first_trade = minute_df.index.min().normalize()
                    last_trade = minute_df.index.max().normalize()
                    asset_data_list.append({
                        'sid': sid,
                        'symbol': symbol,
                        'asset_name': symbol,
                        'start_date': first_trade,
                        'end_date': last_trade,
                        'exchange': 'CSV',
                        'country_code': 'XX',
                    })
                assets_df = pd.DataFrame(asset_data_list).set_index('sid')
                asset_db_writer.write(equities=assets_df)

                # Step 3: Write minute bars
                if show_progress:
                    print(f"  Writing {len(all_minute_data)} symbol(s) to minute bar writer...")
                minute_bar_writer.write(iter(all_minute_data), show_progress=show_progress)

                # Step 4: Aggregate minute data to daily and write to daily bar writer
                if show_progress:
                    print("  Aggregating minute data to daily bars...")

                def daily_data_gen():
                    """Generator that yields aggregated daily data from minute data."""
                    for sid, minute_df in all_minute_data:
                        try:
                            daily_df = aggregate_ohlcv(minute_df, 'daily')
                            if daily_df.empty:
                                print(f"  Warning: No daily data after aggregating minute data for SID {sid}")
                                continue
                            # Ensure UTC timezone and normalize to midnight
                            if daily_df.index.tz is not None:
                                daily_df.index = daily_df.index.tz_convert('UTC').normalize()
                            else:
                                daily_df.index = daily_df.index.tz_localize('UTC').normalize()

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
                # Daily data frequency
                # Step 1: Collect all daily data
                if show_progress:
                    print("  Collecting daily data...")
                all_daily_data = list(data_gen())

                if not all_daily_data:
                    raise RuntimeError("No daily data was collected. Check symbol validity and date range.")

                # Step 2: Build asset metadata from collected data
                asset_data_list = []
                for sid, daily_df in all_daily_data:
                    symbol = symbols_list[sid]
                    first_trade = daily_df.index.min().normalize()
                    last_trade = daily_df.index.max().normalize()
                    asset_data_list.append({
                        'sid': sid,
                        'symbol': symbol,
                        'asset_name': symbol,
                        'start_date': first_trade,
                        'end_date': last_trade,
                        'exchange': 'CSV',
                        'country_code': 'XX',
                    })
                assets_df = pd.DataFrame(asset_data_list).set_index('sid')
                asset_db_writer.write(equities=assets_df)

                # Step 3: Write daily bars
                daily_bar_writer.write(iter(all_daily_data), show_progress=show_progress)

            adjustment_writer.write(splits=None, dividends=None, mergers=None)
        
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


# Backward compatibility aliases
_register_csv_bundle = register_csv_bundle
_normalize_csv_columns = normalize_csv_columns
_parse_csv_filename = parse_csv_filename

