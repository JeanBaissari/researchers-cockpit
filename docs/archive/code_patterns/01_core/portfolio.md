# Portfolio

> Access current portfolio state via `context.portfolio`.

## Overview

The Portfolio object provides read-only access to your algorithm's current holdings, cash, and performance metrics. Access it through `context.portfolio` in any lifecycle function.

---

## Portfolio Class

```python
class zipline.protocol.Portfolio(start_date=None, capital_base=0.0)
```

## Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `cash` | float | Available cash balance |
| `portfolio_value` | float | Total value (cash + positions) |
| `positions` | Positions | Dict-like of current positions |
| `starting_cash` | float | Initial capital at backtest start |
| `returns` | float | Cumulative returns since start |
| `pnl` | float | Total profit and loss |
| `positions_value` | float | Sum of all position values |
| `positions_exposure` | float | Sum of all position exposures |
| `start_date` | Timestamp | Backtest start date |

---

## Methods

### current_portfolio_weights

```python
portfolio.current_portfolio_weights
```

Returns dictionary mapping assets to their portfolio weight (position value / total portfolio value).

```python
def handle_data(context, data):
    weights = context.portfolio.current_portfolio_weights
    
    for asset, weight in weights.items():
        print(f"{asset.symbol}: {weight:.2%}")
```

---

## Examples

### Check Available Cash

```python
def handle_data(context, data):
    if context.portfolio.cash > 10000:
        order(context.asset, 100)
```

### Iterate Positions

```python
def handle_data(context, data):
    for asset, position in context.portfolio.positions.items():
        print(f"{asset.symbol}: {position.amount} shares")
        print(f"  Cost basis: ${position.cost_basis:.2f}")
        print(f"  Current: ${position.last_sale_price:.2f}")
```

### Calculate Unrealized PnL

```python
def handle_data(context, data):
    for asset, pos in context.portfolio.positions.items():
        unrealized = (pos.last_sale_price - pos.cost_basis) * pos.amount
        print(f"{asset.symbol} unrealized PnL: ${unrealized:.2f}")
```

### Portfolio Metrics

```python
def handle_data(context, data):
    port = context.portfolio
    
    record(
        portfolio_value=port.portfolio_value,
        cash=port.cash,
        returns=port.returns,
        pnl=port.pnl
    )
```

### Rebalancing Based on Weights

```python
def rebalance(context, data):
    current_weights = context.portfolio.current_portfolio_weights
    target_weight = 1.0 / len(context.assets)
    
    for asset in context.assets:
        current = current_weights.get(asset, 0)
        
        # Rebalance if drift > 5%
        if abs(current - target_weight) > 0.05:
            order_target_percent(asset, target_weight)
```

### Check if Holding Position

```python
def handle_data(context, data):
    if context.asset in context.portfolio.positions:
        pos = context.portfolio.positions[context.asset]
        if pos.amount > 0:
            print("Currently long")
        elif pos.amount < 0:
            print("Currently short")
    else:
        print("No position")
```

---

## Position Object

Each position in `portfolio.positions` has these attributes:

| Attribute | Type | Description |
|-----------|------|-------------|
| `asset` | Asset | The held asset |
| `amount` | int | Number of shares (negative if short) |
| `cost_basis` | float | Average cost per share |
| `last_sale_price` | float | Most recent trade price |
| `last_sale_date` | Timestamp | Most recent trade date |

---

## Notes

- Portfolio is **read-only** - you cannot directly modify values
- `positions` only contains assets with non-zero holdings
- `portfolio_value` = `cash` + `positions_value`
- Values update after each order fills

---

## See Also

- [Account](account.md)
- [Context Object](context.md)
- [Algorithm State](../09-metrics/algorithm-state.md)
