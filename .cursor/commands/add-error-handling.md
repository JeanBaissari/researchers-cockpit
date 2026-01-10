# Add Error Handling

## Overview

Implement comprehensive error handling for Python/Zipline code using lib/logging/ patterns, custom exceptions, and graceful degradation for backtests, data validation, and strategy execution.

## Steps

1. **Error Detection**
   - Identify potential failure points (backtest execution, data loading, parameter validation)
   - Find unhandled exceptions in strategy code and lib/ modules
   - Detect missing validation for data bundles, strategy parameters, calendar dates
   - Analyze Zipline API calls and data pipeline operations

2. **Error Handling Strategy**
   - Implement try/except blocks with specific exception types
   - Add input validation using lib/validation/ modules
   - Use lib/logging/ for structured error logging with context
   - Design graceful fallbacks for non-critical failures (default configs, cached data)

3. **Recovery Mechanisms**
   - Implement retry logic for transient data source failures
   - Add fallback options for missing data bundles
   - Create validation wrappers for strategy parameters
   - Design proper error propagation with exception chaining

4. **User Experience**
   - Provide clear, actionable error messages referencing strategy names and file paths
   - Include suggestions for resolution (e.g., "Run: python scripts/ingest_data.py")
   - Log errors with full context (strategy, bundle, date range)
   - Preserve exception context with `from e` chaining

## Checklist

- [ ] Identified all potential failure points (backtests, data loading, validation)
- [ ] Implemented try/except blocks with specific exception types
- [ ] Added input validation using lib/validation/ modules
- [ ] Used lib/logging/ for structured error logging
- [ ] Implemented retry logic for transient data failures
- [ ] Added fallback options for missing configs/data
- [ ] Provided clear error messages with resolution suggestions
- [ ] Preserved exception context with chaining

## Error Handling Patterns

**Use lib/logging/ for errors:**
```python
from lib.logging.config import get_logger
from lib.logging.utils import log_exception
from lib.logging.error_codes import ErrorCode

logger = get_logger(__name__)

try:
    result = run_backtest(strategy_name)
except Exception as e:
    log_exception(
        logger,
        f"Backtest failed for {strategy_name}",
        exc=e,
        error_code=ErrorCode.STRATEGY_EXECUTION_ERROR,
        strategy=strategy_name
    )
    raise
```

**Custom exceptions with context:**
```python
class BundleNotFoundError(Exception):
    """Raised when data bundle is not found."""
    pass

try:
    bundle = load_bundle(bundle_name)
except FileNotFoundError as e:
    raise BundleNotFoundError(
        f"Bundle '{bundle_name}' not found.\n"
        f"Run: python scripts/ingest_data.py --source {source}"
    ) from e
```

**Validation with clear messages:**
```python
from lib.validation import ValidationError

def validate_strategy_params(params: dict) -> None:
    required = ['symbol', 'fast_period', 'slow_period']
    missing = [k for k in required if k not in params]
    if missing:
        raise ValidationError(
            f"Missing required parameters: {', '.join(missing)}\n"
            f"Check: strategies/{asset_class}/{strategy_name}/parameters.yaml"
        )
```

**Graceful fallback:**
```python
def load_config_with_fallback(config_path: Path) -> dict:
    try:
        return load_yaml(config_path)
    except FileNotFoundError:
        logger.warning(f"Config not found: {config_path}, using defaults")
        return get_default_config()
    except yaml.YAMLError as e:
        logger.error(f"Invalid YAML: {config_path}", exc_info=True)
        raise ValidationError(f"Config file invalid: {e}") from e
```

## Notes

- Always use lib/logging/ modules, never basic logging or print statements
- Use LogContext for operation-scoped error tracking
- Chain exceptions with `from e` to preserve context
- Provide actionable error messages with file paths and command suggestions
- Never use bare `except:` clauses

## Related Commands

- debug-issue.md - For debugging existing errors
- code-review.md - For reviewing error handling in code