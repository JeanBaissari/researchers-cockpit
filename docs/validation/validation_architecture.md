# Validation Architecture: Pre-Ingestion vs Runtime

> Comprehensive guide to understanding how `lib/validation/` complements Zipline-Reloaded's built-in validation

**Version:** v1.12.0  
**Last Updated:** 2026-01-28

---

## Overview

The Researcher's Cockpit provides **pre-ingestion validation** that runs **before** data enters Zipline bundles, complementing Zipline's **runtime validation** that occurs during bundle creation and backtest execution.

This document clarifies:
1. What our validation does (pre-ingestion, post-ingestion, post-backtest)
2. What Zipline validates (during ingestion, during backtest)
3. How they complement each other
4. When to use each validation layer

---

## Validation Layers

### Layer 1: Pre-Ingestion Validation (Ours)

**When:** Before data enters Zipline bundles  
**Purpose:** Quality assurance on source data  
**Location:** `lib/validation/validators/ingest.py`

**What We Validate:**
- ✅ **Schema validation**: Required OHLCV columns, correct data types
- ✅ **Data quality**: Missing values, duplicates, negative prices
- ✅ **OHLC consistency**: High >= Low, Open/Close within High/Low range
- ✅ **Outlier detection**: Price jumps, volume spikes, statistical anomalies
- ✅ **Gap detection**: Missing trading sessions (calendar-aware)
- ✅ **Stale data detection**: Data freshness checks
- ✅ **Asset-specific rules**: Equity splits, Forex pip values, Crypto 24/7 continuity
- ✅ **Timeframe validation**: Intraday vs daily data characteristics

**Example:**
```python
from lib.validation import validate_before_ingest

# Validate CSV data before ingestion
result = validate_before_ingest(
    df=raw_data,
    asset_name='AAPL',
    timeframe='1d',
    asset_type='equity'
)

if not result:
    print(result.summary())  # Shows all quality issues
    # Fix issues before ingesting
```

**Why This Matters:**
- Catches data quality issues **before** they corrupt bundles
- Provides actionable fix suggestions
- Prevents wasted ingestion time on bad data
- Enables asset-specific validation rules

---

### Layer 2: Zipline Ingestion Validation (Zipline's)

**When:** During bundle creation (`zipline ingest`)  
**Purpose:** Format/structure validation as data is written  
**Location:** Zipline-Reloaded internal validation

**What Zipline Validates:**
- ✅ **Writer format**: Ensures OHLCV columns match expected format
- ✅ **Data types**: Validates numeric types for prices/volumes
- ✅ **Calendar alignment**: Aligns data to trading calendar sessions
- ✅ **Asset metadata**: Validates symbol, exchange, date ranges
- ✅ **Bar continuity**: Ensures no gaps in bar sequences (within calendar)
- ✅ **Volume limits**: Checks uint32 limits for volume data

**What Zipline Does NOT Validate:**
- ❌ Data quality (outliers, price jumps, volume spikes)
- ❌ OHLC consistency (High >= Low, etc.)
- ❌ Stale data detection
- ❌ Asset-specific business rules
- ❌ Statistical anomalies

**Example:**
```python
# Zipline validates during ingestion
from zipline.data.bundles import ingest

# If data has format issues, Zipline will raise errors
ingest('my_bundle')  # Zipline validates format/structure here
```

**Why This Matters:**
- Ensures bundle data structure is correct
- Prevents malformed bundles from being created
- Validates calendar alignment automatically

---

### Layer 3: Post-Ingestion Validation (Ours)

**When:** After bundle creation, before backtest  
**Purpose:** Bundle integrity verification  
**Location:** `lib/validation/validators/bundle.py`

**What We Validate:**
- ✅ **Bundle existence**: Bundle directory and files exist
- ✅ **Metadata integrity**: Bundle metadata.json is valid
- ✅ **Asset files**: Required SQLite/bcolz files present
- ✅ **Date coverage**: Bundle covers requested date range
- ✅ **Symbol availability**: Required symbols exist in bundle

**Example:**
```python
from lib.validation import validate_bundle, verify_bundle_dates

# Validate bundle integrity
result = validate_bundle('my_bundle')
if not result:
    print("Bundle integrity issues:", result.summary())

# Verify date coverage
result = verify_bundle_dates('my_bundle', '2020-01-01', '2024-01-01')
```

**Why This Matters:**
- Catches bundle corruption or missing files
- Validates date range coverage before backtest
- Prevents backtest failures due to missing data

---

### Layer 4: Zipline Runtime Validation (Zipline's)

**When:** During backtest execution (`zipline run`)  
**Purpose:** Data availability and access validation  
**Location:** Zipline-Reloaded internal validation

**What Zipline Validates:**
- ✅ **Data availability**: Checks if data exists for requested dates
- ✅ **Calendar alignment**: Validates backtest dates align with bundle calendar
- ✅ **Symbol resolution**: Ensures symbols can be resolved to assets
- ✅ **Bar access**: Validates data.history() requests are valid
- ✅ **Session continuity**: Ensures no gaps in trading sessions

**What Zipline Does NOT Validate:**
- ❌ Data quality (outliers, anomalies)
- ❌ OHLC consistency
- ❌ Statistical properties

**Example:**
```python
# Zipline validates during backtest
from zipline import run_algorithm

# If data is missing, Zipline will raise errors
perf = run_algorithm(
    start=pd.Timestamp('2020-01-01'),
    end=pd.Timestamp('2024-01-01'),
    capital_base=100000,
    bundle='my_bundle',
    data_frequency='daily'
)
```

**Why This Matters:**
- Ensures backtest can access required data
- Validates calendar alignment at runtime
- Prevents backtest failures due to missing data

---

### Layer 5: Post-Backtest Validation (Ours)

**When:** After backtest execution  
**Purpose:** Results integrity and metrics verification  
**Location:** `lib/validation/validators/results.py`

**What We Validate:**
- ✅ **Metrics consistency**: Sharpe, Sortino, returns calculations
- ✅ **Position/transaction matching**: Positions match transaction history
- ✅ **Returns calculation**: Returns match equity curve
- ✅ **Data integrity**: No NaN or infinite values in results

**Example:**
```python
from lib.validation import validate_backtest_results

# Validate backtest results
result = validate_backtest_results(perf_df, transactions_df, positions_df)
if not result:
    print("Results validation issues:", result.summary())
```

**Why This Matters:**
- Catches calculation errors in metrics
- Validates results integrity
- Ensures backtest results are trustworthy

---

## Validation Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. PRE-INGESTION (Ours)                                      │
│    lib/validation/validators/ingest.py                       │
│    - Schema validation                                       │
│    - Data quality checks                                     │
│    - Outlier detection                                       │
│    - Asset-specific rules                                     │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. ZIPLINE INGESTION (Zipline's)                            │
│    zipline.data.bundles.ingest()                            │
│    - Format validation                                       │
│    - Calendar alignment                                      │
│    - Writer format checks                                    │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. POST-INGESTION (Ours)                                     │
│    lib/validation/validators/bundle.py                      │
│    - Bundle integrity                                        │
│    - Date coverage                                           │
│    - Symbol availability                                     │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. ZIPLINE RUNTIME (Zipline's)                               │
│    zipline.run_algorithm()                                 │
│    - Data availability                                       │
│    - Calendar alignment                                      │
│    - Symbol resolution                                       │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. POST-BACKTEST (Ours)                                      │
│    lib/validation/validators/results.py                      │
│    - Metrics consistency                                     │
│    - Position/transaction matching                           │
│    - Returns verification                                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Distinctions

| Aspect | Our Validation | Zipline Validation |
|--------|---------------|-------------------|
| **Timing** | Pre-ingestion, post-ingestion, post-backtest | During ingestion, during backtest |
| **Focus** | Data quality, business rules, statistical checks | Format, structure, availability |
| **Scope** | Source data quality, bundle integrity, results verification | Bundle format, runtime data access |
| **Actionability** | Provides fix suggestions | Raises errors for invalid format |
| **Asset-specific** | Yes (equity, forex, crypto rules) | No (generic format validation) |

---

## When to Use Each Layer

### Use Pre-Ingestion Validation When:
- ✅ Ingesting data from external sources (Yahoo, CSV, APIs)
- ✅ Validating data quality before bundle creation
- ✅ Checking for outliers, gaps, or anomalies
- ✅ Applying asset-specific business rules
- ✅ Wanting actionable fix suggestions

### Rely on Zipline Ingestion Validation For:
- ✅ Format/structure validation (automatic)
- ✅ Calendar alignment (automatic)
- ✅ Writer format checks (automatic)

### Use Post-Ingestion Validation When:
- ✅ Verifying bundle integrity after creation
- ✅ Checking date range coverage
- ✅ Validating symbol availability
- ✅ Debugging bundle issues

### Rely on Zipline Runtime Validation For:
- ✅ Data availability checks (automatic)
- ✅ Calendar alignment at runtime (automatic)
- ✅ Symbol resolution (automatic)

### Use Post-Backtest Validation When:
- ✅ Verifying metrics calculations
- ✅ Checking results integrity
- ✅ Validating position/transaction consistency

---

## Best Practices

### 1. Always Validate Before Ingestion
```python
# ✅ GOOD: Validate before ingesting
from lib.validation import validate_before_ingest

result = validate_before_ingest(df, asset_name='AAPL', timeframe='1d')
if not result:
    # Fix issues before ingesting
    print(result.summary())
    return

# Now safe to ingest
ingest('my_bundle')
```

### 2. Trust Zipline's Format Validation
```python
# ✅ GOOD: Let Zipline handle format validation
# Our validation catches quality issues, Zipline catches format issues
ingest('my_bundle')  # Zipline validates format automatically
```

### 3. Validate Bundle After Ingestion
```python
# ✅ GOOD: Verify bundle integrity
from lib.validation import validate_bundle

result = validate_bundle('my_bundle')
if not result:
    print("Bundle issues:", result.summary())
```

### 4. Validate Results After Backtest
```python
# ✅ GOOD: Verify backtest results
from lib.validation import validate_backtest_results

result = validate_backtest_results(perf_df, transactions_df, positions_df)
if not result:
    print("Results issues:", result.summary())
```

---

## Summary

**Our validation (`lib/validation/`):**
- **Pre-ingestion**: Data quality, schema, outliers, asset-specific rules
- **Post-ingestion**: Bundle integrity, date coverage, symbol availability
- **Post-backtest**: Metrics consistency, results verification

**Zipline's validation:**
- **During ingestion**: Format, structure, calendar alignment
- **During backtest**: Data availability, symbol resolution, session continuity

**They complement each other:**
- We catch **quality issues** before they enter Zipline
- Zipline catches **format/structure issues** during ingestion
- We verify **bundle integrity** after creation
- Zipline validates **data access** during backtest
- We verify **results integrity** after backtest

**Result:** Comprehensive validation coverage from source data to backtest results.

---

## Related Documentation

- [Data Validation Patterns](../.cursor/rules/lib-validation.mdc)
- [Bundle Management](../api/bundle_inventory.md)
- [Troubleshooting: Data Validation](../troubleshooting/data_validation.md)
- [CSV Ingestion Best Practices](../code_patterns/csv_ingestion_best_practices.md)
