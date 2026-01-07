# Data Validation Troubleshooting

Guide to understanding and resolving data validation errors in The Researcher's Cockpit.

---

## Overview

The data validation API (`lib/data_validation.py`) performs comprehensive checks on OHLCV data before ingestion. This guide helps you understand common validation errors and how to fix them.

**Key Points:**
- **No auto-repair**: The validation API detects issues but does not automatically fix them
- **Manual intervention required**: You must fix data issues manually based on validation results
- **Detailed error messages**: Each validation check provides specific information about what failed

---

## Auto-Repair Removal

### What Changed

The new validation API **does not include auto-repair functionality**. This is an intentional behavioral change from previous implementations.

**Previous behavior (old API):**
- Validation could automatically fix certain data issues
- Data might be modified during validation
- Silent corrections could mask underlying data quality problems

**Current behavior (new API):**
- **Validation only**: The API detects and reports issues but does not modify data
- **Explicit error reporting**: All validation failures are clearly reported with detailed messages
- **Manual intervention required**: Users must fix data issues manually based on validation results

### Why Auto-Repair Was Removed

1. **Data Integrity**: Automatic repairs can introduce subtle errors or mask underlying data quality issues
2. **Transparency**: Manual fixes ensure users understand what changes are being made to their data
3. **Control**: Users have full control over how data issues are resolved
4. **Predictability**: Validation behavior is consistent - it never modifies data unexpectedly

### Impact on Workflow

**Before (with auto-repair):**
```python
# Old API might have silently fixed issues
result = old_validator.validate(df)
# Data might have been modified
```

**After (no auto-repair):**
```python
from lib.data_validation import DataValidator, ValidationConfig

validator = DataValidator(config=ValidationConfig(timeframe='1d'))
result = validator.validate(df, asset_name='AAPL')

if not result.passed:
    # Validation failed - data was NOT modified
    print(result.summary())
    # User must manually fix issues before re-validating
```

See [Auto-Repair Removal](auto_repair_removal.md) for more details.

---

## Common Validation Errors

### 1. Missing Required Columns

**Error Message:**
```
required_columns: Missing required columns: ['volume']
```

**Cause:**
CSV file is missing one or more required OHLCV columns (open, high, low, close, volume).

**Solution:**
1. Check your CSV file has all required columns
2. Column names are case-insensitive (Open, OPEN, open all work)
3. Ensure column names match expected formats:
   - `open`, `high`, `low`, `close`, `volume` (lowercase)
   - `Open`, `High`, `Low`, `Close`, `Volume` (titlecase)
   - `OPEN`, `HIGH`, `LOW`, `CLOSE`, `VOLUME` (uppercase)
   - `O`, `H`, `L`, `C`, `V` (abbreviated, uppercase only)

**Example Fix:**
```python
import pandas as pd

# Load CSV
df = pd.read_csv('data.csv')

# Rename columns to standard format
df = df.rename(columns={
    'Open': 'open',
    'High': 'high',
    'Low': 'low',
    'Close': 'close',
    'Volume': 'volume'
})

# Re-validate
from lib.data_validation import DataValidator
validator = DataValidator()
result = validator.validate(df, asset_name='AAPL')
```

---

### 2. Null Values

**Error Message:**
```
no_nulls: Found 15 null values (2.50%) in AAPL
```

**Cause:**
DataFrame contains missing values (NaN) in OHLCV columns.

**Solution:**
Choose an appropriate strategy based on your data:

**Option 1: Remove rows with nulls**
```python
df = df.dropna()
```

**Option 2: Forward fill**
```python
df = df.fillna(method='ffill')
```

**Option 3: Backward fill**
```python
df = df.fillna(method='bfill')
```

**Option 4: Interpolate**
```python
df = df.interpolate(method='time')
```

**Option 5: Fill with specific value**
```python
# Fill volume with 0, prices with previous close
df['volume'] = df['volume'].fillna(0)
df[['open', 'high', 'low', 'close']] = df[['open', 'high', 'low', 'close']].fillna(method='ffill')
```

**Best Practice:**
- For price data: Use forward fill or interpolation
- For volume data: Consider filling with 0 or removing rows
- Always re-validate after filling

---

### 3. OHLC Consistency Violations

**Error Message:**
```
ohlc_consistency: Found 3 OHLC consistency violations (0.15%) in AAPL
```

**Cause:**
Price relationships are invalid:
- High < Low
- High < Open or High < Close
- Low > Open or Low > Close

**Solution:**
Identify and fix invalid rows:

```python
from lib.data_validation import DataValidator

validator = DataValidator()
result = validator.validate(df, asset_name='AAPL')

# Find rows with OHLC violations
for check in result.error_checks:
    if check.name == 'ohlc_consistency':
        # Check details for specific violations
        violations = check.details.get('total_violations', 0)
        print(f"Found {violations} violations")

# Fix common issues
# 1. High < Low: Swap high and low
mask = df['high'] < df['low']
df.loc[mask, ['high', 'low']] = df.loc[mask, ['low', 'high']].values

# 2. High < Open/Close: Set high to max of open/close
df['high'] = df[['open', 'high', 'close']].max(axis=1)

# 3. Low > Open/Close: Set low to min of open/close
df['low'] = df[['open', 'low', 'close']].min(axis=1)

# Re-validate
result = validator.validate(df, asset_name='AAPL')
```

**Best Practice:**
- Review source data to understand why violations occurred
- Consider removing rows with severe violations rather than correcting them
- Document any corrections made

---

### 4. Negative Values

**Error Message:**
```
no_negative_values: Found 2 negative values in AAPL
```

**Cause:**
DataFrame contains negative prices or volumes.

**Solution:**
```python
# Remove rows with negative prices
df = df[(df['open'] > 0) & (df['high'] > 0) & 
        (df['low'] > 0) & (df['close'] > 0)]

# Remove rows with negative volume (or set to 0)
df = df[df['volume'] >= 0]
# OR
df.loc[df['volume'] < 0, 'volume'] = 0
```

**Best Practice:**
- Negative prices are almost always data errors
- Negative volumes might indicate short sales - verify with data source
- Consider investigating why negative values exist in source data

---

### 5. Future Dates

**Error Message:**
```
no_future_dates: Found 1 future dates in AAPL
```

**Cause:**
DataFrame contains dates in the future (beyond current date).

**Solution:**
```python
from datetime import datetime

# Remove future dates
today = datetime.now().date()
df = df[df.index.date <= today]

# Or filter to specific date range
end_date = datetime(2024, 1, 1).date()
df = df[df.index.date <= end_date]
```

**Best Practice:**
- Future dates are usually data entry errors
- For backtesting, ensure data doesn't extend beyond your backtest end date

---

### 6. Duplicate Dates

**Error Message:**
```
no_duplicate_dates: Found 5 duplicate dates (0.25%) in AAPL
```

**Cause:**
DataFrame index contains duplicate timestamps.

**Solution:**
```python
# Option 1: Keep first occurrence
df = df[~df.index.duplicated(keep='first')]

# Option 2: Keep last occurrence
df = df[~df.index.duplicated(keep='last')]

# Option 3: Aggregate duplicates (average OHLCV)
df = df.groupby(df.index).agg({
    'open': 'first',
    'high': 'max',
    'low': 'min',
    'close': 'last',
    'volume': 'sum'
})

# Option 4: Remove all duplicates
df = df[~df.index.duplicated(keep=False)]
```

**Best Practice:**
- Understand why duplicates exist (data source issue vs. intentional)
- For intraday data, duplicates might represent multiple trades at same timestamp
- Consider aggregating rather than removing

---

### 7. Unsorted Index

**Error Message:**
```
sorted_index: Index is not sorted for AAPL
```

**Cause:**
DataFrame index is not sorted in ascending order.

**Solution:**
```python
# Sort index ascending
df = df.sort_index()

# Verify sorting
assert df.index.is_monotonic_increasing, "Index should be sorted"
```

**Best Practice:**
- Always sort data before validation
- Sorting is required for time-series analysis

---

### 8. Excessive Zero Volume

**Error Message:**
```
zero_volume: Found 50 (10.0%) zero volume bars in AAPL
```

**Cause:**
Too many bars have zero volume (default threshold: 10%).

**Solution:**
```python
# Option 1: Remove zero volume bars
df = df[df['volume'] > 0]

# Option 2: Use lenient validation config
from lib.data_validation import DataValidator, ValidationConfig

config = ValidationConfig(
    timeframe='1d',
    check_zero_volume=True,
    zero_volume_threshold_pct=20.0  # Allow up to 20% zero volume
)
validator = DataValidator(config=config)
result = validator.validate(df, asset_name='AAPL')

# Option 3: Fill zero volume with small value (not recommended)
df.loc[df['volume'] == 0, 'volume'] = 0.01
```

**Best Practice:**
- Zero volume bars might indicate market closures or data issues
- For daily data, zero volume is unusual
- For intraday data, zero volume might be normal during low-liquidity periods

---

### 9. Large Price Jumps

**Error Message:**
```
price_jumps: Found 2 price jumps >50% in AAPL
```

**Cause:**
Sudden large price movements detected (default threshold: 50% change).

**Solution:**
```python
# Option 1: Review and remove suspicious jumps
pct_changes = df['close'].pct_change().abs()
large_jumps = pct_changes[pct_changes > 0.5]
print(f"Large jumps at: {large_jumps.index.tolist()}")

# Remove rows with large jumps
df = df[df['close'].pct_change().abs() <= 0.5]

# Option 2: Adjust threshold in config
from lib.data_validation import DataValidator, ValidationConfig

config = ValidationConfig(
    timeframe='1d',
    check_price_jumps=True,
    price_jump_threshold_pct=100.0  # Allow up to 100% jumps
)
validator = DataValidator(config=config)

# Option 3: Disable price jump checking
config = ValidationConfig(
    timeframe='1d',
    check_price_jumps=False
)
```

**Best Practice:**
- Large price jumps might be legitimate (splits, corporate actions, flash crashes)
- Review jumps manually before removing
- Consider adjusting threshold based on asset class (crypto vs. equities)

---

### 10. Stale Data

**Error Message:**
```
stale_data: Data for AAPL is 30 days old (last: 2023-12-01)
```

**Cause:**
Data is older than threshold (default: 7 days).

**Solution:**
```python
# Option 1: Update data source
# Re-download data from your source

# Option 2: Adjust stale threshold
from lib.data_validation import DataValidator, ValidationConfig

config = ValidationConfig(
    timeframe='1d',
    check_stale_data=True,
    stale_threshold_days=30  # Allow data up to 30 days old
)
validator = DataValidator(config=config)

# Option 3: Disable stale data check
config = ValidationConfig(
    timeframe='1d',
    check_stale_data=False
)
```

**Best Practice:**
- Stale data check is a warning, not an error (unless strict_mode=True)
- For historical backtesting, stale data is expected
- For live trading, ensure data is current

---

### 11. Insufficient Data

**Error Message:**
```
data_sufficiency: Insufficient data for AAPL: 10 rows (minimum: 20)
```

**Cause:**
DataFrame has fewer rows than minimum required (daily: 20, intraday: 100).

**Solution:**
```python
# Option 1: Collect more data
# Download additional historical data

# Option 2: Adjust minimum rows threshold
from lib.data_validation import DataValidator, ValidationConfig

config = ValidationConfig(
    timeframe='1d',
    min_rows_daily=10  # Lower threshold
)
validator = DataValidator(config=config)

# Option 3: Use minimal config (disables data sufficiency check)
config = ValidationConfig.minimal(timeframe='1d')
```

**Best Practice:**
- Minimum rows ensure meaningful statistical analysis
- Consider data requirements for your specific use case
- For backtesting, more data is generally better

---

### 12. Missing Calendar Dates (Gaps)

**Error Message:**
```
date_continuity: Found 15 missing calendar dates (3.2%) in AAPL
```

**Cause:**
Data is missing expected trading days according to trading calendar.

**Solution:**
```python
# Option 1: Fill gaps using forward fill
from lib.utils import fill_data_gaps

df = fill_data_gaps(df, calendar=calendar)

# Option 2: Adjust gap tolerance
from lib.data_validation import DataValidator, ValidationConfig

config = ValidationConfig(
    timeframe='1d',
    check_gaps=True,
    gap_tolerance_days=20  # Allow up to 20 missing days
)
validator = DataValidator(config=config)

# Option 3: Disable gap checking
config = ValidationConfig(
    timeframe='1d',
    check_gaps=False
)
```

**Best Practice:**
- Gaps might be legitimate (market closures, delistings)
- Review gap dates to understand why data is missing
- For backtesting, consider whether gaps affect strategy performance

---

## Handling Validation Failures

### Step-by-Step Process

1. **Run Validation**
   ```python
   from lib.data_validation import DataValidator
   
   validator = DataValidator()
   result = validator.validate(df, asset_name='AAPL')
   ```

2. **Review Results**
   ```python
   if not result.passed:
       print(result.summary())
       
       # Get detailed error information
       for check in result.error_checks:
           print(f"Error: {check.name}")
           print(f"  Message: {check.message}")
           print(f"  Details: {check.details}")
   ```

3. **Fix Issues**
   - Use solutions provided above for each error type
   - Fix issues at the source (CSV files) when possible
   - Document any corrections made

4. **Re-validate**
   ```python
   # After fixing issues
   fixed_df = fix_data_issues(df)
   result = validator.validate(fixed_df, asset_name='AAPL')
   
   if result.passed:
       print("✓ Validation passed - data is ready for ingestion")
   else:
       print("✗ Validation still failing - review remaining issues")
   ```

### Validation During Ingestion

The data ingestion pipeline automatically validates data:

- **Pre-ingestion validation**: Data is validated before being written to bundles
- **Symbols with validation failures are skipped**: Failed symbols are logged but do not block other symbols
- **No automatic fixes**: If validation fails, the symbol is skipped and must be fixed manually

**Example ingestion log:**
```
Validating data for AAPL...
  ✓ Data validation passed for AAPL
Validating data for INVALID...
  Error: Data validation failed for INVALID: required_columns: Missing required columns: ['volume']
  Error: Validation failed for INVALID. Skipping symbol.
```

---

## Best Practices

1. **Validate before ingestion**: Use `scripts/validate_csv_data.py` to check data quality before ingesting
2. **Fix issues at the source**: Correct data files rather than relying on workarounds
3. **Review validation reports**: Use `ValidationResult.summary()` to understand all issues
4. **Use strict mode for critical data**: Enable `strict_mode=True` in `ValidationConfig` to treat warnings as errors
5. **Document corrections**: Keep track of any manual fixes made to data
6. **Re-validate after fixes**: Always re-validate after making corrections

---

## Validation Configurations

### Default Configuration
```python
from lib.data_validation import ValidationConfig

config = ValidationConfig.default(timeframe='1d')
```

### Strict Mode
```python
config = ValidationConfig.strict(timeframe='1d')
# Warnings become errors
```

### Lenient Mode
```python
config = ValidationConfig.lenient(timeframe='1h')
# Relaxed thresholds for intraday data
```

### Minimal Configuration
```python
config = ValidationConfig.minimal(timeframe='1d')
# Only essential checks
```

---

## Getting Help

If you encounter validation errors you cannot resolve:

1. **Check error details**: Use `check.details` to get specific information about failures
2. **Review data source**: Verify data quality at the source
3. **Use validation summary**: `result.summary()` provides a human-readable overview
4. **Check documentation**: See [Data Validation API](../api/data_validation.md) for complete API reference

---

## Related Documentation

- [Data Validation API](../api/data_validation.md) - Complete API reference
- [Auto-Repair Removal](auto_repair_removal.md) - Understanding auto-repair removal
- [Data Ingestion Troubleshooting](data_ingestion.md) - Data ingestion issues
- [Validation Test Requirements](validation_test_requirements.md) - Testing validation

---

## Date

2026-01-07

