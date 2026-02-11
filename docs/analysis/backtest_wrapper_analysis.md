# Backtest Wrapper Analysis

**Date:** 2026-01-27  
**Module:** `lib/backtest/`  
**Objective:** Identify and remove Zipline-Reloaded API wrappers per AD-001 (NO WRAPPERS)

---

## Executive Summary

Analysis of `lib/backtest/` identified **1 critical violation** of v1.12.0 NO WRAPPERS architecture and **2 areas for simplification** to better align with direct Zipline-Reloaded API usage.

**Status:** ⚠️ **Action Required** - SessionManager usage must be removed (runtime error risk)

---

## Findings

### 🔴 Critical Issue: SessionManager Usage (v1.12.0 Violation)

**Location:** `lib/backtest/execution.py:82-111`

**Issue:** Code attempts to import and use `SessionManager` from `lib.calendars.sessions`, but SessionManager was **deleted in v1.12.0** (Task 005). This will cause a runtime `ImportError`.

**Current Code:**
```python
# Phase 2.2 (v1.11.1+): Use SessionManager for execution sessions
if asset_class:
    from ..calendars.sessions import SessionManager  # ❌ Module doesn't exist!
    
    session_mgr = SessionManager.for_asset_class(asset_class)
    execution_sessions = session_mgr.get_execution_sessions(...)
    start_ts = execution_sessions[0]
    end_ts = execution_sessions[-1]
```

**Root Cause:** v1.12.0 removed SessionManager because:
- FOREX calendar now includes Sundays (weekmask updated)
- No session alignment workarounds needed
- Direct `get_calendar()` usage replaces SessionManager

**Fix Required:** Remove SessionManager code block entirely. Use direct calendar sessions from Zipline.

**Impact:** High - Code will fail at runtime when `asset_class` is provided.

---

### 🟡 Simplification Opportunity: get_trading_calendar()

**Location:** `lib/backtest/execution.py:233-279`

**Issue:** Function wraps Zipline's calendar extraction with fallback logic. Could be simplified to use `get_calendar()` directly when asset_class is known.

**Current Code:**
```python
def get_trading_calendar(bundle: str, asset_class: Optional[str] = None):
    """Extract trading calendar from bundle."""
    bundle_data = load_bundle(bundle)
    
    # Try custom calendar first
    if asset_class:
        custom_calendar_name = get_calendar_for_asset_class(asset_class)
        if custom_calendar_name:
            from zipline.utils.calendar_utils import get_calendar
            calendar = get_calendar(custom_calendar_name)
            return calendar
    
    # Fallback: Extract from bundle
    if hasattr(bundle_data, 'equity_daily_bar_reader'):
        calendar = bundle_data.equity_daily_bar_reader.trading_calendar
        return calendar
    # ... more fallback logic
```

**Analysis:** This is a **reasonable wrapper** that provides:
- Asset class → calendar name mapping
- Fallback to bundle calendar if custom calendar unavailable
- Error handling with clear messages

**Recommendation:** Keep this function but simplify by:
1. Using `get_calendar()` directly when asset_class is provided (already done)
2. Removing redundant bundle calendar extraction (Zipline handles this)

**Impact:** Low - Function works correctly, minor simplification possible.

---

### ✅ Acceptable Patterns (Not Wrappers)

#### 1. `execute_zipline_backtest()` - Orchestrator, Not Wrapper

**Location:** `lib/backtest/execution.py:23-231`

**Analysis:** This function orchestrates backtest execution but doesn't wrap Zipline APIs. It:
- Handles parameter injection for optimization (creates temp files)
- Manages metrics_set selection (FOREX workaround)
- Provides error handling and cleanup
- Calls `run_algorithm()` directly (no abstraction)

**Verdict:** ✅ **Keep** - This is orchestration logic, not a wrapper.

#### 2. `run_backtest()` - High-Level Orchestrator

**Location:** `lib/backtest/runner.py:51-170`

**Analysis:** Main entry point that coordinates:
- Strategy loading
- Parameter validation
- Pre-flight checks
- Backtest execution
- Results return

**Verdict:** ✅ **Keep** - This is a high-level API, not a Zipline wrapper.

#### 3. `validate_session_alignment()` - Validation Utility

**Location:** `lib/backtest/preprocessing.py:22-66`

**Analysis:** Validates bundle registration using Zipline's `bundles` dict directly:
```python
from zipline.data.bundles import bundles
if bundle not in bundles:
    raise ValueError(...)
```

**Verdict:** ✅ **Keep** - Uses Zipline APIs directly, provides validation logic.

#### 4. `custom_metrics.py` - Zipline Extension

**Location:** `lib/backtest/custom_metrics.py`

**Analysis:** Registers custom metrics set with Zipline using `@metrics.register()`. This extends Zipline's functionality, doesn't wrap it.

**Verdict:** ✅ **Keep** - Extension pattern, not a wrapper.

---

## Recommended Actions

### Priority 1: Fix Critical Issue

1. **Remove SessionManager usage** from `execution.py:82-111`
   - Delete the entire `if asset_class:` block
   - Remove SessionManager import
   - Update docstring to remove SessionManager references
   - Use direct calendar sessions (Zipline handles this automatically)

### Priority 2: Code Cleanup

2. **Update docstrings** to reflect v1.12.0 changes
   - Remove references to SessionManager
   - Update comments about session alignment

3. **Simplify get_trading_calendar()** (optional)
   - Prefer `get_calendar()` when asset_class provided
   - Simplify bundle calendar extraction

---

## Code Changes Required

### Change 1: Remove SessionManager Block

**File:** `lib/backtest/execution.py`

**Remove lines 82-116:**
```python
# Phase 2.2 (v1.11.1+): Use SessionManager for execution sessions
# ... entire block ...
```

**Replace with:**
```python
# v1.12.0: SessionManager removed - FOREX calendar includes Sundays
# Zipline handles session alignment automatically via trading_calendar
# No session workarounds needed
```

### Change 2: Update Docstring

**File:** `lib/backtest/execution.py`

**Update lines 38-40:**
```python
# OLD:
# Phase 2.2 (v1.11.1+): Uses SessionManager for session alignment.
# When asset_class is provided, SessionManager determines execution sessions
# to match ingestion sessions exactly, eliminating shape mismatch errors.

# NEW:
# v1.12.0: SessionManager removed. FOREX calendar includes Sundays,
# so no session alignment workarounds needed. Zipline handles sessions
# automatically via trading_calendar parameter.
```

---

## Testing Requirements

After fixes, verify:

1. ✅ Backtest execution works with `asset_class='forex'`
2. ✅ Backtest execution works with `asset_class='crypto'`
3. ✅ Backtest execution works with `asset_class=None`
4. ✅ No ImportError for SessionManager
5. ✅ Calendar sessions align correctly (no shape mismatches)

---

## Architecture Compliance

| Component | Status | Notes |
|-----------|--------|-------|
| SessionManager usage | ❌ **VIOLATION** | Must be removed |
| get_trading_calendar() | ⚠️ **SIMPLIFY** | Works but could be cleaner |
| execute_zipline_backtest() | ✅ **COMPLIANT** | Orchestrator, not wrapper |
| run_backtest() | ✅ **COMPLIANT** | High-level API |
| validate_session_alignment() | ✅ **COMPLIANT** | Uses Zipline APIs directly |
| custom_metrics.py | ✅ **COMPLIANT** | Extension, not wrapper |

---

## Conclusion

The `lib/backtest/` package is **mostly compliant** with AD-001 (NO WRAPPERS), but contains **1 critical violation** that must be fixed:

- **SessionManager usage** must be removed (runtime error risk)
- **get_trading_calendar()** could be simplified but is acceptable
- All other functions are orchestrators/extensions, not wrappers

**Next Steps:**
1. Remove SessionManager code block
2. Update docstrings
3. Run tests to verify fixes
4. Update this document with results

---

**Analysis Complete:** 2026-01-27
