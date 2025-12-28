# v1.0.6 TODO: Multi-Timeframe Data Ingestion

## Status: COMPLETE

All architecture fixes have been implemented and verified.

---

## Completed This Session

### Architecture Fixes (Critical) - RESOLVED
- [x] Add `minutes_per_day` configuration for calendar types (390 for equities, 1440 for 24/7 markets)
- [x] Pass `minutes_per_day` to bundle registration via `@register()` decorator
- [x] Add `CALENDAR_MINUTES_PER_DAY` mapping in `lib/data_loader.py`
- [x] Add `get_minutes_per_day()` helper function

### Implementation
- [x] Add timeframe configuration maps (`TIMEFRAME_TO_YF_INTERVAL`, `TIMEFRAME_DATA_LIMITS`)
- [x] Add `--timeframe` CLI option to `scripts/ingest_data.py`
- [x] Add `--list-timeframes` CLI option
- [x] Update bundle naming convention to `{source}_{asset}_{timeframe}`
- [x] Add date validation with auto-adjustment for limited timeframes
- [x] Fix `end_date` registry bug (was storing timeframe string instead of date)
- [x] Add data aggregation utilities to `lib/utils.py`
- [x] Update `config/settings.yaml` with timeframe configuration
- [x] Create test strategy `strategies/equities/test_hourly_momentum/`
- [x] Add validation to reject weekly/monthly with clear error message

### Testing - VERIFIED
- [x] SPY daily, 1h, 15m, 30m (equities)
- [x] AAPL 5m (equities)
- [x] BTC-USD 5m, 1h (crypto) - **NOW WORKING after minutes_per_day fix**
- [x] EURUSD=X 1h (forex)
- [x] Weekly/monthly correctly rejected with helpful error message

---

## Supported Timeframes (Final)

| Timeframe | Zipline Compatible | Data Source | Max History |
|-----------|-------------------|-------------|-------------|
| 1m | Yes (minute) | yfinance | 7 days |
| 5m | Yes (minute) | yfinance | 60 days |
| 15m | Yes (minute) | yfinance | 60 days |
| 30m | Yes (minute) | yfinance | 60 days |
| 1h | Yes (minute) | yfinance | 730 days |
| 4h | Needs aggregation | From 1h | 60 days |
| daily | Yes (daily) | yfinance | Unlimited |
| **weekly** | **NO** | Use aggregation | N/A |
| **monthly** | **NO** | Use aggregation | N/A |

**Note:** Weekly/monthly data cannot be stored in Zipline bundles. Zipline's daily bar writer expects data for EVERY trading session. For weekly/monthly data, use `lib/utils.py` aggregation functions (`aggregate_ohlcv`, `resample_to_timeframe`) to create views from daily data.

---

## Verified Working Combinations

| Asset Class | 5m | 15m | 30m | 1h | daily |
|-------------|-----|-----|-----|-----|-------|
| Equities | ✅ | ✅ | ✅ | ✅ | ✅ |
| Crypto | ✅ | ⚠️ | ⚠️ | ✅ | ✅ |
| Forex | ⚠️ | ⚠️ | ⚠️ | ✅ | ✅ |

✅ = Explicitly tested and verified
⚠️ = Not explicitly tested but uses same configuration (should work)

---

## Key Technical Details

### Root Cause of Crypto/Forex Minute Bar Issue
The issue was that Zipline's `BcolzMinuteBarWriter` needs `minutes_per_day` to build its minute index correctly:
- **Equities (XNYS)**: 390 minutes/day (9:30 AM - 4:00 PM)
- **Crypto/Forex**: 1440 minutes/day (24 hours)

Without the correct `minutes_per_day`, the minute bar writer's index didn't include weekend timestamps, causing the ingestion to fail.

### Fix Applied
```python
# In lib/data_loader.py
CALENDAR_MINUTES_PER_DAY: Dict[str, int] = {
    'XNYS': 390,      # NYSE: 6.5 hours = 390 minutes
    'XNAS': 390,      # NASDAQ: Same as NYSE
    'CRYPTO': 1440,   # Crypto: 24/7 = 1440 minutes
    'FOREX': 1440,    # Forex: 24/5 (24 hours per day)
}

# Pass to bundle registration
@register(bundle_name, calendar_name=calendar_name, minutes_per_day=mpd)
```

### Previous Workarounds - NOW OBSOLETE
The previous session applied workarounds to:
1. Skip calendar session filtering for intraday data
2. Skip gap-filling for intraday data

These were NOT workarounds - they are **correct behavior**. Calendar session filtering and gap-filling are designed for daily data only. Intraday data has different semantics (minute timestamps vs session dates).

---

## Remaining Work (Future Versions)

### Medium Priority
- [ ] Implement 4h timeframe via aggregation from 1h data
- [ ] Implement CSV bundle ingestion
- [ ] Add bundle management CLI (`list`, `delete`, `info`, `validate`)

### Low Priority
- [ ] Implement Binance data source
- [ ] Implement OANDA data source
- [ ] Add incremental bundle updates (append new data)
- [ ] Add post-ingestion data validation
- [ ] Add bundle versioning

---

## Testing Commands

```bash
# Daily data (all asset classes)
python scripts/ingest_data.py --source yahoo --assets equities --symbols SPY
python scripts/ingest_data.py --source yahoo --assets crypto --symbols BTC-USD
python scripts/ingest_data.py --source yahoo --assets forex --symbols EURUSD=X

# Intraday data
python scripts/ingest_data.py --source yahoo --assets equities --symbols SPY -t 5m
python scripts/ingest_data.py --source yahoo --assets equities --symbols SPY -t 15m
python scripts/ingest_data.py --source yahoo --assets equities --symbols SPY -t 30m
python scripts/ingest_data.py --source yahoo --assets equities --symbols SPY -t 1h
python scripts/ingest_data.py --source yahoo --assets crypto --symbols BTC-USD -t 5m
python scripts/ingest_data.py --source yahoo --assets crypto --symbols BTC-USD -t 1h
python scripts/ingest_data.py --source yahoo --assets forex --symbols EURUSD=X -t 1h

# Weekly/monthly will show helpful error (expected)
python scripts/ingest_data.py --source yahoo --assets equities --symbols SPY -t weekly
```

---

**End of TODO Document**
