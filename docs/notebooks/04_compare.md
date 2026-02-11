# 04 - Compare Notebook

**File**: `notebooks/04_compare.ipynb`
**Purpose**: Compare performance metrics across multiple strategies
**Architecture**: v1.12.0 NO WRAPPERS

## Overview

The Compare notebook allows side-by-side comparison of different strategies to identify the best performers or understand strategy variants.

## Configuration

```python
strategy_names = ['spy_sma_cross', 'spy_momentum', 'spy_mean_reversion']
```

**Customization**: Add all strategy names you want to compare (must have results in `results/` directory).

## Key Features

### Side-by-Side Metrics

```python
from lib.metrics import compare_strategies

comparison_df = compare_strategies(returns_dict)
```

**Output**: DataFrame with all strategies as rows, metrics as columns.

**Metrics compared**:
- Total Return
- Annual Return
- Sharpe Ratio
- Sortino Ratio
- Max Drawdown
- Calmar Ratio
- Volatility
- Trade Count
- Win Rate

### Cumulative Return Visualization

```python
# Plot all strategies on same chart
for name, returns in returns_dict.items():
    cumulative = (1 + returns).cumprod()
    plt.plot(cumulative.index, cumulative, label=name)
```

**Purpose**: Visual comparison of equity curves.

**What to look for**:
- Consistency: Smooth vs erratic growth
- Drawdowns: Depth and recovery time
- Correlation: Do strategies diverge or move together?

### Best Strategy Identification

```python
# Automatically identifies best by each metric
best_sharpe = comparison_df['Sharpe Ratio'].idxmax()
best_return = comparison_df['Total Return'].idxmax()
lowest_dd = comparison_df['Max Drawdown'].idxmin()
```

**Output**: Strategy name with best performance for each metric.

**Note**: "Best" depends on objective:
- Risk-averse: Minimize max drawdown
- Return-focused: Maximize total return
- Risk-adjusted: Maximize Sharpe ratio

## When to Use

### Primary Use Cases ✓

- Choosing between strategy variants
- Portfolio construction (diversification check)
- Validating improvements after modifications
- Reporting to stakeholders

### Example Scenarios

**Scenario 1: Parameter Variants**
```python
strategy_names = [
    'spy_sma_fast',    # Fast MA parameters
    'spy_sma_medium',  # Medium MA parameters
    'spy_sma_slow'     # Slow MA parameters
]
```

**Scenario 2: Asset Class Comparison**
```python
strategy_names = [
    'spy_momentum',    # Equity
    'eurusd_momentum', # Forex
    'btc_momentum'     # Crypto
]
```

**Scenario 3: Logic Comparison**
```python
strategy_names = [
    'spy_sma_cross',
    'spy_momentum',
    'spy_mean_reversion'
]
```

## Common Patterns

### Correlation Analysis

```python
# Check strategy correlation
returns_df = pd.DataFrame(returns_dict)
correlation_matrix = returns_df.corr()

print(correlation_matrix)

# Visualize
import seaborn as sns
sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm')
```

**Why it matters**:
- Low correlation (< 0.5): Good for diversification
- High correlation (> 0.8): Similar strategies, redundant
- Negative correlation: Natural hedges

### Risk-Adjusted Ranking

```python
# Rank by Sharpe ratio
ranked = comparison_df.sort_values('Sharpe Ratio', ascending=False)
print(ranked[['Sharpe Ratio', 'Max Drawdown', 'Total Return']])
```

### Identify Outliers

```python
# Find strategies with unusual characteristics
high_vol = comparison_df[comparison_df['Volatility'] > comparison_df['Volatility'].mean() * 1.5]
print(f"High volatility strategies: {list(high_vol.index)}")
```

## Interpretation Guide

### Comparing Returns

**Total Return**: Absolute performance
- Higher is better
- **But**: Ignores risk and time period

**Annual Return**: Normalized by time
- Better for different date ranges
- **But**: Still ignores risk

**Sharpe Ratio**: Risk-adjusted return
- Higher is better (> 1.0 is good, > 2.0 is excellent)
- **Best for**: Comparing risk-adjusted performance

### Comparing Risk

**Max Drawdown**: Worst peak-to-trough decline
- Lower (less negative) is better
- **Critical for**: Risk tolerance assessment

**Volatility**: Return standard deviation
- Lower is better (all else equal)
- **Note**: Some volatility needed for returns

**Calmar Ratio**: Return / Max Drawdown
- Higher is better
- **Best for**: Comparing risk-adjusted with downside focus

### Trade Metrics

**Trade Count**: Number of trades
- More trades → More commission costs
- Too few → Insufficient statistical sample

**Win Rate**: % of profitable trades
- Higher is better
- **Note**: 40-60% is typical for trend-following

**Profit Factor**: Gross profit / Gross loss
- > 1.0 required for profitability
- > 1.5 is good
- > 2.0 is excellent

## Troubleshooting

### "Insufficient strategies"

**Symptom**: Notebook requires 2+ strategies
**Cause**: Only one strategy has results
**Fix**: Run backtests for additional strategies first

### "Strategies have different date ranges"

**Symptom**: Comparison seems unfair
**Cause**: Backtests used different start/end dates
**Fix**: Re-run backtests with same date range for fair comparison

### "Cannot load strategy results"

**Symptom**: Error loading specific strategy
**Cause**: Missing `metrics.json` or `returns.csv` in results directory
**Fix**: Check `results/{strategy_name}/latest/` exists and has required files

## Best Practices

### Do's ✓

1. **Use same date range**: Fair comparison requires same period
2. **Consider correlation**: Portfolio of uncorrelated strategies is best
3. **Look beyond Sharpe**: Consider max drawdown, tail risk
4. **Check trade count**: Ensure statistical significance (> 30 trades)
5. **Document selection**: Explain why you chose one strategy over another

### Don'ts ✗

1. **Don't compare different asset classes directly**: Different risk profiles
2. **Don't ignore transaction costs**: High-frequency may suffer from slippage
3. **Don't select solely on returns**: Risk-adjusted metrics matter
4. **Don't forget sample size**: More data = more confidence
5. **Don't overlook regime dependency**: Works in bull market only?

## Advanced Usage

### Portfolio Construction

```python
# Calculate optimal weights (simple equal-weight)
weights = {name: 1/len(strategy_names) for name in strategy_names}

# Combine returns
portfolio_returns = sum(
    returns_dict[name] * weights[name]
    for name in strategy_names
)

# Calculate portfolio metrics
portfolio_sharpe = portfolio_returns.mean() / portfolio_returns.std() * np.sqrt(252)
print(f"Portfolio Sharpe: {portfolio_sharpe:.3f}")
```

### Mean-Variance Optimization

```python
from scipy.optimize import minimize

def neg_sharpe(weights, returns_df):
    portfolio = (returns_df * weights).sum(axis=1)
    return -portfolio.mean() / portfolio.std()

# Optimize weights
result = minimize(
    neg_sharpe,
    x0=[1/len(strategy_names)] * len(strategy_names),
    args=(returns_df,),
    constraints={'type': 'eq', 'fun': lambda w: w.sum() - 1},
    bounds=[(0, 1)] * len(strategy_names)
)

optimal_weights = dict(zip(strategy_names, result.x))
print(f"Optimal weights: {optimal_weights}")
```

## Output Files

This notebook does not create persistent files. All analysis is displayed inline.

**To save**:
- Export comparison DataFrame: `comparison_df.to_csv('comparison.csv')`
- Save plots manually via notebook interface

## Related Documentation

- **[Metrics API](../api/metrics.md)** - Comparison functions
- **[01_backtest.ipynb](01_backtest.md)** - Generate results to compare
- **[Portfolio Construction Guide](../code_patterns/portfolio_construction.md)**

---

**Last Updated**: 2026-02-09
**Version**: v1.12.0
