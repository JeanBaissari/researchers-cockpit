# 02 - Optimize Notebook

**File**: `notebooks/02_optimize.ipynb`
**Purpose**: Find optimal strategy parameters through systematic search
**Architecture**: v1.12.0 NO WRAPPERS

## Overview

Parameter optimization searches through parameter combinations to find settings that maximize an objective metric (Sharpe, Sortino, etc.) while detecting overfitting.

## Configuration

```python
strategy_name = 'spy_sma_cross'
method = 'grid'  # 'grid' or 'random'
objective = 'sharpe'  # 'sharpe', 'sortino', 'total_return', 'calmar'
train_pct = 0.7  # Training data percentage

# Parameter grid
param_grid = {
    'strategy.fast_period': [5, 10, 15, 20],
    'strategy.slow_period': [30, 50, 100],
}
```

**Customization**:
- `param_grid`: Define parameters and values to test
- `objective`: Metric to maximize
- `train_pct`: Train/test split (0.7 = 70% train, 30% test)

## Key Features

### Grid Search

Tests all parameter combinations:
- **Total runs**: Product of all parameter values
- **Example**: 4 fast × 3 slow = 12 backtests
- **Best for**: Small parameter spaces (< 100 combinations)

### Random Search

Samples parameter space randomly:
- **Total runs**: Specified by `n_iter`
- **Best for**: Large parameter spaces, faster exploration
- **Trade-off**: May miss optimal, but finds good solutions quickly

### Train/Test Split

Prevents overfitting:
- **Train period**: Optimize parameters
- **Test period**: Validate performance
- **Metric**: Out-of-sample (test) performance matters most

### Overfit Detection

Calculates:
- **Efficiency**: OOS performance / IS performance (should be > 0.5)
- **PBO** (Probability of Backtest Overfitting): Risk of overfit (should be < 0.5)
- **Verdict**: Robust / Moderate / Overfitted

## Output

```
results/{strategy_name}/optimize_YYYYMMDD_HHMMSS/
├── optimization_results.csv    # All parameter combinations
├── best_parameters.json        # Optimal parameters
├── overfit_score.json          # Overfit metrics
├── heatmap_sharpe.png          # 2D visualization (if 2 params)
└── parameters.yaml             # Config used
```

## When to Use

- After initial backtest shows promise (Sharpe > 0.5)
- Before walk-forward validation
- When uncertain about parameter values
- To understand parameter sensitivity

## Common Patterns

### Comprehensive Search

```python
param_grid = {
    'strategy.fast_period': range(5, 25, 5),     # 5, 10, 15, 20
    'strategy.slow_period': range(30, 120, 10),  # 30, 40, ..., 110
    'strategy.position_size': [0.8, 0.9, 0.95],  # 3 values
}
# Total: 4 × 9 × 3 = 108 combinations
```

### Quick Exploration

```python
method = 'random'
n_iter = 50  # Test 50 random combinations

param_distributions = {
    'strategy.fast_period': range(5, 50),
    'strategy.slow_period': range(20, 200),
}
```

## Interpreting Results

### Best Parameters

```python
# Displayed after optimization
print(f"Best fast_period: {best_row['strategy.fast_period']}")
print(f"Best slow_period: {best_row['strategy.slow_period']}")
print(f"Test Sharpe: {best_row['test_sharpe']:.3f}")
```

**What to check**:
- Test Sharpe > Train Sharpe (suspicious - may indicate data leak)
- Test Sharpe < 0.5 × Train Sharpe (degradation too large)
- Parameters at grid boundaries (need wider search)

### Overfit Score

```python
{
    "efficiency": 0.65,  # 65% of IS performance retained OOS
    "pbo": 0.32,         # 32% probability of overfit
    "verdict": "Robust"  # Robust / Moderate / Overfitted
}
```

**Interpretation**:
- **Robust** (efficiency > 0.5, PBO < 0.5): Safe to proceed
- **Moderate** (0.3 < efficiency < 0.5): Use with caution
- **Overfitted** (efficiency < 0.3): Re-think strategy

### Heatmap (2 Parameters)

Visual representation of parameter space:
- **Hot spots**: High performance regions
- **Flat plateaus**: Robust (insensitive to small changes)
- **Spikes**: Fragile (sensitive to parameters)

**Prefer**: Broad plateaus over sharp spikes.

## Troubleshooting

### "No improvement found"

**Symptom**: All combinations perform poorly
**Causes**:
- Strategy logic flawed
- Parameter ranges too narrow
- Market regime changed

**Fix**: Return to `01_backtest.ipynb`, revise hypothesis

### "Optimization too slow"

**Symptom**: Hours to complete
**Causes**:
- Too many combinations (grid search)
- Long date range
- Intraday data

**Fix**:
- Use random search instead
- Reduce date range for initial search
- Coarsen parameter grid

### "Best params at boundary"

**Symptom**: Optimal value is min or max of range
**Cause**: True optimum outside search space
**Fix**: Expand parameter range and re-run

## Best Practices

### Do's ✓

1. **Start with wide ranges**: Narrow down iteratively
2. **Use train/test split**: Never optimize on full dataset
3. **Check overfit metrics**: Don't ignore warnings
4. **Test multiple objectives**: Sharpe may differ from Sortino
5. **Document results**: Save best params to strategy config

### Don'ts ✗

1. **Don't optimize on same data you backtest on**: Use walk-forward instead
2. **Don't trust in-sample metrics**: OOS performance is what matters
3. **Don't over-optimize**: Simple often beats complex
4. **Don't ignore PBO warnings**: High PBO = likely to fail live
5. **Don't set train_pct < 0.6**: Need sufficient test data

## Related Documentation

- **[Optimization API](../api/optimize.md)**
- **[05_walkforward.ipynb](05_walkforward.md)** - Next validation step
- **[Overfitting Guide](../code_patterns/overfitting_detection.md)**

---

**Last Updated**: 2026-02-09
**Version**: v1.12.0
