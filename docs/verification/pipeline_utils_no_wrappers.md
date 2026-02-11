# Verification: lib/pipeline_utils.py NO WRAPPERS Compliance

**Date:** 2026-01-28  
**Task:** Verify lib/pipeline_utils.py doesn't wrap Zipline Pipeline APIs  
**Status:** ✅ **COMPLIANT** - Module does not wrap Zipline Pipeline APIs

## Executive Summary

`lib/pipeline_utils.py` is **compliant** with AD-001 (NO WRAPPERS directive). The module provides legitimate orchestration and validation utilities without wrapping Zipline Pipeline APIs.

## Analysis

### What the Module Does

1. **`setup_pipeline()`** - Orchestration function that:
   - Validates pipeline configuration from parameters
   - Checks pipeline API availability
   - Validates asset class compatibility
   - **Calls `attach_pipeline()` directly** (line 106) - no wrapper
   - Sets context attributes for pipeline state

2. **`is_pipeline_available()`** - Simple utility function to check if Pipeline API is available

3. **`validate_pipeline_config()`** - Validation utility for pre-flight checks

### What the Module Does NOT Do

❌ **Does NOT wrap Pipeline construction APIs:**
- Does not wrap `Pipeline()` class
- Does not wrap `SimpleMovingAverage()` or other factors
- Does not wrap `EquityPricing` or other data sources
- Does not abstract Pipeline API usage

❌ **Does NOT wrap `attach_pipeline()`:**
- Calls `attach_pipeline()` directly on line 106
- No abstraction layer between user code and Zipline API

✅ **Provides legitimate utilities:**
- Configuration validation
- Availability checking
- Orchestration logic
- Error handling and warnings

## Code Evidence

### Direct Zipline API Usage

```python
# Line 28: Direct import
from zipline.api import attach_pipeline

# Line 106: Direct call (no wrapper)
attach_pipeline(pipeline, 'my_pipeline')
```

### No Pipeline API Wrappers

```python
# ✅ GOOD - User creates Pipeline directly
def make_pipeline():
    from zipline.pipeline import Pipeline
    from zipline.pipeline.factors import SimpleMovingAverage
    from zipline.pipeline.data import EquityPricing
    sma = SimpleMovingAverage(inputs=[EquityPricing.close], window_length=30)
    return Pipeline(columns={'sma_30': sma})
```

The module expects users to create Pipeline objects directly using Zipline APIs - no wrapping.

## Test Results

All tests pass (12/12):

```
tests/backtest/test_pipeline_utils.py::TestPipelineAvailability::test_is_pipeline_available PASSED
tests/backtest/test_pipeline_utils.py::TestSetupPipeline::test_pipeline_disabled_in_params PASSED
tests/backtest/test_pipeline_utils.py::TestSetupPipeline::test_pipeline_not_available_warning PASSED
tests/backtest/test_pipeline_utils.py::TestSetupPipeline::test_pipeline_warning_for_non_equities PASSED
tests/backtest/test_pipeline_utils.py::TestSetupPipeline::test_pipeline_setup_success PASSED
tests/backtest/test_pipeline_utils.py::TestSetupPipeline::test_pipeline_setup_with_none_pipeline PASSED
tests/backtest/test_pipeline_utils.py::TestSetupPipeline::test_pipeline_setup_with_exception PASSED
tests/backtest/test_pipeline_utils.py::TestSetupPipeline::test_pipeline_setup_without_make_pipeline_func PASSED
tests/backtest/test_pipeline_utils.py::TestValidatePipelineConfig::test_validate_pipeline_disabled PASSED
tests/backtest/test_pipeline_utils.py::TestValidatePipelineConfig::test_validate_pipeline_not_available PASSED
tests/backtest/test_pipeline_utils.py::TestValidatePipelineConfig::test_validate_pipeline_non_equities_warning PASSED
tests/backtest/test_pipeline_utils.py::TestValidatePipelineConfig::test_validate_pipeline_equities_no_warning PASSED
```

## Usage Pattern

The module follows the correct pattern:

```python
# User code (strategies/_template/strategy.py)
from lib.pipeline_utils import setup_pipeline

def make_pipeline():
    # User creates Pipeline directly using Zipline APIs
    from zipline.pipeline import Pipeline
    from zipline.pipeline.factors import SimpleMovingAverage
    from zipline.pipeline.data import EquityPricing
    sma = SimpleMovingAverage(inputs=[EquityPricing.close], window_length=30)
    return Pipeline(columns={'sma_30': sma})

def initialize(context):
    # setup_pipeline() orchestrates, but doesn't wrap
    setup_pipeline(context, params, make_pipeline_func=make_pipeline)
```

## Comparison with Removed Wrappers

### ❌ Removed in v1.12.0 (Wrappers):
- `lib/data/aggregation.py` - Wrapped `pandas.resample()`
- `lib/bundles/csv/` - Wrapped `csvdir_equities()`
- `lib/calendars/sessions/` - Wrapped `get_calendar()`

### ✅ Kept in v1.12.0 (Utilities):
- `lib/pipeline_utils.py` - Orchestration/validation, no wrapping

## Minor Enhancement Opportunity

**Note:** Line 106 hardcodes the pipeline name as `'my_pipeline'`. This could be made configurable in the future, but it's not a violation of AD-001 - it's a legitimate default value.

## Conclusion

✅ **VERIFIED:** `lib/pipeline_utils.py` does NOT wrap Zipline Pipeline APIs.

The module:
- Uses Zipline APIs directly (`attach_pipeline()`)
- Provides legitimate orchestration/validation utilities
- Does not abstract or wrap Pipeline construction APIs
- Follows AD-001 (NO WRAPPERS directive)

**Action Required:** None - module is compliant.
