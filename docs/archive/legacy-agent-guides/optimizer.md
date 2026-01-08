# Optimizer Guide — AI Agent Instructions

> Step-by-step guide for parameter optimization with anti-overfit protocols.

---

## Overview

Optimization searches for better parameter values while guarding against overfitting. This guide ensures optimization follows best practices:

1. **In-sample / Out-of-sample split** — Never optimize on all data
2. **Walk-forward validation** — Test robustness across time
3. **Overfit probability calculation** — Quantify curve-fitting risk
4. **Clear decision framework** — When to proceed vs. abandon

---

## Pre-Flight Checks

Before optimizing, verify:

- [ ] Strategy has been backtested successfully
- [ ] Initial results show promise (Sharpe > 0.3)
- [ ] Parameter ranges are defined
- [ ] Data is sufficient for IS/OOS split (minimum 2 years)

---

## Optimization Methods

### Grid Search

**Use when:**
- ≤3 parameters
- Small parameter ranges
- Need exhaustive search

**Example:**

```python
param_grid = {
    'fast_period': [5, 10, 15, 20],
    'slow_period': [20, 30, 50, 100],
    'trend_filter_period': [0, 100, 200]
}

# Total combinations: 4 × 4 × 3 = 48 backtests
```

### Random Search

**Use when:**
- >3 parameters
- Large parameter ranges
- Need efficient search

**Example:**

```python
param_distributions = {
    'fast_period': range(5, 21),
    'slow_period': range(20, 101),
    'trend_filter_period': [0, 50, 100, 150, 200]
}

n_iter = 100  # Sample 100 random combinations
```

---

## Step-by-Step Process

### Step 1: Define Parameter Ranges

**Source:** Strategy hypothesis, domain knowledge, or initial exploration

```python
param_ranges = {
    'fast_period': {
        'min': 5,
        'max': 20,
        'step': 5,  # For grid search
        'type': 'int'
    },
    'slow_period': {
        'min': 20,
        'max': 100,
        'step': 10,
        'type': 'int'
    }
}
```

**Rules:**
- Start with wide ranges
- Narrow based on initial results
- Avoid testing too many combinations (curse of dimensionality)

### Step 2: Split Data

**CRITICAL:** Never optimize on all data.

```python
from datetime import datetime
import pandas as pd

# Total period
start = pd.Timestamp('2020-01-01', tz='UTC')
end = pd.Timestamp('2024-12-31', tz='UTC')

# Split: 70% train, 30% test
total_days = (end - start).days
train_days = int(total_days * 0.7)

train_end = start + pd.Timedelta(days=train_days)

train_start = start
train_end = train_end
test_start = train_end + pd.Timedelta(days=1)
test_end = end
```

**Validation:**
- Minimum train period: 252 days (1 year)
- Minimum test period: 63 days (3 months)
- Ensure both periods have sufficient data

### Step 3: Run Optimization

**Grid Search Example:**

```python
from lib.optimize import grid_search

results = grid_search(
    strategy_name='btc_sma_cross',
    param_grid={
        'fast_period': [5, 10, 15, 20],
        'slow_period': [30, 50, 100]
    },
    start_date=train_start.strftime('%Y-%m-%d'),
    end_date=train_end.strftime('%Y-%m-%d'),
    objective='sharpe'  # or 'sortino', 'calmar', 'return'
)
```

**Random Search Example:**

```python
from lib.optimize import random_search

results = random_search(
    strategy_name='btc_sma_cross',
    param_distributions={
        'fast_period': range(5, 21),
        'slow_period': range(20, 101)
    },
    n_iter=100,
    start_date=train_start.strftime('%Y-%m-%d'),
    end_date=train_end.strftime('%Y-%m-%d'),
    objective='sharpe'
)
```

### Step 4: Identify Best Parameters

```python
# Results DataFrame has columns: param1, param2, ..., sharpe, sortino, etc.
best_row = results.loc[results['sharpe'].idxmax()]
best_params = {
    'fast_period': int(best_row['fast_period']),
    'slow_period': int(best_row['slow_period'])
}
```

### Step 5: Validate on Out-of-Sample Data

**CRITICAL:** Test best params on held-out data.

```python
from lib.backtest import run_backtest

# Run backtest with best parameters on OOS data
oos_results = run_backtest(
    strategy_name='btc_sma_cross',
    start_date=test_start.strftime('%Y-%m-%d'),
    end_date=test_end.strftime('%Y-%m-%d'),
    params_override=best_params
)

oos_metrics = calculate_metrics(oos_results['returns'])
```

### Step 6: Calculate Overfit Probability

```python
from lib.validate import calculate_overfit_probability

is_sharpe = best_row['sharpe']
oos_sharpe = oos_metrics['sharpe']

overfit_score = calculate_overfit_probability(
    in_sample_sharpe=is_sharpe,
    out_sample_sharpe=oos_sharpe,
    n_trials=len(results)  # Number of parameter combinations tested
)
```

**Interpretation:**
- Score < 0.3: Low overfit risk, proceed
- Score 0.3-0.5: Moderate risk, proceed with caution
- Score > 0.5: High overfit risk, likely curve-fitting

### Step 7: Save Results

```python
from datetime import datetime
from pathlib import Path
import json
import yaml

timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
opt_dir = Path(f"results/{strategy_name}/optimization_{timestamp}")
opt_dir.mkdir(parents=True, exist_ok=True)

# Save all parameter combinations tested
results.to_csv(opt_dir / 'grid_results.csv', index=False)

# Save best parameters
with open(opt_dir / 'best_params.yaml', 'w') as f:
    yaml.dump(best_params, f, default_flow_style=False)

# Save metrics
metrics = {
    'in_sample': {
        'sharpe': float(is_sharpe),
        'sortino': float(best_row['sortino']),
        'max_drawdown': float(best_row['max_drawdown'])
    },
    'out_of_sample': oos_metrics,
    'overfit_score': float(overfit_score)
}

with open(opt_dir / 'metrics.json', 'w') as f:
    json.dump(metrics, f, indent=2)

# Generate heatmap
from lib.plots import plot_parameter_heatmap
plot_parameter_heatmap(results, save_path=opt_dir / 'heatmap_sharpe.png')
```

---

## Decision Framework

After optimization, use this framework:

| OOS Sharpe | Overfit Score | Decision |
|------------|---------------|----------|
| > 1.0 | < 0.3 | ✅ Proceed to validation |
| > 0.7 | < 0.4 | ✅ Proceed with caution |
| > 0.5 | < 0.5 | ⚠️ Re-examine hypothesis |
| > 0.5 | > 0.5 | ❌ Likely overfit, abandon |
| < 0.5 | Any | ❌ Poor performance, abandon |

**Additional Considerations:**
- Walk-forward efficiency (OOS Sharpe / IS Sharpe) should be > 0.5
- OOS metrics should be within 30% of IS metrics
- If OOS Sharpe < 0.3 × IS Sharpe, likely overfit

---

## Walk-Forward Analysis

For more robust validation, use walk-forward analysis:

```python
from lib.validate import walk_forward

wf_results = walk_forward(
    strategy_name='btc_sma_cross',
    start_date='2020-01-01',
    end_date='2024-12-31',
    train_period=252,  # 1 year
    test_period=63,    # 3 months
    optimize_params={
        'fast_period': [5, 10, 15, 20],
        'slow_period': [30, 50, 100]
    }
)

# Results include:
# - In-sample metrics for each window
# - Out-of-sample metrics for each window
# - Robustness score (consistency across windows)
```

**Walk-Forward Efficiency:**

```python
wf_efficiency = wf_results['oos_sharpe_mean'] / wf_results['is_sharpe_mean']

# Should be > 0.5 for acceptable robustness
```

---

## Common Pitfalls

### 1. Optimizing on All Data

**❌ WRONG:**
```python
results = grid_search(
    strategy_name='btc_sma_cross',
    start_date='2020-01-01',
    end_date='2024-12-31',  # Using all data!
    ...
)
```

**✅ CORRECT:**
```python
# Split first
train_start, train_end, test_start, test_end = split_data(...)

# Optimize on train only
results = grid_search(
    strategy_name='btc_sma_cross',
    start_date=train_start,
    end_date=train_end,  # Train data only
    ...
)

# Validate on test
oos_results = run_backtest(..., start_date=test_start, end_date=test_end)
```

### 2. Too Many Parameters

**❌ WRONG:**
```python
# Testing 10 parameters with 5 values each = 5^10 = 9.7M combinations!
param_grid = {
    'param1': [1, 2, 3, 4, 5],
    'param2': [1, 2, 3, 4, 5],
    # ... 8 more parameters
}
```

**✅ CORRECT:**
```python
# Focus on 2-3 key parameters
param_grid = {
    'fast_period': [5, 10, 15, 20],
    'slow_period': [30, 50, 100]
}
```

### 3. Ignoring Out-of-Sample Results

**❌ WRONG:**
```python
# Only looking at in-sample results
best_params = results.loc[results['sharpe'].idxmax()]
# Proceed without OOS validation!
```

**✅ CORRECT:**
```python
best_params = results.loc[results['sharpe'].idxmax()]
oos_results = run_backtest(..., params_override=best_params)
if oos_results['sharpe'] < 0.5:
    print("OOS performance poor, likely overfit")
```

---

## Output Summary Format

After optimization, provide:

```
Optimization complete. Results saved to results/{strategy_name}/optimization_{timestamp}/.

In-Sample Results:
- Best Sharpe: {is_sharpe:.2f}
- Best Parameters: {best_params}

Out-of-Sample Results:
- OOS Sharpe: {oos_sharpe:.2f}
- OOS MaxDD: {oos_maxdd:.2%}

Validation:
- Overfit Score: {overfit_score:.2f}
- Walk-Forward Efficiency: {wf_efficiency:.2f}

Decision: {proceed|proceed_with_caution|re_examine|abandon}
Reason: {explanation}

Next: {suggested_action}
```

---

## Related Files

- **Optimization code:** `lib/optimize.py`
- **Validation code:** `lib/validate.py`
- **Results:** `results/{strategy_name}/optimization_{timestamp}/`
- **Best parameters:** `results/{strategy_name}/optimization_{timestamp}/best_params.yaml`

---

## Next Steps

After optimization:

1. **If proceed:** Run full walk-forward validation
2. **If proceed with caution:** Run Monte Carlo simulation
3. **If re-examine:** Review hypothesis, consider different approach
4. **If abandon:** Document learnings, move to next strategy

**See:** `.agent/analyst.md` for detailed analysis procedures

