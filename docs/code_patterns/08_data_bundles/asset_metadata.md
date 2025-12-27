# Asset Metadata

> Structure and management of asset information in bundles.

## Overview

Asset metadata describes the securities in your bundle: symbols, names, exchanges, and trading date ranges. This data is stored in SQLite and accessed via AssetFinder.

---

## Equity Metadata Schema

Required columns for the equities DataFrame:

| Column | Type | Description |
|--------|------|-------------|
| `symbol` | str | Ticker symbol (e.g., 'AAPL') |
| `asset_name` | str | Full company name |
| `start_date` | datetime | First trading date |
| `end_date` | datetime | Last trading date (or None if active) |
| `exchange` | str | Exchange code (e.g., 'NYSE', 'NASDAQ') |

Optional columns:

| Column | Type | Description |
|--------|------|-------------|
| `first_traded` | datetime | First trade date |
| `auto_close_date` | datetime | Auto-liquidation date |
| `exchange_full` | str | Full exchange name |
| `country_code` | str | ISO 3166-1 alpha-2 (e.g., 'US') |
| `tick_size` | float | Minimum price increment |

---

## Creating Equity Metadata

```python
import pandas as pd

equities = pd.DataFrame({
    'symbol': ['AAPL', 'MSFT', 'GOOGL'],
    'asset_name': ['Apple Inc', 'Microsoft Corporation', 'Alphabet Inc'],
    'start_date': pd.Timestamp('2010-01-01'),
    'end_date': pd.Timestamp('2024-12-31'),
    'exchange': ['NASDAQ', 'NASDAQ', 'NASDAQ'],
    'country_code': ['US', 'US', 'US']
})

# Index becomes the SID (security identifier)
equities.index = [0, 1, 2]
```

---

## Futures Metadata Schema

Required columns for futures:

| Column | Type | Description |
|--------|------|-------------|
| `symbol` | str | Contract symbol (e.g., 'CLF21') |
| `root_symbol` | str | Root symbol (e.g., 'CL') |
| `asset_name` | str | Contract name |
| `start_date` | datetime | First trading date |
| `end_date` | datetime | Last trading date |
| `notice_date` | datetime | First notice date |
| `expiration_date` | datetime | Contract expiration |
| `multiplier` | float | Contract multiplier |
| `exchange` | str | Exchange code |

---

## Exchange Metadata

```python
exchanges = pd.DataFrame({
    'exchange': ['NYSE', 'NASDAQ', 'CME'],
    'canonical_name': ['NEW YORK STOCK EXCHANGE', 'NASDAQ', 'CME GROUP'],
    'country_code': ['US', 'US', 'US']
})
```

---

## Writing Asset Metadata

### Using AssetDBWriter

```python
from zipline.assets import AssetDBWriter
from sqlalchemy import create_engine

engine = create_engine('sqlite:///assets.db')
writer = AssetDBWriter(engine)

writer.write(
    equities=equities_df,
    futures=futures_df,
    exchanges=exchanges_df
)
```

### In Bundle Ingest Function

```python
def ingest(environ, asset_db_writer, minute_bar_writer,
           daily_bar_writer, adjustment_writer, calendar,
           start_session, end_session, cache, show_progress):
    
    # Prepare metadata
    equities = pd.DataFrame({
        'symbol': symbols,
        'asset_name': names,
        'start_date': start_dates,
        'end_date': end_dates,
        'exchange': exchanges
    })
    
    # Write to database
    asset_db_writer.write(equities=equities)
```

---

## Symbol Changes

Handle ticker symbol changes (e.g., Google → GOOGL):

```python
# Symbol history via supplementary mappings
symbol_mappings = pd.DataFrame({
    'sid': [2, 2],
    'symbol': ['GOOG', 'GOOGL'],
    'start_date': [pd.Timestamp('2004-08-19'), pd.Timestamp('2014-04-03')],
    'end_date': [pd.Timestamp('2014-04-02'), pd.NaT]
})

writer.write(
    equities=equities,
    equity_supplementary_mappings=symbol_mappings
)
```

---

## Accessing Metadata

### Via AssetFinder

```python
from zipline.data.bundles import load

bundle = load('my-bundle')
finder = bundle.asset_finder

# Look up by symbol
asset = finder.lookup_symbol('AAPL', as_of_date)

# Get by SID
asset = finder.retrieve_asset(0)

# Get all equities
all_sids = finder.equities_sids
```

### Asset Properties

```python
asset = finder.retrieve_asset(0)

print(asset.symbol)        # 'AAPL'
print(asset.asset_name)    # 'Apple Inc'
print(asset.exchange)      # 'NASDAQ'
print(asset.start_date)    # Timestamp('2010-01-01')
print(asset.end_date)      # Timestamp('2024-12-31')
print(asset.sid)           # 0
```

---

## Validation

Ensure metadata consistency:

```python
def validate_metadata(equities, daily_bars):
    """Check that price data exists for all assets."""
    price_sids = set(daily_bars.keys())
    meta_sids = set(equities.index)
    
    missing = meta_sids - price_sids
    if missing:
        raise ValueError(f"No price data for SIDs: {missing}")
    
    extra = price_sids - meta_sids
    if extra:
        raise ValueError(f"No metadata for SIDs: {extra}")
```

---

## Best Practices

1. **Unique SIDs** - Each asset needs a unique integer identifier
2. **Consistent dates** - Align start/end dates with price data
3. **Valid exchanges** - Use standard exchange codes
4. **Handle delistings** - Set end_date for delisted securities
5. **Track symbol changes** - Use supplementary mappings for renames

---

## See Also

- [Asset Types](../05_assets/asset_types.md)
- [Asset Finder](../05_assets/asset_finder.md)
- [Data Writers](data_writers.md)
- [Bundles Overview](bundles_overview.md)
