# Auto-Repair Removal in Data Validation API

## Overview

The new `lib/data_validation.py` API **does not include auto-repair functionality**. This is an intentional behavioral change from the previous validation implementation. The new API focuses on **validation and reporting** rather than automatic data correction.

## What Changed

### Previous Behavior (Old API)
- Validation could automatically fix certain data issues
- Data might be modified during validation
- Silent corrections could mask underlying data quality problems

### Current Behavior (New API)
- **Validation only**: The API detects and reports issues but does not modify data
- **Explicit error reporting**: All validation failures are clearly reported with detailed messages
- **Manual intervention required**: Users must fix data issues manually based on validation results

## Why Auto-Repair Was Removed

1. **Data Integrity**: Automatic repairs can introduce subtle errors or mask underlying data quality issues
2. **Transparency**: Manual fixes ensure users understand what changes are being made to their data
3. **Control**: Users have full control over how data issues are resolved
4. **Predictability**: Validation behavior is consistent - it never modifies data unexpectedly

## Impact on Workflow

### Before (with auto-repair)
```python
# Old API might have silently fixed issues
result = old_validator.validate(df)
# Data might have been modified
```

### After (no auto-repair)
```python
from lib.data_validation import DataValidator, ValidationConfig

validator = DataValidator(config=ValidationConfig(timeframe='1d'))
result = validator.validate(df, asset_name='AAPL')

if not result.passed:
    # Validation failed - data was NOT modified
    print(result.summary())
    # User must manually fix issues before re-validating
```

## Handling Validation Failures

When validation fails, you have several options:

### 1. Review Validation Errors
```python
result = validator.validate(df, asset_name='AAPL')

if not result.passed:
    # Get detailed error information
    for check in result.error_checks:
        print(f"{check.name}: {check.message}")
        print(f"  Details: {check.details}")
```

### 2. Fix Data Manually
Common fixes for validation failures:

- **Missing columns**: Ensure CSV files have required OHLCV columns (case-insensitive)
- **Null values**: Fill or remove rows with null values
- **OHLC consistency**: Fix rows where High < Low or High < Open/Close
- **Negative values**: Remove or correct negative prices/volumes
- **Future dates**: Remove or correct dates in the future
- **Duplicate dates**: Remove duplicate timestamps or aggregate them
- **Unsorted index**: Sort DataFrame by index before validation
- **Data gaps**: Fill gaps using forward-fill or other methods (see `lib/utils.py::fill_data_gaps`)

### 3. Re-validate After Fixes
```python
# After fixing data issues
fixed_df = fix_data_issues(df)
result = validator.validate(fixed_df, asset_name='AAPL')

if result.passed:
    print("✓ Validation passed - data is ready for ingestion")
else:
    print("✗ Validation still failing - review remaining issues")
```

## Validation During Ingestion

The data ingestion pipeline (`lib/data_loader.py`) uses the new validation API:

- **Pre-ingestion validation**: Data is validated before being written to bundles
- **Symbols with validation failures are skipped**: Failed symbols are logged but do not block other symbols
- **No automatic fixes**: If validation fails, the symbol is skipped and must be fixed manually

Example from ingestion logs:
```
Error: Data validation failed for EURUSD: required_columns: Missing required columns: ['volume']
Error: Validation failed for EURUSD. Skipping symbol.
```

## Best Practices

1. **Validate before ingestion**: Use `scripts/validate_csv_data.py` to check data quality before ingesting
2. **Fix issues at the source**: Correct data files rather than relying on automatic fixes
3. **Review validation reports**: Use `ValidationResult.summary()` to understand all issues
4. **Use strict mode for critical data**: Enable `strict_mode=True` in `ValidationConfig` to treat warnings as errors

## Migration Guide

If you were relying on auto-repair functionality:

1. **Identify what was being auto-repaired**: Review your data to understand what issues existed
2. **Implement manual fixes**: Create scripts or processes to fix common issues
3. **Validate after fixes**: Always re-validate after making manual corrections
4. **Consider data preprocessing**: Add data cleaning steps before validation

## Example: Handling Common Issues

```python
import pandas as pd
from lib.data_validation import DataValidator, ValidationConfig

# Load data
df = pd.read_csv('data.csv', parse_dates=['Date'], index_col='Date')

# Validate
config = ValidationConfig(timeframe='1d')
validator = DataValidator(config=config)
result = validator.validate(df, asset_name='MY_SYMBOL')

if not result.passed:
    # Check for specific issues
    for check in result.error_checks:
        if check.name == 'required_columns':
            print(f"Missing columns: {check.details.get('missing_columns')}")
            # Fix: Ensure CSV has required columns
        
        elif check.name == 'no_nulls':
            null_details = check.details.get('null_counts', {})
            print(f"Null values found: {null_details}")
            # Fix: df = df.dropna() or df = df.fillna(method='ffill')
        
        elif check.name == 'ohlc_consistency':
            print(f"OHLC violations: {check.details.get('total_violations')}")
            # Fix: Remove or correct invalid rows
        
        elif check.name == 'no_negative_values':
            print("Negative values found")
            # Fix: df = df[df['close'] > 0] or correct values
    
    # After fixing, re-validate
    # result = validator.validate(df, asset_name='MY_SYMBOL')
```

## Related Documentation

- [Data Validation API](../api/data_validation.md) - Complete API reference
- [Data Ingestion Troubleshooting](data_ingestion.md) - Common ingestion issues
- [Validation Test Requirements](validation_test_requirements.md) - Testing validation

## Date

2026-01-07

