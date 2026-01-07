# Data Validation API

Comprehensive data validation for OHLCV data before ingestion into bundles.

**Location:** `lib/data_validation.py`

---

## Overview

The Data Validation API provides multi-layer validation for financial data:

- **Pre-ingestion validation**: Validate CSV files before bundle creation
- **Ingestion-time validation**: Automatic validation during data ingestion
- **Bundle integrity validation**: Verify existing bundles are valid
- **Backtest result validation**: Validate backtest metrics and returns

The API uses a flexible, extensible architecture with configurable validation checks and detailed error reporting.

---

## Core Classes

### DataValidator

Validates OHLCV data before ingestion. Performs comprehensive checks for data quality issues that could affect backtest results.

**Signature:**
```python
class DataValidator(BaseValidator):
    def __init__(self, config: Optional[ValidationConfig] = None)
    def validate(
        self,
        df: pd.DataFrame,
        calendar: Optional[Any] = None,
        asset_name: str = "unknown",
        calendar_name: Optional[str] = None,
        asset_type: Optional[Literal['equity', 'forex', 'crypto']] = None,
        suggest_fixes: bool = False
    ) -> ValidationResult
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `config` | ValidationConfig | None | Validation configuration (uses defaults if None) |
| `df` | pd.DataFrame | required | DataFrame with OHLCV columns (case-insensitive) |
| `calendar` | Any | None | Optional trading calendar for gap detection |
| `asset_name` | str | "unknown" | Asset name for logging and error messages |
| `calendar_name` | str | None | Calendar name (e.g., 'XNYS', 'CRYPTO', '24/7') |
| `asset_type` | Literal['equity', 'forex', 'crypto'] | None | Asset type for context-aware validation |
| `suggest_fixes` | bool | False | If True, add fix suggestions to result metadata |

**Returns:** `ValidationResult` - Validation results with all check outcomes

**Example:**
```python
from lib.data_validation import DataValidator, ValidationConfig
import pandas as pd

# Load data
df = pd.read_csv('data.csv', parse_dates=['Date'], index_col='Date')

# Create validator with default config
validator = DataValidator()
result = validator.validate(df, asset_name='AAPL')

# Check results
if not result.passed:
    print(result.summary())
    for check in result.error_checks:
        print(f"{check.name}: {check.message}")
```

**Validation Checks Performed:**

1. **Required columns** - Verifies OHLCV columns exist (case-insensitive)
2. **Null values** - Detects missing data in OHLCV columns
3. **OHLC consistency** - Validates High >= Low, High >= Open/Close, Low <= Open/Close
4. **Negative values** - Detects negative prices or volumes
5. **Future dates** - Identifies dates in the future
6. **Duplicate dates** - Finds duplicate timestamps
7. **Sorted index** - Verifies index is sorted ascending
8. **Zero volume** - Checks for excessive zero volume bars
9. **Price jumps** - Detects sudden large price movements
10. **Stale data** - Identifies data that is too old
11. **Data sufficiency** - Ensures minimum row count for analysis
12. **Price outliers** - Detects statistical outliers using z-scores
13. **Date/bar continuity** - Checks for gaps using trading calendar (if provided)
14. **Sunday bars** - Detects Sunday bars in FOREX/24/7 data (asset-type aware)
15. **Weekend gap integrity** - Validates FOREX weekend gap semantics (Friday-Sunday-Monday relationships)
16. **Volume spikes** - Detects unusual volume spikes using z-score analysis
17. **Potential splits** - Detects potential unadjusted stock splits via price drops and volume spikes (equity only)

**Column Name Support:**

The validator supports multiple column name formats:
- lowercase: `open`, `high`, `low`, `close`, `volume`
- uppercase: `OPEN`, `HIGH`, `LOW`, `CLOSE`, `VOLUME`
- titlecase: `Open`, `High`, `Low`, `Close`, `Volume`
- abbreviated: `O`, `H`, `L`, `C`, `V`

---

### ValidationConfig

Configuration container for validation settings. Centralizes all validation thresholds and flags for consistent behavior.

**Signature:**
```python
@dataclass
class ValidationConfig:
    # Gap checking
    check_gaps: bool = True
    gap_tolerance_days: int = 3
    gap_tolerance_bars: int = 10
    
    # Outlier detection
    check_outliers: bool = True
    outlier_threshold_sigma: float = 5.0
    
    # Value checks
    check_negative_values: bool = True
    check_future_dates: bool = True
    
    # Stale data detection
    check_stale_data: bool = True
    stale_threshold_days: int = 7
    
    # Volume checks
    check_zero_volume: bool = True
    zero_volume_threshold_pct: float = 10.0
    check_volume_spikes: bool = True
    volume_spike_threshold_sigma: float = 5.0
    
    # Price jump detection
    check_price_jumps: bool = True
    price_jump_threshold_pct: float = 50.0
    
    # Adjustment detection
    check_adjustments: bool = True
    
    # Index checks
    check_sorted_index: bool = True
    
    # Data sufficiency
    min_rows_daily: int = 20
    min_rows_intraday: int = 100
    
    # Mode
    strict_mode: bool = False
    suggest_fixes: bool = False
    
    # Context
    timeframe: Optional[str] = None
    asset_type: Optional[Literal['equity', 'forex', 'crypto']] = None
    calendar_name: Optional[str] = None
    
    # FOREX-specific checks
    check_sunday_bars: bool = True
    check_weekend_gaps: bool = True
```

**Factory Methods:**

```python
# Default configuration
config = ValidationConfig.default(timeframe='1d')

# Strict mode (warnings become errors)
config = ValidationConfig.strict(timeframe='1d')

# Lenient mode (relaxed thresholds)
config = ValidationConfig.lenient(timeframe='1h')

# Minimal config (only essential checks)
config = ValidationConfig.minimal(timeframe='1d')

# Asset-type-specific configurations
config = ValidationConfig.for_equity(timeframe='1d')    # Enables split detection, volume checks
config = ValidationConfig.for_forex(timeframe='1d')     # Enables Sunday bar detection, disables volume checks
config = ValidationConfig.for_crypto(timeframe='1h')    # Optimized for 24/7 markets
```

**Example:**
```python
from lib.data_validation import DataValidator, ValidationConfig

# Create strict validation config
config = ValidationConfig.strict(timeframe='1d')
config.gap_tolerance_days = 1  # Override default
config.zero_volume_threshold_pct = 5.0  # Stricter volume check

validator = DataValidator(config=config)
result = validator.validate(df, asset_name='AAPL')
```

**Configuration Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `is_intraday` | bool | True if configured timeframe is intraday |
| `expected_interval` | pd.Timedelta | Expected time interval for timeframe |
| `min_rows` | int | Minimum rows based on timeframe type |

---

### ValidationResult

Container for aggregated validation results. Supports adding individual checks, merging multiple results, and generating summaries.

**Signature:**
```python
@dataclass
class ValidationResult:
    passed: bool = True
    checks: List[ValidationCheck] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    info: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
```

**Key Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `passed` | bool | True if validation passed (no errors) |
| `error_checks` | List[ValidationCheck] | Failed checks with ERROR severity |
| `warning_checks` | List[ValidationCheck] | Failed checks with WARNING severity |
| `failed_checks` | List[ValidationCheck] | All failed checks |
| `passed_checks` | List[ValidationCheck] | All passed checks |
| `check_count` | int | Total number of checks |
| `pass_rate` | float | Percentage of checks that passed |
| `duration_ms` | float | Validation duration in milliseconds |

**Methods:**

```python
# Add a validation check
result.add_check(
    name='test_check',
    passed=True,
    message='Check passed',
    details={'key': 'value'},
    severity=ValidationSeverity.ERROR
)

# Add warning/info/error messages
result.add_warning('Minor issue detected')
result.add_info('Informational message')
result.add_error('Critical error')

# Add metadata
result.add_metadata('asset_name', 'AAPL')

# Merge another result
result.merge(other_result)

# Generate summary
summary = result.summary(max_errors=5)

# Convert to dictionary (JSON serializable)
result_dict = result.to_dict()
```

**Example:**
```python
from lib.data_validation import DataValidator, ValidationResult

validator = DataValidator()
result = validator.validate(df, asset_name='AAPL')

# Check if validation passed
if not result:
    print("Validation failed!")
    print(result.summary())
    
    # Access error details
    for check in result.error_checks:
        print(f"Error: {check.name}")
        print(f"  Message: {check.message}")
        print(f"  Details: {check.details}")
    
    # Access warnings
    for check in result.warning_checks:
        print(f"Warning: {check.name} - {check.message}")
else:
    print(f"Validation passed! ({result.pass_rate:.1f}% checks passed)")
```

**Boolean Usage:**

`ValidationResult` can be used directly in boolean context:

```python
result = validator.validate(df, asset_name='AAPL')

if result:
    print("Validation passed")
else:
    print("Validation failed")
```

---

## Convenience Functions

### validate_before_ingest()

Main entry point for pre-ingestion validation. Validates data before ingestion into a bundle.

**Signature:**
```python
def validate_before_ingest(
    df: pd.DataFrame,
    asset_name: str = "unknown",
    timeframe: Optional[str] = None,
    calendar: Optional[Any] = None,
    calendar_name: Optional[str] = None,
    asset_type: Optional[Literal['equity', 'forex', 'crypto']] = None,
    strict_mode: bool = False,
    suggest_fixes: bool = False,
    config: Optional[ValidationConfig] = None
) -> ValidationResult
```

**Example:**
```python
from lib.data_validation import validate_before_ingest

result = validate_before_ingest(
    df=df,
    asset_name='AAPL',
    timeframe='1d',
    strict_mode=True
)

if not result:
    raise ValueError(f"Validation failed: {result.summary()}")
```

---

### validate_bundle()

Validate an existing bundle for integrity.

**Signature:**
```python
def validate_bundle(
    bundle_name: str,
    bundle_path: Optional[Path] = None,
    config: Optional[ValidationConfig] = None
) -> ValidationResult
```

**Example:**
```python
from lib.data_validation import validate_bundle

result = validate_bundle('yahoo_equities_daily')

if not result.passed:
    print(f"Bundle validation failed: {result.errors}")
```

---

## Validation Severity Levels

The API uses three severity levels:

| Severity | Description | Blocks Validation |
|----------|-------------|-------------------|
| `ERROR` | Critical issue that blocks validation | Yes |
| `WARNING` | Non-fatal issue that should be reviewed | No (unless strict_mode=True) |
| `INFO` | Informational message | No |

**Severity Behavior:**

- **Default mode**: Only ERROR severity checks cause validation to fail
- **Strict mode**: WARNING severity checks also cause validation to fail

```python
# Default mode - warnings don't fail validation
config = ValidationConfig(timeframe='1d')
validator = DataValidator(config=config)
result = validator.validate(df, asset_name='AAPL')
# result.passed = True even if warnings exist

# Strict mode - warnings become errors
config = ValidationConfig.strict(timeframe='1d')
validator = DataValidator(config=config)
result = validator.validate(df, asset_name='AAPL')
# result.passed = False if any warnings exist
```

---

## Usage Examples

### Basic Validation

```python
from lib.data_validation import DataValidator, ValidationConfig
import pandas as pd

# Load data
df = pd.read_csv('data.csv', parse_dates=['Date'], index_col='Date')

# Validate with default config
validator = DataValidator()
result = validator.validate(df, asset_name='AAPL')

if result.passed:
    print("✓ Validation passed")
else:
    print("✗ Validation failed")
    print(result.summary())
```

### Strict Mode Validation

```python
from lib.data_validation import DataValidator, ValidationConfig

# Create strict config
config = ValidationConfig.strict(timeframe='1d')
validator = DataValidator(config=config)

result = validator.validate(df, asset_name='AAPL', calendar=calendar)

if not result:
    # In strict mode, warnings also cause failures
    for check in result.error_checks:
        print(f"Error: {check.message}")
    for check in result.warning_checks:
        print(f"Warning (treated as error): {check.message}")
```

### Custom Configuration

```python
from lib.data_validation import DataValidator, ValidationConfig

# Create custom config
config = ValidationConfig(
    timeframe='1h',
    check_gaps=True,
    gap_tolerance_bars=20,  # Allow more gaps for intraday
    check_zero_volume=True,
    zero_volume_threshold_pct=15.0,  # Allow more zero volume
    check_outliers=False,  # Disable outlier detection
    strict_mode=False
)

validator = DataValidator(config=config)
result = validator.validate(df, asset_name='BTCUSD', calendar_name='CRYPTO')
```

### Asset Type-Aware Validation

The validator can adapt its checks based on asset type (equity, forex, crypto):

```python
from lib.data_validation import DataValidator, ValidationConfig

# FOREX validation - enables Sunday bar detection, disables volume checks
config = ValidationConfig.for_forex(timeframe='1d')
validator = DataValidator(config=config)
result = validator.validate(
    df, 
    asset_name='EURUSD',
    asset_type='forex',
    calendar_name='24/7'
)

# Equity validation - enables split detection, volume checks
config = ValidationConfig.for_equity(timeframe='1d')
validator = DataValidator(config=config)
result = validator.validate(
    df,
    asset_name='AAPL',
    asset_type='equity',
    calendar_name='XNYS'
)

# Crypto validation - 24/7 continuity checks
config = ValidationConfig.for_crypto(timeframe='1h')
validator = DataValidator(config=config)
result = validator.validate(
    df,
    asset_name='BTCUSD',
    asset_type='crypto',
    calendar_name='CRYPTO'
)
```

### Sunday Bar Detection (FOREX)

Detects Sunday bars in FOREX data that should be consolidated to Friday:

```python
from lib.data_validation import DataValidator, ValidationConfig

config = ValidationConfig(
    timeframe='1d',
    asset_type='forex',
    check_sunday_bars=True
)
validator = DataValidator(config=config)
result = validator.validate(df, asset_name='EURUSD', asset_type='forex')

if not result.passed:
    for check in result.warning_checks:
        if check.name == 'sunday_bars':
            print(f"Found Sunday bars: {check.details['sunday_count']}")
            print(f"Dates: {check.details['sunday_dates']}")
            # Use lib.utils.consolidate_sunday_to_friday() to fix
```

### Volume Spike Detection

Detects unusual volume spikes that may indicate data quality issues:

```python
from lib.data_validation import DataValidator, ValidationConfig

config = ValidationConfig(
    timeframe='1d',
    check_volume_spikes=True,
    volume_spike_threshold_sigma=5.0  # Default: 5 standard deviations
)
validator = DataValidator(config=config)
result = validator.validate(df, asset_name='AAPL', asset_type='equity')

if not result.passed:
    for check in result.warning_checks:
        if check.name == 'volume_spikes':
            print(f"Volume spikes detected: {check.details['spike_count']}")
            print(f"Spike dates: {check.details['spike_dates']}")
```

### Split Detection (Equity)

Detects potential unadjusted stock splits:

```python
from lib.data_validation import DataValidator, ValidationConfig

config = ValidationConfig(
    timeframe='1d',
    asset_type='equity',
    check_adjustments=True
)
validator = DataValidator(config=config)
result = validator.validate(df, asset_name='AAPL', asset_type='equity')

if not result.passed:
    for check in result.warning_checks:
        if check.name == 'potential_splits':
            print(f"Potential splits found: {check.details['potential_split_count']}")
            for split in check.details['potential_splits']:
                print(f"  Date: {split['date']}, Ratio: {split['split_ratio']}, "
                      f"Change: {split['price_change_pct']:.2f}%")
            # Consider using adjusted close data
```

### Weekend Gap Integrity (FOREX)

Validates FOREX weekend gap semantics:

```python
from lib.data_validation import DataValidator, ValidationConfig

config = ValidationConfig(
    timeframe='1d',
    asset_type='forex',
    check_weekend_gaps=True
)
validator = DataValidator(config=config)
result = validator.validate(df, asset_name='EURUSD', asset_type='forex')

if not result.passed:
    for check in result.warning_checks:
        if check.name == 'weekend_gap_integrity':
            print(f"Weekend gap issues: {check.details['issues']}")
```

### Fix Suggestions

Enable fix suggestions to get actionable recommendations:

```python
from lib.data_validation import validate_before_ingest

result = validate_before_ingest(
    df,
    asset_name='EURUSD',
    timeframe='1d',
    asset_type='forex',
    suggest_fixes=True
)

if not result.passed:
    fixes = result.metadata.get('suggested_fixes', [])
    for fix in fixes:
        print(f"Issue: {fix['issue']}")
        print(f"Function: {fix['function']}")
        print(f"Description: {fix['description']}")
```

### Validation During Ingestion

The data ingestion pipeline automatically validates data:

```python
from lib.data_loader import ingest_bundle

# Validation happens automatically during ingestion
bundle_name = ingest_bundle(
    source='yahoo',
    assets=['equities'],
    symbols=['AAPL', 'MSFT'],
    timeframe='daily'
)

# Symbols with validation failures are skipped and logged
# Check logs for validation errors
```

### Pre-Ingestion Validation

Validate CSV files before ingestion:

```python
from lib.data_validation import validate_before_ingest
import pandas as pd

# Load CSV
df = pd.read_csv('data/AAPL.csv', parse_dates=['datetime'], index_col='datetime')

# Validate
result = validate_before_ingest(
    df=df,
    asset_name='AAPL',
    timeframe='1d',
    strict_mode=True
)

if result.passed:
    print("Data is ready for ingestion")
else:
    print("Fix issues before ingesting:")
    for check in result.error_checks:
        print(f"  - {check.name}: {check.message}")
```

### Handling Validation Results

```python
from lib.data_validation import DataValidator

validator = DataValidator()
result = validator.validate(df, asset_name='AAPL')

# Check overall status
if result.passed:
    print("Validation passed")
else:
    print(f"Validation failed: {len(result.error_checks)} errors")

# Access specific check results
for check in result.checks:
    status = "✓" if check.passed else "✗"
    print(f"{status} {check.name}: {check.message}")

# Get statistics
print(f"Pass rate: {result.pass_rate:.1f}%")
print(f"Duration: {result.duration_ms:.1f}ms")
print(f"Total checks: {result.check_count}")

# Access metadata
print(f"Asset: {result.metadata.get('asset_name')}")
print(f"Date range: {result.metadata.get('date_range_start')} to {result.metadata.get('date_range_end')}")
```

---

## New Features

### Asset Type Awareness

The validator now supports asset-type-aware validation with three profiles:

- **Equity**: Enables split detection, volume spike checks, and expects zero volume on holidays
- **Forex**: Enables Sunday bar detection and weekend gap integrity checks, disables volume validation (unreliable)
- **Crypto**: Optimized for 24/7 markets, no session gaps expected

Asset type can be specified via:
- `ValidationConfig.asset_type` parameter
- `DataValidator.validate(asset_type=...)` parameter
- Factory methods: `ValidationConfig.for_equity()`, `for_forex()`, `for_crypto()`

### Sunday Bar Detection

Detects Sunday bars in FOREX/24/7 data that should be consolidated to Friday. This check:
- Only runs for FOREX assets or 24/7 calendars
- Identifies all Sunday bars (dayofweek == 6)
- Provides actionable fix suggestions using `lib.utils.consolidate_sunday_to_friday()`
- Returns warning severity (non-blocking)

**Configuration:**
```python
config = ValidationConfig(
    check_sunday_bars=True,  # Default: True
    asset_type='forex'
)
```

### Weekend Gap Integrity

Validates FOREX weekend gap semantics by checking:
- Friday-Sunday pairs (potential duplication)
- Sunday-Monday pairs (should reflect weekend movement)
- Friday-Monday pairs without Sunday (expected for consolidated data)

**Configuration:**
```python
config = ValidationConfig(
    check_weekend_gaps=True,  # Default: True
    asset_type='forex'
)
```

### Volume Spike Detection

Detects unusual volume spikes using z-score analysis:
- Calculates z-scores for volume data
- Flags spikes exceeding threshold (default: 5 sigma)
- Automatically skipped for FOREX assets (volume unreliable)
- Provides spike dates and statistics

**Configuration:**
```python
config = ValidationConfig(
    check_volume_spikes=True,  # Default: True
    volume_spike_threshold_sigma=5.0  # Default: 5.0
)
```

### Split/Dividend Adjustment Detection

Detects potential unadjusted stock splits by:
- Identifying price drops matching common split ratios (2:1, 3:1, 4:1, etc.)
- Cross-referencing with volume spikes on same day
- Detecting reverse splits (1:2, 1:3)
- Only runs for equity assets

**Supported Split Ratios:**
- Forward splits: 5:4 (25% drop), 3:2 (33% drop), 2:1 (50% drop), 3:1 (67% drop), 4:1 (75% drop)
- Reverse splits: 1:2 (100% increase), 1:3 (200% increase)

**Configuration:**
```python
config = ValidationConfig(
    check_adjustments=True,  # Default: True
    asset_type='equity'  # Required for split detection
)
```

### Fix Suggestions

When `suggest_fixes=True`, the validator adds actionable fix suggestions to result metadata:

```python
result = validate_before_ingest(
    df,
    asset_name='EURUSD',
    suggest_fixes=True
)

fixes = result.metadata.get('suggested_fixes', [])
for fix in fixes:
    print(f"Issue: {fix['issue']}")
    print(f"Function: {fix['function']}")
    print(f"Description: {fix['description']}")
```

---

## Integration with Data Ingestion

The validation API is integrated into the data ingestion pipeline:

1. **Pre-ingestion validation**: Each CSV file is validated before being written to bundles
2. **Symbol skipping**: Symbols with validation failures are skipped (not ingested)
3. **Error logging**: Validation errors are logged with detailed messages
4. **No auto-repair**: Data is not automatically fixed - manual intervention required

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

1. **Validate before ingestion**: Use `validate_before_ingest()` or `scripts/validate_csv_data.py` to check data quality
2. **Use appropriate timeframes**: Set `timeframe` in config for context-aware validation
3. **Specify asset type**: Always provide `asset_type` parameter for context-aware validation (equity/forex/crypto)
4. **Review warnings**: Even if validation passes, review warnings for potential issues
5. **Use strict mode for critical data**: Enable `strict_mode=True` for production data
6. **Fix issues at source**: Correct data files rather than working around validation failures
7. **Check validation reports**: Use `result.summary()` to understand all issues
8. **Enable fix suggestions**: Use `suggest_fixes=True` to get actionable recommendations
9. **Asset-specific validation**: Use `ValidationConfig.for_equity()`, `for_forex()`, or `for_crypto()` for optimized validation profiles
10. **Handle FOREX Sunday bars**: Use `lib.utils.consolidate_sunday_to_friday()` to fix Sunday bar issues in FOREX data

---

## Migration from Old API

If you were using the old validation API:

1. **Replace old validator calls** with `DataValidator.validate()`
2. **Update result property access**:
   - Old: `result.has_errors`
   - New: `result.passed` (inverted) or `len(result.error_checks) > 0`
3. **Update error access**:
   - Old: `result.errors`
   - New: `result.error_checks` (list of `ValidationCheck` objects)
4. **Note auto-repair removal**: The new API does not automatically fix data issues

See [Troubleshooting: Data Validation](../troubleshooting/data_validation.md) for more details.

---

## Related Documentation

- [Troubleshooting: Data Validation](../troubleshooting/data_validation.md) - Common validation errors and solutions
- [Troubleshooting: Auto-Repair Removal](../troubleshooting/auto_repair_removal.md) - Understanding the removal of auto-repair
- [Data Loader API](data_loader.md) - Data ingestion with automatic validation
- [Data Integrity Module](../troubleshooting/data_ingestion.md) - Pre-ingestion validation utilities

---

## See Also

- [API Reference](../api/README.md) - Complete API documentation index
- [Code Patterns](../code_patterns/) - Usage patterns and examples
- [Strategy Templates](../templates/strategies/) - Example strategies

