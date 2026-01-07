---
name: zrl-custom-factors
description: This skill should be used when creating custom factors for Zipline Pipeline. It provides patterns for implementing CustomFactor classes, handling windowed computations, multiple inputs/outputs, and efficient numpy operations.
---

# Zipline Custom Factors

Create custom pipeline factors for proprietary signals and indicators.

## Purpose

Extend Zipline's built-in factors with custom calculations. Build efficient, reusable factor implementations using the CustomFactor framework.

## When to Use

- Implementing proprietary indicators
- Creating factors not in built-in library
- Building complex multi-input calculations
- Optimizing frequently-used computations

## CustomFactor Structure

### Basic Template

```python
from zipline.pipeline import CustomFactor
from zipline.pipeline.data import USEquityPricing
import numpy as np

class MyFactor(CustomFactor):
    """Description of what this factor computes."""
    
    # Required: specify input data columns
    inputs = [USEquityPricing.close]
    
    # Required: lookback window
    window_length = 20
    
    def compute(self, today, assets, out, close):
        """
        Compute factor values.
        
        Parameters
        ----------
        today : pd.Timestamp
            Current simulation date
        assets : np.ndarray
            Array of asset sids
        out : np.ndarray
            Output array to fill (shape: num_assets,)
        close : np.ndarray
            Input data (shape: window_length x num_assets)
        """
        # close[0] = oldest, close[-1] = newest (today)
        out[:] = close[-1] / close[0] - 1  # Simple return
```

### Input Array Shape

```
For window_length=5 and 3 assets:

close array shape: (5, 3)
          Asset0  Asset1  Asset2
Day -4:   100.0   200.0   50.0
Day -3:   101.0   201.0   51.0
Day -2:   102.0   199.0   52.0
Day -1:   103.0   202.0   51.5
Day  0:   104.0   203.0   53.0  (today)

Axis 0 = time dimension (oldest to newest)
Axis 1 = asset dimension
```

## Common Factor Implementations

### Simple Moving Average

```python
class SMA(CustomFactor):
    """Simple moving average."""
    inputs = [USEquityPricing.close]
    window_length = 20
    
    def compute(self, today, assets, out, close):
        out[:] = np.nanmean(close, axis=0)
```

### Exponential Moving Average

```python
class EMA(CustomFactor):
    """Exponential moving average."""
    inputs = [USEquityPricing.close]
    window_length = 20
    params = ('span',)
    
    def compute(self, today, assets, out, close):
        alpha = 2.0 / (self.params['span'] + 1)
        weights = (1 - alpha) ** np.arange(self.window_length)[::-1]
        weights /= weights.sum()
        out[:] = np.sum(close * weights[:, np.newaxis], axis=0)
```

### Volatility (Standard Deviation of Returns)

```python
class Volatility(CustomFactor):
    """Annualized volatility of returns."""
    inputs = [USEquityPricing.close]
    window_length = 21
    
    def compute(self, today, assets, out, close):
        returns = np.diff(close, axis=0) / close[:-1]
        daily_vol = np.nanstd(returns, axis=0)
        out[:] = daily_vol * np.sqrt(252)  # Annualize
```

### RSI

```python
class RSI(CustomFactor):
    """Relative Strength Index."""
    inputs = [USEquityPricing.close]
    window_length = 15
    
    def compute(self, today, assets, out, close):
        diff = np.diff(close, axis=0)
        
        ups = np.where(diff > 0, diff, 0)
        downs = np.where(diff < 0, -diff, 0)
        
        avg_up = np.nanmean(ups, axis=0)
        avg_down = np.nanmean(downs, axis=0)
        
        # Avoid division by zero
        avg_down = np.where(avg_down == 0, 1e-10, avg_down)
        
        rs = avg_up / avg_down
        out[:] = 100 - (100 / (1 + rs))
```

### VWAP

```python
class VWAP(CustomFactor):
    """Volume Weighted Average Price."""
    inputs = [USEquityPricing.close, USEquityPricing.volume]
    window_length = 20
    
    def compute(self, today, assets, out, close, volume):
        total_value = np.nansum(close * volume, axis=0)
        total_volume = np.nansum(volume, axis=0)
        
        # Avoid division by zero
        total_volume = np.where(total_volume == 0, 1, total_volume)
        
        out[:] = total_value / total_volume
```

### Price Distance from High

```python
class DistanceFromHigh(CustomFactor):
    """Distance from N-day high as percentage."""
    inputs = [USEquityPricing.high, USEquityPricing.close]
    window_length = 52 * 5  # ~52 week high
    
    def compute(self, today, assets, out, high, close):
        highest = np.nanmax(high, axis=0)
        current = close[-1]
        out[:] = (current - highest) / highest
```

## Multiple Outputs

```python
class BollingerBands(CustomFactor):
    """Bollinger Bands with multiple outputs."""
    inputs = [USEquityPricing.close]
    window_length = 20
    outputs = ['middle', 'upper', 'lower', 'width']
    
    def compute(self, today, assets, out, close):
        mean = np.nanmean(close, axis=0)
        std = np.nanstd(close, axis=0)
        
        out.middle[:] = mean
        out.upper[:] = mean + 2 * std
        out.lower[:] = mean - 2 * std
        out.width[:] = (4 * std) / mean  # Band width as percentage

# Usage
bb = BollingerBands()
middle_band = bb.middle
upper_band = bb.upper
lower_band = bb.lower
band_width = bb.width
```

## Parameterized Factors

```python
class ParameterizedMomentum(CustomFactor):
    """Momentum with configurable parameters."""
    inputs = [USEquityPricing.close]
    params = ('skip_days',)
    
    def __new__(cls, window_length=20, skip_days=1):
        return super().__new__(cls, window_length=window_length, skip_days=skip_days)
    
    def compute(self, today, assets, out, close):
        skip = self.params['skip_days']
        if skip > 0:
            out[:] = close[-(1+skip)] / close[0] - 1
        else:
            out[:] = close[-1] / close[0] - 1

# Usage with different parameters
momentum_20 = ParameterizedMomentum(window_length=20, skip_days=1)
momentum_60 = ParameterizedMomentum(window_length=60, skip_days=5)
```

## Multi-Input Factors

```python
class PriceVolumeTrend(CustomFactor):
    """Price-volume trend indicator."""
    inputs = [
        USEquityPricing.close,
        USEquityPricing.volume,
        USEquityPricing.high,
        USEquityPricing.low
    ]
    window_length = 20
    
    def compute(self, today, assets, out, close, volume, high, low):
        # Calculate typical price
        typical = (high + low + close) / 3
        
        # Money flow
        mf = typical * volume
        
        # Positive/negative flow
        price_change = np.diff(typical, axis=0)
        pos_flow = np.where(price_change > 0, mf[1:], 0)
        neg_flow = np.where(price_change < 0, mf[1:], 0)
        
        pos_sum = np.nansum(pos_flow, axis=0)
        neg_sum = np.nansum(neg_flow, axis=0)
        
        # Money flow ratio
        neg_sum = np.where(neg_sum == 0, 1e-10, neg_sum)
        out[:] = pos_sum / neg_sum
```

## Using Masks

```python
class MaskedFactor(CustomFactor):
    """Factor that respects mask."""
    inputs = [USEquityPricing.close]
    window_length = 20
    # mask parameter inherited from CustomFactor
    
    def compute(self, today, assets, out, close):
        # Computation only runs for unmasked assets
        out[:] = np.nanmean(close, axis=0)

# Usage: only compute for liquid stocks
from zipline.pipeline.factors import AverageDollarVolume
liquid = AverageDollarVolume(window_length=20).top(1000)
masked_factor = MaskedFactor(mask=liquid)
```

## Performance Tips

### Vectorize Operations

```python
# SLOW: Python loops
def compute(self, today, assets, out, close):
    for i in range(len(assets)):
        out[i] = np.mean(close[:, i])

# FAST: Vectorized numpy
def compute(self, today, assets, out, close):
    out[:] = np.nanmean(close, axis=0)
```

### Minimize Memory Allocation

```python
# SLOW: Creates intermediate arrays
def compute(self, today, assets, out, close):
    returns = close[1:] / close[:-1] - 1
    cum_returns = np.cumprod(1 + returns, axis=0)
    out[:] = cum_returns[-1] - 1

# FAST: In-place operations where possible
def compute(self, today, assets, out, close):
    out[:] = close[-1] / close[0] - 1
```

### Use Appropriate dtypes

```python
class EfficientFactor(CustomFactor):
    inputs = [USEquityPricing.close]
    window_length = 20
    dtype = np.float32  # Use float32 if precision allows
    
    def compute(self, today, assets, out, close):
        out[:] = np.nanmean(close.astype(np.float32), axis=0)
```

## Script Reference

### test_factor.py

Test custom factor implementation:

```bash
python scripts/test_factor.py MyFactor --window 20 --data test_data.csv
```

### factor_benchmark.py

Benchmark factor performance:

```bash
python scripts/factor_benchmark.py --factor MyFactor --iterations 100
```

## References

See `references/numpy_patterns.md` for efficient numpy operations.
See `references/factor_testing.md` for testing patterns.
