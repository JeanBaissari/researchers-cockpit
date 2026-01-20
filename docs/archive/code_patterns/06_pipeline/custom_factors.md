# Custom Factors

> Create your own pipeline factors with custom logic.

## CustomFactor Class

```python
class zipline.pipeline.CustomFactor(
    inputs=NotSpecified,
    outputs=NotSpecified,
    window_length=NotSpecified,
    mask=NotSpecified,
    domain=NotSpecified
)
```

### Key Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `inputs` | list | BoundColumns to use as inputs |
| `window_length` | int | Number of bars to look back |
| `outputs` | list | Output names (for multiple outputs) |
| `dtype` | np.dtype | Output data type (default: float64) |

---

## Basic Structure

```python
from zipline.pipeline import CustomFactor
from zipline.pipeline.data import USEquityPricing
import numpy as np

class MyFactor(CustomFactor):
    inputs = [USEquityPricing.close]
    window_length = 20
    
    def compute(self, today, assets, out, close):
        # close.shape = (window_length, num_assets)
        # out.shape = (num_assets,)
        
        out[:] = np.mean(close, axis=0)  # Simple moving average
```

---

## compute() Method

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

### Input Array Shape

```
close array (window_length=5, 3 assets):

          AAPL    MSFT    GOOGL
Day -4:  150.0   280.0   2800.0
Day -3:  151.0   281.0   2810.0
Day -2:  152.0   279.0   2790.0
Day -1:  153.0   282.0   2815.0
Day  0:  154.0   283.0   2820.0

close[0] = oldest day
close[-1] = most recent day (today)
close[:, 0] = all days for AAPL
```

---

## Examples

### Simple Moving Average

```python
class SMA(CustomFactor):
    inputs = [USEquityPricing.close]
    window_length = 20
    
    def compute(self, today, assets, out, close):
        out[:] = np.nanmean(close, axis=0)
```

### Exponential Moving Average

```python
class EMA(CustomFactor):
    inputs = [USEquityPricing.close]
    params = {'span': 20}
    
    def compute(self, today, assets, out, close):
        alpha = 2.0 / (self.params['span'] + 1)
        weights = (1 - alpha) ** np.arange(self.window_length)[::-1]
        weights /= weights.sum()
        out[:] = np.sum(close * weights[:, np.newaxis], axis=0)
```

### Volatility (Standard Deviation of Returns)

```python
class Volatility(CustomFactor):
    inputs = [USEquityPricing.close]
    window_length = 21  # 20 returns need 21 prices
    
    def compute(self, today, assets, out, close):
        returns = np.diff(close, axis=0) / close[:-1]
        out[:] = np.nanstd(returns, axis=0)
```

### RSI

```python
class RSI(CustomFactor):
    inputs = [USEquityPricing.close]
    window_length = 15
    
    def compute(self, today, assets, out, close):
        diff = np.diff(close, axis=0)
        
        ups = np.where(diff > 0, diff, 0)
        downs = np.where(diff < 0, -diff, 0)
        
        avg_up = np.nanmean(ups, axis=0)
        avg_down = np.nanmean(downs, axis=0)
        
        rs = avg_up / np.where(avg_down == 0, 1, avg_down)
        out[:] = 100 - (100 / (1 + rs))
```

### VWAP

```python
class VWAP(CustomFactor):
    inputs = [USEquityPricing.close, USEquityPricing.volume]
    window_length = 20
    
    def compute(self, today, assets, out, close, volume):
        total_value = np.nansum(close * volume, axis=0)
        total_volume = np.nansum(volume, axis=0)
        out[:] = total_value / np.where(total_volume == 0, 1, total_volume)
```

---

## Multiple Outputs

```python
class BollingerBands(CustomFactor):
    inputs = [USEquityPricing.close]
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

## Parameters

```python
class MyFactor(CustomFactor):
    inputs = [USEquityPricing.close]
    params = {'threshold': 0.5, 'method': 'mean'}
    
    def compute(self, today, assets, out, close):
        if self.params['method'] == 'mean':
            out[:] = np.nanmean(close, axis=0)
        else:
            out[:] = np.nanmedian(close, axis=0)

# Usage with different params
factor1 = MyFactor(threshold=0.3)
factor2 = MyFactor(method='median')
```

---

## Using Custom Factors

```python
from zipline.pipeline import Pipeline

def make_pipeline():
    sma_20 = SMA(window_length=20)
    sma_50 = SMA(window_length=50)
    volatility = Volatility()
    
    golden_cross = sma_20 > sma_50
    low_vol = volatility.percentile_between(0, 50)
    
    return Pipeline(
        columns={
            'sma_20': sma_20,
            'sma_50': sma_50,
            'volatility': volatility,
        },
        screen=golden_cross & low_vol
    )
```

---

## See Also

- [Pipeline Overview](pipeline_overview.md)
- [Factors](factors.md)
- [Built-in Factors](builtin_factors.md)
