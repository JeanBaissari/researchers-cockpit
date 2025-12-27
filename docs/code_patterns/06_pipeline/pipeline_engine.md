# Pipeline Engine

> Computation engine for executing Pipeline expressions.

## Overview

The Pipeline Engine executes Pipeline computations efficiently across large asset universes. It handles dependency resolution, caching, and memory management.

---

## Execution Algorithm

1. **Determine domain** - Identify the pipeline's market domain
2. **Build dependency graph** - Map term dependencies and lookback windows
3. **Create lifetimes matrix** - DataFrame of (dates × assets) tradability
4. **Populate workspace** - Load cached/precomputed terms
5. **Topological sort** - Order terms for computation
6. **Execute terms** - Compute each term, manage memory
7. **Extract outputs** - Convert to narrow format per screen

---

## PipelineEngine Base Class

```python
class zipline.pipeline.engine.PipelineEngine
```

Abstract interface for pipeline computation.

### run_pipeline()

```python
engine.run_pipeline(pipeline, start_date, end_date, hooks=None)
```

Compute pipeline values over a date range.

| Parameter | Type | Description |
|-----------|------|-------------|
| `pipeline` | Pipeline | The pipeline to execute |
| `start_date` | Timestamp | Start of computation window |
| `end_date` | Timestamp | End of computation window |
| `hooks` | list | Optional instrumentation hooks |

**Returns:** `pd.DataFrame` with MultiIndex (date, asset)

### run_chunked_pipeline()

```python
engine.run_chunked_pipeline(
    pipeline, start_date, end_date, chunksize, hooks=None
)
```

Execute pipeline in date chunks to reduce memory usage.

| Parameter | Type | Description |
|-----------|------|-------------|
| `chunksize` | int | Days per chunk |

---

## SimplePipelineEngine

```python
class zipline.pipeline.engine.SimplePipelineEngine(
    get_loader,
    asset_finder,
    default_domain=GENERIC,
    populate_initial_workspace=None,
    default_hooks=None
)
```

Standard implementation computing terms independently.

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `get_loader` | callable | Returns PipelineLoader for a term |
| `asset_finder` | AssetFinder | Asset metadata interface |
| `default_domain` | Domain | Default market domain |
| `populate_initial_workspace` | callable | Workspace initialization |
| `default_hooks` | list | Default instrumentation |

### Example Setup

```python
from zipline.pipeline.engine import SimplePipelineEngine
from zipline.pipeline.loaders import USEquityPricingLoader

def get_loader(column):
    if column in USEquityPricing.columns:
        return USEquityPricingLoader(
            bundle_data.equity_daily_bar_reader,
            bundle_data.adjustment_reader,
            None
        )
    raise ValueError(f"No loader for {column}")

engine = SimplePipelineEngine(
    get_loader=get_loader,
    asset_finder=bundle_data.asset_finder
)
```

---

## Running Pipelines Standalone

```python
# Outside of algorithm context
from zipline.pipeline import Pipeline
from zipline.pipeline.factors import Returns

pipeline = Pipeline(
    columns={'returns': Returns(window_length=20)},
    screen=Returns(window_length=20).top(100)
)

result = engine.run_pipeline(
    pipeline,
    start_date=pd.Timestamp('2020-01-01', tz='UTC'),
    end_date=pd.Timestamp('2020-12-31', tz='UTC')
)
```

---

## Chunked Execution

For memory-intensive pipelines:

```python
# Process 30 days at a time
result = engine.run_chunked_pipeline(
    pipeline,
    start_date=pd.Timestamp('2015-01-01', tz='UTC'),
    end_date=pd.Timestamp('2020-12-31', tz='UTC'),
    chunksize=30
)
```

---

## default_populate_initial_workspace()

```python
zipline.pipeline.engine.default_populate_initial_workspace(
    initial_workspace,
    root_mask_term,
    execution_plan,
    dates,
    assets
)
```

Default workspace initialization (returns workspace unchanged).

Custom implementations can pre-populate cached terms:

```python
def custom_workspace(workspace, root_mask, plan, dates, assets):
    # Add pre-computed data
    workspace[MyCustomTerm()] = precomputed_array
    return workspace

engine = SimplePipelineEngine(
    get_loader=get_loader,
    asset_finder=finder,
    populate_initial_workspace=custom_workspace
)
```

---

## Performance Tips

1. **Use chunked execution** for multi-year backtests
2. **Apply screens early** to reduce computation
3. **Use masks** on expensive factors
4. **Cache CustomFactor results** when possible
5. **Profile with hooks** to identify bottlenecks

---

## See Also

- [Pipeline Overview](pipeline_overview.md)
- [Data Loaders](data_loaders.md)
- [Custom Factors](custom_factors.md)
