# 01 - Backtest Notebook

**File**: `notebooks/01_backtest.ipynb`
**Purpose**: Execute a single strategy backtest and view results
**Architecture**: v1.12.0 NO WRAPPERS - Direct Zipline/pandas APIs

## Overview

The Backtest notebook executes a complete backtest for a single strategy and displays results. It's the primary tool for testing hypotheses and validating strategy logic.

## What This Notebook Does

1. **Loads strategy parameters** from `strategies/{asset_class}/{name}/parameters.yaml`
2. **Validates bundle** availability and quality
3. **Runs backtest** using Zipline's `run_algorithm()`
4. **Calculates metrics** (Sharpe, Sortino, max drawdown, etc.)
5. **Saves results** to timestamped directory
6. **Displays visualizations** (equity curve, metrics summary)

## Configuration

```python
# Cell 1: Edit these variables
strategy_name = 'spy_sma_cross'  # Your strategy name
start_date = '2020-01-01'        # Backtest start (YYYY-MM-DD)
end_date = None                  # None = today
capital_base = None              # None = use config value
bundle = None                    # None = auto-detect
asset_class = None               # None = auto-detect from strategy
```

**What to customize**:
- `strategy_name`: Must match directory in `strategies/`
- `start_date` / `end_date`: Define backtest period
- `capital_base`: Override default starting capital if needed

## Key Features

### Automatic Parameter Loading

```python
params = load_strategy_params(strategy_name, asset_class)
asset_class = params.get('strategy', {}).get('asset_class', 'equities')
```

**What it loads**:
- Strategy parameters (fast_period, slow_period, etc.)
- Backtest configuration (capital, commission, slippage)
- Asset class and trading calendar

**Validation**: Raises error if strategy directory doesn't exist.

### Bundle Validation

```python
validation_result = validate_bundle(bundle)
if not validation_result.is_valid:
    print(f"⚠ Bundle validation issues found")
```

**Pre-flight checks**:
- Bundle exists and is accessible
- Data quality meets minimum standards
- No critical errors (warnings okay)

**Action if failed**: Check `00_data_exploration.ipynb` for details.

### Backtest Execution

```python
from lib.backtest import run_backtest

perf = run_backtest(
    strategy_name=strategy_name,
    start_date=start_date,
    end_date=end_date,
    capital_base=capital_base,
    bundle=bundle,
    asset_class=asset_class
)
```

**What happens**:
1. Loads strategy module from `strategies/{asset_class}/{name}/strategy.py`
2. Calls `initialize()` and `handle_data()` functions
3. Applies commission and slippage models
4. Records portfolio metrics at each step
5. Returns performance DataFrame

**Duration**: Depends on:
- Date range (longer = slower)
- Timeframe (intraday = slower)
- Strategy complexity (Pipeline = slower)

### Results Storage

```python
from lib.backtest import save_results

result_dir = save_results(
    strategy_name=strategy_name,
    perf=perf,
    params=params,
    result_type='backtest'
)
```

**Output structure**:
```
results/{strategy_name}/backtest_YYYYMMDD_HHMMSS/
├── metrics.json          # Performance metrics
├── returns.csv           # Daily returns
├── positions.csv         # Position history
├── transactions.csv      # Trade log
├── equity_curve.png      # Visualization
└── parameters.yaml       # Strategy params used
```

**Symlink**: `results/{strategy_name}/latest/` points to most recent run.

### Metrics Display

```python
metrics_file = result_dir / 'metrics.json'
with open(metrics_file) as f:
    metrics = json.load(f)

print(f"Total Return: {metrics['total_return']:.2%}")
print(f"Sharpe Ratio: {metrics['sharpe']:.3f}")
```

**Metrics included**:
- **Returns**: Total, annual, CAGR
- **Risk-adjusted**: Sharpe, Sortino, Calmar
- **Risk**: Max drawdown, volatility, beta
- **Trades**: Count, win rate, profit factor (if available)

## When to Use

### Primary Use Cases ✓

- **Testing new strategies**: First validation of hypothesis
- **Parameter changes**: Quick check after tweaking parameters
- **Date range experiments**: See performance across different periods
- **Debugging**: Understand why strategy behaves unexpectedly

### Not Ideal For

- **Parameter optimization**: Use `02_optimize.ipynb` instead
- **Comparing strategies**: Use `04_compare.ipynb` instead
- **Production deployment**: Use `scripts/run_backtest.py` for automation

## Common Workflows

### 1. Quick Hypothesis Test

```python
# Edit configuration cell
strategy_name = 'my_new_strategy'
start_date = '2023-01-01'
end_date = '2023-12-31'

# Run all cells (Shift+Enter or Run All)
# Review metrics
# If promising → Proceed to optimization
```

### 2. Iterative Development

```python
# 1. Run backtest (this notebook)
# 2. Review results
# 3. Modify strategy.py in strategies/
# 4. Restart kernel & re-run
# 5. Compare metrics
# 6. Repeat until satisfied
```

### 3. Date Range Sensitivity

```python
# Test 1: Recent period
start_date = '2023-01-01'
end_date = '2023-12-31'
# Run and note metrics

# Test 2: Historical period
start_date = '2020-01-01'
end_date = '2021-12-31'
# Run and compare metrics
```

## Troubleshooting

### "Strategy not found"

**Error**: `FileNotFoundError: Strategy 'xyz' not found`
**Cause**: No directory at `strategies/{asset_class}/{strategy_name}/`
**Fix**: Create strategy from template:
```bash
cp -r strategies/_template strategies/equities/xyz
```

### "No bundle specified"

**Error**: `ValueError: No bundle available`
**Cause**: `bundle=None` and auto-detect failed
**Fix**: Explicitly set bundle:
```python
bundle = 'spy_daily'  # Or your bundle name
```

### "Symbol not in bundle"

**Error**: `SymbolNotFound: SPY not in bundle`
**Cause**: Strategy references symbol not in data
**Fix**: Check `00_data_exploration.ipynb` for available symbols or ingest correct data.

### "Insufficient data for start date"

**Error**: `ValueError: No data on 2015-01-01`
**Cause**: Bundle data starts later than `start_date`
**Fix**: Adjust `start_date` or re-ingest with earlier data:
```bash
python scripts/ingest_data.py --start 2015-01-01
```

### "Out of memory"

**Error**: Kernel died or `MemoryError`
**Cause**: Large bundle + long date range
**Fix**:
- Reduce date range
- Use daily timeframe instead of intraday
- Close other applications
- Increase system swap space

## Best Practices

### Do's ✓

1. **Validate data first**: Run `00_data_exploration.ipynb` before backtesting
2. **Use realistic dates**: Don't test on future-known events
3. **Save results**: Let notebook auto-save to `results/`
4. **Review metrics critically**: Don't cherry-pick best date range
5. **Document hypothesis**: Update `hypothesis.md` in strategy directory

### Don'ts ✗

1. **Don't overfit to date range**: Test multiple periods
2. **Don't ignore commission**: Real trading has costs
3. **Don't skip validation**: Quick check prevents hours of debugging
4. **Don't test with insufficient data**: Need minimum 1 year for daily strategies
5. **Don't assume notebook state**: Restart kernel between strategies

## Integration with Other Notebooks

### Before This Notebook

1. **00_data_exploration.ipynb**: Validate data quality
2. **06_strategy_prototype.ipynb** (optional): Rapid prototyping

### After This Notebook

If results are promising:
1. **02_optimize.ipynb**: Find optimal parameters
2. **03_analyze.ipynb**: Deep dive into performance
3. **05_walkforward.ipynb**: Validate robustness

If results are poor:
1. Revise strategy hypothesis
2. Modify strategy logic
3. Re-run this notebook

## Advanced Usage

### Custom Metrics Calculation

```python
# After loading perf DataFrame
from lib.metrics import calculate_rolling_metrics

rolling = calculate_rolling_metrics(
    perf['returns'],
    window=30,
    metrics=['sharpe', 'volatility']
)

# Plot rolling Sharpe
import matplotlib.pyplot as plt
plt.plot(rolling.index, rolling['sharpe'])
plt.title('30-Day Rolling Sharpe Ratio')
plt.show()
```

### Trade-by-Trade Analysis

```python
# After backtest
transactions_file = result_dir / 'transactions.csv'
if transactions_file.exists():
    trades = pd.read_csv(transactions_file, parse_dates=True)

    # Analyze trade distribution
    print(f"Total trades: {len(trades)}")
    print(f"Long trades: {(trades['amount'] > 0).sum()}")
    print(f"Short trades: {(trades['amount'] < 0).sum()}")
```

### Export to Spreadsheet

```python
# Save metrics for external analysis
import json
with open(result_dir / 'metrics.json') as f:
    metrics = json.load(f)

pd.DataFrame([metrics]).to_csv('backtest_summary.csv', index=False)
```

## Performance Expectations

### Execution Time

| Date Range | Timeframe | Typical Duration |
|------------|-----------|------------------|
| 1 year | Daily | 10-30 seconds |
| 3 years | Daily | 30-90 seconds |
| 1 year | 1-hour | 2-5 minutes |
| 1 year | 1-minute | 10-30 minutes |

**Slowdown factors**:
- Pipeline calculations
- Complex order logic
- Large universe (>100 symbols)
- Frequent rebalancing

### Memory Requirements

| Configuration | Typical RAM |
|---------------|-------------|
| Single asset, daily, 5 years | 100-200 MB |
| Portfolio (10 assets), daily, 5 years | 300-500 MB |
| Single asset, 1-min, 1 year | 500-1000 MB |
| Portfolio (10 assets), 1-min, 1 year | 2-4 GB |

## Related Documentation

- **[run_backtest.py Script](../scripts_reference.md#run-backtest)** - CLI equivalent
- **[Backtest API](../api/backtest.md)** - `lib.backtest` module reference
- **[Strategy Template](../../strategies/_template/README.md)** - How to create strategies
- **[02_optimize.ipynb](02_optimize.md)** - Next step: optimization
- **[03_analyze.ipynb](03_analyze.md)** - Deep analysis of results

## Version Notes

### v1.12.0 Changes (NO WRAPPERS)

- **Direct imports**: Uses `zipline.run_algorithm()` directly
- **Bundle loading**: Uses `lib.bundles.load_bundle()` (universal loader)
- **Calendar access**: Uses `get_calendar()` directly
- **No SessionManager**: Removed session alignment workarounds

### Migration from v1.11

```python
# OLD (v1.11)
from lib.backtest.runner import BacktestRunner
runner = BacktestRunner(strategy_name)
perf = runner.run(...)

# NEW (v1.12)
from lib.backtest import run_backtest
perf = run_backtest(strategy_name, ...)
```

---

**Last Updated**: 2026-02-09
**Version**: v1.12.0
**Notebook File**: `notebooks/01_backtest.ipynb`
