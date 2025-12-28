## Plan for FOREX Data Gaps Fix

### Root Cause Analysis

FOREX markets trade Mon-Fri 24h, but Yahoo Finance has inconsistent data coverage. The FOREX calendar expects trading days that may not have corresponding data, causing ingestion failures.

### Recommended Approach: Option 1 (Gap-Filling Logic)

This aligns with the existing architecture where data ingestion is centralized in lib/data\_loader.py.

---

### Files to Modify

| File | Purpose |
| :---- | :---- |
| lib/data\_loader.py | Add gap-filling logic in data\_gen() within \_register\_yahoo\_bundle() |
| lib/extension.py | Ensure FOREX calendar is correctly defined (per PLAN\_02\_CALENDARS.md) |
| lib/utils.py | Add reusable fill\_data\_gaps() helper function |
| config/data\_sources.yaml | Add forex-specific config options (gap\_fill\_method, max\_gap\_days) |

---

### Implementation Steps

1. lib/utils.py — Add fill\_data\_gaps(df, calendar, method='ffill') that:  
* Takes a DataFrame and trading calendar  
* Reindexes to all expected calendar dates  
* Forward-fills missing OHLCV values (volume=0 for filled bars)  
1. lib/data\_loader.py — In \_register\_yahoo\_bundle():  
* Detect asset class from calendar name (FOREX)  
* After fetching Yahoo data, call fill\_data\_gaps() before yielding  
* Log warnings for filled gaps exceeding threshold  
1. lib/extension.py — Verify FOREX calendar excludes weekends (per existing PLAN\_02\_CALENDARS.md)  
1. config/data\_sources.yaml — Add under yahoo:

---

### Key Design Decisions

* Gap-filling happens at ingestion time, not runtime (consistent with bundle architecture)  
* Forward-fill preserves last known price (standard forex practice)  
* Volume set to 0 for synthetic bars (signals no real trades)  
* Configurable via data\_sources.yaml (follows existing pattern)

