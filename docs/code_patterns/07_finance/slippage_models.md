# Slippage Models

> Simulate market impact and execution costs.

## set_slippage()

Configure slippage model.

```python
zipline.api.set_slippage(us_equities=None, us_futures=None)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `us_equities` | SlippageModel | Model for equities |
| `us_futures` | SlippageModel | Model for futures |

---

## VolumeShareSlippage

Price impact based on order size relative to volume.

```python
from zipline.api import set_slippage
from zipline.finance.slippage import VolumeShareSlippage

set_slippage(
    us_equities=VolumeShareSlippage(
        volume_limit=0.025,
        price_impact=0.1
    )
)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `volume_limit` | float | Max % of bar volume to fill (0.025 = 2.5%) |
| `price_impact` | float | Price impact coefficient |

### How It Works

1. **Volume Constraint**: Can only fill up to `volume_limit` × bar_volume per bar
2. **Price Impact**: Execution price is worse than bar price

```
price_impact_pct = volume_share × price_impact
execution_price = bar_price × (1 + price_impact_pct)  # for buys
execution_price = bar_price × (1 - price_impact_pct)  # for sells
```

### Example

```
Buy 10,000 shares
Bar volume: 100,000
volume_limit: 0.025

Max fillable = 100,000 × 0.025 = 2,500 shares
Remaining 7,500 carries to next bar

Volume share = 2,500 / 100,000 = 0.025
Price impact = 0.025 × 0.1 = 0.0025 (0.25%)
If bar_price = $100:
  Execution = $100 × 1.0025 = $100.25
```

---

## FixedSlippage

Fixed spread per share.

```python
from zipline.finance.slippage import FixedSlippage

set_slippage(
    us_equities=FixedSlippage(spread=0.01)
)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `spread` | float | Fixed spread per share |

### How It Works

```
Buy: execution_price = bar_price + spread/2
Sell: execution_price = bar_price - spread/2
```

---

## FixedBasisPointsSlippage

Slippage as basis points of price.

```python
from zipline.finance.slippage import FixedBasisPointsSlippage

# 5 basis points
set_slippage(
    us_equities=FixedBasisPointsSlippage(basis_points=5.0)
)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `basis_points` | float | Slippage in bps (5.0 = 0.05%) |
| `volume_limit` | float | Max % of volume to fill |

---

## NoSlippage

Fill at exact bar price (unrealistic).

```python
from zipline.finance.slippage import NoSlippage

set_slippage(us_equities=NoSlippage())
```

---

## Common Configurations

### Conservative (Retail)

```python
def initialize(context):
    set_slippage(
        us_equities=VolumeShareSlippage(
            volume_limit=0.025,  # 2.5% of volume
            price_impact=0.1
        )
    )
```

### Institutional

```python
def initialize(context):
    set_slippage(
        us_equities=VolumeShareSlippage(
            volume_limit=0.1,   # Can access more volume
            price_impact=0.05  # Lower impact per share
        )
    )
```

### High Frequency

```python
def initialize(context):
    # Need very liquid stocks
    set_slippage(
        us_equities=FixedBasisPointsSlippage(
            basis_points=1.0,
            volume_limit=0.01
        )
    )
```

### Realistic Testing

```python
def initialize(context):
    set_commission(us_equities=PerShare(cost=0.005, min_trade_cost=1.0))
    set_slippage(us_equities=VolumeShareSlippage(volume_limit=0.025, price_impact=0.1))
```

---

## Multi-Day Fill Example

With `volume_limit=0.025`:

```
Day 1:
  Order: Buy 10,000 shares
  Volume: 100,000
  Can fill: 2,500 (2.5%)
  Remaining: 7,500

Day 2:
  Volume: 80,000
  Can fill: 2,000 (2.5%)
  Remaining: 5,500

Day 3:
  Volume: 120,000
  Can fill: 3,000 (2.5%)
  Remaining: 2,500

Day 4:
  Volume: 100,000
  Can fill: 2,500 (all remaining)
  Order complete
```

---

## Slippage Impact Analysis

```python
def analyze(context, perf):
    for date, txns in perf['transactions'].items():
        for txn in txns:
            # txn contains actual execution price
            # Compare to theoretical price for slippage analysis
            print(f"Asset: {txn['sid']}")
            print(f"Amount: {txn['amount']}")
            print(f"Price: {txn['price']}")
```

---

## Best Practices

### Match to Strategy

```python
# High turnover = needs tighter slippage modeling
# Low turnover = can use simpler model

if strategy_type == 'momentum':
    # More trading, need realistic slippage
    set_slippage(us_equities=VolumeShareSlippage(0.025, 0.1))
elif strategy_type == 'value':
    # Less trading
    set_slippage(us_equities=FixedBasisPointsSlippage(5.0))
```

### Test Sensitivity

```python
for impact in [0.05, 0.1, 0.15, 0.2]:
    results = run_algorithm(
        ...,
        initialize=lambda ctx: set_slippage(
            us_equities=VolumeShareSlippage(0.025, impact)
        )
    )
    print(f"Impact {impact}: Sharpe {compute_sharpe(results):.2f}")
```

---

## See Also

- [Commission Models](commission_models.md)
- [Blotter](blotter.md)
- [Trading Controls](../05_assets/trading_controls.md)
