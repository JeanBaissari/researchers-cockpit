# Optimize Parameters

## Overview

Optimize strategy parameters using grid search or random search with anti-overfit protocols (in-sample/out-of-sample split, walk-forward validation, overfit probability).

## Steps

1. **Define Parameter Ranges** - Specify parameter grid or distributions
2. **Split Data** - Divide into training (70%) and test (30%) sets
3. **Run Optimization** - Execute grid or random search over parameter space
4. **Calculate Overfit Score** - Compute probability of overfitting
5. **Validate Results** - Compare in-sample vs out-of-sample performance
6. **Save Results** - Save to results/{strategy}/optimization_{timestamp}/
7. **Update Parameters** - Update parameters.yaml only if validation passes

## Checklist

- [ ] Parameter ranges defined (grid or distributions)
- [ ] Data split into train/test (70/30)
- [ ] Optimization method chosen (grid for <50 combos, random for >50)
- [ ] Overfit score calculated (< 0.4 acceptable)
- [ ] In-sample vs out-of-sample compared
- [ ] Results saved to timestamped directory
- [ ] Parameters updated only if validation passes

## Optimization Methods

**Grid Search (exhaustive):**
```python
from lib.optimize import grid_search

param_grid = {
    'strategy.fast_period': [5, 10, 15, 20],
    'strategy.slow_period': [30, 50, 70, 100]
}
# Total: 4 * 4 = 16 combinations

results = grid_search(
    strategy_name='btc_sma_cross',
    param_grid=param_grid,
    start_date='2020-01-01',
    end_date='2023-12-31',
    objective='sharpe',
    train_pct=0.7
)
```

**Random Search (efficient for large spaces):**
```python
from lib.optimize import random_search

param_distributions = {
    'strategy.fast_period': list(range(5, 50, 5)),  # 9 values
    'strategy.slow_period': list(range(20, 200, 10))  # 18 values
}
# Total: 9 * 18 = 162 combinations
# Use random search: test 100 random combinations

results = random_search(
    strategy_name='btc_sma_cross',
    param_distributions=param_distributions,
    n_iter=100,
    start_date='2020-01-01',
    end_date='2023-12-31',
    objective='sharpe',
    train_pct=0.7
)
```

**Script (CLI):**
```bash
python scripts/run_optimization.py --strategy btc_sma_cross --method grid
python scripts/run_optimization.py --strategy btc_sma_cross --method random --iterations 100
```

## Anti-Overfit Protocols

**In-Sample/Out-of-Sample Split:**
- Train on 70% of data
- Test on held-out 30%
- Compare IS vs OOS performance
- OOS Sharpe should be > 0.5 * IS Sharpe

**Overfit Probability:**
```python
from lib.optimize.overfit import calculate_overfit_score

score = calculate_overfit_score(
    in_sample_metric=1.5,  # IS Sharpe
    out_sample_metric=0.8,  # OOS Sharpe
    n_trials=100
)
# Returns: {'pbo': 0.23, 'verdict': 'acceptable'}
# pbo < 0.4 is acceptable
```

**Walk-Forward Validation:**
- Rolling optimization windows
- Test on subsequent periods
- More realistic than single split
- Use notebooks/05_walkforward.ipynb

## Output Structure

```
results/{strategy}/optimization_{timestamp}/
├── grid_results.csv      # All parameter combinations tested
├── best_params.yaml      # Winning parameters
├── heatmap_sharpe.png    # Parameter sensitivity visualization
├── in_sample_metrics.json
├── out_sample_metrics.json
└── overfit_score.json    # {"pbo": 0.23, "verdict": "acceptable"}
```

## Decision Framework

| OOS Sharpe | Overfit Score | Decision |
|------------|---------------|----------|
| > 1.0      | < 0.3         | Proceed to validation |
| > 0.5      | < 0.5         | Proceed with caution |
| > 0.5      | > 0.5         | Re-examine hypothesis |
| < 0.5      | Any           | Abandon or rethink |

## Notes

- Use grid search for ≤50 combinations
- Use random search for >50 combinations
- Always split data (never optimize on full dataset)
- Calculate overfit score before updating parameters
- Update parameters.yaml only if validation passes
- Document parameter change rationale

## Related Commands

- run-backtest.md - For testing optimized parameters
- validate-strategy.md - For walk-forward validation
- analyze-results.md - For analyzing optimization results
