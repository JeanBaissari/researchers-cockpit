# Pipeline Data Loaders

> Feed data to Pipeline computations.

## Overview

PipelineLoaders provide data to the Pipeline engine. Different loaders handle different data sources: pricing data, fundamental data, event data, etc.

---

## PipelineLoader Base Class

```python
class zipline.pipeline.loaders.base.PipelineLoader
```

Interface that all loaders must implement.

### load_adjusted_array()

```python
loader.load_adjusted_array(domain, columns, dates, sids, mask)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `domain` | Domain | Pipeline's market domain |
| `columns` | list[BoundColumn] | Columns to load |
| `dates` | DatetimeIndex | Dates needed |
| `sids` | Int64Index | Asset IDs needed |
| `mask` | np.array[bool] | Tradability mask |

**Returns:** `dict[BoundColumn → AdjustedArray]`

---

## DataFrameLoader

```python
class zipline.pipeline.loaders.frame.DataFrameLoader(
    column, baseline, adjustments=None
)
```

Load pipeline data from pandas DataFrames. Useful for testing.

| Parameter | Type | Description |
|-----------|------|-------------|
| `column` | BoundColumn | Column this loader provides |
| `baseline` | DataFrame | DatetimeIndex rows, sid columns |
| `adjustments` | DataFrame | Optional adjustment data |

### Example

```python
from zipline.pipeline.loaders import DataFrameLoader

data = pd.DataFrame(
    np.random.randn(100, 50),
    index=pd.date_range('2020-01-01', periods=100, tz='UTC'),
    columns=range(50)  # sids
)

loader = DataFrameLoader(
    column=USEquityPricing.close,
    baseline=data
)
```

---

## EquityPricingLoader

```python
class zipline.pipeline.loaders.EquityPricingLoader(
    raw_price_reader, adjustments_reader, fx_reader
)
```

Load daily OHLCV data for equities. Alias: `USEquityPricingLoader`

| Parameter | Type | Description |
|-----------|------|-------------|
| `raw_price_reader` | SessionBarReader | Raw pricing data |
| `adjustments_reader` | SQLiteAdjustmentReader | Corporate actions |
| `fx_reader` | FXRateReader | Currency conversions |

---

## EventsLoader

```python
class zipline.pipeline.loaders.EventsLoader(
    events, next_value_columns, previous_value_columns
)
```

Load event-based data (earnings, buybacks).

### Required Event Columns

| Column | Type | Description |
|--------|------|-------------|
| `sid` | int64 | Asset ID |
| `event_date` | datetime64 | When event occurs |
| `timestamp` | datetime64 | When we learned about it |

---

## EarningsEstimatesLoader

```python
class zipline.pipeline.loaders.EarningsEstimatesLoader(estimates, name_map)
```

Load earnings estimates with fiscal quarter alignment.

### Required Columns

| Column | Description |
|--------|-------------|
| `sid` | Asset ID |
| `event_date` | Announcement date |
| `timestamp` | Estimate timestamp |
| `fiscal_quarter` | Quarter (1-4) |
| `fiscal_year` | Year |

---

## Loader Selection Pattern

```python
def get_loader(column):
    if column in USEquityPricing.columns:
        return equity_pricing_loader
    elif column in MyDataset.columns:
        return custom_loader
    raise ValueError(f"No loader for {column}")

engine = SimplePipelineEngine(
    get_loader=get_loader,
    asset_finder=finder
)
```

---

## See Also

- [Pipeline Engine](pipeline_engine.md)
- [Pipeline Overview](pipeline_overview.md)
