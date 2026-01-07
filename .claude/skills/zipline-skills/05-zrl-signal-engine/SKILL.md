---
name: zrl-signal-engine
description: This skill should be used when developing signal generation logic for Zipline strategies. It provides patterns for technical indicators, factor signals, event-driven signals, and composite signal combination with proper normalization.
---

# Zipline Signal Engine

Build robust signal generation systems for algorithmic trading strategies.

## Purpose

Create standardized, testable signal generators that transform market data into actionable trading signals. Provides patterns for single indicators through complex composite signals.

## When to Use

- Implementing technical indicators
- Building factor-based signals
- Creating event-driven signals
- Combining multiple signals into composite scores

## Signal Architecture

```
Raw Data → Feature Extraction → Signal Calculation → Normalization → Aggregation → Output
```

### Signal Interface

All signals implement a common interface:

```python
from abc import ABC, abstractmethod
import pandas as pd

class Signal(ABC):
    """Base signal interface."""
    
    @abstractmethod
    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """Calculate signal values."""
        pass
    
    @abstractmethod
    def normalize(self, values: pd.Series) -> pd.Series:
        """Normalize to [-1, 1] or [0, 1] range."""
        pass
```

## Technical Indicator Signals

### Moving Average Cross

```python
class MACrossSignal(Signal):
    """Moving average crossover signal."""
    
    def __init__(self, fast_period: int = 10, slow_period: int = 30):
        self.fast_period = fast_period
        self.slow_period = slow_period
    
    def calculate(self, prices: pd.Series) -> pd.Series:
        fast_ma = prices.rolling(self.fast_period).mean()
        slow_ma = prices.rolling(self.slow_period).mean()
        return (fast_ma - slow_ma) / slow_ma
    
    def normalize(self, values: pd.Series) -> pd.Series:
        return values.clip(-0.1, 0.1) / 0.1  # Scale to [-1, 1]
```

### RSI Signal

```python
class RSISignal(Signal):
    """Relative Strength Index signal."""
    
    def __init__(self, period: int = 14, overbought: float = 70, oversold: float = 30):
        self.period = period
        self.overbought = overbought
        self.oversold = oversold
    
    def calculate(self, prices: pd.Series) -> pd.Series:
        delta = prices.diff()
        gain = delta.where(delta > 0, 0).rolling(self.period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(self.period).mean()
        rs = gain / loss.replace(0, 1e-10)
        return 100 - (100 / (1 + rs))
    
    def normalize(self, rsi: pd.Series) -> pd.Series:
        # Convert to signal: -1 (overbought) to +1 (oversold)
        signal = pd.Series(0.0, index=rsi.index)
        signal[rsi < self.oversold] = 1.0
        signal[rsi > self.overbought] = -1.0
        return signal
```

### Bollinger Band Signal

```python
class BollingerSignal(Signal):
    """Bollinger Bands mean reversion signal."""
    
    def __init__(self, period: int = 20, num_std: float = 2.0):
        self.period = period
        self.num_std = num_std
    
    def calculate(self, prices: pd.Series) -> pd.Series:
        ma = prices.rolling(self.period).mean()
        std = prices.rolling(self.period).std()
        upper = ma + (self.num_std * std)
        lower = ma - (self.num_std * std)
        
        # Position within bands: -1 (at lower) to +1 (at upper)
        return (prices - ma) / (self.num_std * std)
    
    def normalize(self, values: pd.Series) -> pd.Series:
        return values.clip(-1, 1)
```

## Factor-Based Signals

### Momentum Signal

```python
class MomentumSignal(Signal):
    """Price momentum signal."""
    
    def __init__(self, lookback: int = 20, skip_recent: int = 1):
        self.lookback = lookback
        self.skip_recent = skip_recent
    
    def calculate(self, prices: pd.Series) -> pd.Series:
        if self.skip_recent > 0:
            return prices.shift(self.skip_recent).pct_change(self.lookback - self.skip_recent)
        return prices.pct_change(self.lookback)
    
    def normalize(self, values: pd.Series) -> pd.Series:
        # Cross-sectional z-score
        return (values - values.mean()) / values.std()
```

### Value Signal

```python
class ValueSignal(Signal):
    """Value factor signal (e.g., earnings yield)."""
    
    def __init__(self, fundamental_field: str = 'earnings_yield'):
        self.field = fundamental_field
    
    def calculate(self, fundamentals: pd.DataFrame) -> pd.Series:
        return fundamentals[self.field]
    
    def normalize(self, values: pd.Series) -> pd.Series:
        # Rank-based normalization
        ranks = values.rank(pct=True)
        return (ranks - 0.5) * 2  # Scale to [-1, 1]
```

## Composite Signal Aggregation

### Signal Combiner

```python
class SignalCombiner:
    """Combine multiple signals with weights."""
    
    def __init__(self, signals: dict, weights: dict = None):
        self.signals = signals
        self.weights = weights or {name: 1.0 for name in signals}
        
        # Normalize weights
        total = sum(self.weights.values())
        self.weights = {k: v/total for k, v in self.weights.items()}
    
    def combine(self, data: pd.DataFrame) -> pd.Series:
        """Calculate weighted combination of signals."""
        combined = pd.Series(0.0, index=data.index)
        
        for name, signal in self.signals.items():
            raw = signal.calculate(data)
            normalized = signal.normalize(raw)
            combined += self.weights[name] * normalized
        
        return combined
    
    def get_ranks(self, combined: pd.Series, ascending: bool = False) -> pd.Series:
        """Get cross-sectional ranks."""
        return combined.rank(ascending=ascending, pct=True)
```

### Usage Example

```python
def initialize(context):
    context.signals = SignalCombiner(
        signals={
            'momentum': MomentumSignal(lookback=20),
            'rsi': RSISignal(period=14),
            'ma_cross': MACrossSignal(fast=10, slow=30)
        },
        weights={
            'momentum': 0.5,
            'rsi': 0.3,
            'ma_cross': 0.2
        }
    )

def handle_data(context, data):
    prices = data.history(context.assets, 'close', 50, '1d')
    
    combined = context.signals.combine(prices)
    ranks = context.signals.get_ranks(combined)
    
    # Long top 10%, short bottom 10%
    context.longs = ranks[ranks > 0.9].index.tolist()
    context.shorts = ranks[ranks < 0.1].index.tolist()
```

## Signal Validation

### Backtest Signal Quality

```python
def validate_signal(signal: pd.Series, forward_returns: pd.Series) -> dict:
    """Validate signal predictive power."""
    
    # Information Coefficient (IC)
    ic = signal.corr(forward_returns)
    
    # Hit rate
    correct = ((signal > 0) & (forward_returns > 0)) | \
              ((signal < 0) & (forward_returns < 0))
    hit_rate = correct.mean()
    
    # Quintile spread
    quintiles = pd.qcut(signal, 5, labels=[1, 2, 3, 4, 5])
    quintile_returns = forward_returns.groupby(quintiles).mean()
    spread = quintile_returns[5] - quintile_returns[1]
    
    return {
        'ic': ic,
        'hit_rate': hit_rate,
        'quintile_spread': spread,
        'signal_coverage': signal.notna().mean()
    }
```

## Script Reference

### signal_analysis.py

Analyze signal performance:

```bash
python scripts/signal_analysis.py \
    --signal momentum \
    --data /path/to/prices.csv \
    --forward-days 5 \
    --output analysis_report.html
```

### signal_correlations.py

Check signal correlations:

```bash
python scripts/signal_correlations.py \
    --signals momentum,value,rsi \
    --data /path/to/data
```

## Best Practices

1. **Always normalize** signals to comparable scales before combining
2. **Handle NaN values** explicitly - don't let them propagate
3. **Use lookback-adjusted windows** to avoid look-ahead bias
4. **Test signals independently** before combining
5. **Monitor signal decay** over time

## References

See `references/technical_indicators.md` for indicator formulas.
See `references/factor_definitions.md` for factor specifications.
