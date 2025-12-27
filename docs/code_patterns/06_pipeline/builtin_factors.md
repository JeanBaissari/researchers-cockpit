# Built-in Factors

> Pre-built factors for common calculations.

## Price/Volume Factors

### Returns

Price returns over a window.

```python
from zipline.pipeline.factors import Returns

# 20-day returns
returns_20d = Returns(window_length=20)

# 5-day returns
returns_5d = Returns(window_length=5)
```

### AverageDollarVolume

Average dollar volume over a window.

```python
from zipline.pipeline.factors import AverageDollarVolume

# 20-day average dollar volume
adv = AverageDollarVolume(window_length=20)

# Use for liquidity filter
liquid = adv.top(500)
```

### VWAP

Volume-weighted average price.

```python
from zipline.pipeline.factors import VWAP

vwap = VWAP(window_length=20)
```

### AnnualizedVolatility

Annualized return volatility.

```python
from zipline.pipeline.factors import AnnualizedVolatility

# Default: 252 trading days
vol = AnnualizedVolatility(window_length=20)

# Custom annualization
vol_monthly = AnnualizedVolatility(window_length=20, annualization_factor=12)
```

### AverageDailyVolume

Average daily volume (shares).

```python
from zipline.pipeline.factors import AverageDailyVolume

avg_vol = AverageDailyVolume(window_length=20)
```

---

## Technical Factors

### SimpleMovingAverage

```python
from zipline.pipeline.factors import SimpleMovingAverage

sma_20 = SimpleMovingAverage(inputs=[USEquityPricing.close], window_length=20)
sma_50 = SimpleMovingAverage(inputs=[USEquityPricing.close], window_length=50)
```

### ExponentialWeightedMovingAverage

```python
from zipline.pipeline.factors import ExponentialWeightedMovingAverage

ewma = ExponentialWeightedMovingAverage(
    inputs=[USEquityPricing.close],
    window_length=20,
    decay_rate=0.1
)
```

### ExponentialWeightedMovingStdDev

```python
from zipline.pipeline.factors import ExponentialWeightedMovingStdDev

ewmstd = ExponentialWeightedMovingStdDev(
    inputs=[USEquityPricing.close],
    window_length=20,
    decay_rate=0.1
)
```

### BollingerBands

```python
from zipline.pipeline.factors import BollingerBands

bb = BollingerBands(window_length=20, k=2)
middle = bb.middle
upper = bb.upper
lower = bb.lower
```

### Aroon

```python
from zipline.pipeline.factors import Aroon

aroon = Aroon(window_length=25)
aroon_up = aroon.up
aroon_down = aroon.down
```

### FastStochasticOscillator

```python
from zipline.pipeline.factors import FastStochasticOscillator

stoch = FastStochasticOscillator(window_length=14)
```

### IchimokuKinkoHyo

```python
from zipline.pipeline.factors import IchimokuKinkoHyo

ichimoku = IchimokuKinkoHyo()
tenkan = ichimoku.tenkan_sen
kijun = ichimoku.kijun_sen
senkou_a = ichimoku.senkou_span_a
senkou_b = ichimoku.senkou_span_b
chikou = ichimoku.chikou_span
```

### RateOfChangePercentage

```python
from zipline.pipeline.factors import RateOfChangePercentage

roc = RateOfChangePercentage(window_length=10)
```

### TrueRange

```python
from zipline.pipeline.factors import TrueRange

tr = TrueRange()
```

### MaxDrawdown

```python
from zipline.pipeline.factors import MaxDrawdown

mdd = MaxDrawdown(window_length=252)
```

---

## Statistical Factors

### RollingPearsonOfReturns

Correlation with target asset.

```python
from zipline.pipeline.factors import RollingPearsonOfReturns

# Correlation with SPY
spy = symbol('SPY')
correlation = RollingPearsonOfReturns(
    target=spy,
    returns_length=10,
    correlation_length=30
)
```

### RollingSpearmanOfReturns

Rank correlation with target asset.

```python
from zipline.pipeline.factors import RollingSpearmanOfReturns

spearman = RollingSpearmanOfReturns(
    target=symbol('SPY'),
    returns_length=10,
    correlation_length=30
)
```

### RollingLinearRegressionOfReturns

Beta and alpha vs target.

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

---

## Usage Examples

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
    close = USEquityPricing.close.latest
    sma = SimpleMovingAverage(inputs=[USEquityPricing.close], window_length=20)
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

### Low Volatility

```python
def make_pipeline():
    volatility = AnnualizedVolatility(window_length=20)
    volume = AverageDollarVolume(window_length=20)
    
    liquid = volume.top(500)
    
    # Lowest volatility stocks
    low_vol = volatility.bottom(100, mask=liquid)
    
    return Pipeline(
        columns={'volatility': volatility},
        screen=low_vol
    )
```

---

## See Also

- [Pipeline Overview](pipeline_overview.md)
- [Factors](factors.md)
- [Custom Factors](custom_factors.md)
