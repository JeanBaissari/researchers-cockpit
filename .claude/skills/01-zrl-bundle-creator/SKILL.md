---
name: zrl-bundle-creator
description: This skill should be used when creating custom Zipline data bundles from CSV, API, or database sources. It provides deterministic patterns for ingesting OHLCV data, registering bundles, and validating data integrity for backtesting.
---

# Zipline Bundle Creator

Create custom data bundles for Zipline-Reloaded backtesting from any data source.

## Purpose

Transform raw market data (CSV, API, database) into Zipline-compatible bundles with proper asset metadata, corporate actions, and calendar alignment.

## When to Use

- Converting CSV/Parquet price data to Zipline bundles
- Integrating API data sources (Yahoo, Alpha Vantage, custom)
- Building multi-asset bundles (equities, ETFs, crypto)
- Setting up reproducible data pipelines

## Bundle Architecture

```
~/.zipline/
├── extension.py          # Bundle registration
└── data/
    └── <bundle_name>/
        ├── daily_equities.bcolz/
        ├── adjustments.sqlite
        └── assets.sqlite
```

## Core Workflow

### Step 1: Prepare Source Data

Ensure source data contains required columns with correct types:

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| date | datetime | Yes | Trading date (UTC) |
| open | float | Yes | Opening price |
| high | float | Yes | High price |
| low | float | Yes | Low price |
| close | float | Yes | Closing price |
| volume | int | Yes | Trading volume |
| symbol | str | Yes | Ticker symbol |
| dividend | float | No | Cash dividend |
| split | float | No | Split ratio |

### Step 2: Create Bundle Registration

To register a bundle, create or modify `~/.zipline/extension.py`:

```python
from zipline.data.bundles import register
from zipline.data.bundles.csvdir import csvdir_equities

# CSV Directory Bundle
register(
    'my-bundle',
    csvdir_equities(
        ['daily'],
        '/path/to/csv/directory',
    ),
    calendar_name='NYSE',
    start_session=pd.Timestamp('2010-01-01', tz='utc'),
    end_session=pd.Timestamp('2024-12-31', tz='utc'),
)
```

### Step 3: Validate and Ingest

Execute `scripts/validate_bundle.py` before ingestion to check data integrity. Then run:

```bash
zipline ingest -b my-bundle
```

## Script Reference

### validate_bundle.py

Execute to validate source data before ingestion:

```bash
python scripts/validate_bundle.py /path/to/data --calendar NYSE
```

Validates: date continuity, price sanity, volume non-negative, OHLC relationships.

### create_bundle.py

Generate bundle registration code from data source:

```bash
python scripts/create_bundle.py \
    --source /path/to/csvs \
    --name my-bundle \
    --calendar NYSE \
    --start 2010-01-01 \
    --end 2024-12-31
```

### ingest_yahoo.py

Ingest data directly from Yahoo Finance:

```bash
python scripts/ingest_yahoo.py \
    --symbols AAPL,MSFT,GOOGL \
    --start 2015-01-01 \
    --end 2024-12-31 \
    --output /path/to/output
```

## Custom Ingest Function Pattern

For complex data sources, implement a custom ingest function:

```python
@bundles.register('custom-bundle')
def custom_ingest(environ, asset_db_writer, minute_bar_writer,
                  daily_bar_writer, adjustment_writer, calendar,
                  start_session, end_session, cache, show_progress,
                  output_dir):
    
    # 1. Load data from source
    raw_data = load_from_source()
    
    # 2. Build asset metadata DataFrame
    assets = pd.DataFrame({
        'symbol': symbols,
        'asset_name': names,
        'start_date': start_dates,
        'end_date': end_dates,
        'exchange': 'NYSE',
    })
    
    # 3. Write assets
    asset_db_writer.write(equities=assets)
    
    # 4. Generate daily bars iterator
    def daily_bar_generator():
        for sid, symbol in enumerate(symbols):
            df = get_ohlcv(symbol)
            yield sid, df
    
    daily_bar_writer.write(daily_bar_generator(), show_progress=show_progress)
    
    # 5. Write adjustments (splits, dividends)
    adjustment_writer.write(splits=splits_df, dividends=dividends_df)
```

## Validation Checklist

Before using a bundle in backtests:

- [ ] All dates are timezone-aware (UTC)
- [ ] No NaN values in OHLCV columns
- [ ] high >= max(open, close) for all rows
- [ ] low <= min(open, close) for all rows
- [ ] volume >= 0 for all rows
- [ ] Dates align with trading calendar
- [ ] Asset metadata matches price data symbols
- [ ] Adjustments applied correctly (verify adjusted prices)

## Common Issues and Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| `SymbolNotFound` | Symbol not in assets | Verify asset_db_writer.write() includes symbol |
| `NoDataOnDate` | Missing price data | Fill gaps or adjust date range |
| `CalendarMismatch` | Wrong calendar | Match calendar to market (NYSE, XLON, etc.) |
| Stale prices | Forward-fill issues | Check for trading halts, handle appropriately |

## References

See `references/bundle_schemas.md` for detailed DataFrame schemas.
See `references/calendar_list.md` for available trading calendars.
