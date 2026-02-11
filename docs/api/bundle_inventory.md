# Zipline-Reloaded Bundle Management Inventory

> Comprehensive catalog of bundle management capabilities, APIs, and usage patterns for Zipline-Reloaded v3.0+

**Source:** [stefan-jansen/zipline-reloaded](https://github.com/stefan-jansen/zipline-reloaded)  
**Version:** Zipline-Reloaded v3.0+  
**Last Updated:** 2026-01-27

---

## Table of Contents

1. [Core Bundle System](#core-bundle-system)
2. [Bundle Registration](#bundle-registration)
3. [Bundle Ingestion](#bundle-ingestion)
4. [Bundle Loading](#bundle-loading)
5. [Bundle Management](#bundle-management)
6. [Built-in Bundle Types](#built-in-bundle-types)
7. [Data Writers](#data-writers)
8. [Data Readers](#data-readers)
9. [Bundle Data Structure](#bundle-data-structure)
10. [Utility Functions](#utility-functions)
11. [CSV Directory Bundles](#csv-directory-bundles)
12. [Usage Patterns](#usage-patterns)
13. [Best Practices](#best-practices)
14. [Error Handling](#error-handling)

---

## Core Bundle System

### Bundle Concept

Data bundles are Zipline's mechanism for managing market data. A bundle defines how to fetch, process, and store data for backtesting. Bundles contain:

- **Asset metadata** - Symbol information, exchange, trading dates
- **Price data** - Daily and/or minute OHLCV bars
- **Adjustments** - Corporate actions (splits, dividends, mergers)
- **Calendar alignment** - Trading calendar for session alignment

### Bundle Lifecycle

```
┌─────────────────────────────────────────────────────────┐
│  1. REGISTER                                            │
│     Define bundle name and ingest function              │
├─────────────────────────────────────────────────────────┤
│  2. INGEST                                              │
│     Download/process data, write to disk                │
├─────────────────────────────────────────────────────────┤
│  3. LOAD                                                │
│     Read bundle data for backtesting                     │
└─────────────────────────────────────────────────────────┘
```

---

## Bundle Registration

### `register()`

Register a data bundle ingest function.

```python
from zipline.data.bundles import register

register(
    name,
    f,
    calendar_name='NYSE',
    start_session=None,
    end_session=None,
    minutes_per_day=390,
    create_writers=True
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | str | required | Bundle identifier (unique name) |
| `f` | callable | required | Ingest function (see signature below) |
| `calendar_name` | str | `'NYSE'` | Trading calendar name for alignment |
| `start_session` | pd.Timestamp | None | First session to ingest (uses calendar first_session if None) |
| `end_session` | pd.Timestamp | None | Last session to ingest (uses calendar last_session if None) |
| `minutes_per_day` | int | 390 | Trading minutes per day (for minute data) |
| `create_writers` | bool | True | Auto-create data writers (set False for optimization) |

**Ingest Function Signature:**

```python
def my_ingest(
    environ,              # mapping: Environment variables
    asset_db_writer,      # AssetDBWriter: Write asset metadata
    minute_bar_writer,    # BcolzMinuteBarWriter: Write minute bars
    daily_bar_writer,     # BcolzDailyBarWriter: Write daily bars
    adjustment_writer,    # SQLiteAdjustmentWriter: Write adjustments
    calendar,             # TradingCalendar: Trading calendar object
    start_session,        # pd.Timestamp: First session to ingest
    end_session,          # pd.Timestamp: Last session to ingest
    cache,                # DataFrameCache: Temporary dataframe storage
    show_progress,        # bool: Show progress indicators
    output_dir            # str: Output directory path
):
    # Fetch and write data
    pass
```

**Decorator Usage:**

```python
from zipline.data.bundles import register

@register('my-bundle', calendar_name='NYSE')
def my_bundle_ingest(
    environ, asset_db_writer, minute_bar_writer,
    daily_bar_writer, adjustment_writer, calendar,
    start_session, end_session, cache, show_progress, output_dir
):
    # Write asset metadata
    equities_df = pd.DataFrame({
        'symbol': ['AAPL', 'MSFT'],
        'asset_name': ['Apple Inc.', 'Microsoft Corp.'],
        'start_date': [start_session] * 2,
        'end_date': [end_session] * 2,
        'exchange': ['NYSE'] * 2,
        'country_code': ['US'] * 2,
    })
    asset_db_writer.write(equities=equities_df)
    
    # Write daily bars
    def data_gen():
        for sid, symbol in enumerate(['AAPL', 'MSFT']):
            # Fetch data for symbol
            bars_df = fetch_data(symbol, start_session, end_session)
            yield sid, bars_df
    
    daily_bar_writer.write(data_gen(), show_progress=show_progress)
    
    # Write adjustments (splits, dividends)
    adjustment_writer.write(splits=splits_df, dividends=dividends_df)
```

**Returns:** The ingest function (allows decorator chaining)

**Notes:**
- Bundle names must be unique
- Overwriting a bundle triggers a warning
- Calendar is resolved lazily (not at registration time)
- `create_writers=False` is an optimization for bundles that don't need writers

---

## Bundle Ingestion

### `ingest()`

Run the ingest function for a bundle to download and store data.

```python
from zipline.data.bundles import ingest

ingest(
    name,
    environ=os.environ,
    timestamp=None,
    assets_versions=(),
    show_progress=False
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | str | required | Bundle name to ingest |
| `environ` | mapping | `os.environ` | Environment variables |
| `timestamp` | datetime | None | Timestamp for ingestion (defaults to current time) |
| `assets_versions` | Iterable[int] | `()` | Asset DB versions to downgrade to |
| `show_progress` | bool | False | Display progress indicators |

**Returns:** None (data written to disk)

**Raises:**
- `UnknownBundle`: If bundle not registered

**CLI Usage:**

```bash
# Ingest default bundle
zipline ingest

# Ingest specific bundle
zipline ingest -b my-bundle

# Ingest with timestamp
zipline ingest -b my-bundle --date 2024-01-15
```

**Python Usage:**

```python
from zipline.data.bundles import ingest

# Ingest bundle
ingest('my-bundle', show_progress=True)

# Ingest with custom timestamp
from datetime import datetime
ingest('my-bundle', timestamp=datetime(2024, 1, 15))
```

**Notes:**
- Creates timestamped directory for each ingestion
- Multiple ingestions of same bundle create separate directories
- Uses most recent ingestion when loading bundle
- Progress indicators show data fetching/writing progress

---

## Bundle Loading

### `load()`

Load a previously ingested bundle into memory.

```python
from zipline.data.bundles import load

bundle_data = load(
    name,
    environ=os.environ,
    timestamp=None
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | str | required | Bundle name to load |
| `environ` | mapping | `os.environ` | Environment variables |
| `timestamp` | datetime | None | Timestamp of data to load (defaults to most recent) |

**Returns:** `BundleData` namedtuple with:

| Attribute | Type | Description |
|-----------|------|-------------|
| `asset_finder` | AssetFinder | Asset metadata and lookup |
| `equity_minute_bar_reader` | BcolzMinuteBarReader | Minute OHLCV data reader |
| `equity_daily_bar_reader` | BcolzDailyBarReader | Daily OHLCV data reader |
| `adjustment_reader` | SQLiteAdjustmentReader | Corporate actions reader |

**Example:**

```python
from zipline.data.bundles import load

# Load most recent bundle
bundle_data = load('my-bundle')

# Access components
finder = bundle_data.asset_finder
daily_reader = bundle_data.equity_daily_bar_reader
minute_reader = bundle_data.equity_minute_bar_reader
adjustment_reader = bundle_data.adjustment_reader

# Use in backtest
from zipline import run_algorithm

results = run_algorithm(
    initialize=initialize,
    handle_data=handle_data,
    bundle='my-bundle',  # Or use bundle_data directly
    start=pd.Timestamp('2020-01-01', tz='utc'),
    end=pd.Timestamp('2024-01-01', tz='utc'),
)
```

**Context Manager Usage:**

```python
from zipline.data.bundles import load

# BundleData supports context manager for cleanup
with load('my-bundle') as bundle_data:
    finder = bundle_data.asset_finder
    # Use bundle data
    # Resources automatically closed on exit
```

**Raises:**
- `UnknownBundle`: If bundle not registered
- `ValueError`: If no data found for bundle on or before timestamp

---

## Bundle Management

### `bundles`

Immutable mapping of registered bundles.

```python
from zipline.data.bundles import bundles

# List all registered bundles
print(list(bundles.keys()))
# ['quandl', 'my-bundle', 'csvdir', ...]

# Check if bundle exists
if 'my-bundle' in bundles:
    print("Bundle registered")

# Access bundle metadata
bundle = bundles['my-bundle']
print(bundle.calendar_name)  # 'NYSE'
print(bundle.minutes_per_day)  # 390
```

**Type:** `mappingproxy` (immutable dict-like)

**Bundle Metadata:**

Each bundle in `bundles` is a `RegisteredBundle` namedtuple:

| Attribute | Type | Description |
|-----------|------|-------------|
| `calendar_name` | str | Trading calendar name |
| `start_session` | pd.Timestamp | First session (may be None) |
| `end_session` | pd.Timestamp | Last session (may be None) |
| `minutes_per_day` | int | Trading minutes per day |
| `ingest` | callable | Ingest function |
| `create_writers` | bool | Whether to create writers |

**Notes:**
- Updated only via `register()` and `unregister()`
- Immutable - cannot modify directly
- Use `register()` to add/update bundles
- Use `unregister()` to remove bundles

---

### `unregister()`

Remove a bundle registration.

```python
from zipline.data.bundles import unregister

unregister(name)
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | str | Bundle name to unregister |

**Returns:** None

**Raises:**
- `UnknownBundle`: If bundle not registered

**Example:**

```python
from zipline.data.bundles import unregister

# Remove bundle registration
unregister('my-bundle')

# Verify removal
from zipline.data.bundles import bundles
assert 'my-bundle' not in bundles
```

**Notes:**
- Only removes registration, not ingested data
- Use `clean()` to remove ingested data
- Bundle data remains on disk after unregistering

---

### `clean()`

Clean up data created with `ingest()`.

```python
from zipline.data.bundles import clean

cleaned = clean(
    name,
    before=None,
    after=None,
    keep_last=None,
    environ=os.environ
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | str | required | Bundle name to clean |
| `before` | datetime | None | Remove data ingested before this date |
| `after` | datetime | None | Remove data ingested after this date |
| `keep_last` | int | None | Keep only last N ingestions |
| `environ` | mapping | `os.environ` | Environment variables |

**Returns:** `set[str]` - Paths of removed ingestion directories

**Raises:**
- `UnknownBundle`: If bundle not registered
- `BadClean`: If invalid argument combination

**Examples:**

```python
from zipline.data.bundles import clean
from datetime import datetime

# Remove all ingestions before a date
cleaned = clean('my-bundle', before=datetime(2023, 1, 1))

# Remove all ingestions after a date
cleaned = clean('my-bundle', after=datetime(2024, 1, 1))

# Keep only last 3 ingestions
cleaned = clean('my-bundle', keep_last=3)

# Remove all ingestions (keep_last=0)
cleaned = clean('my-bundle', keep_last=0)
```

**Notes:**
- `before` and `after` are mutually exclusive with `keep_last`
- Must provide exactly one of: `before`, `after`, or `keep_last`
- Removes entire ingestion directories (all data for that timestamp)
- Use with caution - data deletion is permanent

---

## Built-in Bundle Types

### Quandl Bundle

Free end-of-day US equity data from Quandl/Nasdaq.

**Registration:** Automatically registered as `'quandl'`

**Requirements:**
- `QUANDL_API_KEY` environment variable

**Usage:**

```bash
# Set API key
export QUANDL_API_KEY=your_key_here

# Ingest
zipline ingest -b quandl
```

```python
from zipline.data.bundles import ingest

# Ingest Quandl bundle
ingest('quandl', show_progress=True)
```

**Data:**
- Daily OHLCV bars for US equities
- NYSE calendar alignment
- Automatic asset metadata

---

### CSV Directory Bundle

Bundle from local CSV files organized in directory structure.

**Registration:** Automatically registered as `'csvdir'` (or use `csvdir_equities()`)

**Directory Structure:**

```
csvdir/
├── daily/
│   ├── AAPL.csv
│   ├── MSFT.csv
│   └── GOOGL.csv
└── minute/
    ├── AAPL.csv
    ├── MSFT.csv
    └── GOOGL.csv
```

**CSV Format:**

```csv
Date,Open,High,Low,Close,Volume
2020-01-01,150.0,155.0,149.0,153.0,1000000
2020-01-02,153.0,158.0,152.0,157.0,1200000
```

**Optional Columns:**
- `split` - Split ratio (1.0 = no split)
- `dividend` - Dividend amount

**Usage:**

```python
from zipline.data.bundles import register
from zipline.data.bundles.csvdir import csvdir_equities

# Register CSV bundle
register(
    'my-csv-bundle',
    csvdir_equities(
        tframes=['daily', 'minute'],
        csvdir='/path/to/csvdir'
    ),
    calendar_name='NYSE'
)

# Ingest
from zipline.data.bundles import ingest
ingest('my-csv-bundle', show_progress=True)
```

**Environment Variable:**

```bash
# Set CSVDIR environment variable
export CSVDIR=/path/to/csvdir

# Use default csvdir bundle
zipline ingest -b csvdir
```

**Notes:**
- Automatically detects `daily` and `minute` subdirectories
- CSV files must have Date as first column (index)
- Supports compressed CSV files (.csv.gz, .csv.bz2)
- Calendar alias `'CSVDIR'` resolves to `'NYSE'`

---

## Data Writers

### AssetDBWriter

Write asset metadata to SQLite database.

```python
from zipline.assets import AssetDBWriter

# In ingest function
asset_db_writer.write(equities=equities_df)
```

**Equities DataFrame Columns:**

| Column | Type | Description |
|--------|------|-------------|
| `symbol` | str | Asset symbol |
| `asset_name` | str | Asset name |
| `start_date` | pd.Timestamp | First trading date |
| `end_date` | pd.Timestamp | Last trading date |
| `auto_close_date` | pd.Timestamp | Day after last trade |
| `exchange` | str | Exchange name |
| `country_code` | str | ISO country code |

**Example:**

```python
equities_df = pd.DataFrame({
    'symbol': ['AAPL', 'MSFT'],
    'asset_name': ['Apple Inc.', 'Microsoft Corp.'],
    'start_date': [pd.Timestamp('2020-01-01', tz='utc')] * 2,
    'end_date': [pd.Timestamp('2024-01-01', tz='utc')] * 2,
    'auto_close_date': [pd.Timestamp('2024-01-02', tz='utc')] * 2,
    'exchange': ['NYSE'] * 2,
    'country_code': ['US'] * 2,
}, index=pd.Index(range(2), name='sid'))

asset_db_writer.write(equities=equities_df)
```

---

### BcolzDailyBarWriter

Write daily OHLCV bars to bcolz format.

```python
from zipline.data.bcolz_daily_bars import BcolzDailyBarWriter

# In ingest function
daily_bar_writer.write(data_generator(), show_progress=show_progress)
```

**Data Generator:**

```python
def data_generator():
    """
    Yield (sid, DataFrame) tuples.
    
    DataFrame must have:
    - Index: pd.DatetimeIndex (UTC, normalized)
    - Columns: 'open', 'high', 'low', 'close', 'volume'
    """
    for sid, symbol in enumerate(symbols):
        # Fetch data
        bars_df = fetch_daily_data(symbol, start_session, end_session)
        
        # Ensure UTC, normalized index
        if bars_df.index.tz is None:
            bars_df.index = bars_df.index.tz_localize('UTC')
        bars_df.index = bars_df.index.normalize()
        
        yield sid, bars_df
```

**DataFrame Requirements:**

- **Index:** `pd.DatetimeIndex` with UTC timezone, normalized (midnight)
- **Columns:** `['open', 'high', 'low', 'close', 'volume']`
- **Types:** All numeric (float64 for prices, int64 for volume)
- **Alignment:** Dates must align with trading calendar sessions

---

### BcolzMinuteBarWriter

Write minute OHLCV bars to bcolz format.

```python
from zipline.data.bcolz_minute_bars import BcolzMinuteBarWriter

# In ingest function
minute_bar_writer.write(data_generator(), show_progress=show_progress)
```

**Data Generator:**

```python
def minute_data_generator():
    """
    Yield (sid, DataFrame) tuples.
    
    DataFrame must have:
    - Index: pd.DatetimeIndex (UTC, not normalized)
    - Columns: 'open', 'high', 'low', 'close', 'volume'
    """
    for sid, symbol in enumerate(symbols):
        # Fetch minute data
        bars_df = fetch_minute_data(symbol, start_session, end_session)
        
        # Ensure UTC timezone (keep time component)
        if bars_df.index.tz is None:
            bars_df.index = bars_df.index.tz_localize('UTC')
        elif str(bars_df.index.tz) != 'UTC':
            bars_df.index = bars_df.index.tz_convert('UTC')
        
        yield sid, bars_df
```

**DataFrame Requirements:**

- **Index:** `pd.DatetimeIndex` with UTC timezone, **not normalized** (keep time)
- **Columns:** `['open', 'high', 'low', 'close', 'volume']`
- **Types:** All numeric
- **Alignment:** Times must align with trading calendar minute sessions

---

### SQLiteAdjustmentWriter

Write corporate actions (splits, dividends, mergers) to SQLite database.

```python
from zipline.data.adjustments import SQLiteAdjustmentWriter

# In ingest function
adjustment_writer.write(
    splits=splits_df,
    dividends=dividends_df,
    mergers=mergers_df  # Optional
)
```

**Splits DataFrame:**

| Column | Type | Description |
|--------|------|-------------|
| `sid` | int | Security ID |
| `ratio` | float | Split ratio (e.g., 2.0 for 2-for-1 split) |
| `effective_date` | pd.Timestamp | Split effective date |

**Dividends DataFrame:**

| Column | Type | Description |
|--------|------|-------------|
| `sid` | int | Security ID |
| `amount` | float | Dividend amount per share |
| `ex_date` | pd.Timestamp | Ex-dividend date |
| `record_date` | pd.Timestamp | Record date (optional) |
| `declared_date` | pd.Timestamp | Declared date (optional) |
| `pay_date` | pd.Timestamp | Pay date (optional) |

**Example:**

```python
# Splits
splits_df = pd.DataFrame({
    'sid': [0],
    'ratio': [2.0],
    'effective_date': [pd.Timestamp('2020-06-09', tz='utc')]
})

# Dividends
dividends_df = pd.DataFrame({
    'sid': [0],
    'amount': [0.82],
    'ex_date': [pd.Timestamp('2020-05-08', tz='utc')],
    'record_date': [pd.NaT],
    'declared_date': [pd.NaT],
    'pay_date': [pd.NaT]
})

adjustment_writer.write(splits=splits_df, dividends=dividends_df)
```

---

## Data Readers

### AssetFinder

Read asset metadata and perform asset lookups.

```python
from zipline.data.bundles import load

bundle_data = load('my-bundle')
finder = bundle_data.asset_finder

# Lookup asset by symbol
asset = finder.lookup_symbol('AAPL', as_of_date=pd.Timestamp('2020-01-01'))

# Get all assets
all_assets = finder.retrieve_all(finder.sids)

# Get asset metadata
metadata = finder.retrieve_asset(0)  # By SID
```

**Common Methods:**

- `lookup_symbol(symbol, as_of_date)` - Find asset by symbol
- `retrieve_asset(sid)` - Get asset by SID
- `retrieve_all(sids)` - Get multiple assets
- `lookup_generic(sid, as_of_date)` - Generic lookup

---

### BcolzDailyBarReader

Read daily OHLCV bars.

```python
from zipline.data.bundles import load

bundle_data = load('my-bundle')
daily_reader = bundle_data.equity_daily_bar_reader

# Get bar for asset and date
bar = daily_reader.get_value(0, pd.Timestamp('2020-01-01', tz='utc'), 'close')

# Load bars for date range
bars = daily_reader.load_raw_arrays(
    ['close', 'volume'],
    pd.Timestamp('2020-01-01', tz='utc'),
    pd.Timestamp('2020-12-31', tz='utc'),
    [0]  # SIDs
)
```

**Common Methods:**

- `get_value(sid, dt, field)` - Get single value
- `load_raw_arrays(fields, start_dt, end_dt, sids)` - Load arrays
- `get_last_traded_dt(sid, dt)` - Get last traded date

---

### BcolzMinuteBarReader

Read minute OHLCV bars.

```python
from zipline.data.bundles import load

bundle_data = load('my-bundle')
minute_reader = bundle_data.equity_minute_bar_reader

# Get bar for asset and minute
bar = minute_reader.get_value(
    0,
    pd.Timestamp('2020-01-01 09:30:00', tz='utc'),
    'close'
)

# Load bars for minute range
bars = minute_reader.load_raw_arrays(
    ['close', 'volume'],
    pd.Timestamp('2020-01-01 09:30:00', tz='utc'),
    pd.Timestamp('2020-01-01 16:00:00', tz='utc'),
    [0]  # SIDs
)
```

**Common Methods:**

- `get_value(sid, dt, field)` - Get single value
- `load_raw_arrays(fields, start_dt, end_dt, sids)` - Load arrays
- `get_last_traded_dt(sid, dt)` - Get last traded minute

---

### SQLiteAdjustmentReader

Read corporate actions (splits, dividends).

```python
from zipline.data.bundles import load

bundle_data = load('my-bundle')
adjustment_reader = bundle_data.adjustment_reader

# Get adjustments for date range
adjustments = adjustment_reader.load_adjustments(
    ['splits', 'dividends'],
    pd.Timestamp('2020-01-01', tz='utc'),
    pd.Timestamp('2020-12-31', tz='utc'),
    [0]  # SIDs
)
```

**Common Methods:**

- `load_adjustments(adjustment_types, start_dt, end_dt, sids)` - Load adjustments
- `get_adjustments_for_sid(sid, adjustment_type, start_dt, end_dt)` - Get for single asset

---

## Bundle Data Structure

### BundleData

Container for all bundle data readers.

```python
from zipline.data.bundles import load

bundle_data = load('my-bundle')

# Attributes
bundle_data.asset_finder              # AssetFinder
bundle_data.equity_minute_bar_reader  # BcolzMinuteBarReader
bundle_data.equity_daily_bar_reader   # BcolzDailyBarReader
bundle_data.adjustment_reader         # SQLiteAdjustmentReader
```

**Context Manager:**

```python
# Automatic resource cleanup
with load('my-bundle') as bundle_data:
    finder = bundle_data.asset_finder
    # Use bundle data
    # Resources closed on exit
```

**Resource Cleanup:**

```python
# Manual cleanup
bundle_data = load('my-bundle')
try:
    # Use bundle data
    pass
finally:
    bundle_data.close()  # Close all resources
```

---

## Utility Functions

### `ingestions_for_bundle()`

Get list of ingestion timestamps for a bundle.

```python
from zipline.data.bundles import ingestions_for_bundle

timestamps = ingestions_for_bundle('my-bundle', environ=os.environ)
# [Timestamp('2024-01-15 10:30:00'), Timestamp('2024-01-14 09:00:00'), ...]
```

**Returns:** `list[pd.Timestamp]` - Sorted list of ingestion timestamps (most recent first)

---

### `to_bundle_ingest_dirname()`

Convert timestamp to bundle ingestion directory name.

```python
from zipline.data.bundles import to_bundle_ingest_dirname
import pandas as pd

ts = pd.Timestamp('2024-01-15 10:30:00')
dirname = to_bundle_ingest_dirname(ts)
# '2024-01-15T10;30;00'
```

**Returns:** `str` - Directory name (ISO format with colons replaced by semicolons)

---

### `from_bundle_ingest_dirname()`

Convert bundle ingestion directory name to timestamp.

```python
from zipline.data.bundles import from_bundle_ingest_dirname

dirname = '2024-01-15T10;30;00'
ts = from_bundle_ingest_dirname(dirname)
# Timestamp('2024-01-15 10:30:00')
```

**Returns:** `pd.Timestamp` - Timestamp object

---

## CSV Directory Bundles

### `csvdir_equities()`

Generate ingest function for CSV directory bundle.

```python
from zipline.data.bundles import register
from zipline.data.bundles.csvdir import csvdir_equities

register(
    'my-csv-bundle',
    csvdir_equities(
        tframes=['daily', 'minute'],
        csvdir='/path/to/csvdir'
    ),
    calendar_name='NYSE'
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `tframes` | tuple | None | Timeframes to ingest (`'daily'`, `'minute'`) |
| `csvdir` | str | None | Path to CSV directory (or `CSVDIR` env var) |

**Directory Structure:**

```
csvdir/
├── daily/
│   ├── AAPL.csv
│   ├── MSFT.csv
│   └── GOOGL.csv
└── minute/
    ├── AAPL.csv
    ├── MSFT.csv
    └── GOOGL.csv
```

**CSV Format:**

```csv
Date,Open,High,Low,Close,Volume
2020-01-01,150.0,155.0,149.0,153.0,1000000
2020-01-02,153.0,158.0,152.0,157.0,1200000
```

**Optional Columns:**

- `split` - Split ratio (1.0 = no split, 2.0 = 2-for-1)
- `dividend` - Dividend amount per share

**Notes:**
- Automatically detects `daily` and `minute` subdirectories if `tframes=None`
- Supports compressed CSV files (.csv.gz, .csv.bz2)
- Date column must be first column (index)
- Calendar alias `'CSVDIR'` resolves to `'NYSE'`

---

## Usage Patterns

### Basic Bundle Registration and Ingestion

```python
from zipline.data.bundles import register, ingest
import pandas as pd

# Define ingest function
def my_ingest(environ, asset_db_writer, minute_bar_writer,
              daily_bar_writer, adjustment_writer, calendar,
              start_session, end_session, cache, show_progress, output_dir):
    # Write asset metadata
    equities_df = pd.DataFrame({
        'symbol': ['AAPL'],
        'asset_name': ['Apple Inc.'],
        'start_date': [start_session],
        'end_date': [end_session],
        'auto_close_date': [end_session + pd.Timedelta(days=1)],
        'exchange': ['NYSE'],
        'country_code': ['US'],
    }, index=pd.Index([0], name='sid'))
    asset_db_writer.write(equities=equities_df)
    
    # Write daily bars
    def data_gen():
        # Fetch and yield (sid, DataFrame) tuples
        pass
    
    daily_bar_writer.write(data_gen(), show_progress=show_progress)
    
    # Write adjustments
    adjustment_writer.write(splits=None, dividends=None)

# Register bundle
register('my-bundle', my_ingest, calendar_name='NYSE')

# Ingest bundle
ingest('my-bundle', show_progress=True)
```

---

### Using Decorator Pattern

```python
from zipline.data.bundles import register
import pandas as pd

@register('my-bundle', calendar_name='NYSE')
def my_ingest(environ, asset_db_writer, minute_bar_writer,
              daily_bar_writer, adjustment_writer, calendar,
              start_session, end_session, cache, show_progress, output_dir):
    # Ingest logic
    pass
```

---

### Loading and Using Bundle in Backtest

```python
from zipline.data.bundles import load
from zipline import run_algorithm
import pandas as pd

# Load bundle
bundle_data = load('my-bundle')

# Use in backtest
def initialize(context):
    context.asset = bundle_data.asset_finder.lookup_symbol(
        'AAPL',
        as_of_date=pd.Timestamp('2020-01-01', tz='utc')
    )

def handle_data(context, data):
    price = data.current(context.asset, 'price')
    # Trading logic

results = run_algorithm(
    initialize=initialize,
    handle_data=handle_data,
    bundle='my-bundle',  # Or use bundle_data
    start=pd.Timestamp('2020-01-01', tz='utc'),
    end=pd.Timestamp('2024-01-01', tz='utc'),
)
```

---

### Multiple Bundle Ingestion Management

```python
from zipline.data.bundles import ingest, ingestions_for_bundle, clean
from datetime import datetime

# Ingest bundle multiple times
ingest('my-bundle', show_progress=True)
# ... later ...
ingest('my-bundle', show_progress=True)

# List all ingestions
ingestions = ingestions_for_bundle('my-bundle')
print(f"Total ingestions: {len(ingestions)}")
print(f"Most recent: {ingestions[0]}")

# Clean old ingestions (keep last 3)
cleaned = clean('my-bundle', keep_last=3)
print(f"Removed {len(cleaned)} old ingestions")
```

---

### CSV Bundle Registration in Extension

```python
# In ~/.zipline/extension.py
from zipline.data.bundles import register
from zipline.data.bundles.csvdir import csvdir_equities
import pandas as pd

# Register CSV bundle
register(
    'eurusd_1h',
    csvdir_equities(
        tframes=['minute'],  # Or ['daily', 'minute']
        csvdir='/path/to/data/csvdir/1h'
    ),
    calendar_name='FOREX',
    start_session=pd.Timestamp('2020-01-01', tz='utc'),
    end_session=pd.Timestamp('2025-12-31', tz='utc')
)
```

---

## Best Practices

### 1. Bundle Naming

- Use descriptive names: `yahoo_equities_daily`, `csv_forex_1h`
- Include source and asset class: `{source}_{asset}_{timeframe}`
- Avoid special characters and spaces

### 2. Calendar Alignment

- Always specify appropriate `calendar_name` for asset class
- Use custom calendars for 24/7 markets (CRYPTO, FOREX)
- Ensure data aligns with calendar sessions

### 3. Data Timezone Handling

- Always use UTC timezone for all timestamps
- Normalize daily bar indices (midnight UTC)
- Keep minute bar indices with time component

### 4. Error Handling

```python
from zipline.data.bundles import UnknownBundle, ingest

try:
    ingest('my-bundle', show_progress=True)
except UnknownBundle as e:
    print(f"Bundle not registered: {e.name}")
except Exception as e:
    print(f"Ingestion failed: {e}")
```

### 5. Resource Cleanup

```python
# Always use context manager for bundle data
with load('my-bundle') as bundle_data:
    # Use bundle data
    pass
# Resources automatically closed
```

### 6. Progress Indicators

- Enable `show_progress=True` for long-running ingestions
- Provides feedback on data fetching and writing
- Helps identify bottlenecks

### 7. Multiple Ingestion Management

- Use `ingestions_for_bundle()` to track ingestions
- Use `clean()` to manage disk space
- Keep last N ingestions for rollback capability

---

## Error Handling

### UnknownBundle

Raised when bundle not registered.

```python
from zipline.data.bundles import UnknownBundle, load

try:
    bundle_data = load('nonexistent-bundle')
except UnknownBundle as e:
    print(f"Bundle '{e.name}' not registered")
    print("Available bundles:", list(bundles.keys()))
```

### BadClean

Raised when invalid `clean()` arguments provided.

```python
from zipline.data.bundles import BadClean, clean

try:
    # Invalid: both before and keep_last
    clean('my-bundle', before=datetime(2023, 1, 1), keep_last=3)
except BadClean as e:
    print(f"Invalid clean arguments: {e}")
```

### ValueError

Raised for various data issues:

- No data found for bundle on or before timestamp
- Invalid CSV directory structure
- Missing required CSV columns

---

## Summary

Zipline-Reloaded's bundle management system provides:

- **Flexible Registration** - Register custom data sources with decorator or function call
- **Multiple Ingestion Support** - Track and manage multiple bundle ingestions
- **Efficient Storage** - Bcolz format for fast bar data access
- **Calendar Alignment** - Automatic session alignment with trading calendars
- **Corporate Actions** - Built-in support for splits and dividends
- **Resource Management** - Context managers for automatic cleanup

**Key Functions:**
- `register()` - Register bundle ingest function
- `ingest()` - Download and store bundle data
- `load()` - Load bundle for backtesting
- `unregister()` - Remove bundle registration
- `clean()` - Clean up old ingestions

**Built-in Bundles:**
- `quandl` - Quandl/Nasdaq equity data
- `csvdir` - CSV directory bundle

**Direct API Usage (v1.12.0+):**
- No wrapper functions - use Zipline APIs directly
- Register CSV bundles in `~/.zipline/extension.py`
- Access `bundles` dict directly for bundle list

---

**Related Documentation:**
- [Zipline-Reloaded Documentation](https://zipline.ml4trading.io)
- [Bundle API Reference](bundles.md)
- [Pipeline Inventory](pipeline_inventory.md)
