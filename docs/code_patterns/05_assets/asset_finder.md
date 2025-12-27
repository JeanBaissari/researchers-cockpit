# AssetFinder

> Interface for looking up and querying asset metadata.

## Overview

AssetFinder provides methods to look up assets by symbol, SID, or other criteria. It's the backend for functions like `symbol()` and `symbols()`.

---

## AssetFinder Class

```python
class zipline.assets.AssetFinder(engine, future_chain_predicates=CHAIN_PREDICATES)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `engine` | Engine | SQLAlchemy engine for asset database |
| `future_chain_predicates` | dict | Predicates for future chain ordering |

---

## Lookup Methods

### retrieve_asset()

```python
finder.retrieve_asset(sid)
```

Get an asset by its unique security identifier.

```python
asset = finder.retrieve_asset(24)  # Returns Asset with sid=24
```

### lookup_symbol()

```python
finder.lookup_symbol(symbol, as_of_date, fuzzy=False)
```

Look up an equity by ticker symbol.

| Parameter | Type | Description |
|-----------|------|-------------|
| `symbol` | str | Ticker symbol |
| `as_of_date` | datetime | Date for symbol resolution |
| `fuzzy` | bool | Allow fuzzy matching |

```python
asset = finder.lookup_symbol('AAPL', pd.Timestamp('2020-01-01', tz='UTC'))
```

### retrieve_equities()

```python
finder.retrieve_equities(sids)
```

Get multiple equities by their SIDs.

```python
equities = finder.retrieve_equities([24, 8554, 5061])
# Returns dict: {24: Equity(...), 8554: Equity(...), ...}
```

### retrieve_futures_contracts()

```python
finder.retrieve_futures_contracts(sids)
```

Get multiple futures contracts by their SIDs.

---

## Query Properties

### equities_sids

```python
finder.equities_sids
```

Returns frozenset of all equity SIDs in the database.

### futures_sids

```python
finder.futures_sids
```

Returns frozenset of all futures SIDs in the database.

---

## Filtering Methods

### equities_sids_for_country_code()

```python
finder.equities_sids_for_country_code(country_code)
```

Get all equity SIDs for a specific country.

```python
us_sids = finder.equities_sids_for_country_code('US')
```

### equities_sids_for_exchange_name()

```python
finder.equities_sids_for_exchange_name(exchange_name)
```

Get all equity SIDs trading on a specific exchange.

```python
nyse_sids = finder.equities_sids_for_exchange_name('NYSE')
```

---

## Grouping Methods

### group_by_type()

```python
finder.group_by_type(sids)
```

Group SIDs by asset type (Equity, Future, etc.).

```python
grouped = finder.group_by_type([24, 8554, 1000])
# Returns: {Equity: [24, 8554], Future: [1000]}
```

---

## Lifetimes

### lifetimes()

```python
finder.lifetimes(dates, include_start_date, country_codes)
```

Get DataFrame of asset lifetimes (which assets trade on which dates).

| Parameter | Type | Description |
|-----------|------|-------------|
| `dates` | DatetimeIndex | Dates to check |
| `include_start_date` | bool | Include asset start date |
| `country_codes` | set | Filter by countries |

**Returns:** DataFrame with dates as index, SIDs as columns, boolean values.

---

## Examples

### Using with Bundle Data

```python
from zipline.data.bundles import load

bundle_data = load('quandl')
finder = bundle_data.asset_finder

# Look up specific asset
aapl = finder.lookup_symbol('AAPL', pd.Timestamp('2020-01-01', tz='UTC'))

# Get all US equities
us_equities = finder.equities_sids_for_country_code('US')
```

### Check Asset Existence

```python
def asset_exists(finder, symbol, date):
    try:
        asset = finder.lookup_symbol(symbol, date)
        return asset is not None
    except SymbolNotFound:
        return False
```

### Get Exchange Assets

```python
def get_exchange_universe(finder, exchange):
    sids = finder.equities_sids_for_exchange_name(exchange)
    return finder.retrieve_equities(list(sids))
```

---

## Exceptions

| Exception | Description |
|-----------|-------------|
| `SymbolNotFound` | Symbol not found on given date |
| `MultipleSymbolsFound` | Multiple assets match symbol |
| `SidsNotFound` | SID doesn't exist |

---

## Notes

- Symbol lookups are date-sensitive (tickers change over time)
- SIDs are stable identifiers that never change
- Use `set_symbol_lookup_date()` in algorithms to control lookup date
- AssetFinder is typically accessed via bundle data, not created directly

---

## See Also

- [Asset Lookup](asset_lookup.md)
- [Asset Types](asset_types.md)
- [Data Bundles](../08_data_bundles/bundles.md)
