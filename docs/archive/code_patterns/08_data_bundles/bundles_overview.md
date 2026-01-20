# Data Bundles Overview

> Understanding Zipline's data bundle system.

## What are Data Bundles?

Data bundles are self-contained packages of market data that Zipline uses for backtesting. Think of them like a frozen snapshot of market data that includes:

- **Price data** - Daily/minute OHLCV bars
- **Adjustments** - Splits, dividends, mergers
- **Asset metadata** - Symbols, exchanges, trading dates

---

## Bundle Lifecycle

```
┌─────────────────────────────────────────────────────────┐
│  1. REGISTER                                            │
│     Define bundle name and ingest function              │
├─────────────────────────────────────────────────────────┤
│  2. INGEST                                              │
│     Download/process data, write to disk                │
├─────────────────────────────────────────────────────────┤
│  3. LOAD                                                │
│     Read bundle data for backtesting                    │
└─────────────────────────────────────────────────────────┘
```

---

## Built-in Bundles

### quandl

Free end-of-day US equity data from Quandl/Nasdaq.

```bash
# Set API key
export QUANDL_API_KEY=your_key_here

# Ingest
zipline ingest -b quandl
```

```python
results = run_algorithm(
    ...,
    bundle='quandl'
)
```

---

## Bundle Commands

### Ingest Data

```bash
# Ingest default bundle
zipline ingest

# Ingest specific bundle
zipline ingest -b quandl

# Ingest with timestamp
zipline ingest -b quandl --date 2024-01-15
```

### List Bundles

```bash
# Show registered bundles
zipline bundles
```

### Clean Bundle Data

```bash
# Remove old ingestions
zipline clean -b quandl --keep-last 1
```

---

## Bundle Storage

Bundles are stored in `$ZIPLINE_ROOT` (default: `~/.zipline`):

```
~/.zipline/
├── data/
│   └── quandl/
│       └── 2024-01-15T12:00:00/
│           ├── daily_equities.bcolz/
│           ├── adjustments.sqlite
│           └── assets-7.sqlite
└── extension.py
```

---

## Using Bundles in Code

### run_algorithm()

```python
from zipline import run_algorithm

results = run_algorithm(
    start=start_date,
    end=end_date,
    initialize=initialize,
    capital_base=100000,
    bundle='quandl'  # Specify bundle name
)
```

### Load Bundle Directly

```python
from zipline.data.bundles import load

bundle_data = load('quandl')

# Access components
prices = bundle_data.equity_daily_bar_reader
adjustments = bundle_data.adjustment_reader
assets = bundle_data.asset_finder
```

---

## Bundle Data Components

| Component | Reader | Description |
|-----------|--------|-------------|
| Daily bars | `equity_daily_bar_reader` | OHLCV data |
| Minute bars | `equity_minute_bar_reader` | Intraday data |
| Adjustments | `adjustment_reader` | Splits, dividends |
| Assets | `asset_finder` | Symbol/SID lookup |

---

## Custom Bundle Workflow

### 1. Create Ingest Function

```python
def my_ingest(environ, asset_db_writer, minute_bar_writer,
              daily_bar_writer, adjustment_writer, calendar,
              start_session, end_session, cache, show_progress):
    
    # Write asset metadata
    asset_db_writer.write(equities=equities_df)
    
    # Write price data
    daily_bar_writer.write(price_data_generator())
    
    # Write adjustments
    adjustment_writer.write(splits=splits_df, dividends=dividends_df)
```

### 2. Register Bundle

```python
from zipline.data.bundles import register

register('my-bundle', my_ingest, calendar_name='NYSE')
```

### 3. Ingest and Use

```bash
zipline ingest -b my-bundle
```

```python
results = run_algorithm(..., bundle='my-bundle')
```

---

## Date Management

Each ingest creates a timestamped snapshot:

```python
from zipline.data.bundles import load

# Load most recent ingest
bundle = load('quandl')

# Load specific ingest date
bundle = load('quandl', timestamp=pd.Timestamp('2024-01-15'))
```

---

## Best Practices

1. **Regular ingestion** - Re-ingest periodically for updated data
2. **Keep backups** - Use `--keep-last N` to manage disk space
3. **Test custom bundles** - Validate data before running backtests
4. **Use appropriate frequency** - Daily for most strategies, minute for intraday

---

## See Also

- [Bundles API](bundles.md)
- [Data Writers](data_writers.md)
- [Data Readers](data_readers.md)
- [Asset Metadata](asset_metadata.md)
