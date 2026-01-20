# Execution Styles

> Order types for controlling how orders are filled.

## ExecutionStyle Base Class

```python
class zipline.finance.execution.ExecutionStyle
```

### Properties

- `exchange` - Target exchange for routing (if applicable)

### Abstract Methods

- `get_limit_price(is_buy)` - Returns limit price or None
- `get_stop_price(is_buy)` - Returns stop price or None

---

## MarketOrder

Execute at current market price. **This is the default.**

```python
class zipline.finance.execution.MarketOrder(exchange=None)
```

### Usage

```python
from zipline.finance.execution import MarketOrder

# Explicit market order
order(asset, 100, style=MarketOrder())

# Implicit (default behavior)
order(asset, 100)
```

### Behavior

- Fills at current bar's price
- No price guarantee
- Always fills if asset is tradeable

---

## LimitOrder

Execute only at specified price or better.

```python
class zipline.finance.execution.LimitOrder(limit_price, asset=None, exchange=None)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `limit_price` | float | Maximum price for buys, minimum for sells |

### Usage

```python
from zipline.finance.execution import LimitOrder

# Buy only if price is $150 or less
order(asset, 100, style=LimitOrder(150.00))

# Alternative: use limit_price parameter
order(asset, 100, limit_price=150.00)
```

### Behavior

- **Buy**: Fills only if price ≤ limit_price
- **Sell**: Fills only if price ≥ limit_price
- May not fill if price doesn't reach limit

---

## StopOrder

Trigger a market order when price reaches threshold.

```python
class zipline.finance.execution.StopOrder(stop_price, asset=None, exchange=None)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `stop_price` | float | Price threshold that triggers the order |

### Usage

```python
from zipline.finance.execution import StopOrder

# Stop loss: sell if price drops to $145
order(asset, -100, style=StopOrder(145.00))

# Stop entry: buy if price rises to $155
order(asset, 100, style=StopOrder(155.00))

# Alternative: use stop_price parameter
order(asset, -100, stop_price=145.00)
```

### Behavior

- **Sell (stop loss)**: Triggers market order when price falls below stop_price
- **Buy (stop entry)**: Triggers market order when price rises above stop_price
- Once triggered, becomes a market order

---

## StopLimitOrder

Trigger a limit order when price reaches threshold.

```python
class zipline.finance.execution.StopLimitOrder(limit_price, stop_price, asset=None, exchange=None)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `limit_price` | float | Limit price after triggered |
| `stop_price` | float | Price that triggers the order |

### Usage

```python
from zipline.finance.execution import StopLimitOrder

# Stop loss with limit: if drops to $145, sell at $144 or better
order(asset, -100, style=StopLimitOrder(144.00, 145.00))

# Alternative: use both parameters
order(asset, -100, limit_price=144.00, stop_price=145.00)
```

### Behavior

1. When price reaches `stop_price`, order becomes active
2. Active order fills only at `limit_price` or better
3. May not fill if price moves too fast past limit

---

## Common Patterns

### Basic Stop Loss

```python
def handle_data(context, data):
    current = data.current(context.asset, 'price')
    
    # Set stop 5% below current price
    stop = current * 0.95
    
    # Place protective stop
    order(context.asset, -context.shares_held, stop_price=stop)
```

### Trailing Stop (Manual)

```python
def initialize(context):
    context.highest = 0

def handle_data(context, data):
    current = data.current(context.asset, 'price')
    context.highest = max(context.highest, current)
    
    # Stop at 10% below highest
    stop = context.highest * 0.90
    
    if current <= stop:
        order_target(context.asset, 0)
```

### Limit Buy Below Market

```python
def handle_data(context, data):
    current = data.current(context.asset, 'price')
    
    # Try to buy 2% below current price
    limit = current * 0.98
    order(context.asset, 100, limit_price=limit)
```

### Bracket Order (Entry + Stop + Target)

```python
def handle_data(context, data):
    current = data.current(context.asset, 'price')
    
    # Entry
    order(context.asset, 100)
    
    # Stop loss at 5% down
    order(context.asset, -100, stop_price=current * 0.95)
    
    # Take profit at 10% up (limit sell)
    order(context.asset, -100, limit_price=current * 1.10)
```

---

## Order Type Summary

| Type | Trigger | Fill |
|------|---------|------|
| Market | Immediate | At market |
| Limit | Immediate | At limit or better |
| Stop | At stop price | At market |
| StopLimit | At stop price | At limit or better |

---

## See Also

- [Basic Orders](basic_orders.md)
- [Target Orders](target_orders.md)
- [Order Management](order_management.md)
