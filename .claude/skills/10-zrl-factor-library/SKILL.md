---
name: zrl-factor-library
description: This skill should be used when implementing pre-built factor libraries for Zipline strategies. It provides a curated collection of production-ready factors organized by category (momentum, value, quality, volatility, technical) with consistent interfaces.
---

# Zipline Factor Library

Production-ready factor implementations for quantitative strategies.

## Purpose

Provide a comprehensive, tested library of commonly-used factors. Reduce development time with standardized, optimized implementations.

## When to Use

- Rapidly prototyping factor strategies
- Building multi-factor models
- Testing factor combinations
- Learning factor construction patterns

## Factor Categories

### Category Overview

| Category | Description | Example Factors |
|----------|-------------|-----------------|
| Momentum | Price trends | Returns, RSI, MACD |
| Value | Fundamental value | Earnings yield, B/P |
| Quality | Business quality | ROE, Accruals |
| Volatility | Risk measures | Vol, Beta, Skew |
| Technical | Chart patterns | SMA, Bollinger |
| Volume | Trading activity | ADV, OBV |

## Momentum Factors

```python
# scripts/factors/momentum.py

from zipline.pipeline import CustomFactor
from zipline.pipeline.data import USEquityPricing
import numpy as np

class Momentum(CustomFactor):
    """N-day price momentum."""
    inputs = [USEquityPricing.close]
    window_length = 20
    
    def compute(self, today, assets, out, close):
        out[:] = (close[-1] / close[0]) - 1

class MomentumSkipRecent(CustomFactor):
    """Momentum excluding recent days (avoiding reversal)."""
    inputs = [USEquityPricing.close]
    window_length = 252
    params = ('skip_days',)
    
    def __new__(cls, window_length=252, skip_days=21):
        return super().__new__(cls, window_length=window_length, skip_days=skip_days)
    
    def compute(self, today, assets, out, close):
        skip = self.params['skip_days']
        out[:] = (close[-(1+skip)] / close[0]) - 1

class RSI(CustomFactor):
    """Relative Strength Index."""
    inputs = [USEquityPricing.close]
    window_length = 15
    
    def compute(self, today, assets, out, close):
        diff = np.diff(close, axis=0)
        up = np.where(diff > 0, diff, 0)
        down = np.where(diff < 0, -diff, 0)
        avg_up = np.nanmean(up, axis=0)
        avg_down = np.nanmean(down, axis=0)
        avg_down = np.where(avg_down == 0, 1e-10, avg_down)
        rs = avg_up / avg_down
        out[:] = 100 - (100 / (1 + rs))

class MACD(CustomFactor):
    """MACD histogram."""
    inputs = [USEquityPricing.close]
    window_length = 35
    outputs = ['macd', 'signal', 'histogram']
    
    def compute(self, today, assets, out, close):
        def ema(data, span):
            alpha = 2 / (span + 1)
            weights = (1 - alpha) ** np.arange(len(data))[::-1]
            weights /= weights.sum()
            return np.sum(data * weights[:, np.newaxis], axis=0)
        
        ema12 = ema(close[-12:], 12)
        ema26 = ema(close[-26:], 26)
        macd_line = ema12 - ema26
        
        out.macd[:] = macd_line
        out.signal[:] = macd_line  # Simplified
        out.histogram[:] = 0
```

## Volatility Factors

```python
# scripts/factors/volatility.py

class Volatility(CustomFactor):
    """Annualized volatility."""
    inputs = [USEquityPricing.close]
    window_length = 21
    
    def compute(self, today, assets, out, close):
        returns = np.diff(close, axis=0) / close[:-1]
        out[:] = np.nanstd(returns, axis=0) * np.sqrt(252)

class AverageTrueRange(CustomFactor):
    """Average True Range."""
    inputs = [USEquityPricing.high, USEquityPricing.low, USEquityPricing.close]
    window_length = 14
    
    def compute(self, today, assets, out, high, low, close):
        prev_close = np.roll(close, 1, axis=0)
        prev_close[0] = close[0]
        
        tr = np.maximum(
            high - low,
            np.maximum(
                np.abs(high - prev_close),
                np.abs(low - prev_close)
            )
        )
        out[:] = np.nanmean(tr, axis=0)

class DownsideVolatility(CustomFactor):
    """Downside deviation (semi-variance)."""
    inputs = [USEquityPricing.close]
    window_length = 60
    
    def compute(self, today, assets, out, close):
        returns = np.diff(close, axis=0) / close[:-1]
        neg_returns = np.where(returns < 0, returns, 0)
        out[:] = np.sqrt(np.nanmean(neg_returns ** 2, axis=0)) * np.sqrt(252)

class MaxDrawdown(CustomFactor):
    """Maximum drawdown over window."""
    inputs = [USEquityPricing.close]
    window_length = 252
    
    def compute(self, today, assets, out, close):
        cummax = np.maximum.accumulate(close, axis=0)
        drawdown = (close - cummax) / cummax
        out[:] = np.nanmin(drawdown, axis=0)
```

## Technical Factors

```python
# scripts/factors/technical.py

class SMA(CustomFactor):
    """Simple Moving Average."""
    inputs = [USEquityPricing.close]
    window_length = 20
    
    def compute(self, today, assets, out, close):
        out[:] = np.nanmean(close, axis=0)

class EMA(CustomFactor):
    """Exponential Moving Average."""
    inputs = [USEquityPricing.close]
    window_length = 20
    
    def compute(self, today, assets, out, close):
        alpha = 2 / (self.window_length + 1)
        weights = (1 - alpha) ** np.arange(self.window_length)[::-1]
        weights /= weights.sum()
        out[:] = np.sum(close * weights[:, np.newaxis], axis=0)

class BollingerBands(CustomFactor):
    """Bollinger Bands position."""
    inputs = [USEquityPricing.close]
    window_length = 20
    outputs = ['middle', 'upper', 'lower', 'pct_b']
    
    def compute(self, today, assets, out, close):
        mean = np.nanmean(close, axis=0)
        std = np.nanstd(close, axis=0)
        
        out.middle[:] = mean
        out.upper[:] = mean + 2 * std
        out.lower[:] = mean - 2 * std
        
        # Percent B: position within bands
        band_width = 4 * std
        band_width = np.where(band_width == 0, 1e-10, band_width)
        out.pct_b[:] = (close[-1] - out.lower) / band_width

class VWAP(CustomFactor):
    """Volume Weighted Average Price."""
    inputs = [USEquityPricing.close, USEquityPricing.volume]
    window_length = 20
    
    def compute(self, today, assets, out, close, volume):
        total_value = np.nansum(close * volume, axis=0)
        total_volume = np.nansum(volume, axis=0)
        total_volume = np.where(total_volume == 0, 1, total_volume)
        out[:] = total_value / total_volume
```

## Volume Factors

```python
# scripts/factors/volume.py

from zipline.pipeline.factors import AverageDollarVolume

class VolumeRatio(CustomFactor):
    """Current volume vs average."""
    inputs = [USEquityPricing.volume]
    window_length = 20
    
    def compute(self, today, assets, out, volume):
        avg_vol = np.nanmean(volume[:-1], axis=0)
        avg_vol = np.where(avg_vol == 0, 1, avg_vol)
        out[:] = volume[-1] / avg_vol

class OnBalanceVolume(CustomFactor):
    """On-Balance Volume trend."""
    inputs = [USEquityPricing.close, USEquityPricing.volume]
    window_length = 20
    
    def compute(self, today, assets, out, close, volume):
        price_change = np.sign(np.diff(close, axis=0))
        obv = np.cumsum(price_change * volume[1:], axis=0)
        out[:] = obv[-1]

class AccumulationDistribution(CustomFactor):
    """Accumulation/Distribution Line."""
    inputs = [USEquityPricing.high, USEquityPricing.low, 
              USEquityPricing.close, USEquityPricing.volume]
    window_length = 20
    
    def compute(self, today, assets, out, high, low, close, volume):
        hl_range = high - low
        hl_range = np.where(hl_range == 0, 1e-10, hl_range)
        mfm = ((close - low) - (high - close)) / hl_range
        mfv = mfm * volume
        out[:] = np.nansum(mfv, axis=0)
```

## Factor Registry

```python
# scripts/factors/registry.py

from .momentum import Momentum, MomentumSkipRecent, RSI, MACD
from .volatility import Volatility, AverageTrueRange, MaxDrawdown
from .technical import SMA, EMA, BollingerBands, VWAP
from .volume import VolumeRatio, OnBalanceVolume

FACTOR_REGISTRY = {
    # Momentum
    'momentum': Momentum,
    'momentum_12_1': lambda: MomentumSkipRecent(window_length=252, skip_days=21),
    'rsi': RSI,
    'macd': MACD,
    
    # Volatility
    'volatility': Volatility,
    'atr': AverageTrueRange,
    'max_drawdown': MaxDrawdown,
    
    # Technical
    'sma_20': lambda: SMA(window_length=20),
    'sma_50': lambda: SMA(window_length=50),
    'ema_20': lambda: EMA(window_length=20),
    'bollinger': BollingerBands,
    'vwap': VWAP,
    
    # Volume
    'volume_ratio': VolumeRatio,
    'obv': OnBalanceVolume,
}

def get_factor(name: str):
    """Get factor by name."""
    factory = FACTOR_REGISTRY.get(name)
    if factory is None:
        raise ValueError(f"Unknown factor: {name}")
    return factory() if callable(factory) else factory
```

## Usage Example

```python
from zipline.pipeline import Pipeline
from factors.registry import get_factor, FACTOR_REGISTRY

def make_multi_factor_pipeline():
    # Load multiple factors
    momentum = get_factor('momentum_12_1')
    volatility = get_factor('volatility')
    volume = get_factor('volume_ratio')
    
    # Combine
    alpha = momentum.zscore() - 0.5 * volatility.zscore()
    
    return Pipeline(
        columns={
            'momentum': momentum,
            'volatility': volatility,
            'volume': volume,
            'alpha': alpha,
        },
        screen=alpha.top(50)
    )
```

## Script Reference

### list_factors.py

List available factors:

```bash
python scripts/list_factors.py --category momentum
```

### factor_performance.py

Analyze factor historical performance:

```bash
python scripts/factor_performance.py momentum --start 2015-01-01 --end 2024-12-31
```

## References

See `references/factor_catalog.md` for complete factor list.
See `references/factor_correlations.md` for factor relationships.
