---
name: zrl-multi-strategy
description: This skill should be used when combining multiple strategies into a portfolio, implementing strategy allocation, and managing multi-strategy systems. It provides frameworks for strategy weighting, correlation analysis, and dynamic allocation.
---

# Zipline Multi-Strategy

Combine multiple trading strategies into a robust portfolio system.

## Purpose

Manage multiple strategies within a single algorithm, implementing allocation schemes, correlation-aware weighting, and dynamic rebalancing across strategies.

## When to Use

- Combining uncorrelated alpha sources
- Implementing strategy diversification
- Building regime-aware allocation systems
- Managing capital allocation across strategies
- Creating ensemble trading systems

## Multi-Strategy Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Multi-Strategy Manager                     │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ Momentum │  │  Value   │  │Mean Rev. │  │Stat Arb  │    │
│  │ Strategy │  │ Strategy │  │ Strategy │  │ Strategy │    │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘    │
│       │             │             │             │          │
│       └─────────────┴──────┬──────┴─────────────┘          │
│                            │                                │
│                    ┌───────▼───────┐                       │
│                    │   Allocator   │                       │
│                    └───────┬───────┘                       │
│                            │                                │
│                    ┌───────▼───────┐                       │
│                    │   Executor    │                       │
│                    └───────────────┘                       │
└─────────────────────────────────────────────────────────────┘
```

## Strategy Interface

Each sub-strategy must implement:

```python
class BaseStrategy:
    """Base class for all sub-strategies."""
    
    def __init__(self, name: str, params: dict = None):
        self.name = name
        self.params = params or {}
    
    def initialize(self, context):
        """Setup strategy state on context."""
        pass
    
    def generate_signals(self, context, data) -> Dict[Asset, float]:
        """
        Generate trading signals.
        
        Returns
        -------
        Dict[Asset, float]
            Mapping of asset to signal strength [-1, 1]
        """
        raise NotImplementedError
    
    def get_target_weights(self, context, data) -> Dict[Asset, float]:
        """
        Get target portfolio weights.
        
        Returns
        -------
        Dict[Asset, float]
            Mapping of asset to target weight
        """
        raise NotImplementedError
```

## Allocation Methods

### 1. Equal Weight

```python
allocator = EqualWeightAllocator(strategies)
# Each strategy gets 1/N allocation
```

### 2. Risk Parity

```python
allocator = RiskParityAllocator(
    strategies,
    lookback=252,
    target_vol=0.10
)
# Weight by inverse volatility
```

### 3. Mean-Variance

```python
allocator = MeanVarianceAllocator(
    strategies,
    lookback=252,
    risk_aversion=2.0
)
# Optimize for risk-adjusted returns
```

### 4. Performance-Based

```python
allocator = PerformanceAllocator(
    strategies,
    metric='sharpe',
    lookback=126,
    min_weight=0.05
)
# Allocate based on recent performance
```

## Core Workflow

### Step 1: Define Strategies

```python
from multi_strategy import MomentumStrategy, MeanReversionStrategy, ValueStrategy

strategies = [
    MomentumStrategy(
        name='momentum',
        params={'lookback': 20, 'holding': 5}
    ),
    MeanReversionStrategy(
        name='mean_rev',
        params={'lookback': 10, 'zscore_threshold': 2.0}
    ),
    ValueStrategy(
        name='value',
        params={'rebalance_freq': 'monthly'}
    ),
]
```

### Step 2: Create Manager

```python
from multi_strategy import MultiStrategyManager, RiskParityAllocator

manager = MultiStrategyManager(
    strategies=strategies,
    allocator=RiskParityAllocator(target_vol=0.12),
    rebalance_freq='weekly'
)
```

### Step 3: Integrate with Algorithm

```python
def initialize(context):
    context.manager = manager
    context.manager.initialize(context)
    
    schedule_function(
        rebalance,
        date_rules.week_start(),
        time_rules.market_open(hours=1)
    )

def rebalance(context, data):
    # Get combined target weights
    targets = context.manager.get_combined_targets(context, data)
    
    # Execute trades
    for asset, weight in targets.items():
        if data.can_trade(asset):
            order_target_percent(asset, weight)
```

## Script Reference

### combine_strategies.py

Combine strategies programmatically:

```bash
python scripts/combine_strategies.py \
    --strategies momentum.py value.py meanrev.py \
    --allocator risk_parity \
    --output combined_strategy.py
```

### analyze_correlation.py

Analyze strategy correlations:

```bash
python scripts/analyze_correlation.py \
    --results strat1.pickle strat2.pickle strat3.pickle \
    --output correlation_report.html
```

### backtest_multi.py

Backtest multi-strategy portfolio:

```bash
python scripts/backtest_multi.py \
    --config multi_config.yaml \
    --start 2015-01-01 \
    --end 2023-12-31 \
    --output results/
```

## MultiStrategyManager Class

```python
class MultiStrategyManager:
    """Manage multiple trading strategies."""
    
    def __init__(self, strategies: List[BaseStrategy],
                 allocator: Allocator,
                 rebalance_freq: str = 'weekly',
                 max_leverage: float = 1.0,
                 net_exposure_limit: float = 1.0):
        """
        Parameters
        ----------
        strategies : List[BaseStrategy]
            List of strategy instances
        allocator : Allocator
            Capital allocation method
        rebalance_freq : str
            How often to reallocate ('daily', 'weekly', 'monthly')
        max_leverage : float
            Maximum gross leverage
        net_exposure_limit : float
            Maximum net exposure
        """
    
    def initialize(self, context)
    def get_strategy_weights(self, context, data) -> Dict[str, float]
    def get_combined_targets(self, context, data) -> Dict[Asset, float]
    def update_allocations(self, context, data)
```

## Allocator Classes

### EqualWeightAllocator

```python
class EqualWeightAllocator:
    """Equal allocation across strategies."""
    
    def allocate(self, strategies: List, context, data) -> Dict[str, float]:
        n = len(strategies)
        return {s.name: 1.0 / n for s in strategies}
```

### RiskParityAllocator

```python
class RiskParityAllocator:
    """Allocate inversely to volatility."""
    
    def __init__(self, lookback: int = 252, target_vol: float = 0.10):
        self.lookback = lookback
        self.target_vol = target_vol
    
    def allocate(self, strategies: List, context, data) -> Dict[str, float]:
        vols = {}
        for strat in strategies:
            # Get strategy returns from tracking
            returns = context.strategy_returns.get(strat.name, pd.Series())
            if len(returns) >= self.lookback:
                vols[strat.name] = returns[-self.lookback:].std() * np.sqrt(252)
            else:
                vols[strat.name] = self.target_vol  # Default
        
        # Inverse volatility weights
        inv_vols = {k: 1/v for k, v in vols.items() if v > 0}
        total = sum(inv_vols.values())
        
        return {k: v/total for k, v in inv_vols.items()}
```

### PerformanceAllocator

```python
class PerformanceAllocator:
    """Allocate based on recent performance."""
    
    def __init__(self, metric: str = 'sharpe',
                 lookback: int = 126,
                 min_weight: float = 0.05):
        self.metric = metric
        self.lookback = lookback
        self.min_weight = min_weight
    
    def allocate(self, strategies: List, context, data) -> Dict[str, float]:
        scores = {}
        
        for strat in strategies:
            returns = context.strategy_returns.get(strat.name, pd.Series())
            if len(returns) >= self.lookback:
                recent = returns[-self.lookback:]
                if self.metric == 'sharpe':
                    scores[strat.name] = (recent.mean() / recent.std() 
                                         if recent.std() > 0 else 0)
                elif self.metric == 'return':
                    scores[strat.name] = recent.sum()
            else:
                scores[strat.name] = 0
        
        # Normalize scores (clip negatives to min_weight)
        min_score = min(scores.values())
        if min_score < 0:
            scores = {k: v - min_score + 0.01 for k, v in scores.items()}
        
        total = sum(scores.values())
        weights = {k: max(v/total, self.min_weight) for k, v in scores.items()}
        
        # Renormalize
        total = sum(weights.values())
        return {k: v/total for k, v in weights.items()}
```

## Correlation Analysis

```python
def analyze_strategy_correlations(strategy_returns: Dict[str, pd.Series]) -> pd.DataFrame:
    """Analyze correlations between strategy returns."""
    returns_df = pd.DataFrame(strategy_returns)
    
    # Calculate correlation matrix
    corr_matrix = returns_df.corr()
    
    # Rolling correlations
    rolling_corr = returns_df.rolling(60).corr()
    
    return corr_matrix
```

### Ideal Diversification

| Correlation | Benefit |
|-------------|---------|
| < 0.3 | Excellent diversification |
| 0.3 - 0.5 | Good diversification |
| 0.5 - 0.7 | Moderate benefit |
| > 0.7 | Limited diversification |

## Strategy Tracking

```python
def initialize(context):
    context.manager = MultiStrategyManager(strategies, allocator)
    context.strategy_returns = {s.name: [] for s in strategies}
    context.strategy_values = {s.name: 1.0 for s in strategies}
    context.last_strategy_allocation = {}

def track_strategy_performance(context, data):
    """Track each strategy's hypothetical returns."""
    for strat in context.manager.strategies:
        # Get current targets
        targets = strat.get_target_weights(context, data)
        
        # Calculate hypothetical return
        daily_return = sum(
            weight * data.history(asset, 'price', 2, '1d').pct_change().iloc[-1]
            for asset, weight in targets.items()
            if data.can_trade(asset)
        )
        
        context.strategy_returns[strat.name].append(daily_return)
        context.strategy_values[strat.name] *= (1 + daily_return)
```

## Regime-Based Allocation

```python
class RegimeAllocator:
    """Allocate based on market regime."""
    
    def __init__(self, regime_detector: Callable,
                 regime_weights: Dict[str, Dict[str, float]]):
        """
        Parameters
        ----------
        regime_detector : Callable
            Function returning current regime string
        regime_weights : Dict
            Mapping of regime -> {strategy: weight}
        """
        self.regime_detector = regime_detector
        self.regime_weights = regime_weights
    
    def allocate(self, strategies, context, data):
        regime = self.regime_detector(context, data)
        return self.regime_weights.get(regime, {})

# Usage
def detect_regime(context, data):
    vix = data.current(symbol('VIX'), 'price')
    if vix > 25:
        return 'high_vol'
    elif vix < 15:
        return 'low_vol'
    return 'normal'

allocator = RegimeAllocator(
    regime_detector=detect_regime,
    regime_weights={
        'high_vol': {'momentum': 0.2, 'mean_rev': 0.5, 'value': 0.3},
        'normal': {'momentum': 0.4, 'mean_rev': 0.3, 'value': 0.3},
        'low_vol': {'momentum': 0.6, 'mean_rev': 0.2, 'value': 0.2},
    }
)
```

## Complete Example

```python
from zipline.api import *
from multi_strategy import (
    MultiStrategyManager, 
    MomentumStrategy, 
    MeanReversionStrategy,
    RiskParityAllocator
)

def initialize(context):
    strategies = [
        MomentumStrategy('momentum', {'period': 20}),
        MeanReversionStrategy('mean_rev', {'period': 10}),
    ]
    
    context.manager = MultiStrategyManager(
        strategies=strategies,
        allocator=RiskParityAllocator(target_vol=0.12),
        max_leverage=1.0
    )
    context.manager.initialize(context)
    
    schedule_function(
        rebalance,
        date_rules.week_start(),
        time_rules.market_open(hours=1)
    )

def rebalance(context, data):
    # Update allocations based on recent performance
    context.manager.update_allocations(context, data)
    
    # Get combined targets
    targets = context.manager.get_combined_targets(context, data)
    
    # Execute
    for asset in context.portfolio.positions:
        if asset not in targets:
            order_target_percent(asset, 0)
    
    for asset, weight in targets.items():
        if data.can_trade(asset):
            order_target_percent(asset, weight)

def handle_data(context, data):
    pass
```

## References

See `references/allocation_methods.md` for detailed allocation algorithms.
See `references/correlation_analysis.md` for diversification guidelines.
