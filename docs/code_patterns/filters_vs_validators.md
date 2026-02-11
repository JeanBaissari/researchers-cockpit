# Zipline Filters vs lib/validation/ Validators

> Comprehensive guide to when to use Zipline's Pipeline filters vs lib/validation/ validators

**Version:** v1.12.0  
**Last Updated:** 2026-01-28

---

## Quick Decision Tree

```
┌─────────────────────────────────────────────────────────┐
│ When do you need to filter/validate?                    │
└─────────────────────────────────────────────────────────┘
                        │
        ┌───────────────┴───────────────┐
        │                                │
   During Backtest              Before/After Backtest
   (Runtime)                    (Pre/Post Processing)
        │                                │
        ▼                                ▼
┌───────────────┐              ┌──────────────────┐
│ Zipline       │              │ lib/validation/   │
│ Pipeline      │              │ Validators        │
│ Filters       │              │                   │
└───────────────┘              └──────────────────┘
```

---

## Overview

This document clarifies the distinction between:

1. **Zipline Pipeline Filters** - Runtime screening during backtest execution
2. **lib/validation/ Validators** - Pre/post-processing data quality validation

They serve **complementary purposes** and are used at **different stages** of the trading pipeline.

---

## Zipline Pipeline Filters

### What They Are

Zipline Pipeline filters are **boolean expressions** that screen assets during backtest execution. They operate on Pipeline factors and are used to:

- Filter assets in real-time during backtest
- Reduce Pipeline output size
- Create universe definitions
- Mask factor calculations

### When to Use

✅ **Use Zipline Filters When:**

- **During backtest execution** - You need to screen assets in real-time
- **In Pipeline API** - You're using `make_pipeline()` function
- **Runtime filtering** - You want to exclude assets based on current data
- **Universe definition** - You need to define which assets to consider
- **Performance optimization** - You want to reduce Pipeline output size

### Common Zipline Filters

```python
from zipline.pipeline import Pipeline
from zipline.pipeline.factors import SimpleMovingAverage, Returns
from zipline.pipeline.data import EquityPricing

def make_pipeline():
    sma = SimpleMovingAverage(inputs=[EquityPricing.close], window_length=30)
    returns = Returns(window_length=20)
    
    # Common filter operations:
    
    # 1. Null/NaN checks
    has_data = sma.isfinite()      # Exclude NaN/Inf values
    valid = sma.notnan()           # Exclude NaN values
    present = sma.notnull()         # Exclude null values
    
    # 2. Comparison filters
    positive_returns = returns > 0
    high_price = EquityPricing.close.latest > 100
    
    # 3. Ranking filters
    top_100 = returns.top(100)      # Top 100 assets
    bottom_50 = returns.bottom(50)  # Bottom 50 assets
    
    # 4. Combining filters
    universe = (
        has_data &
        positive_returns &
        (EquityPricing.close.latest > 5)
    )
    
    return Pipeline(
        columns={'sma': sma, 'returns': returns},
        screen=universe  # Only output assets passing filter
    )
```

### Examples from Codebase

**Strategy Template (`strategies/_template/strategy.py`):**

```python
def make_pipeline():
    sma = SimpleMovingAverage(inputs=[_PRICING_CLASS.close], window_length=30)
    return Pipeline(
        columns={'sma': sma},
        screen=sma.isfinite()  # Exclude assets with invalid SMA
    )
```

**Key Characteristics:**

- ✅ **Runtime execution** - Evaluated during backtest
- ✅ **Pipeline context** - Used in `make_pipeline()` function
- ✅ **Boolean output** - Returns True/False for each asset
- ✅ **Performance impact** - Reduces Pipeline output size
- ✅ **Real-time data** - Operates on current bar data

### Limitations

❌ **Don't Use Zipline Filters For:**

- Pre-ingestion data validation
- Post-ingestion bundle validation
- Post-backtest results validation
- Data quality checks (outliers, gaps, anomalies)
- Statistical validation
- Asset-specific business rules

---

## lib/validation/ Validators

### What They Are

`lib/validation/` validators are **data quality assurance tools** that validate data before it enters Zipline bundles and after backtest execution. They check:

- Data quality (outliers, gaps, anomalies)
- Schema validation (columns, types)
- Business rules (asset-specific validation)
- Statistical properties
- Bundle integrity
- Results consistency

### When to Use

✅ **Use lib/validation/ Validators When:**

- **Before ingestion** - Validating source data (CSV, API, etc.)
- **After ingestion** - Verifying bundle integrity
- **After backtest** - Validating results consistency
- **Data quality checks** - Checking for outliers, gaps, anomalies
- **Business rules** - Applying asset-specific validation rules
- **Pre-flight checks** - Ensuring data is ready for backtest

### Common Validators

```python
from lib.validation import (
    validate_before_ingest,
    validate_bundle,
    validate_backtest_results,
    DataValidator,
    ValidationConfig
)

# 1. Pre-ingestion validation (before bundle creation)
result = validate_before_ingest(
    df=raw_data,
    asset_name='AAPL',
    timeframe='1d',
    asset_type='equity'
)
if not result:
    print(result.summary())  # Shows all quality issues
    # Fix issues before ingesting

# 2. Post-ingestion validation (after bundle creation)
result = validate_bundle('my_bundle')
if not result:
    print("Bundle integrity issues:", result.summary())

# 3. Post-backtest validation (after backtest execution)
result = validate_backtest_results(perf_df, transactions_df, positions_df)
if not result:
    print("Results validation issues:", result.summary())

# 4. Custom validation with configuration
config = ValidationConfig.strict(timeframe='1d')
validator = DataValidator(config=config)
result = validator.validate(df, asset_name='AAPL')
```

### Validation Layers

**Layer 1: Pre-Ingestion** (`lib/validation/validators/ingest.py`)
- Schema validation
- Data quality checks
- Outlier detection
- Gap detection
- Asset-specific rules

**Layer 2: Post-Ingestion** (`lib/validation/validators/bundle.py`)
- Bundle integrity
- Date coverage
- Symbol availability

**Layer 3: Post-Backtest** (`lib/validation/validators/results.py`)
- Metrics consistency
- Position/transaction matching
- Returns verification

### Examples from Codebase

**Pre-Ingestion Validation:**

```python
# scripts/ingest_data.py
from lib.validation import validate_before_ingest

# Validate before ingesting
result = validate_before_ingest(
    df=raw_data,
    asset_name=symbol,
    timeframe=timeframe,
    asset_type=asset_type
)

if not result:
    logger.error(f"Validation failed: {result.summary()}")
    return  # Don't ingest invalid data
```

**Key Characteristics:**

- ✅ **Pre/post processing** - Runs before/after backtest
- ✅ **Data quality focus** - Checks quality, not format
- ✅ **Actionable results** - Provides fix suggestions
- ✅ **Asset-specific** - Supports equity, forex, crypto rules
- ✅ **Comprehensive** - Multiple validation layers

### Limitations

❌ **Don't Use lib/validation/ Validators For:**

- Runtime asset screening during backtest
- Pipeline universe definition
- Real-time data filtering
- Performance optimization in Pipeline
- Boolean asset selection

---

## Comparison Table

| Aspect | Zipline Pipeline Filters | lib/validation/ Validators |
|--------|-------------------------|---------------------------|
| **Timing** | During backtest execution | Before/after backtest |
| **Context** | Pipeline API (`make_pipeline()`) | Pre/post-processing scripts |
| **Purpose** | Runtime asset screening | Data quality assurance |
| **Output** | Boolean (True/False per asset) | ValidationResult with issues |
| **Scope** | Current bar data | Historical data quality |
| **Performance** | Reduces Pipeline output | Validates data integrity |
| **Examples** | `.isfinite()`, `.notnan()`, `>`, `<` | `validate_before_ingest()`, `validate_bundle()` |
| **Use Case** | "Which assets should I consider?" | "Is my data valid?" |

---

## When to Use Each

### Use Zipline Filters For:

1. **Universe Definition**
   ```python
   def make_pipeline():
       volume = AverageDollarVolume(window_length=20)
       liquid = volume.top(500)  # Top 500 liquid stocks
       return Pipeline(screen=liquid)
   ```

2. **Runtime Screening**
   ```python
   def make_pipeline():
       sma = SimpleMovingAverage(inputs=[EquityPricing.close], window_length=30)
       valid = sma.isfinite()  # Exclude invalid values
       return Pipeline(columns={'sma': sma}, screen=valid)
   ```

3. **Conditional Logic**
   ```python
   def make_pipeline():
       returns = Returns(window_length=20)
       positive = returns > 0
       return Pipeline(columns={'returns': returns}, screen=positive)
   ```

### Use lib/validation/ Validators For:

1. **Pre-Ingestion Validation**
   ```python
   from lib.validation import validate_before_ingest
   
   result = validate_before_ingest(df, asset_name='AAPL', timeframe='1d')
   if not result:
       print("Data quality issues:", result.summary())
       # Fix issues before ingesting
   ```

2. **Bundle Integrity**
   ```python
   from lib.validation import validate_bundle
   
   result = validate_bundle('my_bundle')
   if not result:
       print("Bundle issues:", result.summary())
   ```

3. **Results Verification**
   ```python
   from lib.validation import validate_backtest_results
   
   result = validate_backtest_results(perf_df, transactions_df, positions_df)
   if not result:
       print("Results issues:", result.summary())
   ```

---

## Common Patterns

### Pattern 1: Pre-Ingestion + Runtime Filtering

```python
# Step 1: Validate before ingestion (lib/validation/)
from lib.validation import validate_before_ingest

result = validate_before_ingest(df, asset_name='AAPL', timeframe='1d')
if not result:
    raise ValueError("Data quality issues detected")

# Step 2: Ingest into bundle
ingest('my_bundle')

# Step 3: Use filters during backtest (Zipline Pipeline)
def make_pipeline():
    sma = SimpleMovingAverage(inputs=[EquityPricing.close], window_length=30)
    return Pipeline(
        columns={'sma': sma},
        screen=sma.isfinite()  # Runtime filtering
    )
```

### Pattern 2: Bundle Validation + Pipeline Screening

```python
# Step 1: Validate bundle after ingestion (lib/validation/)
from lib.validation import validate_bundle

result = validate_bundle('my_bundle')
if not result:
    raise ValueError("Bundle integrity issues detected")

# Step 2: Use filters in Pipeline (Zipline)
def make_pipeline():
    volume = AverageDollarVolume(window_length=20)
    liquid = volume.top(500)  # Runtime screening
    return Pipeline(screen=liquid)
```

### Pattern 3: Results Validation

```python
# Step 1: Run backtest with Pipeline filters
perf = run_algorithm(...)

# Step 2: Validate results (lib/validation/)
from lib.validation import validate_backtest_results

result = validate_backtest_results(perf_df, transactions_df, positions_df)
if not result:
    print("Results validation issues:", result.summary())
```

---

## Best Practices

### 1. Always Validate Before Ingestion

```python
# ✅ GOOD: Validate before ingesting
from lib.validation import validate_before_ingest

result = validate_before_ingest(df, asset_name='AAPL', timeframe='1d')
if not result:
    print(result.summary())
    return  # Don't ingest invalid data

# Now safe to ingest
ingest('my_bundle')
```

### 2. Use Filters for Runtime Screening

```python
# ✅ GOOD: Use filters in Pipeline for runtime screening
def make_pipeline():
    sma = SimpleMovingAverage(inputs=[EquityPricing.close], window_length=30)
    valid = sma.isfinite()  # Runtime filter
    return Pipeline(columns={'sma': sma}, screen=valid)
```

### 3. Don't Mix Purposes

```python
# ❌ BAD: Using Pipeline filters for data quality validation
def make_pipeline():
    # This is runtime screening, not data quality validation
    sma = SimpleMovingAverage(inputs=[EquityPricing.close], window_length=30)
    return Pipeline(columns={'sma': sma}, screen=sma.isfinite())

# ✅ GOOD: Use lib/validation/ for data quality
from lib.validation import validate_before_ingest
result = validate_before_ingest(df, asset_name='AAPL', timeframe='1d')
```

### 4. Validate at Each Stage

```python
# ✅ GOOD: Validate at each stage
# 1. Pre-ingestion
validate_before_ingest(df, ...)

# 2. Post-ingestion
validate_bundle('my_bundle')

# 3. During backtest (Pipeline filters)
def make_pipeline():
    return Pipeline(screen=some_filter)

# 4. Post-backtest
validate_backtest_results(perf_df, ...)
```

---

## Summary

**Zipline Pipeline Filters:**
- **When:** During backtest execution
- **Where:** In `make_pipeline()` function
- **Purpose:** Runtime asset screening
- **Examples:** `.isfinite()`, `.notnan()`, `>`, `<`, `.top()`

**lib/validation/ Validators:**
- **When:** Before/after backtest
- **Where:** Pre/post-processing scripts
- **Purpose:** Data quality assurance
- **Examples:** `validate_before_ingest()`, `validate_bundle()`, `validate_backtest_results()`

**They complement each other:**
- Validators ensure data quality **before** it enters Zipline
- Filters screen assets **during** backtest execution
- Validators verify results **after** backtest completes

**Result:** Comprehensive validation and filtering coverage from source data to backtest results.

---

## Related Documentation

- [Validation Architecture](../validation/validation_architecture.md) - Complete validation layer overview
- [Pipeline Filters](../archive/code_patterns/06_pipeline/filters.md) - Zipline Pipeline filter patterns
- [Built-in Filters](../archive/code_patterns/06_pipeline/builtin_filters.md) - Zipline built-in filters
- [Data Validation Patterns](../../.cursor/rules/lib-validation.mdc) - Validation module patterns
- [Pipeline Utils API](../api/pipeline_utils.md) - Pipeline utility functions
