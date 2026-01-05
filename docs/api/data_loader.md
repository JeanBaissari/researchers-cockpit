# Data Loader API

Module for data ingestion and bundle management with multi-timeframe support.

**Location:** `lib/data_loader.py`
**CLI Equivalent:** `scripts/ingest_data.py`

---

## ingest_bundle()

Create or update Zipline data bundles from external sources.

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
| `source` | str | required | Data source (`'yahoo'`, `'binance'`, `'oanda'`) |
| `assets` | List[str] | required | Asset classes (`['equities']`, `['crypto']`, `['forex']`) |
| `bundle_name` | str | None | Bundle name (auto-generated if None) |
| `symbols` | List[str] | None | List of symbols (e.g., `['SPY', 'AAPL']`) |
| `start_date` | str | None | Start date `YYYY-MM-DD` (auto-adjusted for limited timeframes) |
| `end_date` | str | None | End date `YYYY-MM-DD` (defaults to today) |
| `calendar_name` | str | None | Trading calendar (`'XNYS'`, `'CRYPTO'`, `'FOREX'`) |
| `timeframe` | str | `'daily'` | Timeframe (`'1m'`, `'5m'`, `'15m'`, `'30m'`, `'1h'`, `'daily'`) |
| `force` | bool | False | Re-register bundle even if already registered |

**Returns:** `str` - Bundle name

**Raises:**
- `ValueError`: If symbols empty, source unsupported, or timeframe invalid
- `RuntimeError`: If ingestion fails

**Example:**
```python
from lib.data_loader import ingest_bundle

# Daily equities
bundle = ingest_bundle(
    source='yahoo',
    assets=['equities'],
    symbols=['SPY', 'AAPL', 'MSFT'],
    timeframe='daily'
)
# Returns: 'yahoo_equities_daily'

# Hourly crypto
bundle = ingest_bundle(
    source='yahoo',
    assets=['crypto'],
    symbols=['BTC-USD', 'ETH-USD'],
    timeframe='1h',
    start_date='2024-01-01'
)
# Returns: 'yahoo_crypto_1h'
```

**CLI Equivalent:**
```bash
# Daily equities
python scripts/ingest_data.py --source yahoo --assets equities --symbols SPY,AAPL,MSFT

# Hourly crypto
python scripts/ingest_data.py --source yahoo --assets crypto --symbols BTC-USD,ETH-USD -t 1h

# List available timeframes
python scripts/ingest_data.py --list-timeframes
```

**Notes:**
- Weekly/monthly timeframes are NOT supported (use daily + aggregation)
- Timeframe data limits: 1m=7d, 5m=60d, 1h=730d, daily=unlimited
- FOREX minute data auto-excludes current day (incomplete session)
- Bundle naming convention: `{source}_{asset}_{timeframe}`

---

## load_bundle()

Load and verify a bundle exists.

**Signature:**
```python
def load_bundle(bundle_name: str) -> Any
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `bundle_name` | str | required | Name of bundle to load |

**Returns:** `BundleData` - Zipline bundle data object

**Raises:**
- `FileNotFoundError`: If bundle doesn't exist
- `RuntimeError`: If bundle loading fails

**Example:**
```python
from lib.data_loader import load_bundle

bundle_data = load_bundle('yahoo_equities_daily')

# Access bundle components
sessions = bundle_data.equity_daily_bar_reader.sessions
calendar = bundle_data.equity_daily_bar_reader.trading_calendar
```

**Notes:**
- Checks both in-memory registry and persistent registry (`~/.zipline/bundle_registry.json`)
- Auto-registers bundles from persistent storage if not in memory

---

## list_bundles()

List all available bundles.

**Signature:**
```python
def list_bundles() -> List[str]
```

**Returns:** `List[str]` - List of bundle names

**Example:**
```python
from lib.data_loader import list_bundles

bundles = list_bundles()
print(bundles)
# ['yahoo_equities_daily', 'yahoo_crypto_1h', 'yahoo_forex_daily']
```

**CLI Equivalent:**
```bash
python scripts/bundle_info.py --list
```

---

## get_bundle_symbols()

Get symbols contained in a bundle.

**Signature:**
```python
def get_bundle_symbols(bundle_name: str) -> List[str]
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `bundle_name` | str | required | Name of bundle |

**Returns:** `List[str]` - List of symbols in bundle

**Raises:**
- `FileNotFoundError`: If bundle not found

**Example:**
```python
from lib.data_loader import get_bundle_symbols

symbols = get_bundle_symbols('yahoo_equities_daily')
print(symbols)
# ['SPY', 'AAPL', 'MSFT']
```

**CLI Equivalent:**
```bash
python scripts/bundle_info.py yahoo_equities_daily
```

---

## Timeframe Configuration

### Supported Timeframes

| Timeframe | yfinance Interval | Data Limit | Zipline Frequency |
|-----------|-------------------|------------|-------------------|
| `1m` | `1m` | 7 days | minute |
| `5m` | `5m` | 60 days | minute |
| `15m` | `15m` | 60 days | minute |
| `30m` | `30m` | 60 days | minute |
| `1h` | `1h` | 730 days | minute |
| `daily` | `1d` | Unlimited | daily |

### NOT Supported
- `weekly` - Zipline requires one bar per session
- `monthly` - Use daily data with aggregation utilities

### Calendar Minutes Per Day

| Calendar | Minutes/Day | Description |
|----------|-------------|-------------|
| `XNYS` | 390 | NYSE: 9:30 AM - 4:00 PM |
| `CRYPTO` | 1440 | 24/7 trading |
| `FOREX` | 1440 | 24h Mon-Fri |

---

## Bundle Registry

Bundles are persisted to `~/.zipline/bundle_registry.json`:

```json
{
  "yahoo_equities_daily": {
    "symbols": ["SPY", "AAPL"],
    "calendar_name": "XNYS",
    "start_date": "2020-01-01",
    "end_date": null,
    "data_frequency": "daily",
    "timeframe": "daily",
    "registered_at": "2024-12-28T10:30:00"
  }
}
```

---

## Internal Functions

### _register_yahoo_bundle()

Registers and configures a Yahoo Finance bundle with multi-timeframe support.

**Key Features:**
- Timezone normalization to UTC
- Calendar session filtering (FOREX Sunday issue)
- Pre-session bar filtering for FOREX
- Gap-filling for missing data (FOREX: 5 days, CRYPTO: 3 days)
- Writes both minute AND daily bars for intraday timeframes

### _load_bundle_registry()

Loads the persistent bundle registry from disk.

### _save_bundle_registry()

Saves bundle metadata to persistent registry.

---

## See Also

- [Troubleshooting: Data Ingestion](../troubleshooting/data_ingestion.md)
- [Bundle Info Script](../../scripts/bundle_info.py)
- [Reingest Script](../../scripts/reingest_all.py)
