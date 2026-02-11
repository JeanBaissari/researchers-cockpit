# 00 - Data Exploration Notebook

**File**: `notebooks/00_data_exploration.ipynb`
**Purpose**: Explore available data bundles and validate data quality before running backtests
**Architecture**: v1.12.0 NO WRAPPERS - Direct Zipline/pandas APIs

## Overview

The Data Exploration notebook is your first stop when working with new data sources. It helps you understand what data is available, validate its quality, and identify potential issues before running strategies.

**Key Principle**: Never run a backtest without first exploring the data.

## What This Notebook Does

### 1. Bundle Discovery
- Lists all available data bundles
- Groups bundles by asset class (equity, forex, crypto)
- Shows bundle metadata (symbols, date ranges)

### 2. Data Quality Validation
- Checks for missing data and gaps
- Validates OHLCV consistency
- Detects outliers and anomalies
- Identifies zero-volume periods

### 3. Visual Analysis
- Price and volume charts
- Return distribution analysis
- Q-Q plots for normality checking
- Multi-symbol volatility comparison

### 4. Calendar Inspection
- Trading calendar information
- Recent trading sessions
- Calendar properties (timezone, name)

## When to Use

### Essential Use Cases ✓

- **Before starting research**: Always explore data first
- **After ingesting new data**: Validate ingestion success
- **When debugging strategies**: Check if data issues exist
- **For asset class analysis**: Understand market characteristics

### Optional Use Cases

- Learning about available symbols
- Comparing data sources
- Educational purposes (understanding OHLCV data)

## Cell-by-Cell Guide

### Setup Cells

```python
# Cell 1: Add project root to path
import sys
from pathlib import Path
project_root = Path().absolute().parent
sys.path.insert(0, str(project_root))

# Cell 2: Import libraries
from lib.bundles import list_bundles, get_bundle_symbols, load_bundle
from lib.validation import validate_bundle
```

**What to customize**: Nothing - these cells are standard setup.

### List Bundles

```python
# Lists all bundles and groups by asset class
available_bundles = list_bundles()
```

**Output**: Categorized list of equity, forex, crypto, and other bundles.

**What to check**:
- Are your expected bundles present?
- Do bundle names follow convention (`{symbol}_{timeframe}`)?
- Are there old/unused bundles to clean up?

### Select Bundle

```python
# Choose bundle to explore
bundle_name = available_bundles[0]  # Modify this
```

**What to customize**: Change index or set explicit name:
```python
bundle_name = 'btcusd_daily'  # Explicit selection
```

### Bundle Metadata

```python
# Get symbols and date range
symbols = get_bundle_symbols(bundle_name)
bundle_data = load_bundle(bundle_name)
```

**Output**:
- Number of symbols in bundle
- Symbol list (truncated if > 20)
- First and last trading sessions
- Total days of data

**What to check**:
- Date range matches expectations
- All expected symbols present
- No unexpected symbols (contamination)

### Data Validation

```python
# Validate bundle quality
validation_result = validate_bundle(bundle_name)
```

**Output**: Validation report with errors and warnings.

**Common warnings**:
- Gap warnings for intraday data aggregated to daily
- Timezone mismatches (usually harmless)
- Low volume periods (normal for some assets)

**Action items**:
- ✓ Review any errors (may require re-ingestion)
- ✓ Check warnings for expected behavior
- ✗ Don't ignore repeated validation failures

### Load Sample Data

```python
# Load OHLCV for first symbol
asset = asset_finder.lookup_symbol(sample_symbol, as_of_date=None)
# Direct Zipline API - load raw arrays
opens = equity_daily_bar_reader.load_raw_arrays(
    ['open'], sessions[0], sessions[-1], [asset.sid]
)[0][:, 0]
```

**Architecture note**: Uses Zipline's direct `load_raw_arrays()` API (NO WRAPPERS).

**Output**:
- DataFrame with OHLCV data
- Basic statistics (describe())
- First/last 5 rows

**What to check**:
- No unexpected NaN values
- Reasonable price ranges
- Volume patterns make sense

### Price Visualization

```python
# Plot price and volume
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8))
ax1.plot(df.index, df['close'], label='Close')
ax2.bar(df.index, df['volume'], label='Volume')
```

**What to look for**:
- ✓ Smooth price action (no sudden jumps without explanation)
- ✓ Consistent volume (no long zero-volume periods)
- ✗ Large gaps in data
- ✗ Extreme outliers

### Return Distribution

```python
# Analyze return distribution
returns = df['close'].pct_change().dropna()
# Histogram + Q-Q plot
```

**Key metrics**:
- **Mean**: Average daily return (should be small)
- **Std Dev**: Daily volatility (varies by asset class)
- **Skewness**: Asymmetry (<0 = left tail, >0 = right tail)
- **Kurtosis**: Fat tails (>3 = more extreme events than normal)

**Interpretation**:
- Equity: Typically negative skew (crash risk)
- Crypto: Often positive skew (moon risk) and high kurtosis
- Forex: Usually close to normal distribution

### Data Quality Checks

```python
# Validate price consistency
invalid_highs = (df['high'] < df['low']).sum()
invalid_opens = ((df['open'] > df['high']) | (df['open'] < df['low'])).sum()
```

**Red flags**:
- High < Low violations → Data corruption
- Open/Close out of range → Bad data source
- Many outliers (z-score > 3) → Check for splits/dividends

**Green lights**:
- Zero violations → Clean data
- Few outliers → Normal market behavior
- No large gaps → Complete data

### Multi-Symbol Analysis

```python
# Compare up to 10 symbols
for symbol in symbols[:10]:
    # Calculate volatility, Sharpe, etc.
```

**Use case**: Understand relative characteristics across portfolio.

**What to compare**:
- Volatility (for position sizing)
- Sharpe ratio (for selection)
- Data completeness (for availability)

### Trading Calendar

```python
# Inspect calendar
calendar_name = get_calendar_for_asset_class(asset_class)
calendar = get_calendar(calendar_name)
```

**Why this matters**:
- FOREX/CRYPTO use custom 24/5 or 24/7 calendars
- Equities use exchange calendars (NYSE, NASDAQ)
- Mismatched calendars cause backtest errors

**What to verify**:
- Calendar name matches asset class
- Recent sessions look correct
- Timezone is appropriate

## Common Issues & Solutions

### Issue: "No bundles found"

**Symptom**: Empty bundle list
**Cause**: No data ingested yet
**Solution**:
```bash
python scripts/ingest_data.py --source yahoo --assets equities --timeframe daily
```

### Issue: "Bundle validation failed"

**Symptom**: Many validation errors
**Cause**: Corrupted data or ingestion failure
**Solution**: Re-ingest with `--force` flag:
```bash
python scripts/ingest_data.py --bundle btcusd_daily --force
```

### Issue: "Symbol not found"

**Symptom**: `lookup_symbol()` raises error
**Cause**: Symbol not in bundle or wrong format
**Solution**: Check `symbols` list for correct symbol name

### Issue: "Large date gaps"

**Symptom**: Gaps > 7 days reported
**Cause**: Expected for:
- FOREX weekends (normal)
- CRYPTO exchanges with downtime (check source)
- Equity holidays (normal)

**Action**: Verify gaps align with expected non-trading periods.

### Issue: "Zero volume days"

**Symptom**: Many days with volume = 0
**Cause**:
- CSV data without volume column (filled with zeros)
- Illiquid assets
- Data source limitation

**Solution**: If CSV, check source data has volume. If API, may be normal.

## Best Practices

### Do's ✓

1. **Run this first**: Before any strategy work
2. **Spot-check multiple symbols**: Don't assume all are clean
3. **Compare timeframes**: Validate daily vs intraday consistency
4. **Document findings**: Note any anomalies in strategy docs
5. **Re-validate after updates**: When data source changes

### Don'ts ✗

1. **Don't skip validation**: Saves hours of debugging later
2. **Don't ignore warnings**: They often indicate real issues
3. **Don't assume API data is perfect**: Always verify
4. **Don't run on huge bundles**: Limit to 10 symbols for exploration
5. **Don't trust old data**: Re-ingest if > 6 months old

## Integration with Workflow

### Before This Notebook

1. Ingest data using `scripts/ingest_data.py`
2. Verify ingestion completed successfully

### After This Notebook

1. **If validation passed** → Proceed to `01_backtest.ipynb`
2. **If issues found** → Fix data and re-run this notebook
3. **Document findings** → Note in strategy `hypothesis.md`

## Output Files

This notebook does not create persistent output files. All analysis is displayed inline.

**Why**: Exploration is interactive and context-dependent.

**If you need to save**:
- Take screenshots of key plots
- Copy metrics to strategy documentation
- Export DataFrames manually if needed

## Customization Examples

### Analyze Specific Date Range

```python
# After loading df
df_subset = df.loc['2023-01-01':'2023-12-31']
print(df_subset.describe())
```

### Compare Returns Across Assets

```python
returns_dict = {}
for symbol in symbols[:5]:
    # Load data for each symbol
    returns_dict[symbol] = calculate_returns(symbol)

# Plot correlation matrix
pd.DataFrame(returns_dict).corr()
```

### Custom Validation Checks

```python
# Add your own validation logic
def check_splits(df):
    # Detect sudden price changes that might be splits
    returns = df['close'].pct_change()
    split_candidates = returns[returns.abs() > 0.3]
    return split_candidates

suspicious_days = check_splits(df)
print(suspicious_days)
```

## Advanced Usage

### Automated Validation Script

Extract validation logic to run on all bundles:

```python
for bundle in available_bundles:
    result = validate_bundle(bundle)
    if not result.is_valid:
        print(f"⚠ {bundle}: {len(result.errors)} errors")
```

### Export Validation Report

```python
# Save validation results
report = []
for bundle in available_bundles:
    result = validate_bundle(bundle)
    report.append({
        'bundle': bundle,
        'valid': result.is_valid,
        'errors': len(result.errors),
        'warnings': len(result.warnings)
    })

pd.DataFrame(report).to_csv('validation_report.csv', index=False)
```

## Related Documentation

- **[Bundle Ingestion Guide](../code_patterns/csv_ingestion_best_practices.md)** - How to ingest data
- **[Data Validation API](../api/validation.md)** - Validation module reference
- **[Troubleshooting: Data Issues](../troubleshooting/data_quality_issues.md)** - Common data problems
- **[01_backtest.ipynb](01_backtest.md)** - Next step after validation

## Version Notes

### v1.12.0 Changes (NO WRAPPERS)

- **Removed**: CSV bundle wrappers - now uses direct `csvdir_equities()`
- **Removed**: SessionManager - now uses direct `get_calendar()`
- **Added**: Direct Zipline API examples (`load_raw_arrays`)
- **Updated**: All imports to use canonical `lib.*` paths

### Migration from v1.11

If using old notebooks:
```python
# OLD (v1.11)
from lib.bundles.csv import load_csv_bundle
from lib.calendars.sessions import SessionManager

# NEW (v1.12)
from lib.bundles import load_bundle  # Universal loader
from zipline.utils.calendar_utils import get_calendar  # Direct
```

---

**Last Updated**: 2026-02-09
**Version**: v1.12.0
**Notebook File**: `notebooks/00_data_exploration.ipynb`
