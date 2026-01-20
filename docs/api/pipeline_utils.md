# Pipeline Utils API

Zipline Pipeline helper utilities for factor construction and pipeline setup.

Provides functions to set up and manage Zipline Pipeline API usage in trading strategies. This module centralizes pipeline validation and setup logic, following the Single Responsibility Principle.

**Location:** `lib/pipeline_utils.py`

---

## Overview

The `lib/pipeline_utils` module provides utilities for working with Zipline's Pipeline API, which is primarily designed for US equities trading. It handles pipeline setup, validation, and availability checking.

**Key Features:**
- Pipeline setup with automatic validation
- Asset class compatibility checking
- Pre-flight configuration validation
- Graceful handling of unavailable Pipeline API

**Important Notes:**
- Pipeline API is primarily designed for **US equities** with proper metadata
- For crypto/forex strategies, consider using direct price data instead
- Pipeline requires bundle metadata with `country_code` column for equities

---

## Installation/Dependencies

**Required:**
- `zipline-reloaded` (for Pipeline API support)
- Python standard library (`logging`, `warnings`, `typing`)

**Note:** Pipeline API may not be available in all Zipline versions. The module handles this gracefully.

---

## Quick Start

```python
from lib.pipeline_utils import setup_pipeline
from zipline.pipeline import Pipeline
from zipline.pipeline.factors import SimpleMovingAverage
from zipline.pipeline.data import EquityPricing

def make_pipeline():
    """Create a simple moving average pipeline."""
    sma = SimpleMovingAverage(
        inputs=[EquityPricing.close],
        window_length=30
    )
    return Pipeline(columns={'sma_30': sma})

# In initialize() function
def initialize(context):
    params = load_strategy_params('my_strategy')
    context.use_pipeline = setup_pipeline(context, params, make_pipeline)
```

---

## Public API Reference

### setup_pipeline()

Set up pipeline if enabled and available.

**Signature:**
```python
def setup_pipeline(
    context: 'Context',
    params: dict,
    make_pipeline_func: Optional[Callable[[], Optional['Pipeline']]] = None
) -> bool
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `context` | Context | required | Zipline context object (will be modified with pipeline state) |
| `params` | dict | required | Strategy parameters dictionary |
| `make_pipeline_func` | Callable | None | Optional function that creates and returns a Pipeline. If None, pipeline will not be attached even if enabled |

**Returns:**
- `bool`: `True` if pipeline is active, `False` otherwise

**Side Effects:**
- Sets `context.use_pipeline` (bool)
- Sets `context.pipeline_data` (initialized to None)
- Sets `context.pipeline_universe` (initialized to empty list)
- May attach pipeline to context via `attach_pipeline()`

**Behavior:**
1. Checks if pipeline is enabled in `params['strategy']['use_pipeline']`
2. Validates Pipeline API availability in Zipline version
3. Validates asset class compatibility (warns if not equities)
4. Attaches pipeline if all checks pass and `make_pipeline_func` is provided

**Warnings:**
- Warns if Pipeline API not available
- Warns if asset class is not 'equities'
- Warns if `make_pipeline_func()` returns None
- Warns if pipeline creation fails

**Example:**
```python
from lib.pipeline_utils import setup_pipeline
from zipline.pipeline import Pipeline
from zipline.pipeline.factors import SimpleMovingAverage, RSI
from zipline.pipeline.data import EquityPricing

def make_pipeline():
    """Create a multi-factor pipeline."""
    sma_50 = SimpleMovingAverage(
        inputs=[EquityPricing.close],
        window_length=50
    )
    rsi = RSI(
        inputs=[EquityPricing.close],
        window_length=14
    )
    return Pipeline(
        columns={
            'sma_50': sma_50,
            'rsi': rsi
        },
        screen=sma_50.isfinite() & rsi.isfinite()
    )

def initialize(context):
    params = load_strategy_params('my_strategy')
    
    # Set up pipeline
    context.use_pipeline = setup_pipeline(
        context,
        params,
        make_pipeline
    )
    
    if context.use_pipeline:
        print("Pipeline enabled and attached")
    else:
        print("Pipeline disabled or unavailable")
```

**Integration with Strategy Template:**
```python
# In strategies/_template/strategy.py
from lib.pipeline_utils import setup_pipeline

def initialize(context):
    params = load_params()
    
    # Set up pipeline using library function
    context.use_pipeline = setup_pipeline(context, params, make_pipeline)
    
    # Pipeline will be available in before_trading_start() if enabled
```

---

### is_pipeline_available()

Check if Pipeline API is available in the current Zipline installation.

**Signature:**
```python
def is_pipeline_available() -> bool
```

**Returns:**
- `bool`: `True` if Pipeline API is available, `False` otherwise

**Example:**
```python
from lib.pipeline_utils import is_pipeline_available

if is_pipeline_available():
    print("Pipeline API is available")
    # Proceed with pipeline setup
else:
    print("Pipeline API not available in this Zipline version")
    # Use alternative data access methods
```

**Use Cases:**
- Pre-flight checks before attempting pipeline setup
- Conditional logic based on Pipeline API availability
- Error handling and fallback strategies

---

### validate_pipeline_config()

Validate pipeline configuration without setting it up.

Useful for pre-flight validation before backtest execution.

**Signature:**
```python
def validate_pipeline_config(params: dict) -> tuple[bool, list[str]]
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `params` | dict | required | Strategy parameters dictionary |

**Returns:**
- `tuple[bool, list[str]]`: Tuple of (is_valid, list_of_warnings)
  - `is_valid`: `True` if configuration is valid
  - `list_of_warnings`: List of warning messages (empty if valid)

**Validation Checks:**
1. Pipeline enabled in parameters
2. Pipeline API availability
3. Asset class compatibility (warns if not equities)

**Example:**
```python
from lib.pipeline_utils import validate_pipeline_config

params = load_strategy_params('my_strategy')
is_valid, warnings = validate_pipeline_config(params)

if not is_valid:
    print("Pipeline configuration issues:")
    for warning in warnings:
        print(f"  - {warning}")
    # Handle validation failures
else:
    if warnings:
        print("Pipeline configuration warnings:")
        for warning in warnings:
            print(f"  - {warning}")
    # Proceed with pipeline setup
```

**Use Cases:**
- Pre-flight validation in scripts
- Parameter validation before backtest execution
- Configuration checking in strategy development

---

## Module Structure

The `lib/pipeline_utils` module consists of:

1. **Pipeline Setup** (`setup_pipeline()`)
   - Main function for pipeline initialization
   - Automatic validation and error handling
   - Context state management

2. **Availability Checking** (`is_pipeline_available()`)
   - Runtime Pipeline API detection
   - Version compatibility checking

3. **Configuration Validation** (`validate_pipeline_config()`)
   - Pre-flight configuration checking
   - Warning generation for issues

**Internal State:**
- `_PIPELINE_AVAILABLE` (module-level): Cached Pipeline API availability check

---

## Examples

### Basic Pipeline Setup

```python
from lib.pipeline_utils import setup_pipeline
from zipline.pipeline import Pipeline
from zipline.pipeline.factors import SimpleMovingAverage
from zipline.pipeline.data import EquityPricing

def make_pipeline():
    sma = SimpleMovingAverage(
        inputs=[EquityPricing.close],
        window_length=30
    )
    return Pipeline(columns={'sma': sma})

def initialize(context):
    params = load_strategy_params('my_strategy')
    context.use_pipeline = setup_pipeline(context, params, make_pipeline)
```

### Multi-Factor Pipeline

```python
from lib.pipeline_utils import setup_pipeline
from zipline.pipeline import Pipeline
from zipline.pipeline.factors import SimpleMovingAverage, RSI, BollingerBands
from zipline.pipeline.data import EquityPricing

def make_pipeline():
    """Create a multi-factor momentum pipeline."""
    sma_20 = SimpleMovingAverage(
        inputs=[EquityPricing.close],
        window_length=20
    )
    sma_50 = SimpleMovingAverage(
        inputs=[EquityPricing.close],
        window_length=50
    )
    rsi = RSI(
        inputs=[EquityPricing.close],
        window_length=14
    )
    bb = BollingerBands(
        inputs=[EquityPricing.close],
        window_length=20
    )
    
    # Screen for liquid stocks with valid data
    screen = (
        sma_20.isfinite() &
        sma_50.isfinite() &
        rsi.isfinite() &
        bb.isfinite()
    )
    
    return Pipeline(
        columns={
            'sma_20': sma_20,
            'sma_50': sma_50,
            'rsi': rsi,
            'bb_upper': bb.upper,
            'bb_lower': bb.lower
        },
        screen=screen
    )

def initialize(context):
    params = load_strategy_params('momentum_strategy')
    context.use_pipeline = setup_pipeline(context, params, make_pipeline)
```

### Pipeline with Pre-Flight Validation

```python
from lib.pipeline_utils import setup_pipeline, validate_pipeline_config

def initialize(context):
    params = load_strategy_params('my_strategy')
    
    # Validate before setup
    is_valid, warnings = validate_pipeline_config(params)
    
    if warnings:
        for warning in warnings:
            logger.warning(warning)
    
    if is_valid:
        context.use_pipeline = setup_pipeline(context, params, make_pipeline)
    else:
        context.use_pipeline = False
        logger.error("Pipeline configuration invalid, disabling pipeline")
```

### Conditional Pipeline Usage

```python
from lib.pipeline_utils import setup_pipeline, is_pipeline_available

def initialize(context):
    params = load_strategy_params('my_strategy')
    
    # Check availability first
    if is_pipeline_available():
        context.use_pipeline = setup_pipeline(context, params, make_pipeline)
    else:
        context.use_pipeline = False
        logger.info("Pipeline API not available, using direct data access")
        # Fall back to data.history() or other methods
```

### Accessing Pipeline Data

```python
def before_trading_start(context, data):
    """Fetch pipeline output before trading starts."""
    if context.use_pipeline:
        try:
            context.pipeline_data = pipeline_output('my_pipeline')
            context.pipeline_universe = context.pipeline_data.index.tolist()
        except (KeyError, AttributeError, ValueError) as e:
            logger.warning(f"Pipeline output not available: {e}")
            context.pipeline_data = None
            context.pipeline_universe = []
```

---

## Configuration

### Strategy Parameters

Pipeline setup is controlled by strategy parameters in `parameters.yaml`:

```yaml
strategy:
  use_pipeline: true  # Enable/disable pipeline
  asset_class: equities  # Asset class (pipeline primarily for equities)
```

**Parameter Path:**
- `params['strategy']['use_pipeline']` - Boolean flag
- `params['strategy']['asset_class']` - Asset class string

### Pipeline Requirements

**For Equities:**
- Bundle must have `country_code` column in asset metadata
- Bundle should be ingested with proper equity metadata
- Pipeline API must be available in Zipline version

**For Crypto/Forex:**
- Pipeline API is not recommended
- Use direct data access (`data.history()`, `data.current()`)
- Set `use_pipeline: false` in parameters

---

## Error Handling

### Pipeline Not Available

If Pipeline API is not available in the Zipline version:

```python
# setup_pipeline() will:
# 1. Issue a UserWarning
# 2. Set context.use_pipeline = False
# 3. Return False

# No exception is raised - graceful degradation
```

### Pipeline Creation Failure

If `make_pipeline_func()` raises an exception:

```python
# setup_pipeline() will:
# 1. Log the error
# 2. Issue a UserWarning
# 3. Set context.use_pipeline = False
# 4. Return False

# The exception is caught and handled gracefully
```

### Invalid Configuration

If pipeline is enabled but configuration is invalid:

```python
# validate_pipeline_config() will:
# 1. Return (False, [list of warnings])
# 2. Not raise exceptions

# setup_pipeline() will handle invalid configs gracefully
```

---

## Best Practices

### 1. Always Check Pipeline State

```python
def before_trading_start(context, data):
    if context.use_pipeline and context.pipeline_data is not None:
        # Use pipeline data
        pass
    else:
        # Fall back to direct data access
        pass
```

### 2. Use Pre-Flight Validation

```python
# In scripts or validation code
is_valid, warnings = validate_pipeline_config(params)
if not is_valid:
    # Handle configuration issues before backtest
    pass
```

### 3. Handle Pipeline Errors Gracefully

```python
def before_trading_start(context, data):
    if context.use_pipeline:
        try:
            context.pipeline_data = pipeline_output('my_pipeline')
        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            context.pipeline_data = None
            # Continue with fallback logic
```

### 4. Use Pipeline for Equities Only

```python
# ✅ GOOD - Equities strategy
strategy:
  use_pipeline: true
  asset_class: equities

# ⚠️ WARNING - Crypto/Forex with pipeline
strategy:
  use_pipeline: true
  asset_class: crypto  # Will generate warning

# ✅ GOOD - Crypto/Forex without pipeline
strategy:
  use_pipeline: false
  asset_class: crypto
```

---

## See Also

- [Strategies API](strategies.md) - Strategy development patterns
- [Backtest API](backtest.md) - Backtest execution
- [Zipline Pipeline Documentation](https://zipline.ml4trading.io/pipeline.html) - Official Pipeline API docs
- [Code Patterns: Pipeline](../code_patterns/06_pipeline/) - Pipeline usage patterns
