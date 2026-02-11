# 05 - Walk-Forward Notebook

**File**: `notebooks/05_walkforward.ipynb`
**Purpose**: Validate strategy robustness through walk-forward analysis
**Architecture**: v1.12.0 NO WRAPPERS

## Overview

Walk-forward validation is the gold standard for testing strategy robustness. It simulates real trading by optimizing parameters on historical data then testing on future (out-of-sample) periods.

## Why Walk-Forward Matters

**Problem**: Single train/test split may be lucky
**Solution**: Multiple rolling windows prove consistency

**Key insight**: If a strategy only works on optimized data but fails on new data, it's overfit.

## Configuration

```python
strategy_name = 'spy_sma_cross'
start_date = '2020-01-01'
end_date = None  # None = today

# Walk-forward parameters
train_period = 252  # Trading days for training (1 year)
test_period = 63    # Trading days for testing (1 quarter)
step_size = 63      # Step between windows (1 quarter)

objective = 'sharpe'  # Optimization objective
```

**Key parameters**:
- `train_period`: Window for optimization
- `test_period`: Window for validation
- `step_size`: How often to re-optimize (sliding window)

## How It Works

```
Data: [--------------------------------]

Window 1: [Train========][Test==]
Window 2:      [Train========][Test==]
Window 3:           [Train========][Test==]
Window 4:                [Train========][Test==]
```

**For each window**:
1. Optimize parameters on train period
2. Test with best parameters on test period
3. Record out-of-sample performance
4. Slide window forward by `step_size`

## Key Metrics

### Walk-Forward Efficiency (WFE)

```python
WFE = Average(OOS Performance) / Average(IS Performance)
```

**Interpretation**:
- **> 0.5**: Good (retains > 50% of IS performance)
- **0.3 - 0.5**: Moderate (some degradation)
- **< 0.3**: Poor (significant overfitting)

**Ideal**: 0.6 - 0.8 (robust but not suspiciously perfect)

### Consistency

```python
Consistency = % of windows with positive OOS Sharpe
```

**Interpretation**:
- **> 70%**: Highly consistent
- **50% - 70%**: Moderately consistent
- **< 50%**: Inconsistent (may be luck)

### Degradation

Difference between IS and OOS performance:
```python
Degradation = Average(IS Sharpe - OOS Sharpe)
```

**Normal**: 10-30% degradation
**Concerning**: > 50% degradation

## When to Use

### Essential Use Cases ✓

- **Before production**: Final validation step
- **After optimization**: Prove robustness
- **For regulatory compliance**: Required by some jurisdictions
- **When uncertain**: High confidence needed

### Not Needed For

- Initial hypothesis testing (use single backtest)
- Parameter exploration (use grid search)
- Quick iterations (too slow)

## Output

```
results/{strategy_name}/walkforward_YYYYMMDD_HHMMSS/
├── walkforward_results.json  # All windows
├── robustness_metrics.json   # WFE, consistency, etc.
├── window_plots.png          # IS vs OOS visualization
└── parameters.yaml           # Config used
```

## Interpreting Results

### Example Output

```json
{
  "summary": {
    "total_windows": 8,
    "avg_test_sharpe": 0.82,
    "consistency": 0.75,
    "wf_efficiency": 0.68
  },
  "windows": [
    {
      "train_start": "2020-01-01",
      "train_end": "2020-12-31",
      "test_start": "2021-01-01",
      "test_end": "2021-03-31",
      "train_sharpe": 1.35,
      "test_sharpe": 0.91,
      "test_return": 0.048
    },
    // ... more windows
  ]
}
```

### Red Flags 🚩

1. **Test Sharpe > Train Sharpe**: Suspicious (data leak or luck)
2. **Highly variable test performance**: Inconsistent across regimes
3. **WFE < 0.3**: Severe overfitting
4. **Negative OOS returns in most windows**: Strategy doesn't work

### Green Lights ✓

1. **Consistent OOS performance**: Similar across windows
2. **WFE > 0.5**: Reasonable degradation
3. **Positive Sharpe in > 70% windows**: Reliable
4. **Stable parameter choices**: Same params often optimal

## Common Patterns

### Conservative Validation

```python
# Long train, short test, frequent re-optimization
train_period = 504  # 2 years
test_period = 21    # 1 month
step_size = 21      # Re-optimize monthly
```

**Pros**: High confidence, detects regime changes quickly
**Cons**: Slow to compute, many windows

### Fast Validation

```python
# Shorter periods, less frequent re-optimization
train_period = 126  # 6 months
test_period = 63    # 1 quarter
step_size = 126     # Re-optimize every 6 months
```

**Pros**: Faster, fewer windows
**Cons**: Less data per window, may miss issues

### Anchored Walk-Forward

```python
# Expanding window instead of rolling
# (train period grows over time)
```

**Use case**: When early data is valuable and shouldn't be dropped.

## Troubleshooting

### "Walk-forward too slow"

**Symptom**: Hours to complete
**Causes**:
- Too many windows
- Complex optimization
- Intraday data

**Fixes**:
- Increase `step_size` (fewer windows)
- Use random search instead of grid
- Use daily data instead of intraday
- Reduce train period

### "All windows fail"

**Symptom**: Negative OOS Sharpe in all windows
**Cause**: Strategy doesn't work or market regime changed
**Fix**: Revisit hypothesis, check if profitable in ANY period

### "High variability across windows"

**Symptom**: OOS Sharpe ranges from -1 to +2
**Cause**: Strategy is regime-dependent
**Interpretation**: May still be valid if positive on average, but risky

## Best Practices

### Do's ✓

1. **Use sufficient train data**: Minimum 6 months (better: 1-2 years)
2. **Test multiple window sizes**: Validate sensitivity
3. **Check parameter stability**: Same params across windows = robust
4. **Document all windows**: Don't cherry-pick best ones
5. **Compare to benchmark**: Walk-forward on buy-and-hold too

### Don'ts ✗

1. **Don't optimize on full dataset first**: Walk-forward should be blind
2. **Don't use overlapping test periods**: Inflates results
3. **Don't stop after one failure**: Look at average performance
4. **Don't ignore degradation**: > 50% is concerning
5. **Don't skip this step**: Most important validation

## Advanced Usage

### Regime-Based Walk-Forward

```python
# Separate bull/bear market windows
for window in windows:
    regime = detect_regime(window['train_data'])
    if regime == 'bull':
        # Use bull market parameters
    else:
        # Use bear market parameters
```

### Multi-Objective Walk-Forward

```python
# Optimize for multiple objectives
objectives = ['sharpe', 'sortino', 'calmar']

for objective in objectives:
    results = walk_forward(
        strategy_name=strategy_name,
        objective=objective,
        # ... other params
    )
    # Compare which objective produces most robust results
```

### Parameter Stability Analysis

```python
# Extract optimal parameters from each window
optimal_params = [
    window['best_params']
    for window in results['windows']
]

# Calculate stability (std dev of param values)
param_stability = pd.DataFrame(optimal_params).std()
print(f"Parameter stability: {param_stability}")
```

Low std dev = stable parameters = robust strategy.

## Integration with Other Notebooks

### Workflow

1. **01_backtest**: Initial validation
2. **02_optimize**: Find good parameters
3. **05_walkforward**: (THIS) Prove robustness
4. **Production**: Deploy with confidence

### If Walk-Forward Fails

- Return to hypothesis (strategy logic)
- Try different objective function
- Simplify strategy (remove parameters)
- Accept strategy may not be robust

## Related Documentation

- **[Validation API](../api/validate.md)** - Walk-forward functions
- **[Overfitting Guide](../code_patterns/overfitting_detection.md)**
- **[02_optimize.ipynb](02_optimize.md)** - Precursor to walk-forward
- **[Monte Carlo Validation](../code_patterns/monte_carlo_validation.md)**

---

**Last Updated**: 2026-02-09
**Version**: v1.12.0
