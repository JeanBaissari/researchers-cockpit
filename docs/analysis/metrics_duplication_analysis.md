# Metrics Duplication Analysis: lib/metrics/ vs Zipline-Reloaded

> Comprehensive analysis of duplications between `lib/metrics/` and Zipline-Reloaded's native metrics system

**Date:** 2026-01-27  
**Status:** Analysis Complete  
**Version:** v1.12.0

---

## Executive Summary

**Key Finding:** `lib/metrics/` provides value beyond Zipline-Reloaded's native metrics, but there are duplications that should be documented and potentially refactored.

**Recommendation:** Keep `lib/metrics/` but document the differences clearly. Refactor strategy `analyze()` functions to use `lib/metrics/` instead of direct empyrical calls.

---

## 1. Zipline-Reloaded Native Metrics

### What Zipline Provides

Zipline-Reloaded v3.0+ provides these metrics natively via its metrics system:

| Metric | Source | Type | Notes |
|--------|--------|------|-------|
| `sharpe` | `ReturnsStatistic()` | Rolling | Calculated every bar |
| `sortino` | `ReturnsStatistic()` | Rolling | Calculated every bar |
| `max_drawdown` | `ReturnsStatistic()` | Rolling | Calculated every bar |
| `alpha` | `AlphaBeta()` | End-of-simulation | Jensen's alpha |
| `beta` | `AlphaBeta()` | End-of-simulation | Beta coefficient |
| `returns` | `Returns()` | Time-series | Period returns |
| `portfolio_value` | Built-in | Time-series | Portfolio value |
| `max_drawdown_duration` | `ReturnsStatistic()` | Rolling | Duration in days |
| `recovery_time` | `ReturnsStatistic()` | Rolling | Recovery time in days |

**Access Pattern:**
```python
results = run_algorithm(...)
final_sharpe = results['sharpe'].iloc[-1]  # Final rolling value
final_alpha = results['alpha'].iloc[-1]     # End-of-simulation value
```

### Limitations

1. **Rolling vs Full-Period:** Zipline's metrics are rolling calculations (calculated every bar), not full-period calculations
2. **FOREX Calendar Bugs:** Known bugs with FOREX calendars (see `lib/backtest/execution.py:46`)
3. **Limited Metrics:** Only basic risk metrics (no omega, tail_ratio, calmar, etc.)
4. **No Trade-Level Analysis:** No win_rate, profit_factor, trade statistics

---

## 2. lib/metrics/ Implementation

### What We Provide

| Metric | Module | Type | Notes |
|--------|--------|------|-------|
| `sharpe` | `performance.py` | Full-period | ✅ DUPLICATED |
| `sortino` | `performance.py` | Full-period | ✅ DUPLICATED |
| `max_drawdown` | `risk.py` | Full-period | ✅ DUPLICATED |
| `alpha` | `risk.py` | Full-period | ✅ DUPLICATED |
| `beta` | `risk.py` | Full-period | ✅ DUPLICATED |
| `annual_return` | `performance.py` | Full-period | ✅ UNIQUE |
| `total_return` | `performance.py` | Full-period | ✅ UNIQUE |
| `annual_volatility` | `performance.py` | Full-period | ✅ UNIQUE |
| `calmar` | `performance.py` | Full-period | ✅ UNIQUE |
| `omega` | `risk.py` | Full-period | ✅ UNIQUE |
| `tail_ratio` | `risk.py` | Full-period | ✅ UNIQUE |
| `max_drawdown_duration` | `risk.py` | Full-period | ✅ DUPLICATED |
| `recovery_time` | `risk.py` | Full-period | ✅ DUPLICATED |
| `win_rate` | `trade.py` | Trade-level | ✅ UNIQUE |
| `profit_factor` | `trade.py` | Trade-level | ✅ UNIQUE |
| `avg_trade_return` | `trade.py` | Trade-level | ✅ UNIQUE |
| `max_consecutive_losses` | `trade.py` | Trade-level | ✅ UNIQUE |
| `trades_per_month` | `trade.py` | Trade-level | ✅ UNIQUE |

**Access Pattern:**
```python
from lib.metrics import calculate_metrics

metrics = calculate_metrics(
    returns=results['returns'],
    transactions=transactions_df,
    benchmark_returns=results.get('benchmark_period_return'),
    risk_free_rate=0.04,
    trading_days_per_year=252
)
```

### Advantages

1. **Full-Period Calculations:** More accurate for final reporting
2. **Better Edge Case Handling:** Comprehensive validation and sanitization
3. **Trade-Level Analysis:** Win rate, profit factor, trade statistics
4. **Additional Risk Metrics:** Omega, tail ratio, Calmar ratio
5. **Works with FOREX:** No calendar bugs (we use `metrics_set='none'`)

---

## 3. Duplication Analysis

### Direct Duplications

These metrics are calculated in both Zipline and `lib/metrics/`:

1. **Sharpe Ratio** (`lib/metrics/performance.py:31`)
   - Zipline: Rolling calculation via `ReturnsStatistic()`
   - Ours: Full-period calculation via `empyrical.sharpe_ratio()` or manual
   - **Status:** ✅ Keep (different calculation method, better for reporting)

2. **Sortino Ratio** (`lib/metrics/performance.py:96`)
   - Zipline: Rolling calculation via `ReturnsStatistic()`
   - Ours: Full-period calculation via `empyrical.sortino_ratio()` or manual
   - **Status:** ✅ Keep (different calculation method, better for reporting)

3. **Max Drawdown** (`lib/metrics/risk.py:31`)
   - Zipline: Rolling calculation via `ReturnsStatistic()`
   - Ours: Full-period calculation via `empyrical.max_drawdown()` or manual
   - **Status:** ✅ Keep (different calculation method, better for reporting)

4. **Alpha/Beta** (`lib/metrics/risk.py:138`)
   - Zipline: End-of-simulation via `AlphaBeta()`
   - Ours: Full-period calculation via `empyrical.alpha()` and `empyrical.beta()`
   - **Status:** ✅ Keep (different calculation method, more flexible)

5. **Max Drawdown Duration** (`lib/metrics/risk.py:246`)
   - Zipline: Rolling calculation via `ReturnsStatistic()`
   - Ours: Full-period calculation via `empyrical.max_drawdown_duration()`
   - **Status:** ✅ Keep (different calculation method)

6. **Recovery Time** (`lib/metrics/risk.py:62`)
   - Zipline: Rolling calculation via `ReturnsStatistic()`
   - Ours: Full-period calculation (custom implementation)
   - **Status:** ✅ Keep (different calculation method, more accurate)

### Strategy-Level Duplications

**Problem:** Strategy `analyze()` functions use `empyrical` directly instead of `lib/metrics/`:

**Files Affected:**
- `strategies/_template/strategy.py:790-820`
- `strategies/forex/breakout_intraday/strategy.py:1058-1088`
- `strategies/forex_breakout_test/strategy.py:859-889`

**Current Pattern:**
```python
# ❌ BAD: Direct empyrical usage in strategies
try:
    import empyrical as ep
    sharpe = float(ep.sharpe_ratio(returns, ...))
    sortino = float(ep.sortino_ratio(returns, ...))
    max_dd = float(ep.max_drawdown(returns))
except ImportError:
    # Manual fallback
    ...
```

**Recommended Pattern:**
```python
# ✅ GOOD: Use lib/metrics
from lib.metrics import calculate_metrics

metrics = calculate_metrics(
    returns=returns,
    risk_free_rate=risk_free_rate,
    trading_days_per_year=trading_days
)
sharpe = metrics['sharpe']
sortino = metrics['sortino']
max_dd = metrics['max_drawdown']
```

**Status:** ⚠️ Should refactor (duplicates logic, inconsistent with backtest runner)

---

## 4. Current Usage Patterns

### Backtest Execution

**File:** `lib/backtest/execution.py`

```python
# We disable Zipline metrics for FOREX (line 46)
metrics_set='none'  # Avoids FOREX calendar bugs

# We use lib/metrics for all calculations (line 48)
# "using lib/metrics.calculate_metrics() from the performance DataFrame"
```

**File:** `lib/backtest/results_serialization.py:309`

```python
# Always use lib/metrics for final reporting
metrics = calculate_metrics(
    returns,
    transactions=transactions_df,
    risk_free_rate=risk_free_rate,
    trading_days_per_year=trading_days_per_year
)
```

**Conclusion:** We **never use Zipline's native metrics** in production code. We always use `lib/metrics/`.

### Strategy Analyze Functions

**Problem:** Strategies duplicate `lib/metrics/` logic by using `empyrical` directly.

**Impact:**
- Inconsistent metric calculations
- Duplicated edge case handling
- Harder to maintain (changes need to be made in multiple places)

---

## 5. Recommendations

### ✅ Keep lib/metrics/ (No Changes)

**Rationale:**
1. **Different Calculation Methods:** Rolling (Zipline) vs Full-Period (Ours)
2. **Better for Reporting:** Full-period metrics are more accurate for final analysis
3. **Additional Metrics:** Omega, tail_ratio, calmar, trade-level metrics
4. **FOREX Compatibility:** Works with `metrics_set='none'` (Zipline has bugs)
5. **Better Edge Case Handling:** Comprehensive validation and sanitization

### ⚠️ Refactor Strategy analyze() Functions

**Action:** Replace direct `empyrical` usage with `lib/metrics/calculate_metrics()`

**Benefits:**
- Consistent metric calculations across codebase
- Single source of truth for edge case handling
- Easier maintenance (changes in one place)
- Better alignment with backtest runner

**Files to Update:**
1. `strategies/_template/strategy.py:790-820`
2. `strategies/forex/breakout_intraday/strategy.py:1058-1088`
3. `strategies/forex_breakout_test/strategy.py:859-889`

### 📝 Document Differences

**Action:** Update `docs/../api/metrics.md` to clearly document:
1. When to use Zipline metrics (time-series plotting)
2. When to use `lib/metrics/` (final reporting)
3. Differences between rolling and full-period calculations

---

## 6. Code Metrics

### Line Count Analysis

| Module | Lines | Duplicated? | Status |
|--------|-------|-------------|--------|
| `lib/metrics/performance.py` | 255 | Partial (Sharpe, Sortino) | ✅ Keep |
| `lib/metrics/risk.py` | 269 | Partial (Max DD, Alpha/Beta) | ✅ Keep |
| `lib/metrics/trade.py` | 352 | No | ✅ Keep |
| `lib/metrics/rolling.py` | 92 | No | ✅ Keep |
| `lib/metrics/comparison.py` | 81 | No | ✅ Keep |
| `lib/metrics/core.py` | 237 | No (orchestration) | ✅ Keep |
| **Total** | **1,286** | **~400 lines duplicated** | **Keep all** |

**Note:** Even "duplicated" metrics serve different purposes (rolling vs full-period).

### Dependencies

**Zipline-Reloaded:**
- Uses internal metrics system (no external dependencies)

**lib/metrics/:**
- Uses `empyrical` (optional, with fallback)
- Uses `numpy`, `pandas` (required)

---

## 7. Conclusion

### Summary

1. **lib/metrics/ provides value** beyond Zipline's native metrics
2. **Duplications are justified** by different calculation methods (rolling vs full-period)
3. **Strategy analyze() functions should be refactored** to use `lib/metrics/` instead of direct `empyrical` calls
4. **Documentation should be updated** to clarify when to use each system

### Action Items

- [x] Complete duplication analysis
- [ ] Refactor strategy `analyze()` functions to use `lib/metrics/`
- [ ] Update `docs/../api/metrics.md` with usage guidelines
- [ ] Add comments in `lib/metrics/` explaining differences from Zipline

### Status

**Current State:** ✅ Acceptable (duplications justified, but strategy refactoring recommended)  
**Target State:** ✅ Improved (strategies use `lib/metrics/`, documentation updated)

---

## References

- [Zipline-Reloaded Metrics Inventory](../api/metrics_inventory.md)
- [Project Metrics API](../api/metrics.md)
- [Backtest Execution](../api/backtest.md)
- [Zipline-Reloaded Repository](https://github.com/stefan-jansen/zipline-reloaded)

---

**Last Updated:** 2026-01-27  
**Next Review:** After strategy refactoring
