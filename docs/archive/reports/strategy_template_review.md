# Strategy Template Review - Zipline-Reloaded API Usage

**Date:** 2026-01-27  
**Reviewer:** AI Assistant  
**Template Version:** v1.12.0  
**Zipline-Reloaded Version:** 3.0+

## Executive Summary

The strategy template (`strategies/_template/strategy.py`) has been reviewed for compliance with Zipline-Reloaded API patterns. The template is **largely correct** and follows the NO WRAPPERS directive (AD-001). Minor improvements have been identified and applied.

## Review Findings

### ✅ Correct Patterns

1. **Direct Zipline API Usage**
   - ✅ `data.history()` - Correct positional argument usage
   - ✅ `data.current()` - Correct field name ('price')
   - ✅ `symbol()` - Correct asset lookup
   - ✅ `schedule_function()` - Correct scheduling pattern
   - ✅ `order_target_percent()` - Correct order execution

2. **Pipeline API**
   - ✅ Proper fallback pattern for `EquityPricing` vs `USEquityPricing`
   - ✅ Graceful handling when Pipeline API unavailable
   - ✅ Correct `attach_pipeline()` and `pipeline_output()` usage

3. **Direct Pandas Aggregation**
   - ✅ `df.resample().agg({...})` pattern (NO wrapper functions)
   - ✅ Correct OHLCV aggregation logic

4. **Calendar Access**
   - ✅ Direct `get_calendar()` usage (NO SessionManager)
   - ✅ Correct calendar name format ('FOREX', 'CRYPTO')

5. **Configuration Loading**
   - ✅ Uses `lib.config.load_strategy_params()`
   - ✅ Proper parameter validation
   - ✅ No hardcoded parameters

### ⚠️ Minor Improvements Applied

1. **API Documentation Clarity**
   - Added explicit note about `data.history()` return types
   - Clarified that 'price' field returns adjusted close
   - Added note about empty DataFrame handling

2. **Error Handling**
   - Enhanced exception handling comments
   - Added guidance on handling insufficient data

3. **Code Comments**
   - Clarified Zipline-Reloaded specific patterns
   - Added references to official Zipline-Reloaded documentation

## API Signature Verification

### data.history()

**Template Usage:**
```python
prices = data.history(context.asset, 'price', lookback, '1d')
```

**Zipline-Reloaded Signature:**
```python
data.history(assets, fields, bar_count, frequency)
```

**Status:** ✅ **CORRECT** - Positional arguments match API signature

**Field Names Verified:**
- ✅ `'price'` - Valid (returns adjusted close, forward-filled)
- ✅ `'close'` - Valid (current bar close, not forward-filled)
- ✅ `['open', 'high', 'low', 'close', 'volume']` - Valid for OHLCV

**Return Type:**
- Single asset + single field → `pd.Series` (DatetimeIndex)
- Single asset + multiple fields → `pd.DataFrame` (DatetimeIndex, columns=fields)

**Template Handling:** ✅ Correct - Uses `.mean()` on Series, checks `len(prices) >= lookback`

### data.current()

**Template Usage:**
```python
current_price = data.current(context.asset, 'price')
```

**Status:** ✅ **CORRECT** - Returns scalar float (adjusted close)

**Field Behavior:**
- `'price'` - Last known close, forward-filled, adjusted ✅
- Returns `NaN` if asset never traded ✅

**Template Handling:** ✅ Correct - Uses value directly in calculations

### Pipeline API

**Template Usage:**
```python
try:
    from zipline.pipeline.data import EquityPricing
    _PRICING_CLASS = EquityPricing
except ImportError:
    from zipline.pipeline.data import USEquityPricing
    _PRICING_CLASS = USEquityPricing
```

**Status:** ✅ **CORRECT** - Two-level fallback pattern matches Zipline-Reloaded 3.x conventions

**Pipeline Setup:**
```python
attach_pipeline(pipeline, 'my_pipeline')
context.pipeline_data = pipeline_output('my_pipeline')
```

**Status:** ✅ **CORRECT** - Matches Zipline-Reloaded Pipeline API

## Comparison with Working Strategies

### Comparison: `strategies/forex/breakout_intraday/strategy.py`

| Pattern | Template | Working Strategy | Status |
|---------|----------|------------------|--------|
| `data.history()` signature | ✅ `(asset, 'price', lookback, '1d')` | ✅ `(asset, fields, bar_count, '1m')` | ✅ Consistent |
| `data.current()` | ✅ `(asset, 'price')` | ✅ `(asset, 'price')` | ✅ Consistent |
| Pipeline fallback | ✅ Two-level fallback | ✅ Two-level fallback | ✅ Consistent |
| Pandas aggregation | ✅ `df.resample().agg()` | ✅ `df.resample().agg()` | ✅ Consistent |
| Calendar access | ✅ `get_calendar('FOREX')` | ✅ Direct usage | ✅ Consistent |

**Conclusion:** Template patterns match working strategies ✅

## Recommendations

### ✅ Applied Improvements

1. **Enhanced Documentation**
   - Added explicit notes about Zipline-Reloaded API versions
   - Clarified field name behavior ('price' vs 'close')
   - Added troubleshooting guidance

2. **Error Handling**
   - Enhanced exception handling with better error messages
   - Added guidance on handling edge cases (insufficient data, NaN values)

3. **Code Examples**
   - Clarified multi-timeframe aggregation examples
   - Added notes about return types and DataFrame handling

### 📝 Future Considerations

1. **Logging Integration** (Optional)
   - Template currently uses `warnings.warn()` for errors
   - Could optionally use `lib.logging.get_logger()` for structured logging
   - **Decision:** Keep minimal for template simplicity ✅

2. **Type Hints** (Optional)
   - Could add type hints for better IDE support
   - **Decision:** Keep minimal for template simplicity ✅

## Compliance Checklist

- ✅ NO wrapper functions (AD-001)
- ✅ Direct Zipline-Reloaded APIs only
- ✅ Direct pandas for aggregation
- ✅ Correct API signatures
- ✅ Proper error handling
- ✅ Configuration from YAML (no hardcoded params)
- ✅ Modular architecture imports (`lib.*`)
- ✅ Pipeline API fallback pattern
- ✅ Calendar access via `get_calendar()`

## Conclusion

The strategy template is **production-ready** and fully compliant with Zipline-Reloaded API patterns. All API signatures are correct, error handling is appropriate, and the code follows the NO WRAPPERS directive (AD-001).

**Status:** ✅ **APPROVED** - Template is ready for use

**Minor improvements applied:** Documentation enhancements, error handling clarifications

---

## References

- [Zipline-Reloaded Repository](https://github.com/stefan-jansen/zipline-reloaded)
- [Zipline-Reloaded Documentation](https://zipline.ml4trading.io)
- Project Documentation: `docs/archive/code_patterns/`
- Architecture Directive: `PDR.md: AD-001 (NO WRAPPERS)`
