# UTC Timezone Standardization

Align all date/timestamp handling with Zipline-Reloaded's UTC-based internal architecture.

## Problem Statement

The current codebase has inconsistent timezone handling with defensive programming patterns that conflict with Zipline's core design. Zipline-Reloaded 3.1.0 uses UTC internally and expects timezone-naive timestamps that represent UTC.

**Current Anti-patterns:**
- `normalize_to_calendar_timezone()` in `utils.py` converts to calendar TZ then strips
- `_normalize_performance_dataframe()` in `backtest.py` converts to EST then normalizes
- Assertions checking for specific times like `09:30:00` or `00:00:00`
- Inconsistent use of `.normalize()` vs `.tz_localize(None)`

## Completed Tasks

(none yet)

## In Progress Tasks

- [ ] Audit all timezone-related code paths
- [ ] Document Zipline's actual UTC expectations

## Future Tasks

### utils.py Refactoring
- [ ] Replace `normalize_to_calendar_timezone()` with `normalize_to_utc()`
- [ ] New function should: accept any timestamp → convert to UTC → strip tz info
- [ ] Remove `time_of_day` parameter (not needed for UTC normalization)
- [ ] Add docstring explaining Zipline's UTC convention

### backtest.py Refactoring
- [ ] Update `_validate_bundle_date_range()` to use UTC normalization
- [ ] Remove time-of-day assertions (lines 444-447)
- [ ] Fix `_normalize_performance_dataframe()` to use UTC, not EST
- [ ] Simplify date parsing: just use `pd.Timestamp(date).tz_localize(None)` for naive inputs

### data_loader.py Refactoring
- [ ] Update `yahoo_ingest()` to work in UTC consistently
- [ ] Remove calendar_tz dependency for timestamp conversion
- [ ] Ensure bar data index is UTC-based before writing

### Testing
- [ ] Create test for UTC normalization function
- [ ] Verify backtest runs with UTC-normalized dates
- [ ] Test across XNYS, CRYPTO, FOREX calendars

## Implementation Plan

### Step 1: Create UTC Normalization Function

Replace the current `normalize_to_calendar_timezone()` with:

```python
def normalize_to_utc(dt: Union[pd.Timestamp, datetime, str]) -> pd.Timestamp:
    """
    Normalize a datetime to UTC timezone-naive timestamp.
    
    Zipline-Reloaded uses UTC internally. All timestamps should be:
    1. Converted to UTC if timezone-aware
    2. Made timezone-naive (Zipline interprets naive as UTC)
    
    Args:
        dt: Datetime (can be naive, aware, or string)
        
    Returns:
        Timezone-naive Timestamp in UTC
    """
    ts = pd.Timestamp(dt)
    
    if ts.tz is not None:
        # Convert to UTC, then remove timezone info
        ts = ts.tz_convert('UTC').tz_localize(None)
    
    # Naive timestamps are assumed to already be in UTC
    return ts
```

### Step 2: Update backtest.py Date Handling

In `_validate_bundle_date_range()`:
- Parse dates as naive UTC: `pd.Timestamp(start_date)`
- Compare against bundle sessions (which are also UTC-naive)
- Remove calendar_tz parameter entirely

In `run_backtest()`:
- Remove time assertions (lines 444-447)
- Keep the timezone-naive assertion as sanity check

### Step 3: Update data_loader.py

In `yahoo_ingest()`:
- Convert yfinance data index to UTC: `hist.index.tz_convert('UTC').tz_localize(None)`
- Remove calendar_tz variable usage
- Ensure start/end session are UTC-naive

### Step 4: Update _normalize_performance_dataframe

```python
def _normalize_performance_dataframe(perf: pd.DataFrame) -> pd.DataFrame:
    """Normalize performance DataFrame index to timezone-naive UTC."""
    perf_normalized = perf.copy()
    if perf_normalized.index.tz is not None:
        # Convert to UTC, then remove timezone
        perf_normalized.index = perf_normalized.index.tz_convert('UTC').tz_localize(None)
    # Already naive = already UTC (Zipline convention)
    return perf_normalized
```

## Relevant Files

- `lib/utils.py` - `normalize_to_calendar_timezone()` → `normalize_to_utc()`
- `lib/backtest.py` - `_validate_bundle_date_range()`, `_normalize_performance_dataframe()`
- `lib/data_loader.py` - `yahoo_ingest()` timestamp handling
- `lib/data_integrity.py` - `verify_bundle_dates()` (minor update)

## Key Principle

**Zipline's Contract:** All internal timestamps are UTC. Timezone-naive timestamps are interpreted as UTC. Calendar timezones only affect market open/close calculations, not data storage.

**Our Approach:** Convert everything to UTC-naive as early as possible. Trust Zipline to handle calendar-specific session boundaries.
