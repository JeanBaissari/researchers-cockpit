# Syntax Error: plots.py Parameter Ordering Issue

## Problem

When importing from `lib.plots` or running scripts that import from `lib`, you encountered:

```
SyntaxError: parameter without a default follows parameter with a default
```

This occurred at line 293 in `lib/plots.py` in the `plot_all()` function.

## Root Cause

In Python, function parameters without default values cannot come after parameters with default values. The original function signature was:

```python
def plot_all(
    returns: pd.Series,
    portfolio_value: Optional[pd.Series] = None,  # Has default
    transactions: Optional[pd.DataFrame] = None,  # Has default
    save_dir: Path,  # ❌ No default, but comes after parameters with defaults
    strategy_name: str = 'Strategy'  # Has default
) -> None:
```

The `save_dir` parameter (required, no default) was positioned after optional parameters (`portfolio_value`, `transactions`), which violates Python's syntax rules.

## Solution

**Fixed:** Moved `save_dir` parameter before optional parameters:

```python
def plot_all(
    returns: pd.Series,
    save_dir: Path,  # ✅ Required parameter first
    portfolio_value: Optional[pd.Series] = None,  # Optional parameters after
    transactions: Optional[pd.DataFrame] = None,
    strategy_name: str = 'Strategy'
) -> None:
```

## Files Modified

1. **`lib/plots.py`** - Fixed function signature (line 289-295)
2. **`lib/backtest.py`** - Updated call to match new parameter order (line 349-355)

## Verification

After the fix, verify imports work:

```bash
source venv/bin/activate
python3 -c "from lib.plots import plot_all; print('✓ Import successful')"
```

## Impact

- **Breaking Change**: Any code calling `plot_all()` with positional arguments needs updating
- **Non-Breaking**: Code using keyword arguments (like `lib/backtest.py`) continues to work
- **Status**: ✅ Fixed and verified

## Prevention

When adding new functions:
- Place required parameters (no defaults) before optional parameters (with defaults)
- Use keyword arguments in function calls for clarity and future-proofing
- Run import tests after signature changes

## Related Files

- `lib/plots.py` - Function definition
- `lib/backtest.py` - Function usage (updated)
- `lib/__init__.py` - Module exports

## Date Fixed

2025-01-23

