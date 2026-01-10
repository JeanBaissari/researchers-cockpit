# Add Documentation

## Overview

Add comprehensive documentation for Python/Zipline code using Google-style docstrings, following project standards in docs/api/ and inline documentation patterns.

## Steps

1. **Function/Method Documentation**
   - Add Google-style docstrings with Args, Returns, Raises sections
   - Include parameter types and descriptions
   - Document return types and values
   - List exceptions that may be raised

2. **Module Documentation**
   - Add module-level docstring explaining purpose
   - Document key classes and their relationships
   - Include usage examples for main functions

3. **Strategy Documentation**
   - Document hypothesis.md with clear research question
   - Explain strategy logic in strategy.py comments
   - Document parameters.yaml with descriptions

4. **API Documentation**
   - Update docs/api/ files for lib/ modules
   - Include example usage with code snippets
   - Document error handling and edge cases

## Checklist

- [ ] Added Google-style docstrings to all functions/methods
- [ ] Documented all parameters with types and descriptions
- [ ] Documented return types and values
- [ ] Listed exceptions in Raises section
- [ ] Added module-level docstrings
- [ ] Updated docs/api/ files for public functions
- [ ] Included example usage code snippets
- [ ] Documented error handling and edge cases
- [ ] Updated hypothesis.md for strategies
- [ ] Added inline comments for complex logic

## Documentation Patterns

**Function docstring (Google style):**
```python
def run_backtest(
    strategy_name: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    capital_base: Optional[float] = None
) -> Tuple[pd.DataFrame, Any]:
    """
    Run a backtest for a strategy.
    
    Args:
        strategy_name: Name of strategy (e.g., 'btc_sma_cross')
        start_date: Start date string (YYYY-MM-DD) or None for default
        end_date: End date string or None for today
        capital_base: Starting capital or None for default
        
    Returns:
        Tuple[pd.DataFrame, Any]: Performance DataFrame and trading calendar
        
    Raises:
        FileNotFoundError: If strategy not found
        ValueError: If dates or bundle invalid
        
    Example:
        >>> returns, calendar = run_backtest('btc_sma_cross', '2023-01-01')
        >>> print(returns.head())
    """
```

**Module docstring:**
```python
"""
Data bundle management and validation.

Provides functions for ingesting, validating, and managing Zipline data bundles.
Supports multiple data sources (Yahoo, Binance, OANDA) and timeframes.
"""
```

**Strategy hypothesis.md:**
```markdown
# Strategy Hypothesis

## The Belief
BTC price trends persist for 15-30 days after a moving average crossover.

## The Reasoning
Retail FOMO creates momentum. Institutional rebalancing creates mean reversion boundaries.

## The Conditions
Works in trending markets. Fails in choppy, sideways conditions.

## The Falsification
If Sharpe < 0.5 across 3+ years of data, the edge doesn't exist.
```

**Inline comments for complex logic:**
```python
# Normalize timestamps to UTC before Zipline ingestion
# Zipline requires UTC for all datetime operations
df['timestamp'] = normalize_to_utc(df['timestamp'])
```

## Notes

- Use Google-style docstrings (Args, Returns, Raises)
- Include type hints in function signatures
- Document public functions in docs/api/
- Keep docstrings concise but complete
- Update hypothesis.md when strategy logic changes
- Add examples for complex functions

## Related Commands

- code-review.md - For reviewing documentation quality
- create-strategy.md - For strategy documentation structure