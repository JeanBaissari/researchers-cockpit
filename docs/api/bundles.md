# Bundles API

Module for data bundle ingestion, management, and access in The Researcher's Cockpit.

**Location:** `lib/bundles/`  
**CLI Equivalent:** `scripts/ingest_data.py`  
**Version:** v1.11.0

---

## Overview

The bundles module provides a unified interface for ingesting market data from multiple sources (Yahoo Finance, CSV files, Binance, OANDA) into Zipline data bundles. Bundles serve as the primary data source for both `handle_data()` and the Zipline Pipeline API.

**Key Features:**
- Multi-timeframe support (1m, 5m, 15m, 30m, 1h, daily)
- Multiple data sources (Yahoo Finance, CSV, Binance, OANDA)
- Automatic calendar registration (CRYPTO, FOREX, XNYS)
- Bundle registry for metadata persistence
- Session management integration for calendar alignment

---

## Installation/Dependencies

**Required:**
- `zipline-reloaded` >= 3.1.0
- `yfinance` (for Yahoo Finance source)
- `pandas` >= 1.3.0

**Optional:**
- `ccxt` (for Binance source - not yet implemented)
- `oandapyV20` (for OANDA source - not yet implemented)

---

## Quick Start

### Basic Bundle Ingestion

```python
from lib.bundles import ingest_bundle, list_bundles

# Ingest daily equities data from Yahoo Finance
bundle_name = ingest_bundle(
    source='yahoo',
    assets=['equities'],
    symbols=['SPY', 'AAPL', 'MSFT'],
    timeframe='daily'
)

print(f"Ingested bundle: {bundle_name}")  # yahoo_equities_daily

# List all available bundles
bundles = list_bundles()
print(f"Available bundles: {bundles}")
```

### Load and Use a Bundle

```python
from lib.bundles import load_bundle, get_bundle_symbols

# Load bundle (verifies it exists and is registered)
bundle_data = load_bundle('yahoo_equities_daily')

# Get symbols in bundle
symbols = get_bundle_symbols('yahoo_equities_daily')
print(f"Symbols: {symbols}")  # ['SPY', 'AAPL', 'MSFT']
```

### CSV Bundle Ingestion

```python
from lib.bundles import ingest_bundle

# Ingest from local CSV files
bundle_name = ingest_bundle(
    source='csv',
    assets=['forex'],
    symbols=['EURUSD', 'GBPUSD'],  # CSV filenames or paths
    timeframe='1h',
    start_date='2020-01-01',
    end_date='2024-01-01'
)
```

---

## Public API Reference

### Main Functions

#### `ingest_bundle()`

Ingest data from a source into a Zipline bundle.

**Signature:**
```python
def ingest_bundle(
    source: str,
    assets: List[str],
    bundle_name: Optional[str] = None,
    symbols: Optional[List[str]] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    calendar_name: Optional[str] = None,
    timeframe: str = 'daily',
    force: bool = False,
    **kwargs
) -> str
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `source` | str | required | Data source name (`'yahoo'`, `'csv'`, `'binance'`, `'oanda'`) |
| `assets` | List[str] | required | List of asset classes (`['equities']`, `['crypto']`, `['forex']`) |
| `bundle_name` | str | None | Custom bundle name. Auto-generated as `{source}_{asset}_{timeframe}` if not provided |
| `symbols` | List[str] | None | List of symbols to ingest (required) |
| `start_date` | str | None | Start date `YYYY-MM-DD`. Adjusted automatically for limited timeframes |
| `end_date` | str | None | End date `YYYY-MM-DD`. Defaults to today (yesterday for FOREX intraday API) |
| `calendar_name` | str | None | Trading calendar (`'XNYS'`, `'CRYPTO'`, `'FOREX'`). Auto-detected from asset class |
| `timeframe` | str | `'daily'` | Data timeframe (`'1m'`, `'5m'`, `'15m'`, `'30m'`, `'1h'`, `'daily'`) |
| `force` | bool | False | If True, unregister and re-register the bundle even if already registered |

**Returns:**
- `str`: Bundle name (e.g., `'yahoo_equities_daily'`)

**Raises:**
- `ValueError`: If symbols empty, source not supported, or timeframe invalid
- `RuntimeError`: If ingestion fails

**Examples:**

```python
# Daily equities from Yahoo Finance
bundle = ingest_bundle(
    source='yahoo',
    assets=['equities'],
    symbols=['SPY', 'AAPL'],
    timeframe='daily'
)

# Hourly crypto data
bundle = ingest_bundle(
    source='yahoo',
    assets=['crypto'],
    symbols=['BTC-USD', 'ETH-USD'],
    timeframe='1h',
    start_date='2022-01-01'
)

# CSV bundle with custom name
bundle = ingest_bundle(
    source='csv',
    assets=['forex'],
    symbols=['EURUSD', 'GBPUSD'],
    bundle_name='my_forex_bundle',
    timeframe='1h'
)
```

---

#### `load_bundle()`

Verify that a bundle exists and is loadable.

**Signature:**
```python
def load_bundle(bundle_name: str) -> Any
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `bundle_name` | str | required | Name of bundle to check |

**Returns:**
- `Any`: Bundle data object from Zipline

**Raises:**
- `FileNotFoundError`: If bundle doesn't exist
- `RuntimeError`: If bundle loading fails

**Example:**
```python
from lib.bundles import load_bundle

# Load bundle (will re-register if needed)
bundle_data = load_bundle('yahoo_equities_daily')
```

**Note:** For dynamically registered bundles, this function will attempt to re-register them if they're not in the registry but data exists. Uses persistent bundle registry to restore metadata across sessions.

---

#### `get_bundle_symbols()`

Get the list of symbols available in a bundle.

**Signature:**
```python
def get_bundle_symbols(bundle_name: str) -> List[str]
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `bundle_name` | str | required | Name of the bundle (e.g., `'yahoo_equities_daily'`) |

**Returns:**
- `List[str]`: List of symbol strings available in the bundle

**Raises:**
- `FileNotFoundError`: If bundle doesn't exist

**Example:**
```python
from lib.bundles import get_bundle_symbols

symbols = get_bundle_symbols('yahoo_equities_daily')
print(symbols)  # ['SPY', 'AAPL', 'MSFT']
```

**Note:** This function first checks the bundle registry for persisted metadata, then falls back to extracting symbols from the bundle's SQLite database.

---

### Registry Functions

#### `list_bundles()`

List all available Zipline bundles.

**Signature:**
```python
def list_bundles() -> List[str]
```

**Returns:**
- `List[str]`: List of bundle names

**Example:**
```python
from lib.bundles import list_bundles

bundles = list_bundles()
print(bundles)  # ['yahoo_equities_daily', 'yahoo_crypto_1h', 'csv_forex_1h']
```

---

#### `register_bundle_metadata()`

Persist bundle metadata to registry file.

**Signature:**
```python
def register_bundle_metadata(
    bundle_name: str,
    symbols: List[str],
    calendar_name: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    data_frequency: str = 'daily',
    timeframe: str = 'daily'
) -> None
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `bundle_name` | str | required | Name of the bundle |
| `symbols` | List[str] | required | List of symbols in the bundle |
| `calendar_name` | str | required | Trading calendar name |
| `start_date` | str | None | Start date for data (`YYYY-MM-DD` format, validated) |
| `end_date` | str | None | End date for data (`YYYY-MM-DD` format, validated) |
| `data_frequency` | str | `'daily'` | Zipline data frequency (`'daily'` or `'minute'`) |
| `timeframe` | str | `'daily'` | Actual data timeframe (`'1m'`, `'5m'`, `'1h'`, `'daily'`, etc.) |

**Note:** Dates are validated before storage to prevent registry corruption. Invalid dates are stored as `None` rather than corrupted values.

---

#### `get_bundle_path()`

Get the path where a bundle should be stored.

**Signature:**
```python
def get_bundle_path(bundle_name: str) -> Path
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `bundle_name` | str | required | Name of the bundle |

**Returns:**
- `Path`: Path to bundle directory

---

#### `unregister_bundle()`

Unregister a bundle from Zipline's registry.

**Signature:**
```python
def unregister_bundle(bundle_name: str) -> bool
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `bundle_name` | str | required | Name of the bundle to unregister |

**Returns:**
- `bool`: `True` if bundle was unregistered, `False` if it wasn't registered

**Note:** This removes the bundle registration from Zipline's in-memory registry, allowing it to be re-registered with new parameters. Does not delete the bundle data from disk.

---

### Timeframe Configuration

#### `get_timeframe_info()`

Get comprehensive information about a timeframe.

**Signature:**
```python
def get_timeframe_info(timeframe: str) -> Dict[str, Any]
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `timeframe` | str | required | Timeframe string (e.g., `'1h'`, `'daily'`, `'5m'`) |

**Returns:**
- `Dict[str, Any]`: Dictionary with:
  - `timeframe`: Normalized timeframe string
  - `yf_interval`: yfinance interval code
  - `data_limit_days`: Data retention limit in days (None for unlimited)
  - `data_frequency`: Zipline data frequency (`'daily'` or `'minute'`)
  - `is_intraday`: Boolean indicating if timeframe is intraday
  - `requires_aggregation`: Boolean indicating if aggregation is required
  - `aggregation_target`: Target timeframe for aggregation (if applicable)

**Raises:**
- `ValueError`: If timeframe is not supported

**Example:**
```python
from lib.bundles import get_timeframe_info

info = get_timeframe_info('1h')
print(info)
# {
#     'timeframe': '1h',
#     'yf_interval': '1h',
#     'data_limit_days': 720,
#     'data_frequency': 'minute',
#     'is_intraday': True,
#     'requires_aggregation': False,
#     'aggregation_target': None
# }
```

---

#### `validate_timeframe_date_range()`

Validate and adjust date range based on timeframe data limits.

**Signature:**
```python
def validate_timeframe_date_range(
    timeframe: str,
    start_date: Optional[str],
    end_date: Optional[str]
) -> tuple
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `timeframe` | str | required | Timeframe string |
| `start_date` | str | None | Requested start date (`YYYY-MM-DD`) |
| `end_date` | str | None | Requested end date (`YYYY-MM-DD`) |

**Returns:**
- `tuple`: `(adjusted_start_date, adjusted_end_date, warning_message)`

**Example:**
```python
from lib.bundles import validate_timeframe_date_range

start, end, warning = validate_timeframe_date_range(
    timeframe='1m',
    start_date='2020-01-01',  # Too far back for 1m data
    end_date='2024-01-01'
)

if warning:
    print(warning)  # "Warning: 1m data only available for last 6 days..."
```

---

### Timeframe Constants

#### `VALID_TIMEFRAMES`

List of all supported timeframes.

**Type:** `List[str]`

**Values:** `['1m', '2m', '5m', '15m', '30m', '1h', '4h', 'daily', '1d', 'weekly', '1wk', 'monthly', '1mo']`

**Note:** `weekly` and `monthly` are not compatible with Zipline bundles. Use daily data with aggregation instead.

---

#### `TIMEFRAME_DATA_LIMITS`

Data retention limits for each timeframe (in days).

**Type:** `Dict[str, Optional[int]]`

**Values:**
```python
{
    '1m': 6,         # 7 days max, use 6 for safety
    '2m': 55,        # 60 days max
    '5m': 55,        # 60 days max
    '15m': 55,       # 60 days max
    '30m': 55,       # 60 days max
    '1h': 720,       # 730 days max
    '4h': 720,       # Uses 1h data limit
    'daily': None,   # Unlimited
    '1d': None,      # Unlimited
}
```

**Note:** These are conservative limits (slightly less than Yahoo Finance maximums) to avoid edge-case rejections from the API.

---

#### `TIMEFRAME_TO_DATA_FREQUENCY`

Maps timeframes to Zipline data frequency.

**Type:** `Dict[str, str]`

**Values:**
```python
{
    '1m': 'minute',
    '5m': 'minute',
    '15m': 'minute',
    '30m': 'minute',
    '1h': 'minute',   # Zipline treats all sub-daily as 'minute'
    '4h': 'minute',   # Requires aggregation from 1h
    'daily': 'daily',
    '1d': 'daily',
}
```

---

### CSV Bundle Functions

#### `register_csv_bundle()`

Register a CSV bundle for ingestion.

**Signature:**
```python
def register_csv_bundle(
    bundle_name: str,
    symbols: List[str],
    calendar_name: str,
    timeframe: str,
    asset_class: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    force: bool = False
) -> None
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `bundle_name` | str | required | Name of the bundle |
| `symbols` | List[str] | required | List of CSV filenames or paths |
| `calendar_name` | str | required | Trading calendar name |
| `timeframe` | str | required | Data timeframe |
| `asset_class` | str | required | Asset class (`'equities'`, `'crypto'`, `'forex'`) |
| `start_date` | str | None | Start date (`YYYY-MM-DD`) |
| `end_date` | str | None | End date (`YYYY-MM-DD`) |
| `force` | bool | False | Force re-registration if bundle exists |

**Note:** CSV files should be in `data/csv/` directory or provide full paths. Column names are automatically normalized.

---

#### `normalize_csv_columns()`

Normalize CSV column names to standard format.

**Signature:**
```python
def normalize_csv_columns(df: pd.DataFrame) -> pd.DataFrame
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `df` | pd.DataFrame | required | DataFrame with potentially non-standard column names |

**Returns:**
- `pd.DataFrame`: DataFrame with normalized column names (`open`, `high`, `low`, `close`, `volume`)

**Example:**
```python
from lib.bundles.csv import normalize_csv_columns

# Normalize column names
df_normalized = normalize_csv_columns(df)
# Converts: 'Open', 'HIGH', 'Low', 'Close', 'Volume' -> 'open', 'high', 'low', 'close', 'volume'
```

---

### Yahoo Finance Bundle Functions

#### `register_yahoo_bundle()`

Register a Yahoo Finance bundle for ingestion.

**Signature:**
```python
def register_yahoo_bundle(
    bundle_name: str,
    symbols: List[str],
    calendar_name: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    data_frequency: str = 'daily',
    timeframe: str = 'daily',
    force: bool = False
) -> None
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `bundle_name` | str | required | Name of the bundle |
| `symbols` | List[str] | required | List of Yahoo Finance symbols |
| `calendar_name` | str | required | Trading calendar name |
| `start_date` | str | None | Start date (`YYYY-MM-DD`) |
| `end_date` | str | None | End date (`YYYY-MM-DD`) |
| `data_frequency` | str | `'daily'` | Zipline data frequency |
| `timeframe` | str | `'daily'` | Actual data timeframe |
| `force` | bool | False | Force re-registration if bundle exists |

---

## Module Structure

The bundles package is organized into focused submodules:

```
lib/bundles/
├── api.py                    # Main public API (thin interface)
├── management.py             # Bundle ingestion orchestration
├── access.py                 # Bundle loading and querying
├── registry.py               # Bundle metadata registry
├── timeframes.py             # Timeframe configuration
├── utils.py                  # Bundle utilities
├── csv/                      # CSV bundle support
│   ├── parser.py             # CSV parsing and column normalization
│   ├── ingestion.py          # CSV data loading and processing
│   ├── writer.py             # Zipline writer interface
│   └── registration.py       # Bundle registration orchestration
└── yahoo/                    # Yahoo Finance support
    ├── fetcher.py            # Data fetching from Yahoo Finance
    ├── processor.py          # Data processing and aggregation
    └── registration.py       # Bundle registration orchestration
```

---

## Examples

### Multi-Timeframe Ingestion

```python
from lib.bundles import ingest_bundle

# Daily data (unlimited history)
daily_bundle = ingest_bundle(
    source='yahoo',
    assets=['equities'],
    symbols=['SPY'],
    timeframe='daily',
    start_date='2010-01-01'
)

# Hourly data (up to 730 days)
hourly_bundle = ingest_bundle(
    source='yahoo',
    assets=['crypto'],
    symbols=['BTC-USD'],
    timeframe='1h',
    start_date='2022-01-01'  # Auto-adjusted if too far back
)

# 5-minute data (up to 60 days)
minute_bundle = ingest_bundle(
    source='yahoo',
    assets=['equities'],
    symbols=['SPY'],
    timeframe='5m',
    start_date='2024-01-01'  # Auto-adjusted to last 60 days
)
```

### CSV Bundle with Custom Calendar

```python
from lib.bundles import ingest_bundle

# Ingest FOREX data from CSV files
bundle = ingest_bundle(
    source='csv',
    assets=['forex'],
    symbols=['EURUSD.csv', 'GBPUSD.csv'],  # Files in data/csv/
    timeframe='1h',
    calendar_name='FOREX',  # 24/5 trading calendar
    start_date='2020-01-01',
    end_date='2024-01-01'
)
```

### Bundle Registry Management

```python
from lib.bundles import (
    list_bundles,
    register_bundle_metadata,
    get_bundle_symbols
)

# List all bundles
bundles = list_bundles()
print(f"Available bundles: {bundles}")

# Get symbols from a bundle
symbols = get_bundle_symbols('yahoo_equities_daily')
print(f"Symbols: {symbols}")

# Manually register bundle metadata (usually done automatically)
register_bundle_metadata(
    bundle_name='my_custom_bundle',
    symbols=['SPY', 'AAPL'],
    calendar_name='XNYS',
    start_date='2020-01-01',
    end_date='2024-01-01',
    data_frequency='daily',
    timeframe='daily'
)
```

---

## Configuration

### Bundle Naming Convention

Bundles are automatically named using the pattern:
```
{source}_{asset_class}_{timeframe}
```

**Examples:**
- `yahoo_equities_daily` - Yahoo Finance, equities, daily
- `yahoo_crypto_1h` - Yahoo Finance, crypto, hourly
- `csv_forex_1h` - CSV source, forex, hourly

### Timeframe Data Limits

| Timeframe | Data Limit | Notes |
|-----------|------------|-------|
| `1m` | 6 days | Conservative limit (Yahoo max: 7 days) |
| `2m` | 55 days | Conservative limit (Yahoo max: 60 days) |
| `5m` | 55 days | Conservative limit (Yahoo max: 60 days) |
| `15m` | 55 days | Conservative limit (Yahoo max: 60 days) |
| `30m` | 55 days | Conservative limit (Yahoo max: 60 days) |
| `1h` | 720 days | Conservative limit (Yahoo max: 730 days) |
| `4h` | 720 days | Uses 1h data limit (requires aggregation) |
| `daily` | Unlimited | Full historical data available |

**Note:** For CSV sources, data limits are not applied. All available data in the CSV files is ingested.

### Calendar Auto-Detection

The calendar is automatically detected from the asset class:

| Asset Class | Calendar | Trading Hours |
|-------------|----------|---------------|
| `equities` | `XNYS` | 9:30 AM - 4:00 PM ET, weekdays |
| `crypto` | `CRYPTO` | 24/7 (365 days/year) |
| `forex` | `FOREX` | 24/5 (Monday-Friday, 24 hours) |

Custom calendars (`CRYPTO`, `FOREX`) are automatically registered when needed.

### FOREX Intraday Data Safeguard

For FOREX intraday data from API sources (Yahoo Finance), the current day is automatically excluded to avoid incomplete session data. This safeguard does not apply to CSV sources.

**Example:**
```python
# FOREX intraday from Yahoo Finance - automatically excludes today
bundle = ingest_bundle(
    source='yahoo',
    assets=['forex'],
    symbols=['EURUSD=X'],
    timeframe='1h'
    # end_date automatically set to yesterday
)

# FOREX intraday from CSV - uses actual file end date
bundle = ingest_bundle(
    source='csv',
    assets=['forex'],
    symbols=['EURUSD.csv'],
    timeframe='1h'
    # end_date uses actual CSV file end date
)
```

---

## Error Handling

### Common Errors and Solutions

#### `ValueError: symbols parameter is required and cannot be empty`

**Cause:** No symbols provided for ingestion.

**Solution:**
```python
# Provide symbols list
bundle = ingest_bundle(
    source='yahoo',
    assets=['equities'],
    symbols=['SPY', 'AAPL']  # Required!
)
```

#### `ValueError: Unsupported timeframe: '4h'`

**Cause:** Timeframe not supported or requires special handling.

**Solution:**
```python
# Use supported timeframes
# For 4h data, use 1h with aggregation (handled automatically)
bundle = ingest_bundle(
    source='yahoo',
    assets=['crypto'],
    symbols=['BTC-USD'],
    timeframe='1h'  # Then aggregate to 4h if needed
)
```

#### `FileNotFoundError: Bundle 'yahoo_equities_daily' not found`

**Cause:** Bundle not ingested or not registered.

**Solution:**
```python
# Ingest the bundle first
bundle = ingest_bundle(
    source='yahoo',
    assets=['equities'],
    symbols=['SPY'],
    timeframe='daily'
)

# Then load it
bundle_data = load_bundle(bundle)
```

#### `RuntimeError: Failed to ingest Yahoo Finance bundle`

**Cause:** Network error, invalid symbols, or API rate limiting.

**Solution:**
- Check internet connection
- Verify symbols are valid (e.g., `'SPY'` not `'SPY '`)
- Wait and retry if rate limited
- Check Yahoo Finance API status

---

## See Also

- [Calendars API](calendars.md) - Trading calendar management
- [Validation API](validation.md) - Data validation before ingestion
- [Data Processing API](data.md) - Data aggregation and normalization
- [Backtest API](backtest.md) - Using bundles in backtests
- [CLI: ingest_data.py](../../scripts/ingest_data.py) - Command-line ingestion
- [Code Patterns: Data Bundles](../../code_patterns/08_data_bundles/) - Usage patterns

---

## Version History

- **v1.11.0**: Modular refactoring (management/access split, CSV/Yahoo subpackages)
- **v1.1.0**: Session management integration for calendar alignment
- **v1.0.6**: Multi-timeframe support with data limits
- **v1.0.5**: Bundle registry for metadata persistence
