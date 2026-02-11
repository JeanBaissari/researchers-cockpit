# Position Sizing API (`lib/position_sizing.py`)

This project uses **Zipline-Reloaded’s order APIs for execution**, and `lib/position_sizing.py` for **reusable position-size calculations**.

- **Zipline-Reloaded**: execute orders with `zipline.api.order_target_percent(asset, target_pct)`
- **This project**: compute a `target_pct` with `lib.position_sizing.compute_position_size(...)` (when you need a reusable algorithm), then pass it to `order_target_percent()`

See also: [Position Sizing Decision Guide](../code_patterns/position_sizing_decision_guide.md)

---

## Key Idea: Calculation vs Execution

### Execution (Zipline-Reloaded)

Use Zipline’s built-in order API to **set a target portfolio weight**:

```python
from zipline.api import order_target_percent

order_target_percent(asset, 0.25)  # target 25% of portfolio value
```

### Calculation (this project)

Use `lib/position_sizing.py` to compute a reusable target percentage based on configuration and market data, then execute with Zipline:

```python
from zipline.api import order_target_percent
from lib.position_sizing import compute_position_size

target_pct = compute_position_size(context, data, context.params)
order_target_percent(context.asset, target_pct)
```

`lib/position_sizing.py` **does not wrap Zipline** and **does not place orders**. It returns a float suitable for `order_target_percent()`.

---

## When to Use Zipline vs When to Use `lib/position_sizing`

### Use Zipline’s `order_target_percent()` directly (3 concrete examples)

1) **Fixed allocation (simple & explicit)**

```python
from zipline.api import order_target_percent

def rebalance(context, data):
    order_target_percent(context.asset, 0.50)
```

2) **Signal bucket sizing (strategy-specific)**

```python
from zipline.api import order_target_percent

def rebalance(context, data):
    signal = context.signal  # e.g., computed elsewhere
    if signal > 0.8:
        order_target_percent(context.asset, 0.90)
    elif signal > 0.5:
        order_target_percent(context.asset, 0.50)
    else:
        order_target_percent(context.asset, 0.0)
```

3) **Equal-weight rebalancing across a universe**

```python
from zipline.api import order_target_percent

def rebalance(context, data):
    w = 1.0 / len(context.assets)
    for asset in context.assets:
        if data.can_trade(asset):
            order_target_percent(asset, w)
```

### Use `lib/position_sizing.py` + `order_target_percent()` (3 concrete examples)

1) **Volatility-scaled sizing (target a volatility level)**

```python
from zipline.api import order_target_percent
from lib.position_sizing import compute_position_size

def rebalance(context, data):
    target_pct = compute_position_size(context, data, context.params)
    order_target_percent(context.asset, target_pct)
```

`parameters.yaml`:

```yaml
position_sizing:
  method: volatility_scaled
  max_position_pct: 0.95
  min_position_pct: 0.10
  volatility_lookback: 20
  volatility_target: 0.15
```

2) **Kelly Criterion sizing (parameterized & reusable)**

```python
from zipline.api import order_target_percent
from lib.position_sizing import compute_position_size

def rebalance(context, data):
    target_pct = compute_position_size(context, data, context.params)
    order_target_percent(context.asset, target_pct)
```

`parameters.yaml`:

```yaml
position_sizing:
  method: kelly
  max_position_pct: 0.95
  min_position_pct: 0.10
  kelly:
    win_rate_estimate: 0.55
    avg_win_loss_ratio: 1.5
    kelly_fraction: 0.25
```

3) **“Fixed” sizing but configured via YAML (so you can swap methods later)**

```python
from zipline.api import order_target_percent
from lib.position_sizing import compute_position_size

def rebalance(context, data):
    target_pct = compute_position_size(context, data, context.params)
    order_target_percent(context.asset, target_pct)
```

`parameters.yaml`:

```yaml
position_sizing:
  method: fixed
  max_position_pct: 0.60
  min_position_pct: 0.10
```

---

## API Reference

### `compute_position_size(context, data, params) -> float`

Computes a **target portfolio percentage** (float) that you should pass to Zipline’s `order_target_percent()`.

- **Inputs**
  - **`context`**: Zipline context (expected to hold `context.asset` and often `context.params`)
  - **`data`**: Zipline data portal (uses Zipline-Reloaded APIs like `data.history()` and `data.can_trade()`)
  - **`params`**: strategy parameters dict (usually from `parameters.yaml`)
- **Output**
  - **float**: in the range \([0.0, 1.0]\) (bounded by `min_position_pct`/`max_position_pct`)

Supported methods:

- **`fixed`**: returns `max_position_pct`
- **`volatility_scaled`**: scales position inversely with realized volatility over a lookback window
- **`kelly`**: fractional Kelly sizing based on a win-rate estimate and win/loss ratio

---

## Notes on Zipline-Reloaded Compatibility

- This module is designed to be used inside Zipline-Reloaded algorithms and complements Zipline’s target order functions.
- Order execution should remain **Zipline-native** (`order_target_percent`, `order_target_value`, etc.).

