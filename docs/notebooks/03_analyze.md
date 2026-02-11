# 03 - Analyze Notebook

**File**: `notebooks/03_analyze.ipynb`
**Purpose**: Deep analysis of backtest results with comprehensive metrics and visualizations
**Architecture**: v1.12.0 NO WRAPPERS

## Overview

The Analyze notebook provides in-depth examination of backtest results beyond the summary metrics shown in `01_backtest.ipynb`.

## Configuration

```python
strategy_name = 'spy_sma_cross'
result_dir = None  # None = use latest, or specify path
```

## Key Features

### Comprehensive Metrics

```python
from lib.metrics import calculate_metrics, calculate_trade_metrics

# Performance metrics
metrics = calculate_metrics(returns)

# Trade analysis
trade_metrics = calculate_trade_metrics(transactions, perf)
```

**Metrics calculated**:
- **Returns**: Total, annual, CAGR, best/worst periods
- **Risk-adjusted**: Sharpe, Sortino, Calmar, Omega
- **Risk**: Max drawdown, volatility, beta, VaR
- **Trades**: Win rate, profit factor, avg win/loss, hold time

### Rolling Metrics

```python
rolling_metrics = calculate_rolling_metrics(
    returns,
    window=30,  # 30-day window
    metrics=['sharpe', 'sortino', 'volatility']
)
```

**Purpose**: See how strategy performs over time
**Use cases**:
- Detect regime changes
- Identify stability periods
- Spot degradation

### Visualizations

Generated plots:
1. **Equity Curve**: Portfolio value over time
2. **Drawdown**: Underwater periods
3. **Monthly Returns**: Heatmap of returns by month/year
4. **Rolling Metrics**: Time series of rolling Sharpe, volatility
5. **Trade Analysis**: Win/loss distribution, hold times

### Return Distribution

```python
# Histogram + Q-Q plot
returns = perf['returns']
plt.hist(returns, bins=50)
scipy.stats.probplot(returns, plot=ax)
```

**Statistics**:
- **Skewness**: Asymmetry of distribution
- **Kurtosis**: Fat tails (extreme events)
- **Normality test**: How close to Gaussian

**Interpretation**:
- Negative skew: Crash risk (many small gains, few large losses)
- Positive kurtosis: Fat tails (more extreme events than normal)
- Q-Q plot deviates: Returns not normally distributed

## When to Use

### Primary Use Cases ✓

- After backtest to understand why strategy works
- Before optimization to identify weaknesses
- For performance attribution
- When preparing investor reports

### Comparison

| Notebook | Metrics | Depth | Purpose |
|----------|---------|-------|---------|
| 01_backtest | Summary only | Basic | Quick validation |
| **03_analyze** | Comprehensive | Deep | Understanding |
| 04_compare | Cross-strategy | Medium | Selection |

## Common Patterns

### Identify Problem Periods

```python
# Find worst drawdown period
dd_start = drawdown.idxmin()
dd_series = perf.loc[:dd_start]

print(f"Worst drawdown started: {dd_start}")
print(f"Drawdown magnitude: {drawdown.min():.2%}")
```

### Analyze Trade Clusters

```python
if transactions is not None:
    # Group trades by month
    transactions['month'] = transactions.index.to_period('M')
    monthly_trades = transactions.groupby('month').size()

    # Find most active months
    print(monthly_trades.nlargest(5))
```

### Compare to Benchmark

```python
# Calculate benchmark returns (e.g., buy-and-hold)
benchmark_returns = perf['benchmark_return']
excess_returns = perf['returns'] - benchmark_returns

print(f"Average excess return: {excess_returns.mean():.4f}")
```

## Troubleshooting

### "No transactions data"

**Symptom**: Trade metrics unavailable
**Cause**: Strategy didn't place orders or `transactions.csv` missing
**Fix**: Check strategy logic places orders via `order_target_percent()`

### "Rolling metrics all NaN"

**Symptom**: Rolling calculations return NaN
**Cause**: Insufficient data for window size
**Fix**: Reduce `window` parameter or use longer backtest period

### "Visualizations don't show"

**Symptom**: Plots not displayed
**Cause**: Matplotlib backend issue or `show=False`
**Fix**: Run `%matplotlib inline` in notebook or set `show=True`

## Best Practices

### Do's ✓

1. **Review all metrics**: Don't focus only on Sharpe
2. **Inspect worst periods**: Understand failure modes
3. **Check trade distribution**: Ensure sufficient sample size
4. **Validate assumptions**: Test normality, correlations
5. **Document findings**: Note insights for strategy docs

### Don'ts ✗

1. **Don't ignore negative skew**: Indicates crash risk
2. **Don't overlook long drawdowns**: May exceed risk tolerance
3. **Don't dismiss outliers**: Investigate causes
4. **Don't skip rolling metrics**: Static metrics hide dynamics
5. **Don't cherry-pick**: Report full picture

## Output Files

```
results/{strategy_name}/latest/
├── equity_curve.png
├── drawdown.png
├── monthly_returns.png
├── rolling_metrics.png
├── trade_analysis.png
└── returns_distribution.png
```

All plots saved automatically when `plot_all()` runs.

## Advanced Usage

### Custom Metric Calculation

```python
# Example: Calculate Omega ratio
def omega_ratio(returns, threshold=0):
    gains = returns[returns > threshold] - threshold
    losses = threshold - returns[returns < threshold]
    return gains.sum() / losses.sum() if losses.sum() > 0 else np.inf

omega = omega_ratio(perf['returns'])
print(f"Omega Ratio: {omega:.3f}")
```

### Performance Attribution

```python
# Decompose returns by signal source
if 'signal_1' in perf.columns and 'signal_2' in perf.columns:
    # Calculate contribution of each signal
    signal_1_contrib = perf['signal_1'] * perf['returns']
    signal_2_contrib = perf['signal_2'] * perf['returns']

    print(f"Signal 1 contribution: {signal_1_contrib.sum():.2%}")
    print(f"Signal 2 contribution: {signal_2_contrib.sum():.2%}")
```

### Regime Analysis

```python
# Identify bull/bear regimes
bull_mask = perf['returns'].rolling(30).mean() > 0
bear_mask = ~bull_mask

bull_sharpe = perf.loc[bull_mask, 'returns'].mean() / perf.loc[bull_mask, 'returns'].std()
bear_sharpe = perf.loc[bear_mask, 'returns'].mean() / perf.loc[bear_mask, 'returns'].std()

print(f"Bull market Sharpe: {bull_sharpe:.3f}")
print(f"Bear market Sharpe: {bear_sharpe:.3f}")
```

## Related Documentation

- **[Metrics API](../api/metrics.md)** - `lib.metrics` reference
- **[Plots API](../api/plots.md)** - `lib.plots` reference
- **[01_backtest.ipynb](01_backtest.md)** - Run backtest first
- **[04_compare.ipynb](04_compare.md)** - Compare strategies

---

**Last Updated**: 2026-02-09
**Version**: v1.12.0
