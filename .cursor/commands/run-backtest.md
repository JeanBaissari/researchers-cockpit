# Run Backtest

## Overview

Execute a backtest for a strategy, validate inputs, run Zipline algorithm, and save results to timestamped directory with metrics and visualizations.

## Steps

1. **Validate Strategy** - Check strategy file exists, syntax valid, parameters loadable
2. **Check Data Bundle** - Verify bundle exists and has data for date range
3. **Validate Parameters** - Check parameter ranges, required fields, warmup period
4. **Run Backtest** - Execute Zipline algorithm with strategy and data
5. **Calculate Metrics** - Compute performance metrics (Sharpe, MaxDD, etc.)
6. **Save Results** - Save to results/{strategy}/backtest_{timestamp}/
7. **Update Symlink** - Update results/{strategy}/latest symlink

## Checklist

- [ ] Strategy file exists and syntax valid
- [ ] Data bundle exists and has data for date range
- [ ] Parameters validated (ranges, required fields)
- [ ] Backtest executed successfully
- [ ] Metrics calculated and saved
- [ ] Results saved to timestamped directory
- [ ] Latest symlink updated
- [ ] Summary metrics reported

## Execution Methods

**Script (CLI):**
```bash
python scripts/run_backtest.py --strategy btc_sma_cross
python scripts/run_backtest.py --strategy btc_sma_cross --start 2023-01-01 --end 2023-12-31
python scripts/run_backtest.py --strategy btc_sma_cross --capital 100000 --bundle yahoo_crypto_daily
```

**Library (Programmatic):**
```python
from lib.backtest import run_backtest, save_results

# Run backtest
returns, calendar = run_backtest(
    strategy_name='btc_sma_cross',
    start_date='2023-01-01',
    end_date='2023-12-31',
    capital_base=100000,
    bundle='yahoo_crypto_daily',
    asset_class='crypto'
)

# Save results
save_results('btc_sma_cross', returns, calendar)
```

**Notebook (Interactive):**
```python
# In notebooks/01_backtest.ipynb
strategy_name = 'btc_sma_cross'
from lib.backtest import run_backtest
returns, calendar = run_backtest(strategy_name)
```

## Output Structure

```
results/{strategy}/backtest_{timestamp}/
├── returns.csv           # Time series of returns
├── positions.csv         # Position sizes over time
├── transactions.csv      # Every trade with prices, costs
├── metrics.json          # Calculated performance metrics
├── parameters_used.yaml  # Exact params (for reproducibility)
└── equity_curve.png      # Visual representation
```

## Metrics Calculated

- Sharpe Ratio (annualized)
- Sortino Ratio
- Maximum Drawdown
- Calmar Ratio
- Annual Return
- Annual Volatility
- Win Rate
- Profit Factor
- Average Trade Duration
- Trades Per Month

## Common Issues

**Bundle not found:**
```bash
# Error: Bundle 'yahoo_crypto_daily' not found
# Solution: Ingest data first
python scripts/ingest_data.py --source yahoo --assets crypto
```

**Calendar mismatch:**
```bash
# Error: Calendar mismatch between bundle and strategy
# Solution: Check asset class matches (crypto uses CRYPTO calendar)
```

**Parameter validation error:**
```bash
# Error: Missing required parameter 'fast_period'
# Solution: Check parameters.yaml has all required fields
```

## Notes

- Use shorter date ranges for quick validation (1 year)
- Expand to full history after initial validation
- Check bundle existence before running backtest
- Validate parameters match strategy requirements
- Results are saved automatically with timestamp

## Related Commands

- create-strategy.md - For creating new strategies
- analyze-results.md - For analyzing backtest results
- optimize-parameters.md - For parameter optimization
