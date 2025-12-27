# Analyst Guide — AI Agent Instructions

> Step-by-step guide for analyzing backtest results and generating actionable insights.

---

## Overview

Analysis transforms raw backtest results into understanding. This guide ensures you:

1. **Examine equity curve shape** — Smooth or jagged?
2. **Analyze trade distribution** — Balanced wins/losses?
3. **Identify regime performance** — Works in bull/bear/sideways?
4. **Assess parameter sensitivity** — Robust or fragile?
5. **Generate recommendations** — Proceed, modify, or abandon?

---

## Pre-Analysis Setup

### Load Results

```python
from pathlib import Path
import pandas as pd
import json

strategy_name = 'btc_sma_cross'
results_dir = Path(f'results/{strategy_name}/latest')

# Load core data
returns = pd.read_csv(results_dir / 'returns.csv', index_col=0, parse_dates=True)
positions = pd.read_csv(results_dir / 'positions.csv', index_col=0, parse_dates=True)
transactions = pd.read_csv(results_dir / 'transactions.csv', index_col=0, parse_dates=True)

# Load metrics
with open(results_dir / 'metrics.json') as f:
    metrics = json.load(f)

# Load parameters used
import yaml
with open(results_dir / 'parameters_used.yaml') as f:
    params = yaml.safe_load(f)
```

---

## Analysis Checklist

### 1. Equity Curve Examination

**Questions to Answer:**
- Is the curve smooth or jagged?
- Are there long flat periods?
- When did drawdowns occur?
- Is growth consistent or episodic?

**Analysis:**

```python
import matplotlib.pyplot as plt
import numpy as np

# Calculate equity curve
equity = (1 + returns).cumprod()

# Plot equity curve
plt.figure(figsize=(12, 6))
plt.plot(equity.index, equity.values)
plt.title('Equity Curve')
plt.xlabel('Date')
plt.ylabel('Portfolio Value')
plt.grid(True)
plt.savefig(results_dir / 'equity_curve_analysis.png')

# Identify drawdown periods
cumulative = equity
running_max = cumulative.cummax()
drawdown = (cumulative - running_max) / running_max

max_dd_period = drawdown.idxmin()
max_dd_value = drawdown.min()

print(f"Maximum Drawdown: {max_dd_value:.2%}")
print(f"Max DD Date: {max_dd_period}")
print(f"Recovery Time: {calculate_recovery_time(drawdown)} days")
```

**Interpretation:**
- **Smooth curve:** Consistent performance, low volatility
- **Jagged curve:** High volatility, many small trades
- **Long flat periods:** Strategy inactive, waiting for signals
- **Sharp drawdowns:** Risk management may be insufficient

### 2. Trade Distribution Analysis

**Questions to Answer:**
- Are wins and losses balanced?
- Any outlier trades driving results?
- Consistent behavior across time?
- Win rate acceptable?

**Analysis:**

```python
# Calculate trade statistics
winning_trades = transactions[transactions['amount'] > 0]
losing_trades = transactions[transactions['amount'] < 0]

n_trades = len(transactions)
n_wins = len(winning_trades)
n_losses = len(losing_trades)
win_rate = n_wins / n_trades if n_trades > 0 else 0

avg_win = winning_trades['amount'].mean() if len(winning_trades) > 0 else 0
avg_loss = abs(losing_trades['amount'].mean()) if len(losing_trades) > 0 else 0
profit_factor = (avg_win * n_wins) / (avg_loss * n_losses) if avg_loss > 0 else 0

# Identify outliers
largest_win = transactions['amount'].max()
largest_loss = transactions['amount'].min()

print(f"Total Trades: {n_trades}")
print(f"Win Rate: {win_rate:.1%}")
print(f"Average Win: ${avg_win:.2f}")
print(f"Average Loss: ${avg_loss:.2f}")
print(f"Profit Factor: {profit_factor:.2f}")
print(f"Largest Win: ${largest_win:.2f}")
print(f"Largest Loss: ${largest_loss:.2f}")
```

**Interpretation:**
- **Win rate > 50%:** Good, but check profit factor
- **Profit factor > 1.5:** Wins larger than losses
- **Outlier trades:** Remove and re-test if single trade drives results
- **Consistent trades:** Good, strategy behaves predictably

### 3. Regime Analysis

**Questions to Answer:**
- Performance in bull markets?
- Performance in bear markets?
- Performance in sideways markets?
- Strategy regime-dependent?

**Analysis:**

```python
# Define regimes (simplified - use more sophisticated methods)
# Bull: SPY up >20% over 6 months
# Bear: SPY down >20% over 6 months
# Sideways: SPY within ±10% over 6 months

# Load benchmark (if available)
benchmark_returns = returns  # Use actual benchmark if available

# Calculate rolling 6-month returns
rolling_6m = benchmark_returns.rolling(126).sum()  # ~6 months

# Classify regimes
regimes = pd.Series(index=returns.index, dtype=str)
regimes[rolling_6m > 0.20] = 'bull'
regimes[rolling_6m < -0.20] = 'bear'
regimes[(rolling_6m >= -0.10) & (rolling_6m <= 0.10)] = 'sideways'
regimes[regimes.isna()] = 'unknown'

# Calculate performance by regime
regime_performance = {}
for regime in ['bull', 'bear', 'sideways']:
    regime_returns = returns[regimes == regime]
    if len(regime_returns) > 0:
        regime_sharpe = np.sqrt(252) * regime_returns.mean() / regime_returns.std()
        regime_performance[regime] = {
            'sharpe': regime_sharpe,
            'total_return': regime_returns.sum(),
            'n_days': len(regime_returns)
        }

print("Regime Performance:")
for regime, perf in regime_performance.items():
    print(f"{regime}: Sharpe={perf['sharpe']:.2f}, Return={perf['total_return']:.2%}")
```

**Interpretation:**
- **Works in all regimes:** Robust strategy
- **Works in 2/3 regimes:** Acceptable, note limitations
- **Works in 1/3 regimes:** Regime-dependent, consider regime filter
- **Fails in all regimes:** Strategy not viable

### 4. Parameter Sensitivity Analysis

**Questions to Answer:**
- Would slight parameter changes destroy results?
- Is the edge robust or fragile?
- Parameter cliff edges?

**Analysis:**

```python
# If optimization was run, use optimization results
opt_dir = Path(f'results/{strategy_name}/optimization_*')
if opt_dir.exists():
    opt_results = pd.read_csv(list(opt_dir.glob('grid_results.csv'))[0])
    
    # Calculate parameter sensitivity
    param_sensitivity = {}
    for param in ['fast_period', 'slow_period']:
        if param in opt_results.columns:
            sharpe_by_param = opt_results.groupby(param)['sharpe'].mean()
            sensitivity = sharpe_by_param.std() / sharpe_by_param.mean()
            param_sensitivity[param] = sensitivity
    
    print("Parameter Sensitivity:")
    for param, sens in param_sensitivity.items():
        robustness = "Robust" if sens < 0.2 else "Fragile"
        print(f"{param}: {sens:.2f} ({robustness})")
```

**Interpretation:**
- **Low sensitivity (<0.2):** Robust, small changes don't matter
- **High sensitivity (>0.5):** Fragile, likely overfit
- **Cliff edges:** Sharp performance drops at certain values

### 5. Risk Characteristics

**Questions to Answer:**
- Maximum drawdown acceptable?
- Recovery time reasonable?
- Volatility consistent?
- Tail risk present?

**Analysis:**

```python
# Calculate risk metrics
max_dd = metrics['max_drawdown']
sortino = metrics['sortino']
calmar = metrics['calmar']  # Return / MaxDD

# Calculate recovery times
drawdown_periods = identify_drawdown_periods(drawdown)
avg_recovery_time = np.mean([p['recovery_days'] for p in drawdown_periods])

# Tail risk (5th percentile daily return)
tail_risk = returns.quantile(0.05)

print(f"Maximum Drawdown: {max_dd:.2%}")
print(f"Sortino Ratio: {sortino:.2f}")
print(f"Calmar Ratio: {calmar:.2f}")
print(f"Average Recovery Time: {avg_recovery_time:.0f} days")
print(f"5th Percentile Daily Return: {tail_risk:.2%}")
```

**Interpretation:**
- **MaxDD < 20%:** Acceptable for most strategies
- **Recovery < 60 days:** Quick recovery, good
- **High tail risk:** Large occasional losses, consider stops

---

## Recommendation Framework

After analysis, generate recommendation:

### Decision Matrix

| Sharpe | MaxDD | Win Rate | Regime Consistency | Recommendation |
|--------|-------|----------|-------------------|----------------|
| > 1.0 | < 20% | > 50% | All regimes | ✅ Proceed to optimization |
| > 0.7 | < 25% | > 45% | 2/3 regimes | ✅ Proceed with caution |
| > 0.5 | < 30% | > 40% | 1/3 regimes | ⚠️ Modify strategy |
| < 0.5 | Any | Any | Any | ❌ Abandon |

### Recommendation Template

```python
def generate_recommendation(metrics, analysis):
    """Generate recommendation based on analysis."""
    
    sharpe = metrics['sharpe']
    max_dd = metrics['max_drawdown']
    win_rate = analysis['win_rate']
    regime_consistency = analysis['regime_consistency']
    
    if sharpe > 1.0 and max_dd < 0.20 and win_rate > 0.50 and regime_consistency == 'all':
        return {
            'action': 'proceed',
            'confidence': 'high',
            'next_step': 'Run parameter optimization',
            'reason': 'Strong performance across all metrics'
        }
    elif sharpe > 0.7 and max_dd < 0.25:
        return {
            'action': 'proceed_with_caution',
            'confidence': 'medium',
            'next_step': 'Run walk-forward validation',
            'reason': 'Good performance but needs validation'
        }
    elif sharpe > 0.5:
        return {
            'action': 'modify',
            'confidence': 'low',
            'next_step': 'Review hypothesis and implementation',
            'reason': 'Marginal performance, likely needs improvement'
        }
    else:
        return {
            'action': 'abandon',
            'confidence': 'high',
            'next_step': 'Document learnings, move to next strategy',
            'reason': 'Poor performance, strategy not viable'
        }
```

---

## Output Summary Format

After analysis, provide:

```
Analysis complete for strategy: {strategy_name}

Performance Summary:
- Sharpe Ratio: {sharpe:.2f}
- Sortino Ratio: {sortino:.2f}
- Max Drawdown: {max_dd:.2%}
- Win Rate: {win_rate:.1%}
- Total Trades: {n_trades}

Equity Curve:
- Shape: {smooth|jagged|episodic}
- Drawdowns: {description}
- Recovery: {avg_recovery_time} days

Trade Distribution:
- Average Win: ${avg_win:.2f}
- Average Loss: ${avg_loss:.2f}
- Profit Factor: {profit_factor:.2f}
- Outliers: {present|absent}

Regime Performance:
- Bull: Sharpe={bull_sharpe:.2f}
- Bear: Sharpe={bear_sharpe:.2f}
- Sideways: Sharpe={sideways_sharpe:.2f}

Parameter Sensitivity:
- {param}: {robust|fragile}

Recommendation: {proceed|proceed_with_caution|modify|abandon}
Reason: {explanation}
Next: {suggested_action}
```

---

## Visualization Checklist

Generate these plots:

- [ ] Equity curve with drawdown overlay
- [ ] Monthly returns heatmap
- [ ] Trade distribution histogram
- [ ] Win/loss scatter plot
- [ ] Regime performance comparison
- [ ] Rolling Sharpe ratio
- [ ] Parameter sensitivity heatmap (if optimization run)

**See:** `lib/plots.py` for plotting functions

---

## Common Issues and Solutions

### Issue: Equity curve is jagged

**Possible causes:**
- Too many small trades
- High transaction costs
- Strategy too sensitive

**Solutions:**
- Increase rebalance frequency threshold
- Reduce position sizing
- Add signal smoothing

### Issue: Long flat periods

**Possible causes:**
- Strategy waiting for signals
- Market conditions not met
- Parameters too restrictive

**Solutions:**
- Review signal generation logic
- Check if filters are too strict
- Consider regime detection

### Issue: Outlier trades driving results

**Possible causes:**
- Single large win/loss
- Data errors
- Exceptional market event

**Solutions:**
- Remove outlier and re-test
- Check data quality
- Add position sizing limits

### Issue: Poor regime performance

**Possible causes:**
- Strategy designed for specific regime
- Missing regime filter
- Parameters not adaptive

**Solutions:**
- Add regime detection
- Use adaptive parameters
- Consider multiple strategies

---

## Related Files

- **Metrics calculation:** `lib/metrics.py`
- **Plotting:** `lib/plots.py`
- **Results:** `results/{strategy_name}/latest/`
- **Optimization results:** `results/{strategy_name}/optimization_*/`

---

## Next Steps

After analysis:

1. **If proceed:** Run parameter optimization
2. **If proceed with caution:** Run walk-forward validation first
3. **If modify:** Review hypothesis, adjust implementation
4. **If abandon:** Document learnings, archive strategy

**See:** `.agent/optimizer.md` for optimization procedures

