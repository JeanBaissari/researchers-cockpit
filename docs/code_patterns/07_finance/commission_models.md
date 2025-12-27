# Commission Models

> Simulate trading costs in backtests.

## set_commission()

Configure commission model.

```python
zipline.api.set_commission(us_equities=None, us_futures=None)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `us_equities` | CommissionModel | Model for equities |
| `us_futures` | CommissionModel | Model for futures |

---

## PerShare

Fixed cost per share traded.

```python
from zipline.api import set_commission
from zipline.finance.commission import PerShare

# $0.005 per share, $1 minimum
set_commission(us_equities=PerShare(cost=0.005, min_trade_cost=1.0))
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `cost` | float | Cost per share |
| `min_trade_cost` | float | Minimum per trade |

### Example Calculation

```
Buy 100 shares:
  100 × $0.005 = $0.50
  But min is $1.00
  Commission = $1.00

Buy 500 shares:
  500 × $0.005 = $2.50
  Commission = $2.50
```

---

## PerTrade

Fixed cost per trade.

```python
from zipline.finance.commission import PerTrade

# $9.99 flat per trade
set_commission(us_equities=PerTrade(cost=9.99))
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `cost` | float | Cost per trade |

---

## PerDollar

Cost as percentage of trade value.

```python
from zipline.finance.commission import PerDollar

# 0.1% of trade value
set_commission(us_equities=PerDollar(cost=0.001))
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `cost` | float | Cost as decimal (0.001 = 0.1%) |

### Example Calculation

```
Buy $10,000 of stock:
  $10,000 × 0.001 = $10.00
  Commission = $10.00
```

---

## No Commission

```python
from zipline.finance.commission import NoCommission

set_commission(us_equities=NoCommission())
```

---

## Common Configurations

### Interactive Brokers Style

```python
def initialize(context):
    # IB-like: $0.005/share, $1 min
    set_commission(
        us_equities=PerShare(cost=0.005, min_trade_cost=1.0)
    )
```

### Discount Broker

```python
def initialize(context):
    # Free trading (Robinhood style)
    set_commission(
        us_equities=NoCommission()
    )
```

### Full-Service Broker

```python
def initialize(context):
    # Higher fixed cost
    set_commission(
        us_equities=PerTrade(cost=19.95)
    )
```

### Institutional

```python
def initialize(context):
    # Basis point model
    set_commission(
        us_equities=PerDollar(cost=0.0005)  # 5 bps
    )
```

### Futures

```python
from zipline.finance.commission import PerContract

def initialize(context):
    set_commission(
        us_futures=PerContract(cost=2.25, exchange_fee=0.01)
    )
```

---

## Impact on Performance

```python
def analyze(context, perf):
    # Total commissions paid
    total_commission = perf['capital_used'].abs().sum() * commission_rate
    
    # Or check transactions
    for date, txns in perf['transactions'].items():
        for txn in txns:
            print(f"Commission: {txn['commission']}")
```

---

## Best Practices

### Start Conservative

```python
def initialize(context):
    # Use realistic costs for live trading prep
    set_commission(us_equities=PerShare(cost=0.005, min_trade_cost=1.0))
    set_slippage(us_equities=VolumeShareSlippage())
```

### Test Sensitivity

```python
# Test with different commission levels
for cost in [0.0, 0.001, 0.005, 0.01]:
    results = run_algorithm(
        ...,
        initialize=lambda ctx: set_commission(us_equities=PerShare(cost=cost))
    )
    print(f"Cost {cost}: Return {results['returns'].sum():.2%}")
```

### Document Assumptions

```python
def initialize(context):
    # Commission assumptions:
    # - Interactive Brokers tiered pricing
    # - $0.0035/share for > 300k shares/month
    # - $1.00 minimum per order
    set_commission(us_equities=PerShare(cost=0.0035, min_trade_cost=1.0))
```

---

## Notes

- Commission is deducted from cash when trade fills
- Affects PnL and available capital
- Applied per transaction (not per order)
- Separate models for equities and futures

---

## See Also

- [Slippage Models](slippage_models.md)
- [Blotter](blotter.md)
- [run_algorithm()](../00_getting_started/run_algorithm.md)
