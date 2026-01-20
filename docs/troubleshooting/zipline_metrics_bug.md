# Zipline Metrics Tracker Bug - v1.11.0 Fix

**Status:** ✅ **FIXED** in v1.11.0  
**Date:** 2026-01-20  
**Affected:** FOREX strategies using custom calendars

---

## The Problem

Zipline's internal metrics tracker has a known bug that causes `IndexError` when using FOREX calendars:

```
IndexError: index 18 is out of bounds for axis 0 with size 18
```

**Location:** `zipline/finance/metrics/metric.py`  
**Root Cause:** Session counting discrepancies between FOREX calendars (24/5 trading) and Zipline's internal session tracking, particularly in the `daily_cumulative_returns` calculation.

**When It Occurs:**
- FOREX strategies using `ForexCalendar` (24/5 trading)
- Strategies using custom calendars with non-standard session counts
- Backtests with session alignment mismatches

---

## The Solution (v1.11.0)

**Automatic Fix:** The system now automatically disables Zipline's built-in metrics for FOREX strategies (`metrics_set='none'`) to avoid this bug.

**How It Works:**

1. **Detection:** `lib/backtest/execution.py` detects FOREX asset class
2. **Metrics Disabled:** Uses `metrics_set='none'` in `run_algorithm()` call
3. **Reconstruction:** `lib/backtest/results_serialization.py` reconstructs portfolio_value from transactions
4. **Metrics Calculation:** All metrics calculated post-backtest using `lib/metrics`

### Implementation Details

**File:** `lib/backtest/execution.py`

```python
# v1.11.0: For FOREX calendars, default to metrics_set='none' to avoid known bugs
use_no_metrics = (asset_class == 'forex')  # FOREX has known metrics bugs

if use_no_metrics:
    logger.info("Using metrics_set='none' for FOREX calendar to avoid known metrics tracker bugs.")
    perf = run_algorithm(
        # ... other parameters ...
        metrics_set='none',  # Disable metrics for FOREX
    )
```

**File:** `lib/backtest/results_serialization.py`

```python
# Reconstruct portfolio_value from transactions when metrics_set='none'
if 'returns' not in perf.columns and 'portfolio_value' not in perf.columns:
    portfolio_value = calculate_portfolio_value_from_transactions(
        perf, transactions_df, positions_df, initial_capital
    )
    returns = portfolio_value.pct_change().dropna()
```

---

## What This Means for Users

### ✅ Benefits

- **No More Crashes:** FOREX backtests complete successfully
- **All Metrics Available:** Metrics calculated using `lib/metrics` (more accurate)
- **Automatic:** No user action required - works transparently
- **Backward Compatible:** Existing equity/crypto strategies unaffected

### ⚠️ Important Notes

1. **Performance DataFrame:** When `metrics_set='none'` is used, the initial `perf` DataFrame may not have `returns` or `portfolio_value` columns
2. **Automatic Reconstruction:** These are automatically added during `save_results()`
3. **Metrics Always Calculated:** All metrics are still calculated and saved to `metrics.json`

---

## Verification

### Check If Fix Is Working

```python
from lib.backtest import run_backtest, save_results
from lib.config import load_strategy_params

# Run FOREX backtest
perf, calendar = run_backtest(
    strategy_name='my_forex_strategy',
    asset_class='forex',
    start_date='2024-01-01',
    end_date='2024-12-31'
)

# Check initial columns (may be missing returns/portfolio_value)
print("Initial columns:", list(perf.columns))

# Save results (reconstructs portfolio_value)
params = load_strategy_params('my_forex_strategy', 'forex')
result_dir = save_results('my_forex_strategy', perf, params, calendar)

# Verify metrics were calculated
import json
from pathlib import Path
metrics_file = result_dir / 'metrics.json'
if metrics_file.exists():
    with open(metrics_file) as f:
        metrics = json.load(f)
        print(f"✓ Metrics calculated: {len(metrics)} metrics")
        print(f"  Sharpe: {metrics.get('sharpe', 'N/A')}")
        print(f"  Total Return: {metrics.get('total_return', 'N/A')}")
```

### Expected Output

```
Initial columns: ['period_open', 'period_close', 'signal', 'price', ...]
✓ Metrics calculated: 15 metrics
  Sharpe: 1.23
  Total Return: 12.5
```

---

## Technical Details

### Portfolio Value Reconstruction

The `calculate_portfolio_value_from_transactions()` function:

1. **Tracks Cash Balance:**
   - Starts with `initial_capital`
   - Subtracts `(amount * price + commission)` for buys
   - Adds `(abs(amount) * price - commission)` for sells

2. **Calculates Position Values:**
   - Uses `last_sale_price` from positions DataFrame if available
   - Falls back to `cost_basis` if needed

3. **Portfolio Value:**
   - `portfolio_value = cash_balance + sum(position_values)`
   - Forward-filled for missing dates

4. **Returns Calculation:**
   - `returns = portfolio_value.pct_change().dropna()`

### Error Handling

If reconstruction fails:
- Logs warning
- Returns empty metrics dictionary
- Backtest still completes (no crash)

---

## Related Issues

- **Session Alignment:** Calendar/session alignment issues can also cause metrics bugs
- **See:** [Calendar Date Parsing](calendar_date_parsing.md)
- **See:** [Backtest API](../api/backtest.md) - Portfolio value reconstruction

---

## References

- **Implementation:** `lib/backtest/execution.py` (lines 95-153)
- **Reconstruction:** `lib/backtest/results_serialization.py` (lines 105-180)
- **Metrics Calculation:** `lib/metrics/core.py`
- **Task Documentation:** `tasks/v1.11.0/004_STRATEGY_TEMPLATE/METRICS_FIX_IMPLEMENTATION.md`

---

**Status:** ✅ **RESOLVED** - Automatic fix in v1.11.0, no user action required
