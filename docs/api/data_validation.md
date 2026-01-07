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
        calendar_name: Optional[str] = None
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
    
    # Price jump detection
    check_price_jumps: bool = True
    price_jump_threshold_pct: float = 50.0
    
    # Index checks
    check_sorted_index: bool = True
    
    # Data sufficiency
    min_rows_daily: int = 20
    min_rows_intraday: int = 100
    
    # Mode
    strict_mode: bool = False
    
    # Context
    timeframe: Optional[str] = None
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
    strict_mode: bool = False,
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
3. **Review warnings**: Even if validation passes, review warnings for potential issues
4. **Use strict mode for critical data**: Enable `strict_mode=True` for production data
5. **Fix issues at source**: Correct data files rather than working around validation failures
6. **Check validation reports**: Use `result.summary()` to understand all issues

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

