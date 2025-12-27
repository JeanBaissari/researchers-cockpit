# Pipeline API Alignment

Fix the strategy template to work correctly with Zipline's Pipeline API across all asset classes.

## Problem Statement

The current `strategy.py` template uses `USEquityPricing` which is specific to US equities:

```python
from zipline.pipeline.data import USEquityPricing
# ...
sma_30 = SimpleMovingAverage(inputs=[USEquityPricing.close], window_length=30)
```

This will fail for crypto and forex backtests because:
1. `USEquityPricing` expects US equity-specific data columns
2. Crypto/Forex bundles use different data loaders that may not populate the same tables
3. The Pipeline screen assumes USEquityPricing is always valid

## Completed Tasks

(none yet)

## In Progress Tasks

- [ ] Research Zipline-Reloaded 3.1.0 Pipeline data sources
- [ ] Identify correct approach for multi-asset-class pipelines

## Future Tasks

### Strategy Template Updates
- [ ] Replace `USEquityPricing` with `EquityPricing` (generic)
- [ ] Or: Use asset-class-conditional imports
- [ ] Add fallback for when Pipeline is not needed
- [ ] Document Pipeline usage patterns for each asset class

### Pipeline Factory Pattern
- [ ] Create `lib/pipeline_utils.py` for pipeline construction helpers
- [ ] Add `get_pricing_data_source(asset_class)` function
- [ ] Add `make_default_pipeline(asset_class)` function

### Testing
- [ ] Test pipeline with equities bundle
- [ ] Test pipeline with crypto bundle (may need custom data source)
- [ ] Test pipeline-free strategy execution

## Implementation Plan

### Step 1: Understand Zipline's Pipeline Data Sources

Zipline-Reloaded 3.1.0 provides several pricing data sources:
- `zipline.pipeline.data.EquityPricing` - Generic equity pricing
- `zipline.pipeline.data.USEquityPricing` - US-specific (legacy)
- Custom data sources can be registered for non-equity assets

For crypto/forex, we may need to:
1. Use the generic `EquityPricing` (works if bundle structure matches)
2. Create custom `CryptoPricing` / `ForexPricing` data sources
3. Skip Pipeline entirely for simple strategies (use `data.history()` instead)

### Step 2: Update Strategy Template

**Option A: Generic EquityPricing (Simplest)**

```python
# In strategy.py template
from zipline.pipeline.data import EquityPricing

def make_pipeline():
    """Create Pipeline with generic pricing data."""
    sma_30 = SimpleMovingAverage(
        inputs=[EquityPricing.close], 
        window_length=30
    )
    return Pipeline(
        columns={'sma_30': sma_30},
        screen=sma_30.isfinite(),
    )
```

**Option B: Conditional Import Based on Asset Class**

```python
# In strategy.py template
def _get_pricing_source():
    """Get appropriate pricing data source for asset class."""
    params = load_params()
    asset_class = params.get('strategy', {}).get('asset_class', 'equities')
    
    if asset_class == 'equities':
        from zipline.pipeline.data import USEquityPricing
        return USEquityPricing
    else:
        # Generic for crypto/forex
        from zipline.pipeline.data import EquityPricing
        return EquityPricing

def make_pipeline():
    Pricing = _get_pricing_source()
    sma_30 = SimpleMovingAverage(inputs=[Pricing.close], window_length=30)
    return Pipeline(columns={'sma_30': sma_30}, screen=sma_30.isfinite())
```

**Option C: Pipeline-Optional Pattern (Most Flexible)**

```python
# In strategy.py template
USE_PIPELINE = True  # Set to False for simple strategies

def initialize(context):
    params = load_params()
    context.params = params
    context.asset = symbol(params['strategy']['asset_symbol'])
    
    if USE_PIPELINE:
        attach_pipeline(make_pipeline(), 'my_pipeline')
        context.use_pipeline = True
    else:
        context.use_pipeline = False
    
    # ... rest of initialization

def before_trading_start(context, data):
    if context.use_pipeline:
        context.pipeline_data = pipeline_output('my_pipeline')
    else:
        context.pipeline_data = None

def compute_signals(context, data):
    if context.use_pipeline:
        # Use pipeline data
        pass
    else:
        # Use data.history() directly
        prices = data.history(context.asset, 'close', 30, '1d')
        sma_30 = prices.mean()
        # ...
```

### Step 3: Create Pipeline Utilities (Optional Enhancement)

Create `lib/pipeline_utils.py`:

```python
"""Pipeline construction utilities for different asset classes."""

from typing import Optional
from zipline.pipeline import Pipeline
from zipline.pipeline.factors import SimpleMovingAverage

def get_pricing_data(asset_class: str = 'equities'):
    """Get appropriate pricing data source for asset class."""
    if asset_class == 'equities':
        from zipline.pipeline.data import USEquityPricing
        return USEquityPricing
    else:
        from zipline.pipeline.data import EquityPricing
        return EquityPricing

def make_sma_pipeline(
    asset_class: str = 'equities',
    window_length: int = 30
) -> Pipeline:
    """Create a simple SMA pipeline."""
    Pricing = get_pricing_data(asset_class)
    sma = SimpleMovingAverage(inputs=[Pricing.close], window_length=window_length)
    return Pipeline(columns={'sma': sma}, screen=sma.isfinite())
```

### Step 4: Update Template Documentation

Add to the strategy template docstring:

```python
"""
Strategy Template Notes:
==============================================================================
PIPELINE USAGE:
- Pipelines work with data from ingested bundles
- For equities: use USEquityPricing or EquityPricing
- For crypto/forex: use EquityPricing (generic)
- For simple strategies: skip Pipeline, use data.history() instead

SIMPLE APPROACH (no Pipeline):
    def compute_signals(context, data):
        prices = data.history(context.asset, 'close', 30, '1d')
        sma_30 = prices.mean()
        current = data.current(context.asset, 'close')
        signal = 1 if current > sma_30 else -1
        return signal, {'sma_30': sma_30}
"""
```

## Relevant Files

- `strategies/_template/strategy.py` - Main template file (lines 11-14, 105-120)
- `lib/pipeline_utils.py` - New utility module (to be created)
- `strategies/_template/parameters.yaml` - Add `asset_class` parameter

## Recommended Approach

For the MVP, use **Option A (Generic EquityPricing)** as it's the simplest change:

1. Replace `USEquityPricing` with `EquityPricing` in the template
2. This works for all asset classes that have OHLCV data in the bundle
3. Add documentation explaining when Pipeline is/isn't appropriate

Advanced users can customize further based on their needs.

## Testing Checklist

```python
# Test pipeline with equities
from zipline.pipeline.data import EquityPricing
from zipline.pipeline.factors import SimpleMovingAverage

sma = SimpleMovingAverage(inputs=[EquityPricing.close], window_length=30)
# Should not raise ImportError

# Verify factor computes with bundle
# (requires actual backtest execution)
```
