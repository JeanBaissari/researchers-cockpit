# Strategy Examples

> Complete algorithm templates for common strategies.

## Buy and Hold

```python
from zipline.api import symbol, order_target_percent

def initialize(context):
    context.asset = symbol('SPY')

def handle_data(context, data):
    if context.asset not in context.portfolio.positions:
        order_target_percent(context.asset, 1.0)
```

---

## Moving Average Crossover

```python
from zipline.api import symbol, order_target_percent, record

def initialize(context):
    context.asset = symbol('AAPL')
    context.fast = 10
    context.slow = 30

def handle_data(context, data):
    prices = data.history(context.asset, 'price', context.slow + 1, '1d')
    
    fast_ma = prices[-context.fast:].mean()
    slow_ma = prices.mean()
    
    if fast_ma > slow_ma:
        order_target_percent(context.asset, 1.0)
    else:
        order_target_percent(context.asset, 0.0)
    
    record(fast_ma=fast_ma, slow_ma=slow_ma)
```

---

## Mean Reversion

```python
from zipline.api import symbol, order_target_percent
import numpy as np

def initialize(context):
    context.asset = symbol('AAPL')
    context.lookback = 20
    context.z_threshold = 2.0

def handle_data(context, data):
    prices = data.history(context.asset, 'price', context.lookback, '1d')
    
    mean = prices.mean()
    std = prices.std()
    current = prices[-1]
    
    z_score = (current - mean) / std
    
    if z_score < -context.z_threshold:
        order_target_percent(context.asset, 1.0)
    elif z_score > context.z_threshold:
        order_target_percent(context.asset, 0.0)
```

---

## Momentum with Rebalancing

```python
from zipline.api import (
    symbols, order_target_percent,
    schedule_function, date_rules, time_rules
)

def initialize(context):
    context.assets = symbols('AAPL', 'MSFT', 'GOOGL', 'AMZN')
    context.lookback = 60
    context.n_positions = 2
    
    schedule_function(
        rebalance,
        date_rules.month_start(),
        time_rules.market_open(minutes=30)
    )

def rebalance(context, data):
    # Calculate momentum
    momentum = {}
    for asset in context.assets:
        if data.can_trade(asset):
            prices = data.history(asset, 'price', context.lookback, '1d')
            momentum[asset] = (prices[-1] / prices[0]) - 1
    
    # Rank and select top N
    ranked = sorted(momentum.items(), key=lambda x: x[1], reverse=True)
    winners = [asset for asset, _ in ranked[:context.n_positions]]
    
    # Rebalance
    weight = 1.0 / context.n_positions
    for asset in context.assets:
        if asset in winners:
            order_target_percent(asset, weight)
        else:
            order_target_percent(asset, 0)
```

---

## Pipeline-Based Strategy

```python
from zipline.api import (
    attach_pipeline, pipeline_output,
    order_target_percent,
    schedule_function, date_rules, time_rules
)
from zipline.pipeline import Pipeline
from zipline.pipeline.factors import Returns, AverageDollarVolume

def initialize(context):
    attach_pipeline(make_pipeline(), 'my_pipeline')
    
    schedule_function(
        rebalance,
        date_rules.week_start(),
        time_rules.market_open()
    )

def make_pipeline():
    returns = Returns(window_length=20)
    volume = AverageDollarVolume(window_length=20)
    
    universe = volume.top(500)
    longs = returns.top(10, mask=universe)
    shorts = returns.bottom(10, mask=universe)
    
    return Pipeline(
        columns={
            'longs': longs,
            'shorts': shorts
        },
        screen=longs | shorts
    )

def before_trading_start(context, data):
    context.output = pipeline_output('my_pipeline')
    context.longs = context.output[context.output['longs']].index.tolist()
    context.shorts = context.output[context.output['shorts']].index.tolist()

def rebalance(context, data):
    # Equal weight long/short
    long_weight = 0.5 / max(len(context.longs), 1)
    short_weight = -0.5 / max(len(context.shorts), 1)
    
    for asset in context.longs:
        if data.can_trade(asset):
            order_target_percent(asset, long_weight)
    
    for asset in context.shorts:
        if data.can_trade(asset):
            order_target_percent(asset, short_weight)
```

---

## RSI Strategy

```python
from zipline.api import symbol, order_target_percent
import numpy as np

def initialize(context):
    context.asset = symbol('AAPL')
    context.period = 14
    context.oversold = 30
    context.overbought = 70

def compute_rsi(prices, period):
    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    avg_gain = np.mean(gains[-period:])
    avg_loss = np.mean(losses[-period:])
    
    if avg_loss == 0:
        return 100
    
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def handle_data(context, data):
    prices = data.history(context.asset, 'price', context.period + 2, '1d')
    rsi = compute_rsi(prices.values, context.period)
    
    if rsi < context.oversold:
        order_target_percent(context.asset, 1.0)
    elif rsi > context.overbought:
        order_target_percent(context.asset, 0.0)
```

---

## Pairs Trading

```python
from zipline.api import symbols, order_target_percent
import numpy as np

def initialize(context):
    context.stock1, context.stock2 = symbols('KO', 'PEP')
    context.lookback = 30
    context.z_entry = 2.0
    context.z_exit = 0.5

def handle_data(context, data):
    p1 = data.history(context.stock1, 'price', context.lookback, '1d')
    p2 = data.history(context.stock2, 'price', context.lookback, '1d')
    
    # Calculate spread
    spread = p1 / p2
    z_score = (spread[-1] - spread.mean()) / spread.std()
    
    # Trading logic
    if z_score > context.z_entry:
        # Spread too high: short stock1, long stock2
        order_target_percent(context.stock1, -0.5)
        order_target_percent(context.stock2, 0.5)
    elif z_score < -context.z_entry:
        # Spread too low: long stock1, short stock2
        order_target_percent(context.stock1, 0.5)
        order_target_percent(context.stock2, -0.5)
    elif abs(z_score) < context.z_exit:
        # Exit positions
        order_target_percent(context.stock1, 0)
        order_target_percent(context.stock2, 0)
```

---

## See Also

- [Algorithm Lifecycle](../00_getting_started/algorithm_lifecycle.md)
- [Pipeline Overview](../06_pipeline/pipeline_overview.md)
- [Quick Reference](quick_reference.md)
