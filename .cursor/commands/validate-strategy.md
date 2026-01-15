# Validate Strategy

## Overview

Validate strategy with walk-forward analysis and Monte Carlo simulation to ensure robustness and detect overfitting before production consideration.

## Steps

1. **Walk-Forward Analysis** - Split data into multiple train/test periods, optimize on each, test on subsequent period
2. **Monte Carlo Simulation** - Shuffle trade returns, generate thousands of equity paths, calculate confidence intervals
3. **Regime Robustness** - Test performance across bull/bear/sideways market regimes
4. **Calculate Metrics** - Walk-forward efficiency, overfit probability, Monte Carlo percentiles
5. **Save Results** - Save to results/{strategy}/walkforward_{timestamp}/ or montecarlo_{timestamp}/
6. **Make Determination** - Pass/fail based on validation thresholds

## Checklist

- [ ] Walk-forward analysis completed
- [ ] Monte Carlo simulation completed (1000+ paths)
- [ ] Regime robustness tested (bull/bear/sideways)
- [ ] Walk-forward efficiency calculated (> 0.5 required)
- [ ] Overfit probability calculated (< 0.4 required)
- [ ] Monte Carlo 5th percentile calculated (> 0 required)
- [ ] Results saved to timestamped directory
- [ ] Pass/fail determination made with reasoning

## Validation Methods

**Walk-Forward Analysis:**
```python
from lib.validate import walk_forward, save_walk_forward_results

results = walk_forward(
    strategy_name='btc_sma_cross',
    start_date='2020-01-01',
    end_date='2023-12-31',
    train_window_months=12,
    test_window_months=6,
    param_grid={'strategy.fast_period': [5, 10, 15], 'strategy.slow_period': [30, 50, 70]}
)

# Calculate efficiency
from lib.validate import calculate_walk_forward_efficiency
efficiency = calculate_walk_forward_efficiency(results)
print(f"Walk-forward efficiency: {efficiency:.2f}")  # Should be > 0.5

# Save results
save_walk_forward_results('btc_sma_cross', results)
```

**Monte Carlo Simulation:**
```python
from lib.validate import monte_carlo, save_monte_carlo_results

# Load returns from backtest
returns = pd.read_csv('results/btc_sma_cross/latest/returns.csv', index_col=0, parse_dates=True)

# Run Monte Carlo
simulation_results = monte_carlo(
    returns=returns['returns'],
    n_simulations=1000,
    confidence_levels=[0.05, 0.50, 0.95]
)

# Check 5th percentile
percentile_5 = simulation_results['percentiles'][0.05]
print(f"5th percentile return: {percentile_5:.2%}")  # Should be > 0

# Save results
save_monte_carlo_results('btc_sma_cross', simulation_results)
```

**Notebook (Interactive):**
```python
# In notebooks/05_walkforward.ipynb
strategy_name = 'btc_sma_cross'
# Run walk-forward and Monte Carlo analysis
```

## Validation Thresholds

| Metric | Minimum Threshold | Meaning |
|--------|-------------------|---------|
| Walk-Forward Efficiency | > 0.5 | OOS performance / IS performance |
| Monte Carlo 5th percentile | > 0 | Shouldn't lose money in worst scenarios |
| Overfit Probability | < 0.4 | Low probability of overfitting |
| Regime Consistency | Positive in 2/3 regimes | Works across market conditions |

## Output Structure

**Walk-Forward:**
```
results/{strategy}/walkforward_{timestamp}/
├── in_sample_results.csv
├── out_sample_results.csv
├── robustness_score.json
└── regime_breakdown.png
```

**Monte Carlo:**
```
results/{strategy}/montecarlo_{timestamp}/
├── simulation_paths.csv      # 1000 equity curves
├── confidence_intervals.json  # 5th, 50th, 95th percentile
└── distribution.png
```

## Decision Framework

**Pass Criteria:**
- Walk-forward efficiency > 0.5
- Monte Carlo 5th percentile > 0
- Overfit probability < 0.4
- Positive in 2/3 market regimes

**Fail Criteria:**
- Any threshold not met
- Strategy fails in multiple regimes
- High overfit probability (> 0.5)

## Notes

- Walk-forward is more realistic than single train/test split
- Monte Carlo shows range of possible outcomes
- Regime robustness ensures strategy works across conditions
- Validation is required before production consideration
- Document validation results in strategy report

## Related Commands

- optimize-parameters.md - For parameter optimization before validation
- analyze-results.md - For analyzing validation results
- generate-report.md - For documenting validation in report










