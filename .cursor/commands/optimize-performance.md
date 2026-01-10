# Optimize Performance

## Overview

Analyze and optimize backtest execution speed, parameter search efficiency, and data loading performance while maintaining code quality and research workflow.

## Steps

1. **Performance Analysis**
   - Profile backtest execution time (identify slow strategies)
   - Measure parameter optimization speed (grid vs random search)
   - Analyze data bundle loading and caching
   - Detect redundant computations in metrics calculation

2. **Optimization Strategies**
   - Use random search instead of grid search for large parameter spaces
   - Implement data caching for frequently accessed bundles
   - Optimize date range selection (shorter periods for quick tests)
   - Parallelize independent backtests when possible

3. **Implementation**
   - Provide optimized code with performance impact estimates
   - Suggest profiling approaches (cProfile, line_profiler)
   - Consider trade-offs: speed vs accuracy, memory vs computation
   - Document performance improvements

## Checklist

- [ ] Profiled backtest execution time
- [ ] Identified slow parameter search operations
- [ ] Analyzed data bundle loading performance
- [ ] Detected redundant metric calculations
- [ ] Suggested random search for large parameter spaces
- [ ] Recommended data caching strategies
- [ ] Provided optimized code with explanations
- [ ] Included performance impact estimates
- [ ] Considered trade-offs between speed and accuracy

## Performance Optimization Patterns

**Use random search for large parameter spaces:**
```python
# ❌ Slow: Grid search with many combinations
param_grid = {
    'fast_period': list(range(5, 50, 5)),  # 9 values
    'slow_period': list(range(20, 200, 10)),  # 18 values
    'threshold': [0.01, 0.02, 0.03, 0.04, 0.05]  # 5 values
}
# Total: 9 * 18 * 5 = 810 combinations (very slow!)

# ✅ Fast: Random search with same coverage
from lib.optimize import random_search
results = random_search(
    strategy_name='btc_sma_cross',
    param_distributions=param_grid,
    n_iter=100  # Test 100 random combinations instead
)
```

**Optimize date ranges for quick tests:**
```python
# ❌ Slow: Full history for initial testing
results = run_backtest('btc_sma_cross', '2020-01-01', '2024-12-31')

# ✅ Fast: 1 year for quick validation
results = run_backtest('btc_sma_cross', '2023-01-01', '2023-12-31')
# Then expand to full history if promising
```

**Cache frequently accessed data:**
```python
# ✅ Use bundle caching (automatic in lib/bundles/)
# Bundles are cached after first load
from lib.bundles.registry import get_bundle_info
info = get_bundle_info('yahoo_crypto_daily')  # Cached after first call
```

**Profile backtest execution:**
```python
import cProfile
import pstats
from lib.backtest import run_backtest

# Profile backtest
profiler = cProfile.Profile()
profiler.enable()
returns, _ = run_backtest('btc_sma_cross', '2023-01-01', '2023-12-31')
profiler.disable()

# Analyze results
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)  # Top 20 slowest functions
```

**Optimize metrics calculation:**
```python
# ✅ Calculate metrics once, reuse results
from lib.metrics import calculate_metrics
metrics = calculate_metrics(returns)
sharpe = metrics['sharpe']
sortino = metrics['sortino']  # Reuse same calculation

# ❌ Slow: Recalculate for each metric
sharpe = calculate_sharpe_ratio(returns)
sortino = calculate_sortino_ratio(returns)  # Redundant calculation
```

## Performance Targets

- **Quick validation backtest**: < 30 seconds (1 year of daily data)
- **Full backtest**: < 5 minutes (5 years of daily data)
- **Grid search (100 combinations)**: < 1 hour
- **Random search (100 iterations)**: < 30 minutes

## Notes

- Use random search for >50 parameter combinations
- Test with shorter date ranges first, expand if promising
- Profile before optimizing (measure, don't guess)
- Consider parallel execution for independent backtests
- Cache data bundles to avoid redundant loading

## Related Commands

- optimize-parameters.md - For parameter optimization workflow
- run-backtest.md - For backtest execution
- debug-issue.md - For debugging performance issues