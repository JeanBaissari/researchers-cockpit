# Assess Risk

## Overview

Perform risk assessment for strategies including drawdown analysis, VaR calculation, position sizing recommendations, and stress testing scenarios.

## Steps

1. **Calculate Risk Metrics** - Compute MaxDD, VaR, volatility, and other risk metrics
2. **Analyze Drawdown Patterns** - Examine drawdown duration, recovery time, frequency
3. **Recommend Position Sizing** - Suggest fixed, volatility-scaled, or Kelly-based sizing
4. **Stress Testing** - Test strategy under extreme market conditions
5. **Risk Mitigation Strategies** - Recommend stop losses, position limits, diversification

## Checklist

- [ ] Risk metrics calculated (MaxDD, VaR, volatility)
- [ ] Drawdown patterns analyzed
- [ ] Position sizing recommendations provided
- [ ] Stress testing scenarios run
- [ ] Risk mitigation strategies documented
- [ ] Risk assessment report generated

## Risk Assessment Patterns

**Calculate risk metrics:**
```python
from lib.metrics import calculate_metrics
from lib.backtest.results import load_backtest_results
from pathlib import Path
import pandas as pd

# Load results
results_dir = Path('results/btc_sma_cross/latest')
returns = pd.read_csv(results_dir / 'returns.csv', index_col=0, parse_dates=True)

# Calculate risk metrics
metrics = calculate_metrics(returns)

print("Risk Metrics:")
print(f"  Max Drawdown: {metrics['max_drawdown']:.2%}")
print(f"  Volatility: {metrics['volatility']:.2%}")
print(f"  Sharpe Ratio: {metrics['sharpe']:.2f}")
print(f"  Sortino Ratio: {metrics['sortino']:.2f}")
print(f"  Calmar Ratio: {metrics['calmar']:.2f}")
```

**Analyze drawdown patterns:**
```python
import pandas as pd

cumulative = (1 + returns).cumprod()
running_max = cumulative.expanding().max()
drawdown = (cumulative - running_max) / running_max

max_dd = drawdown.min()
max_dd_date = drawdown.idxmin()
print(f"Max Drawdown: {max_dd:.2%} on {max_dd_date.date()}")
```

**Recommend position sizing:**
```python
from lib.position_sizing import compute_position_size

# Fixed sizing (simple)
fixed_params = {'position_sizing': {'method': 'fixed', 'max_position_pct': 0.95}}

# Volatility-scaled (risk parity)
vol_params = {'position_sizing': {'method': 'volatility_scaled', 'max_position_pct': 0.95, 'target_volatility': 0.15}}

# Kelly Criterion (aggressive)
kelly_params = {'position_sizing': {'method': 'kelly', 'max_position_pct': 0.95, 'kelly': {'win_rate_estimate': 0.55, 'kelly_fraction': 0.25}}}

# Recommend based on metrics
if metrics['sharpe'] > 1.5 and metrics['win_rate'] > 0.55:
    print("Recommendation: Use volatility-scaled or Kelly sizing")
else:
    print("Recommendation: Use conservative fixed sizing (50-75%)")
```

**Stress testing:**
```python
high_vol_periods = returns[returns.rolling(20).std() > returns.rolling(20).std().quantile(0.9)]
if len(high_vol_periods) > 0:
    stress_metrics = calculate_metrics(high_vol_periods)
    print(f"Stress Test - Sharpe: {stress_metrics['sharpe']:.2f}, MaxDD: {stress_metrics['max_drawdown']:.2%}")
```

## Risk Metrics to Calculate

- **Max Drawdown** - Worst peak-to-trough decline
- **VaR (Value at Risk)** - Potential loss at confidence level
- **Volatility** - Standard deviation of returns
- **Sharpe/Sortino** - Risk-adjusted returns
- **Calmar Ratio** - Return/MaxDD ratio
- **Recovery Time** - Days to recover from max drawdown

## Position Sizing Methods

- **Fixed** - Constant position size (simple, predictable)
- **Volatility-Scaled** - Adjust size based on volatility (risk parity)
- **Kelly Criterion** - Optimal sizing based on win rate and edge (aggressive)

## Notes

- Use `lib/risk_management.py` and `lib/position_sizing.py` (don't duplicate risk logic)
- Use `lib/metrics/` for risk metric calculations
- Single responsibility: risk assessment only
- Be conservative with position sizing recommendations
- Stress test under extreme conditions before live trading

## Related Commands

- analyze-results.md - For detailed performance analysis
- run-backtest.md - For running backtests to assess risk
- optimize-parameters.md - For optimizing risk parameters

