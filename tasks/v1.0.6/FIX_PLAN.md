# v1.0.6 Fix Plan - Codebase Architect Analysis

**Date:** 2025-12-29
**Status:** Ready for Implementation
**Analyst:** Codebase Architect Agent

---

## Executive Summary

After thorough analysis of the VERIFICATION_REPORT.md and codebase, this document provides:
1. Root cause analysis of documented issues
2. Verification status of previously applied fixes
3. Prioritized fix plan with implementation details

---

## 1. Issue Analysis

### Issue #1: FOREX 1h Current-Day Data Alignment

**Status:** Confirmed - Requires Fix

**Root Cause Analysis:**

The original report incorrectly stated the first minute is 05:01 UTC. Actual findings:
- FOREX calendar first minute: `05:00:00 UTC` (midnight America/New_York = 05:00 UTC)
- FOREX session spans: 05:00 UTC on day N → 04:58 UTC on day N+1

**The Real Problem:**
When ingesting FOREX hourly data for the current day:
1. yfinance returns bars at 00:00-04:00 UTC on today's date
2. These timestamps belong to YESTERDAY's session (which ends at 04:58 UTC)
3. But they're labeled with today's date
4. The minute bar writer creates index starting at 05:00 UTC for today's session
5. Bars at 00:00-04:00 UTC don't exist in today's minute index → **KeyError**

**Evidence (from analysis):**
```python
# Today's session (2025-12-29)
Session open: 05:00:00 UTC
Session first minute: 05:00:00 UTC

# yfinance returns for "today":
2025-12-29 00:00:00 UTC  # Belongs to 2025-12-28 session!
2025-12-29 01:00:00 UTC  # Belongs to 2025-12-28 session!
2025-12-29 02:00:00 UTC  # Belongs to 2025-12-28 session!
2025-12-29 03:00:00 UTC  # Belongs to 2025-12-28 session!
2025-12-29 04:00:00 UTC  # Belongs to 2025-12-28 session!
2025-12-29 05:00:00 UTC  # Belongs to 2025-12-29 session ✓
2025-12-29 06:00:00 UTC  # Belongs to 2025-12-29 session ✓
```

**Current Code Gap:**
In `lib/data_loader.py:475-508`, calendar session filtering is only applied for daily data:
```python
if data_frequency == 'daily' and len(bars_df) > 0:
    # ... filtering logic
```

For minute data, there's no equivalent filtering to align bars with calendar sessions.

---

### Issue #2: Bundle Registry Corruption

**Status:** FIXED (just now)

**Original Issue:** `end_date: "daily"` instead of `null` in registry.

**Verification:**
- Found 1 remaining corrupted entry (`yahoo_equities_daily`)
- Fixed via Python script during this analysis
- Registry now clean

---

### Issue #3: Missing CLI Option for Minute Backtests

**Status:** FIXED (verified)

**Verification:**
- `--data-frequency [daily|minute]` option present in `run_backtest.py:42-43`
- Tested via `--help` output

---

## 2. Prioritized Fix Plan

### Priority 1: FOREX Intraday Session Filtering (Required)

**Location:** `lib/data_loader.py`

**Fix Strategy:** Add intraday session filtering for FOREX calendar

**Implementation:**
```python
# After line 508 in lib/data_loader.py, add:

# === INTRADAY SESSION FILTERING (for FOREX) ===
# For FOREX intraday data, bars at 00:00-04:00 UTC belong to previous session
# These must be filtered out to avoid KeyError during minute bar writing
if data_frequency == 'minute' and 'FOREX' in calendar_name.upper():
    try:
        # Get session for each bar's date
        # Bars before session open belong to previous day's session
        session_opens = []
        for idx_date in bars_df.index.normalize().unique():
            try:
                # Convert to naive for calendar API
                idx_naive = idx_date.tz_convert(None) if idx_date.tz else idx_date
                session_open = calendar_obj.session_open(idx_naive)
                session_opens.append((idx_date, session_open))
            except Exception:
                continue

        if session_opens:
            # Filter bars: keep only those >= session open for their date
            valid_mask = pd.Series(True, index=bars_df.index)
            for date_utc, session_open in session_opens:
                date_bars = bars_df.index.normalize() == date_utc
                pre_session = bars_df.index < session_open
                invalid = date_bars & pre_session
                valid_mask[invalid] = False

            excluded = (~valid_mask).sum()
            if excluded > 0 and show_progress:
                print(f"  {symbol}: Filtered {excluded} pre-session bars (FOREX)")
            bars_df = bars_df[valid_mask]
    except Exception as e:
        print(f"Warning: FOREX intraday session filtering failed: {e}")
```

**Alternative Fix (Simpler):** Auto-exclude current day when end_date is None:
```python
# In ingest_bundle(), before calling _register_yahoo_bundle:
if end_date is None and calendar_name == 'FOREX' and tf_info['data_frequency'] == 'minute':
    # Exclude current day to avoid incomplete session data
    end_date = (datetime.now().date() - timedelta(days=1)).isoformat()
    logger.info(f"FOREX intraday: Auto-setting end_date to {end_date} (excluding current day)")
```

**Recommendation:** Implement both - auto-exclude current day by default AND filter pre-session bars for robustness.

---

### Priority 2: Bundle Frequency Auto-Detection

**Location:** `scripts/run_backtest.py`

**Current Behavior:** User must specify `--data-frequency minute` for intraday bundles

**Fix Strategy:** Auto-detect from bundle registry

**Implementation:**
```python
# In main(), after loading bundle but before run_backtest:

# Auto-detect data frequency from bundle registry
if data_frequency is None:  # Change default from 'daily' to None
    from lib.data_loader import _load_bundle_registry
    registry = _load_bundle_registry()
    if bundle and bundle in registry:
        detected_freq = registry[bundle].get('data_frequency', 'daily')
        click.echo(f"Auto-detected data frequency: {detected_freq}")
        data_frequency = detected_freq
    else:
        data_frequency = 'daily'  # Fallback
```

**CLI Change Required:**
```python
@click.option('--data-frequency', default=None, type=click.Choice(['daily', 'minute']),
              help='Data frequency (auto-detected if not specified)')
```

---

### Priority 3: Bundle Validation Utility

**Location:** New file `scripts/validate_bundles.py`

**Purpose:** Detect and fix registry corruption, validate bundle integrity

**Scope:**
- Check for corrupted `end_date` values
- Verify bundle data exists on disk
- Validate calendar/timeframe consistency
- Provide `--fix` option for auto-repair

---

### Priority 4: lib/timeframe.py Assessment

**Findings:**

`lib/utils.py` already contains:
- `aggregate_ohlcv()` - Aggregate OHLCV to higher timeframe
- `resample_to_timeframe()` - Validate and resample between timeframes
- `create_multi_timeframe_data()` - Create multiple timeframe views
- `get_timeframe_multiplier()` - Calculate timeframe ratios

**Assessment:** `lib/timeframe.py` from ARCHITECTURAL_ANALYSIS.md provides:
- `MultiTimeframeData` class for strategy use with `data.history()` API
- `aggregate_to_timeframe()` for strategy-level aggregation

**Recommendation:** The `MultiTimeframeData` class is useful for strategies but NOT essential. The existing `lib/utils.py` functions are sufficient for most use cases. Mark as LOW priority.

---

### Priority 5: Integration Tests

**Location:** `tests/integration/test_multi_timeframe.py`

**Scope:**
- Test ingestion of 5m, 1h, daily data for each asset class
- Test backtest execution with minute frequency
- Test FOREX session boundary handling
- Test bundle auto-detection

---

## 3. Implementation Order

| Order | Task | Priority | Estimated Complexity |
|-------|------|----------|---------------------|
| 1 | FOREX intraday session filtering | High | Medium |
| 2 | Fix remaining registry entry (DONE) | High | Simple |
| 3 | Bundle frequency auto-detection | Medium | Simple |
| 4 | Bundle validation utility | Medium | Medium |
| 5 | Integration tests | Medium | Medium |
| 6 | lib/timeframe.py (optional) | Low | Simple |

---

## 4. Verification Checklist

After implementing fixes:

- [ ] FOREX 1h ingestion works without `--end-date` workaround
- [ ] Bundle registry has no corrupted entries
- [ ] `run_backtest.py` auto-detects frequency from bundle
- [ ] All test strategies pass (spy_sma_cross, crypto, forex)
- [ ] Integration tests pass

---

## 5. Files to Modify

| File | Changes |
|------|---------|
| `lib/data_loader.py` | Add FOREX intraday session filtering, auto-exclude current day |
| `scripts/run_backtest.py` | Add bundle frequency auto-detection |
| `scripts/validate_bundles.py` | New file - bundle validation utility |
| `tests/integration/test_multi_timeframe.py` | New file - integration tests |

---

**Document prepared by Codebase Architect Agent**
**Ready for implementation approval**
