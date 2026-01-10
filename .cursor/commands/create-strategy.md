# Create Strategy

## Overview

Create a new trading strategy from the template, following the hypothesis → strategy → backtest workflow pattern.

## Steps

1. **Copy Template** - Copy `strategies/_template/` to new strategy directory
2. **Create Hypothesis** - Write hypothesis.md with research question, reasoning, conditions, falsification
3. **Implement Strategy** - Edit strategy.py following Zipline-reloaded 3.1.0 patterns
4. **Configure Parameters** - Set initial parameters in parameters.yaml (externalize all tunable values)
5. **Validate Strategy** - Check syntax, imports, and parameter loading
6. **Create Results Symlink** - Link strategy/results to results/{strategy_name}/

## Checklist

- [ ] Strategy directory created from template
- [ ] hypothesis.md written with all required sections
- [ ] strategy.py implemented with Zipline patterns
- [ ] parameters.yaml configured (no hardcoded params in strategy.py)
- [ ] Strategy syntax validated
- [ ] Results symlink created
- [ ] Strategy ready for backtest

## Strategy Creation Patterns

**Copy template:**
```bash
# From project root
cp -r strategies/_template strategies/crypto/btc_new_strategy
cd strategies/crypto/btc_new_strategy
```

**Write hypothesis.md:**
```markdown
# Strategy Hypothesis

## The Belief
BTC price trends persist for 15-30 days after a moving average crossover.

## The Reasoning
Retail FOMO creates momentum. Institutional rebalancing creates mean reversion boundaries.

## The Conditions
Works in trending markets. Fails in choppy, sideways conditions.

## The Falsification
If Sharpe < 0.5 across 3+ years of data, the edge doesn't exist.
```

**Implement strategy.py:**
```python
from zipline.api import order_target_percent, symbol, record
from lib.config.strategy import load_strategy_params

def initialize(context):
    """Initialize strategy with parameters from parameters.yaml."""
    params = load_strategy_params('btc_new_strategy', asset_class='crypto')
    context.symbol = symbol(params['strategy']['symbol'])
    context.fast_period = params['strategy']['fast_period']
    context.slow_period = params['strategy']['slow_period']
    
def handle_data(context, data):
    """Handle data each bar."""
    if not data.can_trade(context.symbol):
        return
    
    prices = data.history(context.symbol, 'price', context.slow_period, '1d')
    fast_ma = prices[-context.fast_period:].mean()
    slow_ma = prices.mean()
    
    if fast_ma > slow_ma:
        order_target_percent(context.symbol, 1.0)
    else:
        order_target_percent(context.symbol, 0.0)
    
    record(fast_ma=fast_ma, slow_ma=slow_ma)
```

**Configure parameters.yaml:**
```yaml
strategy:
  symbol: BTC-USD
  fast_period: 10
  slow_period: 50

position_sizing:
  max_position_pct: 0.95

risk:
  stop_loss_pct: 0.02
  take_profit_pct: 0.05
```

**Create results symlink:**
```bash
# From strategy directory
ln -s ../../../results/btc_new_strategy results
```

## Notes

- Always start from `strategies/_template/` (don't copy from other strategies)
- Externalize ALL parameters to parameters.yaml (no hardcoded values)
- Use lib/config.strategy.load_strategy_params() to load parameters
- Follow Zipline-reloaded 3.1.0 Pipeline API patterns
- Use UTC timezone for all datetime operations
- Validate strategy syntax before first backtest

## Related Commands

- run-backtest.md - For running first backtest
- add-documentation.md - For documenting strategy logic
- optimize-parameters.md - For parameter optimization
