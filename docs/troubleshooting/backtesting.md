# Backtesting Troubleshooting

Best practices and working features for backtest execution.

---

## Warmup Period Validation

### How It Works

The system calculates required warmup days from your strategy's indicator periods:

```yaml
# parameters.yaml
strategy:
  fast_period: 10
  slow_period: 50  # <-- This is the max, so warmup = 50 days
```

### Validation Check

Before running, the system verifies:
```
available_days > warmup_days
```

### Error: Insufficient Data

```
ValueError: Insufficient data for strategy 'spy_sma_cross':
strategy requires 50 days warmup, but only 30 days provided
(2024-01-01 to 2024-01-31).
Either extend the backtest date range or reduce indicator periods in parameters.yaml.
```

**Solutions:**
1. Extend date range: `--start 2023-01-01`
2. Reduce indicator periods in `parameters.yaml`
3. Disable validation (not recommended): Add `validate_warmup: false` to `backtest` section

### Skip Warmup Check

```bash
python scripts/run_backtest.py --strategy my_strategy --skip-warmup-check
```

A warning is logged when skipping.

---

## Calendar Consistency

### What It Checks

The system warns if bundle calendar differs from backtest calendar:

```
WARNING: Calendar mismatch: Bundle 'yahoo_crypto_daily' was ingested with
calendar 'CRYPTO' but backtest is using 'XNYS'. This may cause session
misalignment errors.
```

### How to Fix

Ensure strategy's asset class matches bundle:

```yaml
# For crypto bundle, use crypto strategy location
strategies/crypto/my_strategy/

# Not equities location with crypto bundle
strategies/equities/my_strategy/  # Wrong!
```

### Explicit Calendar Override

```bash
python scripts/run_backtest.py --strategy my_strategy \
    --bundle yahoo_crypto_daily \
    --asset-class crypto
```

---

## Date Range Validation

### Checks Performed

1. Start date >= bundle first session
2. End date <= bundle last session

### Error: Date Out of Range

```
ValueError: Requested start date 2015-01-01 is before bundle start date 2020-01-01.
Bundle 'yahoo_equities_daily' covers: 2020-01-01 to 2024-12-28.
Re-ingest data with extended date range:
python scripts/ingest_data.py --source yahoo --symbols SPY --start-date 2015-01-01
```

**Solutions:**
1. Adjust backtest dates to bundle range
2. Re-ingest bundle with wider date range

### Check Bundle Date Range

```bash
python scripts/bundle_info.py yahoo_equities_daily
```

---

## Bundle Auto-Detection

### How It Works

If `--bundle` not specified, system infers from strategy:

1. Look at strategy path: `strategies/{asset_class}/{strategy_name}/`
2. Get default bundle for asset class from `config/settings.yaml`

### Default Bundles

| Asset Class | Default Bundle |
|-------------|----------------|
| equities | `yahoo_equities_daily` |
| crypto | `yahoo_crypto_daily` |
| forex | `yahoo_forex_daily` |

### Override Auto-Detection

```bash
python scripts/run_backtest.py --strategy my_strategy \
    --bundle my_custom_bundle
```

---

## Data Frequency Auto-Detection

### How It Works

If `--data-frequency` not specified, system queries bundle registry:

```json
// ~/.zipline/bundle_registry.json
{
  "yahoo_equities_1h": {
    "data_frequency": "minute"  // <-- Used for auto-detection
  }
}
```

### Override Auto-Detection

```bash
python scripts/run_backtest.py --strategy my_strategy \
    --bundle yahoo_equities_1h \
    --data-frequency minute
```

---

## Results Structure

### Standard Output

```
results/{strategy}/backtest_{YYYYMMDD}_{HHMMSS}/
├── returns.csv          # Daily/minute returns
├── positions.csv        # Position history
├── transactions.csv     # All executed trades
├── metrics.json         # Performance metrics
├── parameters_used.yaml # Config snapshot
└── equity_curve.png     # Visualization
```

### Latest Symlink

```
results/{strategy}/latest -> backtest_{YYYYMMDD}_{HHMMSS}/
```

Updated automatically after each run.

### Broken Symlinks

The system auto-repairs broken symlinks. Manual check:

```bash
python -c "from lib.utils import check_and_fix_symlinks; print(check_and_fix_symlinks('my_strategy'))"
```

---

## Common Commands

### Basic Backtest

```bash
python scripts/run_backtest.py --strategy spy_sma_cross
```

### With Date Range

```bash
python scripts/run_backtest.py --strategy spy_sma_cross \
    --start 2020-01-01 --end 2024-01-01
```

### With Custom Capital

```bash
python scripts/run_backtest.py --strategy spy_sma_cross --capital 50000
```

### With Specific Bundle

```bash
python scripts/run_backtest.py --strategy spy_sma_cross \
    --bundle yahoo_equities_1h --data-frequency minute
```

### Skip Warmup Validation

```bash
python scripts/run_backtest.py --strategy my_strategy --skip-warmup-check
```

---

## Error Messages and Solutions

### "Strategy file not found"

```
FileNotFoundError: Strategy file not found: strategies/equities/my_strategy/strategy.py
```

**Solutions:**
1. Check strategy exists: `ls strategies/*/my_strategy/`
2. Check for typos in strategy name
3. Specify asset class: `--asset-class crypto`

### "Strategy must have an 'initialize' function"

**Solution:** Add `initialize(context)` function to `strategy.py`:

```python
def initialize(context):
    context.asset = symbol('SPY')
```

### "Bundle not found"

```
FileNotFoundError: Bundle 'my_bundle' not found.
Run: python scripts/ingest_data.py --source yahoo --symbols <SYMBOLS>
```

**Solutions:**
1. Ingest the bundle first
2. Check bundle name: `python scripts/bundle_info.py --list`

### "Symbol not found in bundle"

```
ValueError: Strategy 'spy_sma_cross' requires symbol 'SPY' but bundle
'yahoo_crypto_daily' contains: [BTC-USD, ETH-USD].
```

**Solutions:**
1. Use correct bundle for strategy
2. Update `parameters.yaml` to use available symbol
3. Re-ingest bundle with correct symbol

### "Backtest execution failed"

**Common causes:**
1. Data gaps in bundle
2. Strategy logic errors
3. Missing imports in strategy.py

**Debug steps:**
1. Check bundle health: `python scripts/bundle_info.py <bundle> --verbose`
2. Run with smaller date range
3. Add logging to strategy.py

---

## Performance Tips

### Use Appropriate Timeframe

| Research Stage | Recommended |
|----------------|-------------|
| Initial testing | Daily data (fast) |
| Signal refinement | 1h data (balance) |
| Final validation | Minute data (accurate) |

### Limit Date Range During Development

```bash
# Fast iteration with 1 year
python scripts/run_backtest.py --strategy my_strategy \
    --start 2023-01-01 --end 2024-01-01

# Full backtest for validation
python scripts/run_backtest.py --strategy my_strategy \
    --start 2018-01-01 --end 2024-01-01
```

---

## See Also

- [Common Issues](common_issues.md)
- [Data Ingestion Troubleshooting](data_ingestion.md)
- [Backtest API](../api/backtest.md)
