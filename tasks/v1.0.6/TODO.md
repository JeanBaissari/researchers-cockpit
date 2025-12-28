# v1.0.6 TODO: Multi-Timeframe Data Ingestion

## Completed This Session

- [x] Add timeframe configuration maps (`TIMEFRAME_TO_YF_INTERVAL`, `TIMEFRAME_DATA_LIMITS`)
- [x] Add `--timeframe` CLI option to `scripts/ingest_data.py`
- [x] Add `--list-timeframes` CLI option
- [x] Update bundle naming convention to `{source}_{asset}_{timeframe}`
- [x] Add date validation with auto-adjustment for limited timeframes
- [x] Fix `end_date` registry bug (was storing timeframe string instead of date)
- [x] Add data aggregation utilities to `lib/utils.py`
- [x] Update `config/settings.yaml` with timeframe configuration
- [x] Create test strategy `strategies/equities/test_hourly_momentum/`
- [x] Test and verify: SPY daily, SPY 1h, AAPL 5m (equities only)

## Workarounds Applied (Need Proper Fix)

- [x] Skip calendar session filtering for intraday data - **TEMPORARY WORKAROUND**
- [x] Skip gap-filling for intraday data - **TEMPORARY WORKAROUND**

These workarounds suppress errors but don't address the root cause. See "Architecture Fixes Needed" below.

---

## Architecture Fixes Needed (Critical)

### 1. Minute Bar Infrastructure Misuse

**Problem:** The current implementation uses daily-style calendar APIs for minute data.

**Evidence:**
```
Warning: Parameter `start` parsed as '2024-06-03 13:30:00' although a Date must have a time component of 00:00.
```

**Root Cause Analysis:**
- Calling `calendar.sessions_in_range()` with intraday timestamps
- Not using `calendar.minutes_for_sessions_in_range()` for minute data
- Possible misuse of `BcolzMinuteBarWriter` interface

**Required Actions:**
- [ ] Audit `lib/data_loader.py` for session-level API calls in minute data paths
- [ ] Replace `sessions_in_range()` with `minutes_for_sessions_in_range()` where appropriate
- [ ] Verify `minute_bar_writer.write()` receives correctly formatted data
- [ ] Remove the "skip calendar filtering" workaround after proper fix

### 2. Crypto Calendar Investigation

**Problem:** Crypto minute ingestion fails with a Timestamp error.

**Incorrect Initial Assumption:** Zipline can't handle 24/7 calendars.

**Actual Situation:**
- `exchange_calendars` DOES support 24/7 calendars (CRYPTO)
- Zipline-Reloaded has dedicated intraday infrastructure
- The issue is likely in bundle configuration, not Zipline core

**Required Actions:**
- [ ] Verify `exchange_calendars` version in requirements.txt supports 24/7
- [ ] Review CRYPTO calendar definition in `.zipline/extension.py`
- [ ] Test with explicit calendar parameters in bundle registration
- [ ] Consider HDF5 storage (`hdf5_daily_bars.py`) as alternative to bcolz
- [ ] Debug the actual Timestamp error to find root cause

### 3. Calendar-Aware Minute Data Flow

**What Zipline Expects:**
- Minute bars should be validated against trading minutes, not sessions
- `BcolzMinuteBarWriter` handles calendar integration internally
- Different storage format than daily bars

**What We're Doing Wrong:**
- Using daily-style ingestion patterns for minute data
- Normalizing timestamps incorrectly for minute storage
- Calling wrong calendar methods

**Required Actions:**
- [ ] Study `src/zipline/data/bcolz_minute_bars.py` for expected data format
- [ ] Study `src/zipline/data/fx/` for how FX (24-hour) data is handled
- [ ] Align our implementation with Zipline's internal patterns

---

## Remaining Work (After Architecture Fixes)

### Medium Priority (Missing Features)

- [ ] **Implement CSV bundle ingestion**
  - Create `ingest_csv_bundle()` in `lib/data_loader.py`
  - Support single CSV and directory of CSVs
  - Configurable column mapping

- [ ] **Add bundle management CLI**
  - `scripts/manage_bundles.py list` - Show all bundles with metadata
  - `scripts/manage_bundles.py delete <name>` - Remove bundle
  - `scripts/manage_bundles.py info <name>` - Detailed bundle info
  - `scripts/manage_bundles.py validate <name>` - Check integrity

- [ ] **Test remaining timeframes**
  - 2m, 15m, 30m for equities
  - 1h, 5m for forex
  - weekly, monthly for all

### Low Priority (Nice to Have)

- [ ] Implement Binance data source
- [ ] Implement OANDA data source
- [ ] Add incremental bundle updates (append new data)
- [ ] Add post-ingestion data validation
- [ ] Add bundle versioning

---

## Known Issues Summary

| Issue | Workaround Applied | Proper Fix Needed |
|-------|-------------------|-------------------|
| Calendar session warnings for intraday | Skip filtering | Use minute-level calendar APIs |
| Crypto 5m ingestion fails | None (fails) | Investigate calendar config + minute bar writer |
| Gap-filling for intraday | Disabled | May not be needed for minute data |
| Old bundles with `end_date: "daily"` | None | Re-ingest or clean registry |

---

## Testing Commands

```bash
# Verify working timeframes
python scripts/ingest_data.py --source yahoo --assets equities --symbols SPY -t 1h
python scripts/ingest_data.py --source yahoo --assets equities --symbols AAPL -t 5m

# Test failing timeframes (needs architecture fix)
python scripts/ingest_data.py --source yahoo --assets crypto --symbols BTC-USD -t 5m

# Test untested timeframes
python scripts/ingest_data.py --source yahoo --assets equities --symbols SPY -t 15m
python scripts/ingest_data.py --source yahoo --assets forex --symbols EURUSD=X -t 1h
python scripts/ingest_data.py --source yahoo --assets equities --symbols SPY -t weekly
```

---

## Files to Investigate

For proper minute bar implementation, review:

1. `src/zipline/data/bcolz_minute_bars.py` - Minute bar writer implementation
2. `src/zipline/data/fx/` - FX data handling (24-hour markets)
3. `exchange_calendars` source - CRYPTO calendar implementation
4. `hdf5_daily_bars.py` - Alternative storage option
