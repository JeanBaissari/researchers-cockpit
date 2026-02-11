# Zipline-Reloaded Pipeline System Inventory

> Comprehensive catalog of Pipeline capabilities, components, and usage patterns for Zipline-Reloaded v3.0+

**Source:** [stefan-jansen/zipline-reloaded](https://github.com/stefan-jansen/zipline-reloaded)  
**Version:** Zipline-Reloaded v3.0+  
**Last Updated:** 2026-01-27 (Enhanced)

---

## Table of Contents

1. [Core Components](#core-components)
2. [Built-in Factors](#built-in-factors)
3. [Built-in Filters](#built-in-filters)
4. [Common Filters: AllPresent, isnan, notnan](#common-filters-allpresent-isnan-notnan)
5. [Pipeline API Functions](#pipeline-api-functions)
6. [Factor Methods](#factor-methods)
7. [Filter Operations](#filter-operations)
8. [Data Sources](#data-sources)
9. [Custom Factor Creation](#custom-factor-creation)
10. [Classifiers](#classifiers)
11. [Domains](#domains)
12. [Pipeline Engine](#pipeline-engine)
13. [Data Loaders](#data-loaders)
14. [Usage Patterns](#usage-patterns)
15. [Best Practices](#best-practices)
16. [Advanced Performance Tips](#advanced-performance-tips)

---

## Core Components

### Pipeline Class

```python
from zipline.pipeline import Pipeline

Pipeline(columns=None, screen=None, domain=GENERIC)
```

**Parameters:**
- `columns` (dict): Named expressions to compute (factors, filters, classifiers)
- `screen` (Filter): Assets to include in output (reduces output size)
- `domain` (Domain): Asset universe domain (default: GENERIC)

**Purpose:** Container for Pipeline computations that executes before each trading day.

### Term Types

| Term Type | Output Type | Description | Common Uses |
|-----------|-------------|-------------|-------------|
| **Factor** | Numeric (float64) | Produces numeric values for each asset/date pair | Moving averages, ratios, rankings |
| **Filter** | Boolean | Produces boolean values for each asset/date pair | Screening assets, combining conditions |
| **Classifier** | Categorical | Produces categorical or integer values for each asset/date pair | Sector/industry classification, grouping |

**Base Classes:**
- `zipline.pipeline.Factor`
- `zipline.pipeline.Filter`
- `zipline.pipeline.Classifier`
- `zipline.pipeline.Term` (base class for all terms)

---

## Built-in Factors

### Price/Volume Factors

#### Returns
```python
from zipline.pipeline.factors import Returns

returns_20d = Returns(window_length=20)
returns_5d = Returns(window_length=5)
```
**Purpose:** Price returns over a window.  
**Input:** EquityPricing (defaults to close)  
**Output:** Float64 returns

#### AverageDollarVolume
```python
from zipline.pipeline.factors import AverageDollarVolume

adv = AverageDollarVolume(window_length=20)
```
**Purpose:** Average dollar volume over a window.  
**Common Use:** Liquidity screening (`adv.top(500)`)

#### VWAP
```python
from zipline.pipeline.factors import VWAP

vwap = VWAP(window_length=20)
```
**Purpose:** Volume-weighted average price.

#### AnnualizedVolatility
```python
from zipline.pipeline.factors import AnnualizedVolatility

vol = AnnualizedVolatility(window_length=20)
vol_monthly = AnnualizedVolatility(window_length=20, annualization_factor=12)
```
**Purpose:** Annualized return volatility.  
**Default:** 252 trading days annualization

#### AverageDailyVolume
```python
from zipline.pipeline.factors import AverageDailyVolume

avg_vol = AverageDailyVolume(window_length=20)
```
**Purpose:** Average daily volume (shares, not dollar volume).

### Technical Indicators

#### SimpleMovingAverage
```python
from zipline.pipeline.factors import SimpleMovingAverage

sma_20 = SimpleMovingAverage(inputs=[EquityPricing.close], window_length=20)
sma_50 = SimpleMovingAverage(inputs=[EquityPricing.close], window_length=50)
```
**Purpose:** Simple moving average of price data.

#### ExponentialWeightedMovingAverage
```python
from zipline.pipeline.factors import ExponentialWeightedMovingAverage

ewma = ExponentialWeightedMovingAverage(
    inputs=[EquityPricing.close],
    window_length=20,
    decay_rate=0.1
)
```
**Purpose:** Exponentially weighted moving average.

#### ExponentialWeightedMovingStdDev
```python
from zipline.pipeline.factors import ExponentialWeightedMovingStdDev

ewmstd = ExponentialWeightedMovingStdDev(
    inputs=[EquityPricing.close],
    window_length=20,
    decay_rate=0.1
)
```
**Purpose:** Exponentially weighted moving standard deviation.

#### BollingerBands
```python
from zipline.pipeline.factors import BollingerBands

bb = BollingerBands(window_length=20, k=2)
middle = bb.middle
upper = bb.upper
lower = bb.lower
```
**Purpose:** Bollinger Bands indicator with middle, upper, and lower bands.

#### Aroon
```python
from zipline.pipeline.factors import Aroon

aroon = Aroon(window_length=25)
aroon_up = aroon.up
aroon_down = aroon.down
```
**Purpose:** Aroon indicator (up and down components).

#### FastStochasticOscillator
```python
from zipline.pipeline.factors import FastStochasticOscillator

stoch = FastStochasticOscillator(window_length=14)
```
**Purpose:** Fast stochastic oscillator.

#### IchimokuKinkoHyo
```python
from zipline.pipeline.factors import IchimokuKinkoHyo

ichimoku = IchimokuKinkoHyo()
tenkan = ichimoku.tenkan_sen
kijun = ichimoku.kijun_sen
senkou_a = ichimoku.senkou_span_a
senkou_b = ichimoku.senkou_span_b
chikou = ichimoku.chikou_span
```
**Purpose:** Ichimoku Kinko Hyo indicator with multiple components.

#### RateOfChangePercentage
```python
from zipline.pipeline.factors import RateOfChangePercentage

roc = RateOfChangePercentage(window_length=10)
```
**Purpose:** Rate of change percentage.

#### TrueRange
```python
from zipline.pipeline.factors import TrueRange

tr = TrueRange()
```
**Purpose:** True Range indicator (requires high, low, close).

#### MaxDrawdown
```python
from zipline.pipeline.factors import MaxDrawdown

mdd = MaxDrawdown(window_length=252)
```
**Purpose:** Maximum drawdown over a window.

### Statistical Factors

#### RollingPearsonOfReturns
```python
from zipline.pipeline.factors import RollingPearsonOfReturns
from zipline.api import symbol

spy = symbol('SPY')
correlation = RollingPearsonOfReturns(
    target=spy,
    returns_length=10,
    correlation_length=30
)
```
**Purpose:** Correlation with target asset (Pearson).

#### RollingSpearmanOfReturns
```python
from zipline.pipeline.factors import RollingSpearmanOfReturns

spearman = RollingSpearmanOfReturns(
    target=symbol('SPY'),
    returns_length=10,
    correlation_length=30
)
```
**Purpose:** Rank correlation with target asset (Spearman).

#### RollingLinearRegressionOfReturns
```python
from zipline.pipeline.factors import RollingLinearRegressionOfReturns

regression = RollingLinearRegressionOfReturns(
    target=symbol('SPY'),
    returns_length=10,
    regression_length=30
)

alpha = regression.alpha
beta = regression.beta
r_value = regression.r_value
p_value = regression.p_value
stderr = regression.stderr
```
**Purpose:** Beta and alpha vs target asset with regression statistics.

---

## Built-in Filters

### Asset Selection Filters

#### StaticAssets
```python
from zipline.pipeline.filters import StaticAssets
from zipline.api import symbols

my_universe = symbols('AAPL', 'MSFT', 'GOOGL', 'AMZN')
static_filter = StaticAssets(my_universe)
```
**Purpose:** Filter to a fixed set of assets.

#### StaticSids
```python
from zipline.pipeline.filters import StaticSids

known_sids = [24, 8554, 5061]  # AAPL, SPY, etc.
sid_filter = StaticSids(known_sids)
```
**Purpose:** Filter to a fixed set of security IDs.

### Universe Filters

#### QTradableStocksUS
```python
from zipline.pipeline.filters import QTradableStocksUS

universe = QTradableStocksUS()
```
**Purpose:** Filter for liquid, tradeable US equities (data-dependent).

#### Q500US / Q1500US / Q3000US
```python
from zipline.pipeline.filters import Q500US

universe = Q500US()
```
**Purpose:** Pre-defined universes of top US stocks by market cap (data-dependent).

**Note:** These filters require appropriate fundamental data to be available.

### Common Filters: AllPresent, isnan, notnan

This section shows **runtime** filters for column availability and missing-data handling. Use these in Pipeline screens or masks; for pre-ingestion data quality, use `lib/validation/` instead (see [filters_vs_validators](../../code_patterns/filters_vs_validators.md)).

#### AllPresent

`AllPresent` (Zipline-Reloaded) restricts the Pipeline to assets/dates where **all** specified columns have non-missing values. Use it when a factor uses multiple inputs (e.g. OHLC) and you want to exclude rows where any input is missing.

```python
from zipline.pipeline import Pipeline
from zipline.pipeline.factors import SimpleMovingAverage
from zipline.pipeline.filters import AllPresent
from zipline.pipeline.data import EquityPricing

def make_pipeline():
    # Only include assets where close, high, low all have data (no missing inputs)
    all_present = AllPresent(
        inputs=[EquityPricing.close, EquityPricing.high, EquityPricing.low]
    )
    sma = SimpleMovingAverage(inputs=[EquityPricing.close], window_length=20)
    return Pipeline(
        columns={'sma': sma},
        screen=all_present
    )
```

**Notes:**

- **Column availability:** Assets or dates with missing data in any of `inputs` are filtered out before downstream factors run.
- **Typical use:** Multi-column factors (e.g. TrueRange, Bollinger from OHLC) or when you need full OHLCV for the screen.
- **API:** See Zipline-Reloaded [pipeline filters](https://github.com/stefan-jansen/zipline-reloaded) for optional `mask` and exact signature in your version.

#### isnan() / notnan()

Factor methods that return a **Filter** indicating where values are NaN or not. Use them to screen out (or restrict to) assets with missing factor output.

```python
from zipline.pipeline import Pipeline
from zipline.pipeline.factors import Returns, SimpleMovingAverage
from zipline.pipeline.data import EquityPricing

def make_pipeline():
    returns_20 = Returns(window_length=20)
    sma_30 = SimpleMovingAverage(inputs=[EquityPricing.close], window_length=30)

    # Exclude assets where returns or SMA is NaN (e.g. insufficient history)
    valid_returns = returns_20.notnan()
    valid_sma = sma_30.notnan()
    screen = valid_returns & valid_sma

    return Pipeline(
        columns={'returns': returns_20, 'sma': sma_30},
        screen=screen
    )
```

**Exclude NaNs (common):**

```python
valid = factor.notnan()   # True where value is not NaN → use as screen to keep only valid
missing = factor.isnan()  # True where value is NaN → use to drop or mask
```

**Notes:**

- **Missing data behavior:** Factors can produce NaN for insufficient history, missing inputs, or division-by-zero. Using `.notnan()` in the screen avoids passing NaNs into ordering or ranking logic.
- **Column availability:** `.notnan()`/`.isnan()` apply to the factor’s **output**. For requiring non-missing **inputs** across multiple columns, use `AllPresent` (see above).

---

## Pipeline API Functions

### attach_pipeline()

```python
from zipline.api import attach_pipeline

attach_pipeline(pipeline, name, chunks=None, eager=True)
```

**Parameters:**
- `pipeline` (Pipeline): Pipeline to attach
- `name` (str): Name for retrieval
- `chunks` (int, optional): Days to compute at once
- `eager` (bool): Compute before `before_trading_start` (default: True)

**Returns:** The same Pipeline object.

**Usage:**
```python
def initialize(context):
    attach_pipeline(make_pipeline(), 'my_pipeline')
```

### pipeline_output()

```python
from zipline.api import pipeline_output

output = pipeline_output(name)
```

**Parameters:**
- `name` (str): Pipeline name

**Returns:** `pd.DataFrame` - Results for current day. Index is assets, columns are factor names.

**Raises:** `NoSuchPipeline` - Pipeline name not found.

**Usage:**
```python
def before_trading_start(context, data):
    output = pipeline_output('my_pipeline')
    # output.index = assets
    # output.columns = ['volume', 'returns']
    context.longs = output[output['returns'] > 0].index.tolist()
```

---

## Factor Methods

### Ranking & Normalization

#### rank()
```python
factor.rank(method='ordinal', ascending=True, mask=NotSpecified, groupby=NotSpecified)
```
**Purpose:** Convert to cross-sectional ranks.  
**Example:** `ranked = momentum.rank(ascending=False)`

#### zscore()
```python
factor.zscore(mask=NotSpecified, groupby=NotSpecified)
```
**Purpose:** Normalize to z-scores (mean=0, std=1).  
**Example:** `normalized = momentum.zscore()`

#### demean()
```python
factor.demean(mask=NotSpecified, groupby=NotSpecified)
```
**Purpose:** Subtract cross-sectional mean.  
**Example:** `demeaned = momentum.demean()`

### Selection Methods

#### top() / bottom()
```python
factor.top(N, mask=NotSpecified, groupby=NotSpecified)
factor.bottom(N, mask=NotSpecified, groupby=NotSpecified)
```
**Purpose:** Select top or bottom N assets. **Returns Filter.**  
**Example:** `top_100 = volume.top(100)`

#### percentile_between()
```python
factor.percentile_between(min_percentile, max_percentile, mask=NotSpecified)
```
**Purpose:** Select assets in percentile range. **Returns Filter.**  
**Example:** `mid_volume = volume.percentile_between(25, 75)`

### Missing Data Methods

#### isnull() / notnull()
```python
has_data = factor.notnull()  # Returns Filter
missing = factor.isnull()     # Returns Filter
```
**Purpose:** Check for missing values.

#### isnan() / notnan()
```python
valid = factor.notnan()  # Returns Filter
```
**Purpose:** Check for NaN values.

#### fillna()
```python
factor.fillna(fill_value)
factor.fillna(other_factor)
```
**Purpose:** Replace missing values.  
**Example:** `filled = momentum.fillna(0)`

### Data Transformation

#### clip()
```python
factor.clip(min_bound, max_bound)
```
**Purpose:** Clip values to range.  
**Example:** `clipped = momentum.clip(-0.5, 0.5)`

#### winsorize()
```python
factor.winsorize(min_percentile, max_percentile, mask=NotSpecified, groupby=NotSpecified)
```
**Purpose:** Clip to percentile boundaries.  
**Example:** `winsorized = momentum.winsorize(0.01, 0.99)`

### Mathematical Operations

#### Arithmetic
```python
combined = f1 + f2
difference = f1 - f2
product = f1 * f2
ratio = f1 / f2
average = (f1 + f2) / 2.0
```

#### Comparisons (Return Filters)
```python
filter1 = f1 > f2
filter2 = f1 >= 10.0
filter3 = f1.eq(f2)  # f1 == f2
filter4 = f1 != 0
```

---

## Filter Operations

### Boolean Operations

#### AND (&)
```python
tradeable = high_volume & positive_momentum
```
**Purpose:** Both conditions must be True.

#### OR (|)
```python
extreme = top_momentum | bottom_momentum
```
**Purpose:** Either condition can be True.

#### NOT (~)
```python
allowed = ~restricted
```
**Purpose:** Invert the filter.

#### Complex Combinations
```python
final_filter = (filter_a & filter_b) | (filter_c & ~filter_d)
```

### Conditional Selection

#### if_else()
```python
filter.if_else(if_true, if_false)
```
**Purpose:** Select values based on filter condition.  
**Parameters:**
- `if_true` (Term): Value when True
- `if_false` (Term): Value when False

**Example:**
```python
high_vol = volume > 1000000
alpha = high_vol.if_else(momentum_factor, value_factor)
```

### Using Filters

#### As Screen
```python
return Pipeline(
    columns={'volume': volume},
    screen=liquid  # Reduces output to 500 rows
)
```

#### As Mask
```python
momentum_rank = momentum.rank(mask=liquid)
top_momentum = momentum.top(50, mask=liquid)
```

---

## Data Sources

### EquityPricing / USEquityPricing

```python
from zipline.pipeline.data import EquityPricing  # Zipline-Reloaded 3.x
from zipline.pipeline.data import USEquityPricing  # Legacy compatibility

# Available columns:
EquityPricing.open
EquityPricing.high
EquityPricing.low
EquityPricing.close
EquityPricing.volume

# Latest values:
EquityPricing.close.latest
EquityPricing.volume.latest
```

**Purpose:** OHLCV pricing data for equities.  
**Note:** Zipline-Reloaded 3.x uses `EquityPricing` (generic), legacy code may use `USEquityPricing`.

### Custom Data Sources

Pipeline supports custom data sources through:
- Custom `Dataset` classes
- Custom `BoundColumn` definitions
- Custom `PipelineLoader` implementations

**See:** `docs/archive/code_patterns/06_pipeline/data_loaders.md`

---

## Custom Factor Creation

### CustomFactor Class

```python
from zipline.pipeline import CustomFactor
from zipline.pipeline.data import EquityPricing
import numpy as np

class MyFactor(CustomFactor):
    inputs = [EquityPricing.close]
    window_length = 20
    
    def compute(self, today, assets, out, close):
        # close.shape = (window_length, num_assets)
        # out.shape = (num_assets,)
        out[:] = np.mean(close, axis=0)
```

### Key Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `inputs` | list | BoundColumns to use as inputs |
| `window_length` | int | Number of bars to look back |
| `outputs` | list | Output names (for multiple outputs) |
| `dtype` | np.dtype | Output data type (default: float64) |
| `params` | dict | Custom parameters |

### compute() Method Signature

```python
def compute(self, today, assets, out, *inputs):
    """
    Parameters
    ----------
    today : pd.Timestamp
        Current simulation date
    assets : np.ndarray
        Array of asset sids
    out : np.ndarray
        Output array to fill (shape: num_assets,)
    *inputs : np.ndarray
        One array per input (shape: window_length x num_assets)
    """
    pass
```

### Multiple Outputs

```python
class BollingerBands(CustomFactor):
    inputs = [EquityPricing.close]
    window_length = 20
    outputs = ['middle', 'upper', 'lower']
    
    def compute(self, today, assets, out, close):
        mean = np.nanmean(close, axis=0)
        std = np.nanstd(close, axis=0)
        
        out.middle[:] = mean
        out.upper[:] = mean + 2 * std
        out.lower[:] = mean - 2 * std

# Usage
bb = BollingerBands()
middle = bb.middle
upper = bb.upper
lower = bb.lower
```

---

## Usage Patterns

### Momentum Strategy

```python
from zipline.pipeline import Pipeline
from zipline.pipeline.factors import Returns, AverageDollarVolume

def make_pipeline():
    momentum = Returns(window_length=20)
    volume = AverageDollarVolume(window_length=20)
    
    liquid = volume.top(500)
    
    longs = momentum.top(50, mask=liquid)
    shorts = momentum.bottom(50, mask=liquid)
    
    return Pipeline(
        columns={
            'momentum': momentum,
            'longs': longs,
            'shorts': shorts,
        },
        screen=longs | shorts
    )
```

### Mean Reversion

```python
def make_pipeline():
    close = EquityPricing.close.latest
    sma = SimpleMovingAverage(inputs=[EquityPricing.close], window_length=20)
    volume = AverageDollarVolume(window_length=20)
    
    # Distance from mean
    deviation = (close - sma) / sma
    
    liquid = volume.top(500)
    
    # Buy oversold, sell overbought
    oversold = deviation.bottom(50, mask=liquid)
    overbought = deviation.top(50, mask=liquid)
    
    return Pipeline(
        columns={
            'deviation': deviation,
            'longs': oversold,
            'shorts': overbought,
        }
    )
```

### Multi-Factor Model

```python
def make_pipeline():
    momentum = Returns(window_length=20)
    volume = AverageDollarVolume(window_length=20)
    
    # Normalize factors
    momentum_z = momentum.zscore()
    volume_z = volume.zscore()
    
    # Combine (simple alpha)
    alpha = 0.7 * momentum_z + 0.3 * volume_z
    
    # Filters
    liquid = volume.top(1000)
    valid = momentum.notnull() & volume.notnull()
    
    # Top 50 by combined alpha
    longs = alpha.top(50, mask=liquid & valid)
    shorts = alpha.bottom(50, mask=liquid & valid)
    
    return Pipeline(
        columns={
            'alpha': alpha,
            'momentum': momentum,
            'volume': volume,
            'longs': longs,
            'shorts': shorts,
        },
        screen=liquid & valid
    )
```

### Sector Neutral

```python
def make_pipeline():
    alpha = SomeAlphaFactor()
    sector = SectorClassifier()  # Custom classifier
    volume = AverageDollarVolume(window_length=20)
    universe = volume.top(500)
    
    # Top 5 per sector
    longs = alpha.top(5, mask=universe, groupby=sector)
    
    return Pipeline(
        columns={'longs': longs},
        screen=longs
    )
```

### Universe Definition

```python
def make_pipeline():
    volume = AverageDollarVolume(window_length=20)
    price = EquityPricing.close.latest
    
    # Liquid + priced reasonably
    liquid = volume.top(1500)
    priced_ok = (price > 5) & (price < 1000)
    has_data = volume.notnull() & price.notnull()
    
    universe = liquid & priced_ok & has_data
    
    return Pipeline(screen=universe)
```

---

## Best Practices

### 1. Leverage for Universe Selection

Use Pipeline to efficiently filter a large universe of assets down to a manageable watchlist based on fundamental or technical criteria.

### 2. Factor Pre-computation

All computationally intensive factor calculations should be done in the Pipeline to avoid re-calculating them inside `handle_data` or `before_trading_start`.

### 3. Cross-sectional Analysis

Pipeline excels at cross-sectional comparisons (e.g., top N stocks by momentum, relative valuation) which are difficult to do efficiently otherwise.

### 4. Keep it Focused

Each pipeline should serve a specific purpose (e.g., liquidity screening, momentum calculation).

### 5. Optimize Factors

Use built-in factors whenever possible, and optimize custom factors for performance.

### 6. Clear Naming

Use descriptive names for your pipeline and its columns.

### 7. Testing

Thoroughly test your pipeline logic in isolation before integrating into a strategy.

### 8. Asset Class Compatibility

**Important:** Pipeline API is primarily designed for **US equities** with proper metadata. For crypto/forex strategies, consider using direct price data (`data.history()`, `data.current()`) instead.

### 9. Always Check Pipeline State

```python
def before_trading_start(context, data):
    if context.use_pipeline and context.pipeline_data is not None:
        # Use pipeline data
        pass
    else:
        # Fall back to direct data access
        pass
```

### 10. Handle Pipeline Errors Gracefully

```python
def before_trading_start(context, data):
    if context.use_pipeline:
        try:
            context.pipeline_data = pipeline_output('my_pipeline')
        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            context.pipeline_data = None
            # Continue with fallback logic
```

---

## Classifiers

### Overview

Classifiers produce categorical or integer values for each asset/date pair. They're used for grouping assets (e.g., by sector, industry) and enabling groupby operations in factors.

### CustomClassifier Class

```python
from zipline.pipeline import CustomClassifier
from zipline.pipeline.data import EquityPricing

class SectorClassifier(CustomClassifier):
    inputs = [EquityPricing.close]  # Can use any data source
    dtype = int64  # or object for string categories
    
    def compute(self, today, assets, out, *inputs):
        # out.shape = (num_assets,)
        # Assign category values to out array
        out[:] = assign_sectors(assets, today)
```

### Using Classifiers with groupby

```python
from zipline.pipeline.factors import Returns

momentum = Returns(window_length=20)
sector = SectorClassifier()

# Rank within each sector
sector_rank = momentum.rank(groupby=sector)

# Z-score within each sector
sector_zscore = momentum.zscore(groupby=sector)

# Top 5 per sector
top_per_sector = momentum.top(5, mask=universe, groupby=sector)
```

### Sector-Neutral Strategy Example

```python
def make_pipeline():
    alpha = SomeAlphaFactor()
    sector = SectorClassifier()
    volume = AverageDollarVolume(window_length=20)
    universe = volume.top(500)
    
    # Top 5 per sector (sector-neutral selection)
    longs = alpha.top(5, mask=universe, groupby=sector)
    
    return Pipeline(
        columns={
            'alpha': alpha,
            'sector': sector,
            'longs': longs,
        },
        screen=longs
    )
```

**Purpose:** Classifiers enable sector-neutral, industry-neutral, or other grouped strategies by allowing factor operations within categories.

---

## Domains

### Overview

Domains define the asset universe and trading calendar for a Pipeline. They ensure proper calendar alignment and asset metadata handling.

### Built-in Domains

```python
from zipline.pipeline.domain import (
    GENERIC,           # Generic domain (default)
    US_EQUITIES,       # US equities domain
    CA_EQUITIES,       # Canadian equities domain
    GB_EQUITIES,       # UK equities domain
    # ... other country-specific domains
)

# Use in Pipeline
pipeline = Pipeline(
    columns={'momentum': Returns(window_length=20)},
    domain=US_EQUITIES  # Explicitly set domain
)
```

### Domain Purpose

- **Calendar Alignment:** Ensures Pipeline uses correct trading calendar
- **Asset Metadata:** Provides proper asset finder and metadata
- **Data Source Mapping:** Maps to appropriate data loaders

### Default Domain

If no domain is specified, Pipeline uses `GENERIC` domain:

```python
# These are equivalent:
pipeline1 = Pipeline(columns={...})
pipeline2 = Pipeline(columns={...}, domain=GENERIC)
```

**Note:** For US equity strategies, explicitly use `US_EQUITIES` domain for proper calendar and metadata handling.

---

## Pipeline Engine

### Overview

The Pipeline Engine executes Pipeline computations efficiently. It handles dependency resolution, caching, and memory management.

### SimplePipelineEngine

```python
from zipline.pipeline.engine import SimplePipelineEngine
from zipline.pipeline.loaders import EquityPricingLoader

def get_loader(column):
    if column in EquityPricing.columns:
        return EquityPricingLoader(
            bundle_data.equity_daily_bar_reader,
            bundle_data.adjustment_reader,
            None  # FX reader (optional)
        )
    raise ValueError(f"No loader for {column}")

engine = SimplePipelineEngine(
    get_loader=get_loader,
    asset_finder=bundle_data.asset_finder
)
```

### Standalone Pipeline Execution

Execute pipelines outside of algorithm context:

```python
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

# result is DataFrame with MultiIndex (date, asset)
# result.columns = ['returns']
```

### Chunked Execution

For memory-intensive pipelines or long date ranges:

```python
# Process 30 days at a time
result = engine.run_chunked_pipeline(
    pipeline,
    start_date=pd.Timestamp('2015-01-01', tz='UTC'),
    end_date=pd.Timestamp('2020-12-31', tz='UTC'),
    chunksize=30  # Days per chunk
)
```

**Benefits:**
- Reduced memory usage
- Better for multi-year backtests
- Prevents out-of-memory errors

### Execution Algorithm

1. **Determine domain** - Identify the pipeline's market domain
2. **Build dependency graph** - Map term dependencies and lookback windows
3. **Create lifetimes matrix** - DataFrame of (dates × assets) tradability
4. **Populate workspace** - Load cached/precomputed terms
5. **Topological sort** - Order terms for computation
6. **Execute terms** - Compute each term, manage memory
7. **Extract outputs** - Convert to narrow format per screen

---

## Data Loaders

### Overview

PipelineLoaders provide data to the Pipeline engine. Different loaders handle different data sources: pricing data, fundamental data, event data, etc.

### PipelineLoader Interface

```python
class PipelineLoader:
    def load_adjusted_array(self, domain, columns, dates, sids, mask):
        """
        Load data for Pipeline computation.
        
        Parameters:
        - domain: Pipeline's market domain
        - columns: List of BoundColumns to load
        - dates: DatetimeIndex of dates needed
        - sids: Int64Index of asset IDs needed
        - mask: Boolean array for tradability
        
        Returns:
        - dict[BoundColumn → AdjustedArray]
        """
        pass
```

### EquityPricingLoader

Load daily OHLCV data for equities:

```python
from zipline.pipeline.loaders import EquityPricingLoader

loader = EquityPricingLoader(
    raw_price_reader=bundle_data.equity_daily_bar_reader,
    adjustments_reader=bundle_data.adjustment_reader,
    fx_reader=None  # Optional FX rate reader
)
```

### DataFrameLoader

Load pipeline data from pandas DataFrames (useful for testing):

```python
from zipline.pipeline.loaders import DataFrameLoader

data = pd.DataFrame(
    np.random.randn(100, 50),
    index=pd.date_range('2020-01-01', periods=100, tz='UTC'),
    columns=range(50)  # sids
)

loader = DataFrameLoader(
    column=EquityPricing.close,
    baseline=data
)
```

### EventsLoader

Load event-based data (earnings, buybacks):

```python
from zipline.pipeline.loaders import EventsLoader

loader = EventsLoader(
    events=earnings_events_df,
    next_value_columns=[EarningsEstimates.eps_estimate],
    previous_value_columns=[]
)
```

**Required Event Columns:**
- `sid` (int64): Asset ID
- `event_date` (datetime64): When event occurs
- `timestamp` (datetime64): When we learned about it

### Custom Loaders

Create custom loaders for proprietary data sources:

```python
class MyCustomLoader(PipelineLoader):
    def load_adjusted_array(self, domain, columns, dates, sids, mask):
        # Load your custom data
        data = load_my_data(dates, sids)
        return {column: AdjustedArray(data, ...) for column in columns}
```

### Loader Selection Pattern

```python
def get_loader(column):
    if column in EquityPricing.columns:
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

## Advanced Performance Tips

### 1. Use Chunked Execution

For multi-year backtests, use `run_chunked_pipeline()`:

```python
result = engine.run_chunked_pipeline(
    pipeline,
    start_date=start,
    end_date=end,
    chunksize=30  # Adjust based on memory
)
```

### 2. Apply Screens Early

Screens reduce computation by limiting assets:

```python
# Good: Screen early
liquid = volume.top(500)
momentum = Returns(window_length=20, mask=liquid)

# Less efficient: Compute for all assets first
momentum = Returns(window_length=20)
liquid = volume.top(500)
```

### 3. Use Masks on Expensive Factors

Apply masks to reduce computation:

```python
# Only compute for liquid stocks
expensive_factor = CustomFactor(
    inputs=[...],
    window_length=252,
    mask=liquid  # Reduces computation
)
```

### 4. Cache CustomFactor Results

When possible, cache expensive custom factor results:

```python
class CachedFactor(CustomFactor):
    # Use workspace caching if available
    pass
```

### 5. Reuse Terms

Avoid redundant calculations by reusing terms:

```python
# Good: Reuse
momentum = Returns(window_length=20)
longs = momentum.top(50)
shorts = momentum.bottom(50)

# Less efficient: Recompute
longs = Returns(window_length=20).top(50)
shorts = Returns(window_length=20).bottom(50)
```

### 6. Profile with Hooks

Use instrumentation hooks to identify bottlenecks:

```python
from zipline.pipeline.hooks import ProgressHooks

hooks = [ProgressHooks()]
result = engine.run_pipeline(
    pipeline,
    start_date=start,
    end_date=end,
    hooks=hooks
)
```

### 7. Monitor Reference Counts

For complex pipelines, monitor memory usage and reference counts to optimize.

---

## Integration with Project

### Using lib.pipeline_utils

This project provides `lib.pipeline_utils` for Pipeline setup:

```python
from lib.pipeline_utils import setup_pipeline

def initialize(context):
    params = load_strategy_params('my_strategy')
    context.use_pipeline = setup_pipeline(context, params, make_pipeline)
```

**See:** `docs/api/pipeline_utils.md` for complete API documentation.

### Strategy Template Pattern

```python
# In strategies/_template/strategy.py
from lib.pipeline_utils import setup_pipeline

def make_pipeline():
    """Create pipeline if use_pipeline: true in parameters.yaml"""
    from zipline.pipeline import Pipeline
    from zipline.pipeline.factors import SimpleMovingAverage
    from zipline.pipeline.data import EquityPricing
    
    sma = SimpleMovingAverage(
        inputs=[EquityPricing.close],
        window_length=30
    )
    return Pipeline(columns={'sma_30': sma})

def initialize(context):
    params = load_strategy_params('my_strategy')
    context.use_pipeline = setup_pipeline(context, params, make_pipeline)
```

---

## References

### Official Documentation

- [Zipline-Reloaded Repository](https://github.com/stefan-jansen/zipline-reloaded)
- [Zipline Pipeline Documentation](https://zipline.ml4trading.io/pipeline.html)

### Project Documentation

- `docs/api/pipeline_utils.md` - Pipeline utilities API
- `docs/archive/code_patterns/06_pipeline/` - Pipeline code patterns
- `lib/pipeline_utils.py` - Pipeline setup utilities
- `strategies/_template/strategy.py` - Strategy template with Pipeline example

### Related Components

- `lib/backtest/` - Backtest execution
- `lib/bundles/` - Data bundle management
- `lib/calendars/` - Trading calendar support

---

## Version History

- **2026-01-27**: Initial inventory created
- **2026-01-27**: Enhanced with Classifiers, Domains, Pipeline Engine, Data Loaders, and Advanced Performance Tips
- **Source**: Zipline-Reloaded v3.0+ (stefan-jansen/zipline-reloaded)
- **Status**: Complete inventory of Pipeline system capabilities

---

**Note:** This inventory is based on Zipline-Reloaded v3.0+. For legacy Quantopian zipline patterns, refer to migration guides. Always use Zipline-Reloaded patterns exclusively.
