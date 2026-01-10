# Compare Strategies

## Overview

Compare multiple strategies side-by-side with metrics, ranking, and correlation analysis to identify best performers and understand strategy relationships.

## Steps

1. **Load Strategy Metrics** - Load latest metrics from multiple strategies using `lib/metrics/comparison.py`
2. **Create Comparison DataFrame** - Build comparison table with key metrics
3. **Rank Strategies** - Sort by Sharpe, Sortino, MaxDD, or other metrics
4. **Analyze Correlations** - Check if strategies are correlated or diversified
5. **Visualize Comparison** - Create equity curves overlay and comparison charts
6. **Identify Best Performers** - Highlight top strategies by different criteria

## Checklist

- [ ] Multiple strategies selected for comparison
- [ ] Metrics loaded from results/{strategy}/latest/metrics.json
- [ ] Comparison DataFrame created with key metrics
- [ ] Strategies ranked by different metrics
- [ ] Correlation analysis completed (if multiple strategies)
- [ ] Visualizations generated (equity curves overlay)
- [ ] Best performers identified and documented

## Comparison Patterns

**Load and compare strategies:**
```python
from lib.metrics import compare_strategies
from lib.utils import get_project_root
import pandas as pd

# Compare multiple strategies
strategy_names = ['btc_sma_cross', 'eth_momentum', 'spy_sma_cross']
comparison_df = compare_strategies(strategy_names)

# Display comparison
print(comparison_df.to_string(index=False))
```

**Rank by different metrics:**
```python
# Rank by Sharpe ratio
sharpe_ranked = comparison_df.sort_values('sharpe', ascending=False)
print("Ranked by Sharpe:")
print(sharpe_ranked[['strategy', 'sharpe', 'annual_return', 'max_drawdown']])

# Rank by Sortino ratio
sortino_ranked = comparison_df.sort_values('sortino', ascending=False)
print("\nRanked by Sortino:")
print(sortino_ranked[['strategy', 'sortino', 'annual_return', 'max_drawdown']])

# Rank by Calmar ratio
calmar_ranked = comparison_df.sort_values('calmar', ascending=False)
print("\nRanked by Calmar:")
print(calmar_ranked[['strategy', 'calmar', 'annual_return', 'max_drawdown']])
```

**Visualize equity curves overlay:**
```python
from lib.plots import plot_equity_curve
import pandas as pd
import json
from pathlib import Path

root = get_project_root()
equity_curves = {}

# Load equity curves for each strategy
for strategy_name in strategy_names:
    results_dir = root / 'results' / strategy_name / 'latest'
    returns = pd.read_csv(results_dir / 'returns.csv', index_col=0, parse_dates=True)
    equity_curves[strategy_name] = (1 + returns).cumprod()

# Plot overlay
import matplotlib.pyplot as plt
for name, equity in equity_curves.items():
    plt.plot(equity.index, equity.values, label=name)
plt.legend()
plt.title('Strategy Equity Curves Comparison')
plt.xlabel('Date')
plt.ylabel('Cumulative Return')
plt.savefig('strategy_comparison.png')
```

**Notebook (Interactive):**
```python
# In notebooks/04_compare.ipynb
from lib.metrics import compare_strategies

strategy_names = ['btc_sma_cross', 'eth_momentum']
comparison_df = compare_strategies(strategy_names)

# Display and analyze
print(comparison_df)
```

## Key Metrics to Compare

- **Sharpe Ratio** - Risk-adjusted returns
- **Sortino Ratio** - Downside risk-adjusted returns
- **Annual Return** - Absolute performance
- **Max Drawdown** - Worst peak-to-trough decline
- **Calmar Ratio** - Return/MaxDD ratio
- **Win Rate** - Percentage of winning trades
- **Trade Count** - Number of trades executed

## Notes

- Use `lib/metrics/comparison.py:compare_strategies()` (don't duplicate comparison logic)
- Load metrics from `results/{strategy}/latest/metrics.json`
- Compare strategies with similar asset classes for meaningful comparison
- Consider correlation when building portfolio of strategies
- Rank by multiple metrics to get comprehensive view

## Related Commands

- analyze-results.md - For detailed analysis of individual strategies
- run-backtest.md - For running backtests before comparison
