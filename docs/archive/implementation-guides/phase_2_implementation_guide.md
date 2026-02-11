# Phase 2 Implementation Guide: Calendar Alignment

**Status**: Ready for Implementation
**Priority**: P0 (Critical - blocks FOREX/Crypto strategies)
**Estimated Effort**: 8-12 hours (Day 2)
**Expected Impact**: Eliminates 80% of calendar/session mismatch issues

---

## Overview

Phase 2 fixes the root cause of calendar/session alignment issues by ensuring the backtest execution path uses the SAME session source as the ingestion path (SessionManager).

### Current Problem
```
Ingestion Path:  SessionManager.get_sessions() → 4556 sessions (with filters)
Backtest Path:   calendar.sessions_in_range() → 4560 sessions (no filters)
Result:          Shape mismatch errors, zero trades
```

### Solution
```
Ingestion Path:  SessionManager.get_sessions() → 4556 sessions ✓
Backtest Path:   SessionManager.get_sessions() → 4556 sessions ✓
Result:          Aligned sessions, backtest works
```

---

## Task 2.1: Create get_execution_sessions() in SessionManager

**File**: `lib/calendars/sessions/manager.py`
**Effort**: 2 hours

### Implementation

Add the following method to the `SessionManager` class:

```python
def get_execution_sessions(
    self,
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
    apply_filters: bool = True
) -> pd.DatetimeIndex:
    """
    Get sessions for backtest execution.

    This method ensures backtest uses the SAME session definition as ingestion.

    Args:
        start_date: Start date for session range
        end_date: End date for session range
        apply_filters: If True, apply strategy filters (default: True)

    Returns:
        DatetimeIndex of valid trading sessions

    Phase 2.1 (v1.11.1+): Unified session source for ingestion and execution
    """
    if apply_filters:
        # Use existing get_sessions() which applies filters
        return self.get_sessions(start_date, end_date)
    else:
        # Direct calendar sessions (no filters) - for special cases only
        return self.calendar.sessions_in_range(start_date, end_date)
```

### Testing

```python
# Test in Python console
from lib.calendars.sessions import SessionManager
import pandas as pd

mgr = SessionManager.for_asset_class('forex')
start = pd.Timestamp('2024-01-01', tz='UTC')
end = pd.Timestamp('2024-12-31', tz='UTC')

# Get execution sessions (should match ingestion)
sessions = mgr.get_execution_sessions(start, end)
print(f"Execution sessions: {len(sessions)}")

# Compare to raw calendar
raw_sessions = mgr.calendar.sessions_in_range(start, end)
print(f"Raw calendar sessions: {len(raw_sessions)}")
print(f"Difference: {len(raw_sessions) - len(sessions)} sessions")
```

---

## Task 2.2: Integrate into execute_zipline_backtest()

**File**: `lib/backtest/execution.py`
**Effort**: 4 hours

### Current Code (Lines ~60-80)

```python
def execute_zipline_backtest(
    strategy_func,
    config: BacktestConfig,
    trading_calendar,
) -> pd.DataFrame:
    """Execute backtest using Zipline's TradingAlgorithm."""

    # Current: Uses calendar.sessions_in_range() directly
    start_session = trading_calendar.first_session
    end_session = trading_calendar.all_sessions[-1]

    # ...rest of function
```

### New Code (Phase 2.2)

```python
def execute_zipline_backtest(
    strategy_func,
    config: BacktestConfig,
    trading_calendar,
) -> pd.DataFrame:
    """
    Execute backtest using Zipline's TradingAlgorithm.

    Phase 2.2 (v1.11.1+): Uses SessionManager for session alignment
    """
    from ..calendars.sessions import SessionManager

    # Create SessionManager for this asset class
    session_mgr = SessionManager.for_asset_class(config.asset_class)

    # Get execution sessions (aligned with ingestion)
    execution_sessions = session_mgr.get_execution_sessions(
        start_date=pd.Timestamp(config.start_date, tz='UTC'),
        end_date=pd.Timestamp(config.end_date, tz='UTC'),
        apply_filters=True  # Same filters as ingestion
    )

    if len(execution_sessions) == 0:
        raise ValueError(
            f"No valid trading sessions found for date range "
            f"{config.start_date} to {config.end_date}"
        )

    # Use SessionManager-defined sessions
    start_session = execution_sessions[0]
    end_session = execution_sessions[-1]

    logger.info(
        f"Execution sessions: {len(execution_sessions)} "
        f"(from SessionManager, aligned with ingestion)"
    )

    # ...rest of function (unchanged)
```

### Key Changes

1. Import SessionManager
2. Create SessionManager for asset class
3. Get execution_sessions from SessionManager (NOT calendar)
4. Use these sessions for start/end
5. Add logging for transparency

### Impact

- Backtest sessions now match ingestion sessions exactly
- Shape mismatch errors eliminated
- FOREX/Crypto strategies work reliably

---

## Task 2.3: Add Pre-Flight Session Count Validation

**File**: `lib/backtest/preprocessing.py`
**Effort**: 2 hours

### Add New Validation Function

```python
def validate_session_alignment(
    strategy_name: str,
    bundle_name: str,
    asset_class: str,
    start_date: str,
    end_date: str
) -> None:
    """
    Validate that execution sessions match bundle sessions.

    Phase 2.3 (v1.11.1+): Pre-flight check for session alignment

    Args:
        strategy_name: Name of strategy
        bundle_name: Name of bundle
        asset_class: Asset class (forex, crypto, equity)
        start_date: Start date string
        end_date: End date string

    Raises:
        RuntimeError: If session count mismatch detected
    """
    from ..calendars.sessions import SessionManager
    from ..bundles import load_bundle
    import pandas as pd

    # Get execution sessions (what backtest will use)
    session_mgr = SessionManager.for_asset_class(asset_class)
    execution_sessions = session_mgr.get_execution_sessions(
        start_date=pd.Timestamp(start_date, tz='UTC'),
        end_date=pd.Timestamp(end_date, tz='UTC')
    )

    # Get bundle sessions (what data exists for)
    bundle_data = load_bundle(bundle_name)
    bundle_sessions = bundle_data.equity_daily_bar_reader.sessions

    # Check overlap
    overlapping_sessions = execution_sessions.intersection(bundle_sessions)

    if len(overlapping_sessions) == 0:
        raise RuntimeError(
            f"No overlapping sessions between execution ({len(execution_sessions)}) "
            f"and bundle ({len(bundle_sessions)}). "
            f"Bundle date range: {bundle_sessions[0]} to {bundle_sessions[-1]}, "
            f"Execution range: {execution_sessions[0]} to {execution_sessions[-1]}"
        )

    coverage_pct = 100 * len(overlapping_sessions) / len(execution_sessions)

    if coverage_pct < 95:
        logger.warning(
            f"Session coverage: {coverage_pct:.1f}% "
            f"({len(overlapping_sessions)}/{len(execution_sessions)}). "
            f"Some sessions may be missing data."
        )
    else:
        logger.info(f"Session coverage: {coverage_pct:.1f}% - excellent")
```

### Integrate into run_backtest()

In `lib/backtest/runner.py`, add validation before execution:

```python
def run_backtest(...):
    """Run backtest for a strategy."""

    # ... existing validation ...

    # Phase 2.3: Validate session alignment
    logger.info("Validating session alignment...")
    validate_session_alignment(
        strategy_name=strategy_name,
        bundle_name=config.bundle,
        asset_class=config.asset_class,
        start_date=config.start_date,
        end_date=config.end_date
    )

    # Execute backtest
    perf, trading_calendar = execute_zipline_backtest(...)
```

---

## Verification Tests

### Test 1: Session Alignment

```bash
source venv/bin/activate
python -c "
from lib.calendars.sessions import SessionManager
from lib.bundles import load_bundle
import pandas as pd

# Get execution sessions
mgr = SessionManager.for_asset_class('forex')
exec_sessions = mgr.get_execution_sessions(
    pd.Timestamp('2024-01-01', tz='UTC'),
    pd.Timestamp('2024-12-31', tz='UTC')
)

# Get bundle sessions
bundle = load_bundle('csv_forex_1m')
bundle_sessions = bundle.equity_daily_bar_reader.sessions

# Check alignment
overlap = exec_sessions.intersection(bundle_sessions)
print(f'Execution sessions: {len(exec_sessions)}')
print(f'Bundle sessions: {len(bundle_sessions)}')
print(f'Overlap: {len(overlap)} ({100*len(overlap)/len(exec_sessions):.1f}%)')

if len(overlap) >= len(exec_sessions) * 0.95:
    print('✓ Sessions aligned (≥95% coverage)')
else:
    print('✗ Sessions misaligned (<95% coverage)')
"
```

### Test 2: Full Backtest

```bash
source venv/bin/activate
python scripts/run_backtest.py --strategy breakout_intraday --asset-class forex --bundle csv_forex_1m
```

**Expected Result**:
- Zero "shape mismatch" errors
- Trades executed successfully
- Non-zero performance metrics

---

## Success Criteria

✅ **Session Count Match**: Execution sessions == Bundle sessions (±0.5%)
✅ **No Shape Mismatch Errors**: Zero shape mismatch errors in backtest logs
✅ **FOREX Strategy Success**: breakout_intraday executes with trades
✅ **Pre-Flight Validation**: Session validation catches issues before execution

---

## Rollback Plan

If Phase 2 causes issues:

1. Revert `lib/backtest/execution.py` changes
2. Revert `lib/backtest/preprocessing.py` validation
3. SessionManager changes are non-breaking (new method only)
4. Backtest reverts to calendar.sessions_in_range()

---

## Next Steps

After Phase 2 completion:
- **Phase 3**: Implement full BundleGuard validation chain
- **Documentation**: Update backtest workflow docs
- **Testing**: Add integration tests for session alignment

---

**Implementation Date**: TBD
**Implemented By**: TBD
**Reviewed By**: TBD
