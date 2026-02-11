# Phase 2 Findings: Deeper Root Cause Discovered

**Date**: 2026-01-21
**Status**: Phase 2 Implemented, But Insufficient
**Discovery**: Shape mismatch occurs at Zipline internal level, not run_algorithm level

---

## What Was Implemented (Phase 2)

### ✅ Task 2.1: get_execution_sessions() Method
**File**: `lib/calendars/sessions/manager.py`
**Status**: ✅ Complete

Added method to SessionManager:
```python
def get_execution_sessions(
    self,
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
    apply_filters: bool = True
) -> pd.DatetimeIndex:
    """Get sessions for backtest execution (same as ingestion)."""
```

### ✅ Task 2.2: SessionManager Integration
**File**: `lib/backtest/execution.py`
**Status**: ✅ Complete

Modified `execute_zipline_backtest()` to:
- Create SessionManager for asset_class
- Get execution_sessions from SessionManager
- Adjust start_ts/end_ts to match SessionManager sessions
- Added logging for transparency

### ✅ Task 2.3: Enhanced Session Validation
**File**: `lib/backtest/preprocessing.py`
**Status**: ✅ Complete

Enhanced `validate_session_alignment()` to:
- Calculate session coverage percentage
- Report overlapping sessions
- Warn if coverage < 95%
- Generate detailed reports

---

## Why Phase 2 Didn't Solve the Problem

### The Deeper Issue

The shape mismatch occurs **inside Zipline's data fetching**, not at the run_algorithm level.

**Sequence of Events**:

1. **Bundle Ingestion** (csv_forex_1m)
   - SessionManager applies 4 filters
   - Removes Sunday bars, applies gap filling, etc.
   - Results in **4556 sessions** stored in bundle

2. **Backtest Execution** (Phase 2 changes)
   - SessionManager adjusts start_ts/end_ts
   - Passes adjusted dates to run_algorithm()
   - But also passes `trading_calendar` object

3. **Zipline Internal Execution**
   - Strategy calls `data.history(bars=100)`
   - Zipline uses `trading_calendar` to calculate expected bars
   - `trading_calendar` says there are **4560 sessions** in date range
   - Zipline expects 4560 bars but bundle only has 4556
   - **Shape mismatch**: (4556,1) vs (4560,1)

### Root Cause

```
Phase 2 Fixed:     run_algorithm(start, end, ...)  ✓ Adjusted
Phase 2 Didn't Fix: run_algorithm(..., trading_calendar=cal, ...)  ✗ Still has 4560 sessions

Shape mismatch happens here:
  └─> data.history()
       └─> Zipline internal data reader
            └─> Uses trading_calendar to calculate bars
                 └─> Expects 4560, gets 4556
                      └─> Shape mismatch error
```

**The Issue**: We adjusted the start/end dates, but we're still passing a `trading_calendar` object that has 4560 sessions. Zipline's internal data readers use this calendar object to calculate expected data shapes, causing the mismatch.

---

## What Would Actually Fix This

### Option A: Custom Calendar with Exact Sessions (Complex)

Create a custom calendar object with exactly the 4556 sessions that exist in the bundle:

```python
# Pseudo-code
filtered_sessions = session_mgr.get_execution_sessions(start, end)
custom_calendar = create_custom_calendar(filtered_sessions)
run_algorithm(..., trading_calendar=custom_calendar)
```

**Pros**: Aligns perfectly with bundle
**Cons**:
- Requires creating custom Calendar class
- Zipline's Calendar API is complex
- May break other Zipline internals
- High complexity, high risk

### Option B: Bundle Re-Ingestion Without Filters (Simpler)

Re-ingest bundles WITHOUT SessionManager filters, so bundle has all 4560 sessions:

```python
# In CSV ingestion
# Don't apply filters - keep all calendar sessions
sessions = calendar.sessions_in_range(start, end)  # 4560 sessions
# Write all 4560 sessions to bundle
```

**Pros**:
- Simpler solution
- Aligns with Zipline's expectations
- No custom calendar needed

**Cons**:
- Loses benefits of SessionManager filters
- May include "bad" sessions (Sunday data, gaps, etc.)
- Requires re-ingestion of all data

### Option C: Fix at Strategy Level (Workaround)

Catch shape mismatch errors in strategy and handle gracefully:

```python
def before_trading_start(context, data):
    try:
        hist = data.history(...)
    except ValueError as e:
        if "shape mismatch" in str(e):
            # Fallback: Use current bar only
            return
        raise
```

**Pros**: Quick workaround
**Cons**:
- Doesn't fix root cause
- Strategy can't use history
- Severely limits strategy capabilities

---

## Recommended Solution

**Option B: Bundle Re-Ingestion Without Filters**

1. **Modify CSV Bundle Ingestion**
   - Remove SessionManager filter application
   - Use raw calendar sessions
   - Ingest all 4560 sessions

2. **Keep SessionManager for Other Purposes**
   - Still use for validation
   - Still use for reporting
   - Just don't apply filters during ingestion

3. **Accept Imperfect Data**
   - Some sessions may have gaps
   - Some sessions may be Sunday (FOREX)
   - But shape will match calendar expectations

### Implementation

```python
# In lib/bundles/csv/ingestion.py
def load_and_process_csv(...):
    # ...load CSV data...

    # DON'T apply SessionManager filters
    # Just use calendar sessions directly
    sessions = calendar.sessions_in_range(start, end)

    # Filter DataFrame to these sessions (but don't modify sessions list)
    df_filtered = df[df.index.isin(sessions)]

    # Return with all calendar sessions
    return df_filtered
```

---

## Phase 2 Value Delivered

Even though Phase 2 didn't solve the shape mismatch, it still provides value:

✅ **Infrastructure**: SessionManager integration for future use
✅ **Validation**: Enhanced pre-flight session validation
✅ **Logging**: Better visibility into session alignment
✅ **Foundation**: Groundwork for future calendar improvements

---

## Next Steps

### Immediate (To Fix FOREX Backtests)

1. **Implement Option B**: Re-ingest without filters
2. **Test with FOREX strategy**
3. **Verify shape mismatch resolved**

### Long-term (Architectural)

1. **Research Custom Calendar Approach** (Option A)
2. **Evaluate Zipline Fork** for better calendar control
3. **Consider Alternative Backtesting Engine** if Zipline limitations persist

---

## Lessons Learned

1. **Shape Mismatch is Deep**: Occurs in Zipline internals, not at API level
2. **Calendar Object Matters**: Not just start/end dates
3. **SessionManager Filters**: Useful for validation, problematic for ingestion
4. **Zipline Assumptions**: Expects bundle sessions to match calendar exactly

---

## Files Modified in Phase 2

| File | Changes | Status |
|------|---------|--------|
| `lib/calendars/sessions/manager.py` | Added get_execution_sessions() | ✅ Useful |
| `lib/backtest/execution.py` | SessionManager integration | ✅ Good foundation |
| `lib/backtest/preprocessing.py` | Enhanced validation | ✅ Very useful |

**Total Lines**: ~90 lines added
**Value**: Infrastructure and validation improvements

---

## Conclusion

Phase 2 was implemented correctly but discovered a deeper architectural issue with how Zipline handles calendar sessions internally. The solution requires either:
- Creating custom calendar objects (complex)
- Re-ingesting without filters (simpler)
- Working around at strategy level (hacky)

**Recommendation**: Implement Option B (re-ingest without filters) as quickest path to working FOREX backtests, then evaluate Option A (custom calendars) for future architectural improvement.

---

**Status**: Phase 2 Complete (with deeper issue discovered)
**Next**: Implement Option B or proceed with Phase 3
**Priority**: High (blocks FOREX strategies)
