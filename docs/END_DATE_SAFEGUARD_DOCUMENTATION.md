# End Date Safeguard Documentation
## Professional Implementation for Production Trading Systems

**Date:** 2026-01-15
**Version:** v1.0.9+
**Status:** ✅ Implemented & Tested

---

## Overview

The data ingestion pipeline implements an intelligent **end date safeguard** that prevents incomplete session data from contaminating production bundles. This safeguard applies **only to live API sources** and explicitly excludes pre-validated CSV data.

---

## The Problem

### FOREX Market Characteristics
- **24/5 Trading**: FOREX markets trade continuously from Monday 00:00 UTC to Friday 23:59 UTC
- **Session Boundaries**: FOREX sessions span midnight UTC (05:00 UTC to 04:58 UTC next day)
- **Incomplete Data Risk**: Current-day data from live APIs may include:
  - Partial trading sessions
  - Missing bars at session boundaries
  - Incomplete volume/pricing data
  - Timezone alignment issues

### Impact on Backtests
Incomplete current-day data can cause:
- Indexing errors (shape mismatches)
- Incorrect session counts
- Calendar alignment failures
- Look-ahead bias (if data gets updated after initial ingestion)

---

## The Solution

### Intelligent Source-Based Safeguard

```python
# lib/bundles/api.py lines 165-176

# === AUTO-EXCLUDE CURRENT DAY FOR FOREX INTRADAY (API SOURCES ONLY) ===
if calendar_name == 'FOREX' and data_frequency == 'minute' and end_date is None and source != 'csv':
    yesterday = (datetime.now().date() - timedelta(days=1)).isoformat()
    logger.info(
        f"FOREX intraday (API source): Auto-excluding current day. "
        f"Setting end_date to {yesterday} to avoid incomplete session data."
    )
    print(f"Note: FOREX intraday API data excludes current day (end_date set to {yesterday})")
    end_date = yesterday
```

### Key Design Decisions

#### 1. Source-Specific Behavior

| Source Type | Behavior | Rationale |
|-------------|----------|-----------|
| **API (Yahoo, Binance, etc.)** | Exclude current day | Live data may be incomplete |
| **CSV (local files)** | Use actual file end date | Pre-validated, complete data |

#### 2. Condition Logic

The safeguard triggers **only when ALL conditions are met**:

```python
calendar_name == 'FOREX'      # FOREX markets only
and data_frequency == 'minute' # Intraday data only
and end_date is None           # User didn't specify end_date
and source != 'csv'            # NOT a local CSV file
```

#### 3. User Override

Professional traders can **override** the safeguard by explicitly providing `--end-date`:

```bash
# Safeguard applies (end_date=None)
python scripts/ingest_data.py --source yahoo --assets forex --symbols EURUSD --timeframe 1h

# Safeguard bypassed (explicit end_date)
python scripts/ingest_data.py --source yahoo --assets forex --symbols EURUSD --timeframe 1h --end-date 2026-01-15
```

---

## Examples

### Example 1: Yahoo API Ingestion (Safeguard Active)

```bash
$ python scripts/ingest_data.py \
    --source yahoo \
    --assets forex \
    --symbols EURUSD \
    --timeframe 1h \
    --calendar FOREX

# Output:
# Note: FOREX intraday API data excludes current day (end_date set to 2026-01-14)
# Ingesting 1h data from yahoo for 1 symbols...
```

**Result:** Bundle ends at 2026-01-14 (yesterday), ensuring complete sessions

---

### Example 2: CSV Ingestion (Safeguard Inactive)

```bash
$ python scripts/ingest_data.py \
    --source csv \
    --assets forex \
    --symbols EURUSD \
    --timeframe 1m \
    --calendar FOREX

# Output:
# Ingesting 1m data from csv for 1 symbols...
# (No safeguard message - uses actual CSV end date)
```

**Result:** Bundle ends at actual CSV file's last date (e.g., 2025-07-17)

---

### Example 3: User Override (Safeguard Bypassed)

```bash
$ python scripts/ingest_data.py \
    --source yahoo \
    --assets forex \
    --symbols EURUSD \
    --timeframe 1h \
    --calendar FOREX \
    --end-date 2026-01-15

# Output:
# Ingesting 1h data from yahoo for 1 symbols...
# (No safeguard message - user specified end_date)
```

**Result:** Bundle ends at 2026-01-15 (user-specified, may include incomplete data)

---

## Behavior Matrix

| Scenario | Calendar | Frequency | Source | end_date Param | Safeguard Active? | Final end_date |
|----------|----------|-----------|--------|----------------|-------------------|----------------|
| API Intraday FOREX | FOREX | minute | yahoo | None | ✅ YES | Yesterday |
| CSV Intraday FOREX | FOREX | minute | csv | None | ❌ NO | CSV file's actual date |
| API Daily FOREX | FOREX | daily | yahoo | None | ❌ NO | Today or user-specified |
| API Intraday Crypto | CRYPTO | minute | binance | None | ❌ NO | Today or user-specified |
| API Intraday FOREX (override) | FOREX | minute | yahoo | 2026-01-15 | ❌ NO | 2026-01-15 (user override) |

---

## Professional Use Cases

### For Backtesting (Recommended)
```bash
# Use CSV data with actual end dates for maximum historical coverage
python scripts/ingest_data.py \
    --source csv \
    --assets forex \
    --symbols EURUSD,GBPUSD,USDJPY \
    --timeframe 1m \
    --calendar FOREX
```

### For Live Trading Preparation
```bash
# Use API data, let safeguard exclude incomplete current day
python scripts/ingest_data.py \
    --source yahoo \
    --assets forex \
    --symbols EURUSD \
    --timeframe 1h \
    --calendar FOREX
```

### For Advanced Users (Custom Date Range)
```bash
# Explicitly specify date range, bypassing safeguard
python scripts/ingest_data.py \
    --source yahoo \
    --assets forex \
    --symbols EURUSD \
    --timeframe 1h \
    --calendar FOREX \
    --start-date 2024-01-01 \
    --end-date 2025-12-31
```

---

## Testing & Validation

### Verification Steps

1. **Check Bundle Registry:**
```bash
cat ~/.zipline/bundle_registry.json | python -m json.tool | grep -A 5 "csv_eurusd_1m"
```

Expected for CSV:
```json
"end_date": "2025-07-17"  // Actual CSV file date
```

Expected for API (no override):
```json
"end_date": "2026-01-14"  // Yesterday (safeguard active)
```

2. **Check Ingestion Logs:**
```bash
# CSV ingestion - should NOT see safeguard message
python scripts/ingest_data.py --source csv --assets forex --symbols EURUSD --timeframe 1m

# API ingestion - should see safeguard message
python scripts/ingest_data.py --source yahoo --assets forex --symbols EURUSD --timeframe 1h
```

---

## Migration Notes

### For Existing Deployments

**Before v1.0.9:**
- Safeguard applied to ALL sources (incorrect)
- CSV bundles had end_date = yesterday (data loss)

**After v1.0.9:**
- Safeguard applies ONLY to API sources (correct)
- CSV bundles use actual file end dates (correct)

### Re-ingestion Required

If you have existing bundles ingested before this fix:

```bash
# Re-ingest CSV bundles to get correct end dates
python scripts/ingest_data.py --source csv --assets forex --symbols EURUSD --timeframe 1m --force

# Check registry to confirm correct end_date
cat ~/.zipline/bundle_registry.json | python -m json.tool
```

---

## Code Review Checklist

- [x] Safeguard only applies to API sources
- [x] CSV sources use actual file end dates
- [x] User can override via `--end-date` parameter
- [x] Clear logging explains behavior
- [x] Backward compatible (doesn't break existing API ingestion)
- [x] Well-documented in code comments
- [x] Professional trader use cases covered

---

## Related Issues

**Issue #11:** CSV End Date Override
- **Fixed:** 2026-01-15
- **Files Changed:** `lib/bundles/api.py:169`
- **Impact:** Critical - prevents data loss in CSV bundles

---

## References

- FOREX Market Hours: Monday 00:00 UTC - Friday 23:59 UTC
- Session Boundaries: 05:00 UTC to 04:58 UTC next day
- Calendar Implementation: `lib/calendars/forex.py`
- Gap Filling Logic: `lib/data/filters.py`

---

**Maintained by:** Researchers Cockpit Team
**Last Updated:** 2026-01-15
**Review Cycle:** Quarterly or when calendar logic changes
