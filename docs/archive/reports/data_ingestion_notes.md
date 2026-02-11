# Data Ingestion Notes

## CSV Ingestion Optimizations

### Gap Filling Disabled for CSV Sources
**Date:** 2026-01-21
**File:** `lib/bundles/csv/writer.py:94-101`

**Change:** Removed gap filling for CSV-sourced data.

**Rationale:**
- CSV files are assumed to be complete and pre-validated
- Gap filling designed for API sources (Yahoo) where data may be incomplete
- Aggregating intraday data (15m→daily) creates false gap warnings
- The `fill_data_gaps()` function uses `.normalize()` which creates duplicate dates from intraday timestamps, causing "1568 consecutive days" false positives

**Example False Warning:**
```
15m data: ['2020-01-02 00:00', '2020-01-02 00:15', '2020-01-02 00:30', ...]
After .normalize(): ['2020-01-02', '2020-01-02', '2020-01-02', ...]  # Duplicates!
Gap detection: Calculates false gap of 1568 days
```

**Impact:**
- ✅ Eliminates false "Large gap detected" warnings
- ✅ Eliminates "cannot reindex on an axis with duplicate labels" errors
- ✅ Faster ingestion (skips unnecessary gap filling)
- ⚠️ CSV data MUST be complete before ingestion (use validation scripts)

## Fixed Bugs

### 1. LogContext API Mismatch
**Date:** 2026-01-21
**File:** `scripts/ingest_data.py:157`

**Error:** `TypeError: LogContext() got an unexpected keyword argument 'source'`

**Fix:** Changed `source=source, assets=assets` to `asset_type=assets` (removed `source`, renamed `assets`)

**LogContext Signature:**
```python
LogContext(
    phase: str,
    strategy: Optional[str] = None,
    run_id: Optional[str] = None,
    asset_type: Optional[str] = None,  # ← Correct parameter name
    bundle_name: Optional[str] = None,
    timeframe: Optional[str] = None,
)
```

### 2. FOREX Calendar Holiday Handling
**Date:** 2026-01-21
**File:** `lib/calendars/forex.py:63-74`

**Error:**
```
AssertionError: Got 1442 rows for daily bars table with first day=2020-01-02, last day=2025-07-16, expected 1445 rows.
Missing sessions: [Timestamp('2020-12-25 00:00:00'), Timestamp('2021-01-01 00:00:00'), Timestamp('2025-04-18 00:00:00')]
```

**Root Cause:** The `regular_holidays` property returned `pd.DatetimeIndex([])` instead of a `HolidayCalendar` object. This caused holidays to not be excluded from trading sessions.

**Fix:** Changed return type from `pd.DatetimeIndex` to `HolidayCalendar` with proper Holiday rules:
```python
from pandas.tseries.holiday import Holiday, GoodFriday
from exchange_calendars.exchange_calendar import HolidayCalendar

@property
def regular_holidays(self) -> HolidayCalendar:
    return HolidayCalendar([
        Holiday('Christmas', month=12, day=25),
        Holiday('New Year', month=1, day=1),
        GoodFriday,
    ])
```

**Impact:** FOREX calendar now properly excludes Christmas, New Year's Day, and Good Friday from trading sessions.
