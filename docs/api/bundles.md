# Bundles API

Module for data bundle ingestion, management, and access in The Researcher's Cockpit.

**Location:** `lib/bundles/`
**CLI Equivalent:** `scripts/ingest_data.py`
**Version:** v1.12.0

---

## Overview

The bundles module provides a unified interface for ingesting market data from multiple sources (Yahoo Finance, Binance, OANDA) into Zipline data bundles. Bundles serve as the primary data source for both `handle_data()` and the Zipline Pipeline API.

**v1.12.0 Changes:**
- **CSV bundles** now use direct `csvdir_equities()` registration in `~/.zipline/extension.py`
- **Bundle registry** removed → Use Zipline's native `bundles` dictionary
- **SessionManager** removed → Use direct `get_calendar()` for calendar access

**Key Features:**
- Multi-timeframe support (1m, 5m, 15m, 30m, 1h, daily)
- Multiple data sources (Yahoo Finance, Binance, OANDA)
- Automatic calendar registration (CRYPTO, FOREX, XNYS)
- Direct Zipline API usage (NO wrappers, AD-001)

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

## Main API

### Core Functions

| Function | Purpose |
|----------|---------|
| `ingest_bundle()` | Ingest market data into Zipline bundle |
| `list_bundles()` | List all available bundles |
| `load_bundle()` | Load and verify bundle exists |
| `get_bundle_symbols()` | Get symbols available in bundle |

### Bundle Management

| Function | Purpose |
|----------|---------|
| `register_csv_bundle()` | Register CSV bundle (v1.12.0+: use csvdir_equities) |
| `unregister_bundle()` | Unregister a bundle |
| `get_bundle_metadata()` | Get bundle metadata (dates, symbols) |

---

### Load and Use a Bundle

```python
from lib.bundles import load_bundle, get_bundle_symbols

# Load bundle (verifies it exists and is registered)
bundle_data = load_bundle('yahoo_equities_daily')

# Get symbols in bundle
symbols = get_bundle_symbols('yahoo_equities_daily')
print(f"Symbols: {symbols}")  # ['SPY', 'AAPL', 'MSFT']
```

### CSV Bundle Registration (v1.12.0+)

**Note:** CSV bundles are now registered directly in `~/.zipline/extension.py` using Zipline's native `csvdir_equities()`.

```python
# In ~/.zipline/extension.py:
from zipline.data.bundles import register
from zipline.data.bundles.csvdir import csvdir_equities

register(
    'eurusd_1h',
    csvdir_equities(
        ['EURUSD'],
        csvdir='/path/to/csvdir'
    ),
    calendar_name='FOREX'
)
```

See strategy template for complete examples.

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

### Registry Functions (v1.12.0 - Removed)

**Note:** Bundle registry functions have been removed in v1.12.0. Use Zipline's native `bundles` dictionary directly:

```python
from zipline.data.bundles import bundles, unregister

# List all bundles
bundle_names = list(bundles.keys())

# Check if bundle exists
if 'btcusd_daily' in bundles:
    print("Bundle registered")

# Unregister a bundle
unregister('btcusd_daily')
```

Bundle metadata is now tracked by Zipline natively. No persistent registry file is maintained.

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

### CSV Bundle Functions (v1.12.0 - Removed)

**Note:** CSV bundle wrapper functions have been removed in v1.12.0. Use Zipline's native `csvdir_equities()` directly in `~/.zipline/extension.py`:

```python
# In ~/.zipline/extension.py:
from zipline.data.bundles import register
from zipline.data.bundles.csvdir import csvdir_equities

register(
    'eurusd_1m',
    csvdir_equities(
        ['EURUSD'],  # Symbol list
        csvdir='/path/to/data/csvdir'  # Directory containing EURUSD/ folder
    ),
    calendar_name='FOREX'
)
```

**CSV Directory Structure:**
```
data/csvdir/
├── EURUSD/
│   └── EURUSD.csv  # Contains: date, open, high, low, close, volume
└── GBPUSD/
    └── GBPUSD.csv
```

Column names should be: `date`, `open`, `high`, `low`, `close`, `volume` (lowercase).

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

## Module Structure (v1.12.0)

The bundles package is organized into focused submodules:

```
lib/bundles/
├── api.py                    # Main public API (thin interface)
├── management.py             # Bundle ingestion orchestration
├── access.py                 # Bundle loading and querying
├── timeframes.py             # Timeframe configuration
├── utils.py                  # Bundle utilities
├── initialization.py         # Calendar registration
└── yahoo/                    # Yahoo Finance support
    ├── fetcher.py            # Data fetching from Yahoo Finance
    ├── processor.py          # Data processing and aggregation
    └── registration.py       # Bundle registration orchestration
```

**v1.12.0 Removals:**
- ~~csv/~~ — Deleted (use csvdir_equities() directly)
- ~~registry.py~~ — Deleted (use Zipline's bundles dict)

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

**v1.12.0+** (Direct API usage):
```
{symbol}_{timeframe}
```

**Examples:**
- `btcusd_daily` - Bitcoin, daily
- `btcusd_1h` - Bitcoin, hourly
- `eurusd_1m` - Euro/Dollar, 1-minute
- `aapl_daily` - Apple stock, daily

**Legacy (v1.11.1 and earlier):**
```
{source}_{asset_class}_{timeframe}
```
- `yahoo_equities_daily`
- `yahoo_crypto_1h`
- `csv_forex_1h`

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

- **v1.12.0**: NO WRAPPERS refactoring - Removed CSV bundle wrappers (use csvdir_equities()), removed registry (use Zipline's bundles dict), bundle naming changed to {symbol}_{timeframe}
- **v1.11.0**: Modular refactoring (management/access split, CSV/Yahoo subpackages)
- **v1.1.0**: Session management integration for calendar alignment
- **v1.0.6**: Multi-timeframe support with data limits
- **v1.0.5**: Bundle registry for metadata persistence

---

**Last Updated:** 2026-02-09
**Version:** v1.12.0
**Status:** NO WRAPPERS Architecture
