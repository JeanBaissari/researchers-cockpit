# Bundle Data Schemas

## Daily OHLCV DataFrame

Required format for `daily_bar_writer.write()`:

```
Index: DatetimeIndex (UTC timezone)
Columns:
  - open: float64 (opening price)
  - high: float64 (highest price)
  - low: float64 (lowest price)
  - close: float64 (closing price)
  - volume: int64 (trading volume)
```

Example:
```python
pd.DataFrame({
    'open': [100.0, 101.0, 102.0],
    'high': [101.5, 102.5, 103.0],
    'low': [99.5, 100.5, 101.0],
    'close': [101.0, 102.0, 102.5],
    'volume': [1000000, 1200000, 900000]
}, index=pd.DatetimeIndex(['2024-01-02', '2024-01-03', '2024-01-04'], tz='UTC'))
```

## Asset Metadata DataFrame

Required format for `asset_db_writer.write(equities=df)`:

```
Index: int64 (sid - security identifier)
Required Columns:
  - symbol: str (ticker symbol)
  - asset_name: str (full company name)
  - start_date: datetime64[ns] (first trading date)
  - end_date: datetime64[ns] (last trading date)
  - exchange: str (exchange name)

Optional Columns:
  - auto_close_date: datetime64[ns] (default: end_date + 1 day)
  - tick_size: float (minimum price increment)
```

## Splits DataFrame

Required format for `adjustment_writer.write(splits=df)`:

```
Columns:
  - sid: int64 (security identifier)
  - effective_date: datetime64[ns] (split date)
  - ratio: float64 (split ratio, e.g., 2.0 for 2:1 split)
```

## Dividends DataFrame

Required format for `adjustment_writer.write(dividends=df)`:

```
Columns:
  - sid: int64 (security identifier)
  - ex_date: datetime64[ns] (ex-dividend date)
  - declared_date: datetime64[ns] (announcement date)
  - pay_date: datetime64[ns] (payment date)
  - record_date: datetime64[ns] (record date)
  - amount: float64 (dividend per share)
```

## CSV File Format

For `csvdir_equities` bundle:

```csv
date,open,high,low,close,volume,dividend,split
2024-01-02,100.00,101.50,99.50,101.00,1000000,0.0,1.0
2024-01-03,101.00,102.50,100.50,102.00,1200000,0.0,1.0
```

File naming: `{symbol}.csv` (lowercase), e.g., `aapl.csv`, `msft.csv`
