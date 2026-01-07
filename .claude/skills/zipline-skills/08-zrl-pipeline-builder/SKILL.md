---
name: zrl-pipeline-builder
description: This skill should be used when constructing Zipline Pipeline objects for factor-based strategies. It provides patterns for building efficient pipelines, combining factors, creating screens, and optimizing pipeline performance.
---

# Zipline Pipeline Builder

Construct efficient, maintainable pipelines for cross-sectional analysis.

## Purpose

Build Pipeline objects that efficiently compute factors across large asset universes. Provides patterns for factor combination, screen construction, and performance optimization.

## When to Use

- Building factor-based strategies
- Creating asset screening logic
- Computing cross-sectional metrics
- Optimizing universe selection

## Pipeline Fundamentals

### Basic Structure

```python
from zipline.pipeline import Pipeline
from zipline.pipeline.factors import Returns, AverageDollarVolume
from zipline.api import attach_pipeline, pipeline_output

def make_pipeline():
    # Define factors
    momentum = Returns(window_length=20)
    liquidity = AverageDollarVolume(window_length=20)
    
    # Define screens
    liquid = liquidity.top(500)
    
    return Pipeline(
        columns={
            'momentum': momentum,
            'liquidity': liquidity,
        },
        screen=liquid
    )

def initialize(context):
    attach_pipeline(make_pipeline(), 'factors')

def before_trading_start(context, data):
    context.output = pipeline_output('factors')
```

## Factor Composition Patterns

### Multi-Factor Alpha

```python
def make_alpha_pipeline():
    """Build multi-factor alpha pipeline."""
    from zipline.pipeline.factors import Returns, AverageDollarVolume
    
    # Individual factors
    momentum = Returns(window_length=20)
    reversion = -Returns(window_length=5)  # Negative for mean reversion
    volume = AverageDollarVolume(window_length=20)
    
    # Normalize factors
    momentum_z = momentum.zscore()
    reversion_z = reversion.zscore()
    
    # Combine with weights
    alpha = (0.6 * momentum_z) + (0.4 * reversion_z)
    
    # Universe filter
    universe = volume.top(1000)
    
    # Selection filters
    longs = alpha.top(50, mask=universe)
    shorts = alpha.bottom(50, mask=universe)
    
    return Pipeline(
        columns={
            'alpha': alpha,
            'momentum': momentum,
            'reversion': reversion,
            'longs': longs,
            'shorts': shorts,
        },
        screen=longs | shorts
    )
```

### Sector-Neutral Pipeline

```python
def make_sector_neutral_pipeline(sector_classifier):
    """Build sector-neutral factor pipeline."""
    from zipline.pipeline.factors import Returns
    
    momentum = Returns(window_length=20)
    
    # Sector-neutralize: demean within sectors
    sector_neutral_momentum = momentum.demean(groupby=sector_classifier)
    
    # Rank within sectors
    sector_rank = momentum.rank(groupby=sector_classifier)
    
    # Top 5 per sector
    longs = momentum.top(5, groupby=sector_classifier)
    
    return Pipeline(
        columns={
            'momentum': momentum,
            'sector_neutral': sector_neutral_momentum,
            'sector_rank': sector_rank,
            'longs': longs,
        },
        screen=longs
    )
```

## Screen Construction

### Composite Screens

```python
def build_universe_screen():
    """Build comprehensive universe filter."""
    from zipline.pipeline.factors import AverageDollarVolume, AnnualizedVolatility
    from zipline.pipeline.data import USEquityPricing
    
    # Liquidity filter
    adv = AverageDollarVolume(window_length=20)
    liquid = adv > 1_000_000  # $1M daily volume
    
    # Price filter
    price = USEquityPricing.close.latest
    price_ok = (price > 5) & (price < 1000)
    
    # Volatility filter
    vol = AnnualizedVolatility(window_length=20)
    vol_ok = vol < 0.80  # Less than 80% annual vol
    
    # Data availability
    has_data = price.notnull() & adv.notnull()
    
    # Combine all filters
    universe = liquid & price_ok & vol_ok & has_data
    
    return universe
```

### Dynamic Screens

```python
def make_dynamic_universe_pipeline():
    """Pipeline with adaptive universe."""
    from zipline.pipeline.factors import AverageDollarVolume, Returns
    
    adv = AverageDollarVolume(window_length=20)
    
    # Adaptive: use top 500 by volume
    universe = adv.top(500)
    
    # Further filter within universe
    momentum = Returns(window_length=20)
    positive_momentum = momentum > 0
    
    # Final selection
    final_universe = universe & positive_momentum
    
    return Pipeline(
        columns={'momentum': momentum},
        screen=final_universe
    )
```

## Pipeline Factory Pattern

```python
class PipelineFactory:
    """Factory for building standardized pipelines."""
    
    def __init__(self, universe_size: int = 500, lookback: int = 20):
        self.universe_size = universe_size
        self.lookback = lookback
    
    def create_momentum_pipeline(self) -> Pipeline:
        """Create momentum strategy pipeline."""
        from zipline.pipeline.factors import Returns, AverageDollarVolume
        
        returns = Returns(window_length=self.lookback)
        volume = AverageDollarVolume(window_length=20)
        
        universe = volume.top(self.universe_size)
        longs = returns.top(20, mask=universe)
        
        return Pipeline(
            columns={'returns': returns, 'longs': longs},
            screen=longs
        )
    
    def create_value_pipeline(self, value_factor) -> Pipeline:
        """Create value strategy pipeline."""
        from zipline.pipeline.factors import AverageDollarVolume
        
        volume = AverageDollarVolume(window_length=20)
        universe = volume.top(self.universe_size)
        
        longs = value_factor.top(20, mask=universe)
        
        return Pipeline(
            columns={'value': value_factor, 'longs': longs},
            screen=longs
        )
    
    def create_multi_factor_pipeline(self, factors: dict, weights: dict) -> Pipeline:
        """Create weighted multi-factor pipeline."""
        from zipline.pipeline.factors import AverageDollarVolume
        
        volume = AverageDollarVolume(window_length=20)
        universe = volume.top(self.universe_size)
        
        # Normalize and combine factors
        combined = None
        for name, factor in factors.items():
            weighted = factor.zscore() * weights.get(name, 1.0)
            combined = weighted if combined is None else combined + weighted
        
        longs = combined.top(20, mask=universe)
        shorts = combined.bottom(20, mask=universe)
        
        columns = {name: f for name, f in factors.items()}
        columns.update({'combined': combined, 'longs': longs, 'shorts': shorts})
        
        return Pipeline(columns=columns, screen=longs | shorts)
```

## Performance Optimization

### Mask Usage

```python
def optimized_pipeline():
    """Use masks to reduce computation."""
    from zipline.pipeline.factors import Returns, AverageDollarVolume, VWAP
    
    # First, create a coarse universe
    adv = AverageDollarVolume(window_length=20)
    coarse_universe = adv.top(2000)
    
    # Expensive calculations only on coarse universe
    momentum = Returns(window_length=60, mask=coarse_universe)
    vwap = VWAP(window_length=20, mask=coarse_universe)
    
    # Further filtering
    longs = momentum.top(50, mask=coarse_universe)
    
    return Pipeline(
        columns={'momentum': momentum, 'vwap': vwap},
        screen=longs
    )
```

### Chunked Execution

```python
def initialize(context):
    # Use chunks for memory efficiency
    attach_pipeline(
        make_pipeline(),
        'factors',
        chunks=30  # Process 30 days at a time
    )
```

## Multiple Pipelines

```python
def initialize(context):
    # Main alpha pipeline
    attach_pipeline(make_alpha_pipeline(), 'alpha')
    
    # Risk factors pipeline
    attach_pipeline(make_risk_pipeline(), 'risk')
    
    # Universe pipeline
    attach_pipeline(make_universe_pipeline(), 'universe')

def before_trading_start(context, data):
    alpha_output = pipeline_output('alpha')
    risk_output = pipeline_output('risk')
    universe_output = pipeline_output('universe')
    
    # Combine outputs
    context.combined = alpha_output.join(risk_output).join(universe_output)
```

## Script Reference

### pipeline_profiler.py

Profile pipeline performance:

```bash
python scripts/pipeline_profiler.py \
    --pipeline strategy.py \
    --start 2020-01-01 \
    --end 2020-12-31 \
    --output profile.html
```

### pipeline_validator.py

Validate pipeline construction:

```bash
python scripts/pipeline_validator.py strategy.py
```

## Common Patterns Summary

| Pattern | Use Case | Key Feature |
|---------|----------|-------------|
| Multi-Factor | Combine signals | Z-score normalization |
| Sector-Neutral | Remove sector bias | `demean(groupby=sector)` |
| Adaptive Universe | Dynamic selection | `top(N)` filters |
| Masked Computation | Performance | `mask=` parameter |
| Pipeline Factory | Reusable templates | Class-based construction |

## References

See `references/factor_catalog.md` for available factors.
See `references/pipeline_optimization.md` for performance tips.
