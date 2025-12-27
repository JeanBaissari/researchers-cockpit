# Parameter Validation

## Overview

Strategy parameters are validated before backtest execution to catch configuration errors early.

## Validation Rules

### Required Fields

- `strategy.asset_symbol` - Must be non-empty string
- `strategy.rebalance_frequency` - Must be one of: 'daily', 'weekly', 'monthly'

### Type Checks

- `position_sizing.max_position_pct` - Must be number between 0.0 and 1.0
- `risk.stop_loss_pct` - Must be positive number
- `strategy.minutes_after_open` - Must be integer between 0 and 60

### Range Checks

- `risk.take_profit_pct` - Must be greater than `stop_loss_pct` (if both provided)
- `position_sizing.max_position_pct` - Must be ≤ 1.0 (100%)

### Enum Checks

- `strategy.rebalance_frequency` - Must be 'daily', 'weekly', or 'monthly'
- `position_sizing.method` - Must be 'fixed', 'volatility_scaled', or 'kelly'

## Usage

```python
from lib.config import validate_strategy_params, load_strategy_params

# Load and validate parameters
params = load_strategy_params('spy_sma_cross', asset_class='equities')
is_valid, errors = validate_strategy_params(params, 'spy_sma_cross')

if not is_valid:
    print("Validation errors:")
    for error in errors:
        print(f"  - {error}")
```

## Error Messages

Validation errors are clear and actionable:

```
Invalid parameters for strategy 'spy_sma_cross':
  - Missing required parameter: 'strategy.asset_symbol'
  - 'position_sizing.max_position_pct' must be between 0.0 and 1.0. Got: 1.5
  - 'risk.take_profit_pct' (0.03) should be greater than 'risk.stop_loss_pct' (0.05)
```

## Integration

Parameter validation is automatically called:
- In `lib/backtest.py::run_backtest()` after loading parameters
- In `scripts/run_backtest.py` before executing backtest

## Date Fixed

2025-01-23



