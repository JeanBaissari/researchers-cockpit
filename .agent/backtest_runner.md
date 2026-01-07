# Backtest Runner Guide — AI Agent Instructions

> Step-by-step guide for executing backtests correctly and safely.

---

## Overview

Running a backtest executes a strategy against historical data to produce returns, positions, and transactions. This guide ensures backtests are executed correctly with proper validation and result saving.

---

## Pre-Flight Checks

Before running any backtest, verify:

### 1. Strategy Exists and is Valid

```bash
STRATEGY_NAME="btc_sma_cross"
ASSET_CLASS="crypto"  # Determine from strategy location

# Check files exist
test -f strategies/${ASSET_CLASS}/${STRATEGY_NAME}/strategy.py || echo "ERROR: strategy.py missing"
test -f strategies/${ASSET_CLASS}/${STRATEGY_NAME}/hypothesis.md || echo "ERROR: hypothesis.md missing"
test -f strategies/${ASSET_CLASS}/${STRATEGY_NAME}/parameters.yaml || echo "ERROR: parameters.yaml missing"
```

### 2. Syntax Validation

```bash
python -m py_compile strategies/${ASSET_CLASS}/${STRATEGY_NAME}/strategy.py
```

**If errors:** Fix syntax before proceeding.

### 3. Parameter Validation

```bash
python -c "
import yaml
from pathlib import Path

params_path = Path('strategies/${ASSET_CLASS}/${STRATEGY_NAME}/parameters.yaml')
params = yaml.safe_load(open(params_path))
print(f"Asset: {params['strategy']['asset_symbol']}")
print(f"Parameters loaded successfully")
"
```

**If errors:** Fix YAML syntax or missing keys.

**Optional: Schema Validation for Parameters**

```python
from lib.data_validation import SchemaValidator, ValidationConfig

# If you need to validate parameter structure
# (usually not necessary, but useful for complex parameter schemas)
schema_validator = SchemaValidator(
    required_columns={'strategy', 'backtest'},  # Example: validate YAML structure
    allow_extra_columns=True
)

# Note: This is typically handled by parameter loading functions
# but can be useful for custom validation requirements
```

### 4. Data Bundle Availability and Validation

**Basic Check:**
```bash
# Check if bundle exists
ASSET_SYMBOL="BTC-USD"  # From parameters.yaml
BUNDLE_NAME="yahoo_crypto_daily"  # Determine from asset class

if [ ! -d "data/bundles/${BUNDLE_NAME}" ]; then
    echo "WARNING: Bundle ${BUNDLE_NAME} not found"
    echo "Run: python scripts/ingest_data.py --source yahoo --assets crypto"
fi
```

**Comprehensive Validation (Recommended):**
```python
from lib.data_validation import validate_bundle, ValidationConfig, ValidationSeverity
from lib.data_validation import CONTINUOUS_CALENDARS

# Determine asset type from asset class
ASSET_TYPE_MAP = {
    'crypto': 'crypto',
    'forex': 'forex',
    'equities': 'equity'
}
asset_type = ASSET_TYPE_MAP.get(asset_class, 'equity')

# Configure validation based on asset type
# Crypto and forex use 24/7 calendars (no weekend gaps expected)
is_continuous = asset_type in ('crypto', 'forex')
config = ValidationConfig(
    timeframe='daily',  # or '1m', '1h', etc. based on data_frequency
    asset_type=asset_type,
    strict_mode=False,  # Set to True for stricter validation
    suggest_fixes=True  # Get actionable recommendations
)

# Validate bundle integrity
result = validate_bundle(BUNDLE_NAME, config=config)

# Check validation results
if not result.passed:
    print(f"Bundle validation FAILED:")
    print(result.summary())
    
    # Check for blocking errors
    if result.error_checks:
        print("\nBlocking errors found:")
        for check in result.error_checks:
            print(f"  - {check.name}: {check.message}")
        raise ValueError(f"Bundle validation failed: {result.summary()}")
    
    # Warnings are non-blocking unless strict_mode=True
    if result.warning_checks:
        print("\nWarnings (non-blocking):")
        for check in result.warning_checks:
            print(f"  - {check.name}: {check.message}")

# Get fix suggestions if available
if result.metadata.get('suggested_fixes'):
    print("\nSuggested fixes:")
    for fix in result.metadata['suggested_fixes']:
        print(f"  - {fix}")
```

**If missing:** Ingest data before backtesting.

**Configuration Options:**
- Use `ValidationConfig.strict()` for production backtests (warnings become errors)
- Use `ValidationConfig.for_crypto()`, `ValidationConfig.for_forex()`, or `ValidationConfig.for_equity()` for asset-specific validation
- Set `suggest_fixes=True` to get actionable recommendations
- Reference constants from `lib.data_validation`:
  - `DEFAULT_MIN_ROWS_DAILY`: Minimum rows for daily data (default: 20)
  - `DEFAULT_MIN_ROWS_INTRADAY`: Minimum rows for intraday data (default: 100)
  - `DEFAULT_GAP_TOLERANCE_DAYS`: Max consecutive missing days (default: 3)
  - `DEFAULT_GAP_TOLERANCE_BARS`: Max consecutive missing bars for intraday (default: 10)
  - `REQUIRED_OHLCV_COLUMNS`: Required columns for OHLCV data
  - `CONTINUOUS_CALENDARS`: Set of 24/7 calendar identifiers

**Chained Validation (Advanced):**

```python
from lib.data_validation import (
    CompositeValidator, BundleValidator, SchemaValidator,
    ValidationConfig, REQUIRED_OHLCV_COLUMNS
)

# Create composite validator for comprehensive checks
config = ValidationConfig.for_crypto(timeframe='daily')
composite = CompositeValidator([
    BundleValidator(config=config),
    SchemaValidator(required_columns=REQUIRED_OHLCV_COLUMNS)
])

# Run all validations in sequence
result = composite.validate(bundle_name=BUNDLE_NAME, df=some_dataframe)

# All results are merged into single ValidationResult
if not result.passed:
    print(result.summary())
```

### 5. Date Range Validation

```bash
START_DATE="2020-01-01"
END_DATE="2023-12-31"

# Validate date format
python -c "
from datetime import datetime
datetime.strptime('${START_DATE}', '%Y-%m-%d')
datetime.strptime('${END_DATE}', '%Y-%m-%d')
print('Dates valid')
"
```

### 6. Warmup Period Validation

**CRITICAL:** Ensure the backtest period is long enough for indicator initialization.

```python
from lib.config import load_strategy_params, get_warmup_days
from datetime import datetime

# Load strategy parameters
params = load_strategy_params("${STRATEGY_NAME}", "${ASSET_CLASS}")

# Get required warmup days
warmup_days = get_warmup_days(params)

# Calculate available days
start = datetime.strptime("${START_DATE}", '%Y-%m-%d')
end = datetime.strptime("${END_DATE}", '%Y-%m-%d')
available_days = (end - start).days

if available_days <= warmup_days:
    print(f"ERROR: Insufficient data for warmup")
    print(f"  Required warmup: {warmup_days} days")
    print(f"  Available: {available_days} days")
    print(f"  Solution: Extend date range or reduce indicator periods")
else:
    print(f"Warmup validation passed: {warmup_days} days required, {available_days} days available")
```

**Why this matters:**
- Strategies with long indicator periods (e.g., 200-day SMA) need 200+ days of data before generating signals
- Without sufficient warmup, the backtest runs but produces 0% returns (no trades executed)
- The pre-flight validation catches this early with a clear error message

**Configuration:**
- Set `warmup_days` in `parameters.yaml` → `backtest.warmup_days`
- If not set, calculated dynamically from max of all `*_period` parameters
- Disable validation with `backtest.validate_warmup: false` (not recommended)

---

## Execution Steps

### Step 1: Load Strategy and Parameters

```python
from pathlib import Path
import yaml
import sys

strategy_path = Path(f"strategies/{asset_class}/{strategy_name}")
sys.path.insert(0, str(strategy_path))

# Load parameters
params_path = strategy_path / 'parameters.yaml'
with open(params_path) as f:
    params = yaml.safe_load(f)

# Import strategy module
import strategy
```

### Step 2: Determine Data Bundle and Asset Context

```python
from lib.data_validation import CONTINUOUS_CALENDARS

# Map asset class to bundle name
bundle_map = {
    'crypto': {'daily': 'yahoo_crypto_daily', 'minute': 'yahoo_crypto_minute'},
    'forex': {'daily': 'yahoo_forex_daily', 'minute': 'yahoo_forex_minute'},
    'equities': {'daily': 'yahoo_equities_daily', 'minute': 'yahoo_equities_minute'}  # or 'quandl' for daily
}

bundle_name = bundle_map.get(asset_class, 'quandl')

# Map asset class to asset_type for validation
ASSET_TYPE_MAP = {
    'crypto': 'crypto',
    'forex': 'forex',
    'equities': 'equity'
}
asset_type = ASSET_TYPE_MAP.get(asset_class, 'equity')

# Determine calendar context (24/7 assets don't have weekend gaps)
is_continuous = asset_type in ('crypto', 'forex')
calendar_name = '24/7' if is_continuous else 'NYSE'  # or appropriate calendar
```

**Calendar-Aware Validation:**
- Crypto and forex use continuous calendars (24/7 trading)
- Equities use market calendars (weekends/holidays excluded)
- Validation automatically adjusts gap detection for continuous calendars
- Use `CONTINUOUS_CALENDARS` constant to check if calendar is 24/7

### Step 3: Set Date Range

```python
from datetime import datetime
import pandas as pd

# Use provided dates or defaults from config
start_date = start_date or params.get('backtest', {}).get('start_date', '2020-01-01')
end_date = end_date or params.get('backtest', {}).get('end_date', None)

if end_date is None:
    end_date = pd.Timestamp.now(tz='UTC').strftime('%Y-%m-%d')

start = pd.Timestamp(start_date, tz='UTC')
end = pd.Timestamp(end_date, tz='UTC')
```

### Step 4: Set Capital Base

```python
# Load from config or use default
from lib.config import load_settings

settings = load_settings()
capital_base = capital_base or settings['capital']['default_initial']
```

### Step 5: Execute Backtest

```python
from zipline import run_algorithm

# Determine data_frequency from strategy parameters or default
data_frequency = params.get('backtest', {}).get('data_frequency', 'daily')

results = run_algorithm(
    start=start,
    end=end,
    initialize=strategy.initialize,
    handle_data=strategy.handle_data,
    analyze=strategy.analyze,
    before_trading_start=getattr(strategy, 'before_trading_start', None), # Pass if defined
    capital_base=capital_base,
    data_frequency=data_frequency,  # Use the determined data_frequency
    bundle=bundle_name
)
```

**Error Handling:**

```python
import traceback
import logging

logger = logging.getLogger('cockpit.backtest')

try:
    results = run_algorithm(...)
except Exception as e:
    logger.error(f"Backtest failed: {e}", exc_info=True)
    # Save error log
    error_log_path = results_dir / 'error.log'
    with open(error_log_path, 'w') as f:
        f.write(f"Backtest failed: {e}\n")
        f.write(traceback.format_exc())
    raise
```

**Pre-Execution Schema Validation (Optional):**

```python
from lib.data_validation import SchemaValidator, REQUIRED_OHLCV_COLUMNS, ColumnMapping

# If you need to validate data schema before backtest
# (usually handled by bundle validation, but can be done here)
schema_validator = SchemaValidator(
    required_columns=REQUIRED_OHLCV_COLUMNS,
    allow_extra_columns=True  # Allow adj_close, dividends, etc.
)

# Note: This is typically done during bundle creation/validation
# but can be useful for custom data sources
```

---

## Result Saving

### Step 1: Create Timestamped Directory

```python
from datetime import datetime
from pathlib import Path

timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
results_dir = Path(f"results/{strategy_name}/backtest_{timestamp}")
results_dir.mkdir(parents=True, exist_ok=True)
```

### Step 2: Save Core Results

```python
import pandas as pd
import json

# Returns
returns = results['returns']
returns.to_csv(results_dir / 'returns.csv')

# Positions
positions = results['positions']
positions.to_csv(results_dir / 'positions.csv')

# Transactions
transactions = results['transactions']
transactions.to_csv(results_dir / 'transactions.csv')
```

### Step 3: Calculate and Save Metrics

```python
from lib.metrics import calculate_metrics

metrics = calculate_metrics(returns)
with open(results_dir / 'metrics.json', 'w') as f:
    json.dump(metrics, f, indent=2)
```

### Step 4: Save Parameters Used

```python
# Save exact parameters used (for reproducibility)
with open(results_dir / 'parameters_used.yaml', 'w') as f:
    yaml.dump(params, f, default_flow_style=False)
```

### Step 5: Generate Equity Curve Plot

```python
from lib.plots import plot_equity_curve

plot_equity_curve(returns, save_path=results_dir / 'equity_curve.png')
```

### Step 6: Update Latest Symlink

```python
from pathlib import Path

latest_link = Path(f"results/{strategy_name}/latest")

# Remove old symlink if exists
if latest_link.exists() or latest_link.is_symlink():
    latest_link.unlink()

# Create new symlink
latest_link.symlink_to(results_dir.name)
```

---

## Post-Execution Validation

### Check Results Exist

```bash
RESULTS_DIR="results/${STRATEGY_NAME}/backtest_${TIMESTAMP}"

test -f ${RESULTS_DIR}/returns.csv || echo "ERROR: returns.csv missing"
test -f ${RESULTS_DIR}/positions.csv || echo "ERROR: positions.csv missing"
test -f ${RESULTS_DIR}/transactions.csv || echo "ERROR: transactions.csv missing"
test -f ${RESULTS_DIR}/metrics.json || echo "ERROR: metrics.json missing"
test -f ${RESULTS_DIR}/parameters_used.yaml || echo "ERROR: parameters_used.yaml missing"
```

### Validate Backtest Results (Comprehensive)

```python
from lib.data_validation import validate_backtest_results, ValidationConfig, ValidationSeverity
import pandas as pd
import json

# Load results
returns = pd.read_csv(results_dir / 'returns.csv', index_col=0, parse_dates=True)
transactions = pd.read_csv(results_dir / 'transactions.csv', index_col=0, parse_dates=True)
positions = pd.read_csv(results_dir / 'positions.csv', index_col=0, parse_dates=True)

with open(results_dir / 'metrics.json') as f:
    metrics = json.load(f)

# Configure validation
config = ValidationConfig(
    strict_mode=False,  # Set True for production
    suggest_fixes=True   # Get actionable recommendations
)

# Validate backtest results
result = validate_backtest_results(
    results=metrics,
    returns=returns,
    transactions=transactions,
    positions=positions,
    config=config
)

# Check validation results
if not result.passed:
    print(f"Backtest results validation FAILED:")
    print(result.summary())
    
    # Check for blocking errors
    if result.error_checks:
        print("\nBlocking errors found:")
        for check in result.error_checks:
            print(f"  - {check.name}: {check.message}")
            if check.details:
                print(f"    Details: {check.details}")
        raise ValueError(f"Backtest results validation failed: {result.summary()}")
    
    # Warnings are non-blocking unless strict_mode=True
    if result.warning_checks:
        print("\nWarnings (non-blocking):")
        for check in result.warning_checks:
            print(f"  - {check.name}: {check.message}")

# Get fix suggestions if available
if result.metadata.get('suggested_fixes'):
    print("\nSuggested fixes:")
    for fix in result.metadata['suggested_fixes']:
        print(f"  - {fix}")

# Save validation report
validation_report_path = results_dir / 'validation_report.json'
with open(validation_report_path, 'w') as f:
    json.dump(result.to_dict(), f, indent=2)
```

### Validate Metrics (Basic Check)

```python
import json

with open(f"{results_dir}/metrics.json") as f:
    metrics = json.load(f)

# Check for required metrics
required_metrics = ['sharpe', 'sortino', 'max_drawdown', 'annual_return']
for metric in required_metrics:
    if metric not in metrics:
        raise ValueError(f"Missing metric: {metric}")
```,

**Validation Severity Levels:**
- `ERROR`: Critical issues that block validation (e.g., missing required metrics, inconsistent data)
- `WARNING`: Non-fatal issues that should be reviewed (e.g., unusual return patterns, sparse transactions)
- `INFO`: Informational messages (e.g., validation duration, check counts)

**Using ValidationResult:**
- `result.passed`: Boolean indicating overall validation status
- `result.error_checks`: List of failed checks with ERROR severity
- `result.warning_checks`: List of failed checks with WARNING severity
- `result.summary()`: Human-readable formatted summary
- `result.to_dict()`: JSON-serializable dictionary for reports

### Check Symlink

```bash
# Verify latest symlink points to correct directory
LATEST_TARGET=$(readlink results/${STRATEGY_NAME}/latest)
EXPECTED="backtest_${TIMESTAMP}"

if [ "$LATEST_TARGET" != "$EXPECTED" ]; then
    echo "WARNING: Latest symlink may be incorrect"
fi
```

---

## Error Scenarios and Solutions

### Error: "No data available"

**Cause:** Bundle doesn't contain required dates or symbols.

**Solution:**
```bash
# Check bundle contents
python -c "
from zipline.data.bundles import load
bundle = load('${BUNDLE_NAME}')
print(bundle.asset_finder.retrieve_all(bundle.asset_finder.sids))
"

# Validate bundle with detailed diagnostics
python -c "
from lib.data_validation import validate_bundle, ValidationConfig
result = validate_bundle('${BUNDLE_NAME}', config=ValidationConfig(suggest_fixes=True))
print(result.summary())
if not result.passed and result.error_checks:
    for check in result.error_checks:
        print(f'  ERROR: {check.name} - {check.message}')
"

# Re-ingest if needed
python scripts/ingest_data.py --source yahoo --assets crypto --force
```

### Error: "Strategy import failed"

**Cause:** Syntax error or missing imports.

**Solution:**
```bash
# Check syntax
python -m py_compile strategies/${ASSET_CLASS}/${STRATEGY_NAME}/strategy.py

# Check imports
python -c "
import sys
sys.path.insert(0, 'strategies/${ASSET_CLASS}/${STRATEGY_NAME}')
import strategy
"
```

### Error: "Parameter not found"

**Cause:** Missing key in parameters.yaml.

**Solution:**
```bash
# Validate YAML structure
python -c "
import yaml
params = yaml.safe_load(open('strategies/${ASSET_CLASS}/${STRATEGY_NAME}/parameters.yaml'))
# Check required keys exist
"
```

### Error: "Insufficient capital"

**Cause:** Capital base too low for minimum position size.

**Solution:**
- Increase capital_base in backtest call
- Or reduce max_position_pct in parameters.yaml

### Error: "Insufficient data for strategy warmup"

**Cause:** Backtest period is shorter than required warmup days for indicator initialization.

**Solution:**
```bash
# Option 1: Extend the backtest date range
python scripts/run_backtest.py --strategy ${STRATEGY_NAME} \
    --start 2019-01-01 --end 2024-01-01

# Option 2: Reduce indicator periods in parameters.yaml
# Change slow_period from 200 to 50, for example

# Option 3: Increase warmup_days if auto-calculation is wrong
# Edit parameters.yaml:
#   backtest:
#     warmup_days: 200

# Option 4: Skip validation (not recommended)
python scripts/run_backtest.py --strategy ${STRATEGY_NAME} --skip-warmup-check
```

**Prevention:**
- Always calculate warmup_days as max(all indicator periods)
- For 50/200 SMA crossover, use warmup_days: 200
- Ensure bundle contains data from (start_date - warmup_days)

---

## Output Summary Format

After completing a backtest, provide:

```
Backtest complete. Results saved to results/{strategy_name}/backtest_{timestamp}/.

Summary:
- Total Return: {total_return:.2%}
- Sharpe Ratio: {sharpe:.2f}
- Max Drawdown: {max_dd:.2%}
- Win Rate: {win_rate:.1%}
- Total Trades: {n_trades}

Recommendation: {proceed|modify|abandon}
Next: {suggested_action}
```

---

## Best Practices

1. **Always validate before execution** — Pre-flight checks prevent wasted time
   - Use `validate_bundle()` with appropriate `ValidationConfig` for asset type
   - Check warmup period sufficiency before running backtest
   - Validate strategy syntax and parameters

2. **Use Configuration-Aware Validation** — Leverage `ValidationConfig` for consistent thresholds
   - Use `ValidationConfig.for_crypto()`, `ValidationConfig.for_forex()`, or `ValidationConfig.for_equity()`
   - Set `strict_mode=True` for production backtests
   - Use `suggest_fixes=True` to get actionable recommendations

3. **Asset Type Context** — Pass correct `asset_type` for calendar-aware validation
   - Crypto and forex use 24/7 calendars (no weekend gap detection)
   - Equities use market calendars (weekend/holiday gaps expected)
   - Reference `CONTINUOUS_CALENDARS` constant for calendar checks

4. **Save parameters used** — Critical for reproducibility
   - Always save `parameters_used.yaml` with exact configuration
   - Include validation configuration in metadata if custom

5. **Update symlinks** — Makes latest results easily accessible
   - Automatically update `results/{strategy}/latest` symlink

6. **Handle errors gracefully** — Use structured error reporting
   - Use `ValidationResult.error_checks` to identify blocking issues
   - Use `ValidationResult.summary()` for formatted error output
   - Save validation reports alongside results

7. **Validate results comprehensively** — Use `validate_backtest_results()` for integrity checks
   - Validate metrics consistency
   - Check returns/transactions/positions alignment
   - Save validation reports for audit trail

8. **Provide summaries** — Help humans understand results quickly
   - Use `ValidationResult.summary()` for formatted output
   - Include severity levels (ERROR/WARNING/INFO) in reports

---

## Related Files

- **Strategy code:** `strategies/{asset_class}/{strategy_name}/strategy.py`
- **Parameters:** `strategies/{asset_class}/{strategy_name}/parameters.yaml`
- **Results:** `results/{strategy_name}/backtest_{timestamp}/`
- **Latest results:** `results/{strategy_name}/latest/` (symlink)
- **Metrics calculation:** `lib/metrics.py`
- **Plotting:** `lib/plots.py`
- **Data validation:** `lib/data_validation.py`
  - `validate_bundle()`: Pre-flight bundle validation
  - `validate_backtest_results()`: Post-execution results validation
  - `ValidationConfig`: Configuration for validation thresholds
  - `ValidationResult`: Structured validation results with error reporting
  - `SchemaValidator`: DataFrame schema validation
  - `CompositeValidator`: Chain multiple validators together

---

## Next Steps

After successful backtest:

1. **Review metrics** — Are results promising?
2. **Analyze equity curve** — Smooth or jagged?
3. **Check trade distribution** — Balanced wins/losses?
4. **Proceed to optimization** — If Sharpe > 0.3
5. **Or modify strategy** — If results are poor

**See:** `.agent/analyst.md` for detailed analysis procedures

