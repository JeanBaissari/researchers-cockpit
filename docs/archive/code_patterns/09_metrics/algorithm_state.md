# Algorithm State

> Track portfolio, positions, and account information.

## Ledger

```python
class zipline.finance.ledger.Ledger(
    trading_sessions, capital_base, data_frequency
)
```

Central tracker for orders, transactions, and portfolio state.

### Key Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `portfolio` | Portfolio | Current portfolio state |
| `account` | Account | Current account state |
| `position_tracker` | PositionTracker | Position details |
| `todays_returns` | float | Current day's returns |
| `daily_returns_series` | Series | All daily returns |

### Key Methods

| Method | Description |
|--------|-------------|
| `orders(dt=None)` | Get orders for a bar or all |
| `transactions(dt=None)` | Get transactions for a bar or all |
| `update_portfolio()` | Force portfolio recomputation |

---

## Portfolio

```python
class zipline.protocol.Portfolio(start_date=None, capital_base=0.0)
```

Read-only access to portfolio state via `context.portfolio`.

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `cash` | float | Available cash |
| `portfolio_value` | float | Total value (cash + positions) |
| `positions` | Positions | Dict-like of current positions |
| `starting_cash` | float | Initial capital |
| `returns` | float | Cumulative returns |
| `pnl` | float | Profit and loss |
| `positions_value` | float | Total position value |
| `positions_exposure` | float | Total position exposure |

### current_portfolio_weights

```python
portfolio.current_portfolio_weights
```

Returns dict mapping assets to portfolio weight (value / total value).

### Example

```python
def handle_data(context, data):
    port = context.portfolio
    
    # Check cash available
    if port.cash > 10000:
        # Place order
        pass
    
    # Check current positions
    for asset, position in port.positions.items():
        print(f"{asset}: {position.amount} shares")
    
    # Get weights
    weights = port.current_portfolio_weights
```

---

## Position

Individual position within the portfolio.

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `asset` | Asset | The held asset |
| `amount` | int | Number of shares |
| `cost_basis` | float | Average cost per share |
| `last_sale_price` | float | Most recent price |
| `last_sale_date` | Timestamp | Most recent trade date |

### Example

```python
def handle_data(context, data):
    pos = context.portfolio.positions.get(context.asset)
    
    if pos:
        shares = pos.amount
        avg_cost = pos.cost_basis
        current_price = pos.last_sale_price
        unrealized_pnl = (current_price - avg_cost) * shares
```

---

## Account

```python
class zipline.protocol.Account
```

Read-only access to account state via `context.account`.

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `settled_cash` | float | Settled cash balance |
| `buying_power` | float | Available buying power |
| `equity_with_loan` | float | Equity including margin |
| `total_positions_value` | float | Sum of position values |
| `total_positions_exposure` | float | Sum of position exposures |
| `leverage` | float | Current leverage ratio |
| `net_leverage` | float | Net leverage |
| `net_liquidation` | float | Liquidation value |

### Example

```python
def handle_data(context, data):
    acct = context.account
    
    # Check leverage
    if acct.leverage > 1.5:
        # Reduce positions
        pass
    
    # Check buying power
    available = acct.buying_power
```

---

## PositionTracker

Detailed position tracking with exposure calculations.

### Key Attributes

| Attribute | Description |
|-----------|-------------|
| `position_amounts` | Series of position sizes |
| `position_exposure_array` | Exposure by asset |
| `position_exposure_series` | Exposure as Series |

---

## Common Patterns

### Portfolio Rebalancing

```python
def rebalance(context, data):
    weights = context.portfolio.current_portfolio_weights
    target = 1.0 / len(context.assets)
    
    for asset in context.assets:
        current = weights.get(asset, 0)
        if abs(current - target) > 0.01:
            order_target_percent(asset, target)
```

### Position Sizing

```python
def handle_data(context, data):
    cash = context.portfolio.cash
    price = data.current(context.asset, 'price')
    
    # Size position to 10% of portfolio
    target_value = context.portfolio.portfolio_value * 0.10
    shares = int(target_value / price)
```

---

## See Also

- [Context Object](../01_core/context.md)
- [Target Orders](../04_orders/target_orders.md)
- [Risk Metrics](risk_metrics.md)
