# Metrics Duplication Analysis - Summary

> Quick reference for metrics duplication findings

**Date:** 2026-01-27  
**Status:** Analysis Complete

---

## Quick Findings

### ✅ Keep lib/metrics/ (No Changes Needed)

**Reason:** Duplications are justified by different calculation methods:
- **Zipline:** Rolling calculations (every bar) - good for time-series plotting
- **Ours:** Full-period calculations (once) - better for final reporting

### ⚠️ Refactor Strategy analyze() Functions

**Problem:** Strategies use `empyrical` directly instead of `lib/metrics/`

**Files to Update:**
1. `strategies/_template/strategy.py:790-820`
2. `strategies/forex/breakout_intraday/strategy.py:1058-1088`
3. `strategies/forex_breakout_test/strategy.py:859-889`

**Current Pattern:**
```python
# ❌ BAD: Direct empyrical
import empyrical as ep
sharpe = ep.sharpe_ratio(returns, ...)
```

**Recommended Pattern:**
```python
# ✅ GOOD: Use lib/metrics
from lib.metrics import calculate_metrics
metrics = calculate_metrics(returns=returns, ...)
sharpe = metrics['sharpe']
```

---

## Duplicated Metrics

| Metric | Zipline Type | Our Type | Status |
|--------|-------------|----------|--------|
| Sharpe | Rolling | Full-period | ✅ Keep (different method) |
| Sortino | Rolling | Full-period | ✅ Keep (different method) |
| Max Drawdown | Rolling | Full-period | ✅ Keep (different method) |
| Alpha/Beta | End-of-sim | Full-period | ✅ Keep (different method) |
| Max DD Duration | Rolling | Full-period | ✅ Keep (different method) |
| Recovery Time | Rolling | Full-period | ✅ Keep (different method) |

---

## Unique Metrics (No Duplication)

- `annual_return`, `total_return`, `annual_volatility`
- `calmar`, `omega`, `tail_ratio`
- `win_rate`, `profit_factor`, `avg_trade_return`
- `max_consecutive_losses`, `trades_per_month`

---

## Current Usage

- ✅ Backtest runner: Always uses `lib/metrics/` (never Zipline metrics)
- ✅ Results serialization: Always uses `lib/metrics/`
- ⚠️ Strategy analyze(): Uses `empyrical` directly (should use `lib/metrics/`)

---

## Recommendations

1. **Keep lib/metrics/** - Provides value beyond Zipline
2. **Refactor strategies** - Use `lib/metrics/` instead of direct `empyrical`
3. **Update documentation** - Clarify when to use each system

---

**Full Analysis:** See `docs/analysis/metrics_duplication_analysis.md`
