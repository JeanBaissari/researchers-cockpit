# Analyze Results

## Overview

Analyze backtest results to understand strategy performance, examine equity curve, trade distribution, regime breakdown, and generate visualizations.

## Steps

1. **Load Results** - Load metrics, returns, positions, transactions from results directory
2. **Examine Equity Curve** - Analyze shape, drawdowns, smoothness
3. **Analyze Trade Distribution** - Check win/loss balance, outlier trades
4. **Regime Analysis** - Performance in bull/bear/sideways markets
5. **Parameter Sensitivity** - Check robustness to parameter changes
6. **Generate Visualizations** - Create equity curve, drawdown, trade distribution plots
7. **Summarize Findings** - Document insights and recommendations

## Checklist

- [ ] Results loaded from results/{strategy}/latest/
- [ ] Equity curve examined (shape, drawdowns, smoothness)
- [ ] Trade distribution analyzed (wins/losses, outliers)
- [ ] Regime breakdown completed (bull/bear/sideways)
- [ ] Parameter sensitivity assessed
- [ ] Visualizations generated
- [ ] Findings summarized with recommendations

## Analysis Methods

**Load results:**
```python
from lib.backtest.results import load_backtest_results
import json

results_dir = Path('results/btc_sma_cross/latest')
results = load_backtest_results(results_dir)

# Load metrics
with open(results_dir / 'metrics.json') as f:
    metrics = json.load(f)

# Load returns
returns = pd.read_csv(results_dir / 'returns.csv', index_col=0, parse_dates=True)
```

**Examine equity curve:**
```python
from lib.plots import plot_equity_curve, plot_drawdown

# Plot equity curve
plot_equity_curve(returns, save_path='equity_curve.png')

# Plot drawdown
plot_drawdown(returns, save_path='drawdown.png')

# Analyze shape
print(f"Max drawdown: {metrics['max_drawdown']}")
print(f"Recovery time: {metrics['recovery_time_days']} days")
```

**Analyze trade distribution:**
```python
transactions = pd.read_csv(results_dir / 'transactions.csv', parse_dates=True)

# Win rate
wins = transactions[transactions['amount'] > 0]
losses = transactions[transactions['amount'] < 0]
win_rate = len(wins) / len(transactions)

# Average win/loss
avg_win = wins['amount'].mean()
avg_loss = abs(losses['amount'].mean())
profit_factor = avg_win / avg_loss if avg_loss > 0 else 0

print(f"Win rate: {win_rate:.2%}")
print(f"Profit factor: {profit_factor:.2f}")
```

**Regime analysis:**
```python
# Identify market regimes
bull_period = returns['2021-01-01':'2021-11-01']
bear_period = returns['2022-01-01':'2022-12-31']
sideways_period = returns['2023-01-01':'2023-06-30']

from lib.metrics import calculate_metrics

bull_metrics = calculate_metrics(bull_period)
bear_metrics = calculate_metrics(bear_period)
sideways_metrics = calculate_metrics(sideways_period)

print(f"Bull Sharpe: {bull_metrics['sharpe']:.2f}")
print(f"Bear Sharpe: {bear_metrics['sharpe']:.2f}")
print(f"Sideways Sharpe: {sideways_metrics['sharpe']:.2f}")
```

**Notebook (Interactive):**
```python
# In notebooks/03_analyze.ipynb
strategy_name = 'btc_sma_cross'
results_dir = Path(f'results/{strategy_name}/latest')

# Load and analyze
# ... analysis code ...
```

## Key Questions to Answer

- **Is the hypothesis supported?** (Yes/No/Partially)
- **What's the realistic Sharpe?** (Be conservative)
- **What's the maximum drawdown I should expect?** (Usually worse than backtest)
- **Should I optimize or abandon?**
- **Does it work across different market regimes?**

## Visualizations

- Equity curve (portfolio value over time)
- Drawdown chart (peak-to-trough declines)
- Trade distribution (win/loss histogram)
- Monthly returns heatmap
- Regime breakdown (performance by market condition)

## Notes

- Be conservative with Sharpe estimates (real-world usually worse)
- Check for outlier trades driving results
- Verify consistent behavior across time periods
- Assess parameter sensitivity (robust vs fragile)
- Document findings in hypothesis.md or analysis notes

## Related Commands

- run-backtest.md - For running backtests
- optimize-parameters.md - For parameter optimization
- validate-strategy.md - For validation after analysis
