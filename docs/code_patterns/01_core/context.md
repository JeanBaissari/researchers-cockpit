# Context Object

> The `context` object stores algorithm state across function calls.

## Overview

The `context` object is your algorithm's persistent namespace. It's passed to every lifecycle function and preserves state between calls.

```python
def initialize(context):
    context.asset = symbol('AAPL')
    context.lookback = 20
    context.target_weight = 0.5

def handle_data(context, data):
    # Access values set in initialize
    price = data.current(context.asset, 'price')
```

---

## Lifecycle Access

| Function | Has `context` | Has `data` |
|----------|---------------|------------|
| `initialize()` | ✓ | ✗ |
| `before_trading_start()` | ✓ | ✓ |
| `handle_data()` | ✓ | ✓ |
| `analyze()` | ✓ | ✗ |
| Scheduled functions | ✓ | ✓ |

---

## Built-in Attributes

The context object provides access to portfolio and account state:

### context.portfolio

Read-only access to current portfolio state.

```python
def handle_data(context, data):
    cash = context.portfolio.cash
    value = context.portfolio.portfolio_value
    positions = context.portfolio.positions
```

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `cash` | float | Available cash |
| `portfolio_value` | float | Total portfolio value |
| `positions` | dict | Current positions |
| `starting_cash` | float | Initial capital |
| `returns` | float | Cumulative returns |

### context.account

Read-only access to account information.

```python
def handle_data(context, data):
    leverage = context.account.leverage
    buying_power = context.account.buying_power
```

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `leverage` | float | Current leverage |
| `buying_power` | float | Available buying power |
| `net_liquidation` | float | Net liquidation value |

---

## Custom Attributes

Store any Python object on context:

```python
def initialize(context):
    # Simple values
    context.stop_loss_pct = 0.02
    
    # Collections
    context.watchlist = ['AAPL', 'MSFT', 'GOOGL']
    context.signals = {}
    
    # Complex objects
    context.model = None  # Set later
```

---

## Common Patterns

### Strategy Parameters

```python
def initialize(context):
    context.params = {
        'fast_period': 10,
        'slow_period': 30,
        'threshold': 0.02,
        'max_position': 0.1
    }
```

### State Tracking

```python
def initialize(context):
    context.days_held = {}
    context.entry_prices = {}
    context.last_rebalance = None

def handle_data(context, data):
    for asset in context.portfolio.positions:
        context.days_held[asset] = context.days_held.get(asset, 0) + 1
```

### Flag Variables

```python
def initialize(context):
    context.first_trade = True
    context.rebalance_needed = False
    context.warmup_complete = False
```

---

## Best Practices

1. **Initialize everything** - Set all context variables in `initialize()`
2. **Use descriptive names** - `context.momentum_lookback` not `context.n`
3. **Group related values** - Use dicts or named tuples for parameters
4. **Don't store data** - Use `data.history()` instead of caching prices
5. **Avoid large objects** - Context persists in memory throughout backtest

---

## See Also

- [Algorithm Lifecycle](../00_getting_started/algorithm_lifecycle.md)
- [Portfolio Access](portfolio.md)
- [Account Access](account.md)
