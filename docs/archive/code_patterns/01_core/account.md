# Account

> Access account-level information via `context.account`.

## Overview

The Account object provides read-only access to account-level metrics like leverage, buying power, and margin information. Access it through `context.account` in any lifecycle function.

---

## Account Class

```python
class zipline.protocol.Account
```

## Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `settled_cash` | float | Cash available for trading |
| `accrued_interest` | float | Interest accrued but not yet paid |
| `buying_power` | float | Available buying power |
| `equity_with_loan` | float | Equity value including margin loans |
| `total_positions_value` | float | Sum of all position values |
| `total_positions_exposure` | float | Sum of all position exposures |
| `regt_equity` | float | Regulation T equity |
| `regt_margin` | float | Regulation T margin |
| `initial_margin_requirement` | float | Initial margin required |
| `maintenance_margin_requirement` | float | Maintenance margin required |
| `available_funds` | float | Funds available for trading |
| `excess_liquidity` | float | Excess liquidity above margin |
| `cushion` | float | Cushion percentage |
| `day_trades_remaining` | int | Pattern day trades remaining |
| `leverage` | float | Current leverage ratio |
| `net_leverage` | float | Net leverage (long - short) |
| `net_liquidation` | float | Net liquidation value |

---

## Examples

### Check Leverage

```python
def handle_data(context, data):
    if context.account.leverage > 1.5:
        # Reduce exposure
        for asset in context.portfolio.positions:
            order_target_percent(asset, 0.5)
```

### Monitor Buying Power

```python
def handle_data(context, data):
    buying_power = context.account.buying_power
    
    if buying_power > 50000:
        # Have capacity for new positions
        order_value(context.asset, 10000)
```

### Record Account Metrics

```python
def handle_data(context, data):
    acct = context.account
    
    record(
        leverage=acct.leverage,
        net_leverage=acct.net_leverage,
        buying_power=acct.buying_power
    )
```

### Leverage-Based Position Sizing

```python
def handle_data(context, data):
    max_leverage = 1.5
    current_leverage = context.account.leverage
    
    if current_leverage < max_leverage:
        # Calculate available leverage capacity
        available = max_leverage - current_leverage
        
        # Size new position within limits
        position_size = min(0.1, available)
        order_target_percent(context.asset, position_size)
```

### Margin Check Before Trading

```python
def handle_data(context, data):
    acct = context.account
    
    # Ensure sufficient margin cushion
    if acct.cushion > 0.25:
        # Safe to add positions
        order(context.asset, 100)
    else:
        log.warn("Margin cushion too low")
```

---

## Leverage Calculation

```
leverage = gross_exposure / net_liquidation

gross_exposure = sum(abs(position_value) for all positions)
net_liquidation = cash + positions_value
```

### Example

```
Long $60,000 AAPL
Short $40,000 MSFT
Cash: $50,000

gross_exposure = $60,000 + $40,000 = $100,000
net_liquidation = $50,000 + $60,000 - $40,000 = $70,000
leverage = $100,000 / $70,000 = 1.43
```

---

## Net vs Gross Leverage

| Metric | Formula | Use Case |
|--------|---------|----------|
| `leverage` | gross / net_liq | Total risk exposure |
| `net_leverage` | (long - short) / net_liq | Directional exposure |

```python
def handle_data(context, data):
    # Gross leverage: total exposure regardless of direction
    gross = context.account.leverage
    
    # Net leverage: directional exposure
    net = context.account.net_leverage
    
    print(f"Gross: {gross:.2f}x, Net: {net:.2f}x")
```

---

## Notes

- Account is **read-only** - you cannot directly modify values
- Values update after each order fills
- Leverage limits are enforced by trading controls, not account object
- Use `set_max_leverage()` to enforce leverage limits

---

## See Also

- [Portfolio](portfolio.md)
- [Context Object](context.md)
- [Trading Controls](../05_assets/trading_controls.md)
