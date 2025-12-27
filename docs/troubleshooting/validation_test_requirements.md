# Validation Test Requirements Analysis

## Overview

This document analyzes what's needed to implement the validation tests outlined in `docs/testing/quick_validations.md`.

## Current Status

### ✅ Implemented Features

1. **Strategy Creation**
   - `lib/utils.py::create_strategy()` - Creates strategy from template
   - `lib/utils.py::create_strategy_from_template()` - Creates with asset symbol configured
   - Template exists at `strategies/_template/`

2. **Error Handling**
   - Missing strategy: `lib/backtest.py` raises `FileNotFoundError` with clear message
   - Missing bundle: `lib/backtest.py` raises `FileNotFoundError` with ingestion command suggestion
   - Invalid parameters: YAML loading will raise `yaml.YAMLError` or `KeyError`
   - Symlink management: `lib/utils.py::update_symlink()` handles creation/updates

3. **Data Integrity**
   - Date normalization: `lib/data_loader.py::_normalize_to_calendar_timezone()` ensures proper date handling
   - Bundle verification: `lib/backtest.py` checks bundle existence before running

4. **Results Management**
   - Timestamped directories: `lib/utils.py::timestamp_dir()`
   - Latest symlink: `lib/utils.py::update_symlink()` creates/updates symlinks
   - Results saving: `lib/backtest.py::save_results()` saves all outputs

### ⚠️ Missing/Incomplete Features

1. **Broken Symlink Detection & Auto-Fix**
   - **Status**: Not implemented
   - **Need**: Function to detect broken symlinks and auto-fix them
   - **Location**: Should be in `lib/utils.py`
   - **Test**: Test 2.5 requires this

2. **Parameter Validation**
   - **Status**: Partial (YAML loading validates syntax, but not values)
   - **Need**: Validate parameter ranges, required fields, types
   - **Location**: Could be in `lib/config.py` or `lib/utils.py`
   - **Test**: Test 2.3 requires this

3. **Data Integrity Validation**
   - **Status**: Partial (date normalization exists)
   - **Need**: Functions to verify:
     - Bundle dates match requested range
     - Returns calculated correctly
     - Positions match transactions
     - Metrics match manual calculations
   - **Location**: Could be in `lib/validate.py` or new `lib/data_integrity.py`
   - **Test**: Test 3 requires this

4. **Insufficient Data Handling**
   - **Status**: Not explicitly handled
   - **Need**: Graceful handling when data doesn't cover requested date range
   - **Location**: `lib/backtest.py` or `lib/data_loader.py`
   - **Test**: Test 2.4 requires this

5. **Multi-Strategy Comparison**
   - **Status**: Function exists (`lib/metrics.py::compare_strategies()`)
   - **Need**: Verify it works correctly and generates comparison reports
   - **Test**: Test 4 requires this

6. **Edge Case Handling**
   - **Status**: Not explicitly tested
   - **Need**: Ensure all edge cases are handled gracefully:
     - Very short backtest (1 month)
     - Very long backtest (10 years)
     - Single trade strategy
     - No trades strategy
     - Extreme parameters
     - Missing data periods
   - **Test**: Test 5 requires this

## Implementation Recommendations

### Priority 1: Critical for Basic Functionality

1. **Broken Symlink Detection** (`lib/utils.py`)
   ```python
   def check_and_fix_symlinks(strategy_name: str, asset_class: Optional[str] = None) -> List[str]:
       """
       Check for broken symlinks and auto-fix them.
       
       Returns:
           List of fixed symlink paths
       """
   ```

2. **Parameter Validation** (`lib/config.py`)
   ```python
   def validate_strategy_params(params: dict, strategy_name: str) -> Tuple[bool, List[str]]:
       """
       Validate strategy parameters.
       
       Returns:
           (is_valid, list_of_errors)
       """
   ```

3. **Insufficient Data Handling** (`lib/backtest.py`)
   - Check data availability before running backtest
   - Provide clear error message with date range available

### Priority 2: Important for Data Integrity

4. **Data Integrity Checks** (`lib/validate.py` or new module)
   ```python
   def verify_bundle_dates(bundle_name: str, start_date: str, end_date: str) -> bool:
       """Verify bundle covers requested date range."""
   
   def verify_returns_calculation(returns: pd.Series, transactions: pd.DataFrame) -> bool:
       """Verify returns match transactions."""
   
   def verify_positions_match_transactions(positions: pd.DataFrame, transactions: pd.DataFrame) -> bool:
       """Verify positions are consistent with transactions."""
   ```

### Priority 3: Nice to Have

5. **Edge Case Tests** - Create test strategies for each edge case
6. **Comparison Report Generation** - Enhance `lib/report.py` for multi-strategy comparison

## Test Implementation Strategy

### Test 1: End-to-End Workflow
- **Status**: Can be run manually now
- **Automation**: Create test script `tests/test_end_to_end.py`
- **Dependencies**: All Priority 1 features

### Test 2: Error Handling
- **Status**: Partially testable
- **Missing**: Broken symlink detection, parameter validation
- **Dependencies**: Priority 1 features

### Test 3: Data Integrity
- **Status**: Not testable yet
- **Dependencies**: Priority 2 features

### Test 4: Multi-Strategy Workflow
- **Status**: Mostly testable
- **Dependencies**: Test 1 must pass first

### Test 5: Edge Cases
- **Status**: Can be tested manually
- **Dependencies**: Test 1 must pass first

## Next Steps

1. ✅ Fix syntax error in `lib/plots.py` (DONE)
2. Implement broken symlink detection
3. Implement parameter validation
4. Implement data integrity checks
5. Create test scripts for automated validation
6. Run full validation suite

## Related Files

- `docs/testing/quick_validations.md` - Test requirements
- `lib/utils.py` - Utility functions (symlink management)
- `lib/config.py` - Configuration loading (parameter validation)
- `lib/backtest.py` - Backtest execution (error handling)
- `lib/validate.py` - Validation functions (data integrity)
- `lib/metrics.py` - Metrics calculation (comparison)

## Date Created

2025-01-23



