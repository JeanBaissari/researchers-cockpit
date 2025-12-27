# Sharpe Ratio API Error - Empyrical Parameter Naming

## Problem

When running backtests, you encountered:

```
TypeError: sharpe_ratio() got an unexpected keyword argument 'risk_free_rate'
```

This error occurs when calling empyrical functions with incorrect parameter names.

## Root Cause

The `empyrical` library uses different parameter names than expected:

- `sharpe_ratio()` uses `risk_free` (not `risk_free_rate`)
- `sortino_ratio()` uses `required_return` (not `risk_free_rate`)
- `alpha()` uses `risk_free` (not `risk_free_rate`)
- `omega_ratio()` uses `risk_free` (not `risk_free_rate`)
- `beta()` uses `risk_free` (not `risk_free_rate`)

## Solution

**Fixed:** Updated all empyrical function calls in `lib/metrics.py` to use correct parameter names:

```python
# Before (incorrect)
ep.sharpe_ratio(returns, risk_free_rate=risk_free_rate, period='daily')
ep.sortino_ratio(returns, risk_free_rate=risk_free_rate, period='daily')
ep.alpha(returns, risk_free_rate=risk_free_rate, period='daily')

# After (correct)
ep.sharpe_ratio(returns, risk_free=risk_free_rate, period='daily')
ep.sortino_ratio(returns, required_return=risk_free_rate, period='daily')
ep.alpha(returns, returns, risk_free=risk_free_rate, period='daily')
```

## Files Modified

- `lib/metrics.py` - Fixed all empyrical API calls:
  - Line 66: `sharpe_ratio()` - changed to `risk_free`
  - Line 76: `sortino_ratio()` - changed to `required_return`
  - Line 109: `alpha()` - changed to `risk_free` (also fixed missing `factor_returns` parameter)
  - Line 110: `beta()` - changed to `risk_free`
  - Line 116: `omega_ratio()` - changed to `risk_free` and added `required_return`

## Verification

After the fix, verify metrics calculate correctly:

```bash
source venv/bin/activate
python3 -c "from lib.metrics import calculate_metrics; import pandas as pd; import numpy as np; test_returns = pd.Series(np.random.randn(100) * 0.01, index=pd.date_range('2020-01-01', periods=100)); metrics = calculate_metrics(test_returns); print('✓ Metrics calculation successful')"
```

Or run a full backtest:

```bash
python scripts/run_backtest.py --strategy spy_sma_cross --start 2020-01-01 --end 2025-12-01
```

## Empyrical API Reference

To check empyrical function signatures:

```python
import empyrical as ep
import inspect

print(inspect.signature(ep.sharpe_ratio))
print(inspect.signature(ep.sortino_ratio))
print(inspect.signature(ep.alpha))
print(inspect.signature(ep.omega_ratio))
print(inspect.signature(ep.beta))
```

## Related Issues

- Similar parameter naming issues may exist in other empyrical function calls
- Always verify function signatures when updating dependencies

## Date Fixed

2025-01-23



