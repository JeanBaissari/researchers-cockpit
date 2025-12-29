# v1.0.6 Architectural Analysis: Multi-Timeframe Data System

**Date:** 2025-12-28
**Status:** Research Complete - Awaiting Implementation Approval

---

## Executive Summary

After deep analysis of the Zipline-Reloaded source code (`data_portal.py`, `bcolz_minute_bars.py`, `bcolz_daily_bars.py`, `resample.py`), this document provides a corrected understanding of Zipline's data architecture and a revised plan for multi-timeframe support.

**Key Discovery:** Zipline's design is fundamentally built around TWO storage frequencies (daily/minute) with on-the-fly aggregation, NOT arbitrary timeframe storage.

---

## 1. Zipline's Core Data Architecture

### 1.1 Storage Frequencies

Zipline stores data at exactly TWO granularities:

| Storage Type | Bar Writer | Data Structure | Index |
|-------------|-----------|----------------|-------|
| **Daily (Session)** | `BcolzDailyBarWriter` | One row per trading session | Session dates |
| **Minute** | `BcolzMinuteBarWriter` | Rows at minute resolution | Minute timestamps |

**Critical Constraint from `bcolz_daily_bars.py:286-305`:**
```python
if len(table) != len(asset_sessions):
    raise AssertionError(
        f"Got {len(table)} rows for daily bars table with "
        f"first day={asset_first_day.date()}, last "
        f"day={asset_last_day.date()}, expected {len(asset_sessions)} rows."
    )
```

The daily bar writer **requires exactly one row per trading session with NO GAPS**.

### 1.2 history() API Frequencies

From `data_portal.py:80`:
```python
HISTORY_FREQUENCIES = set(["1m", "1d"])
```

From `data_portal.py:891-906`:
```python
if frequency == "1d":
    # Daily history logic
elif frequency == "1m":
    # Minute history logic
else:
    raise ValueError(f"Invalid frequency: {frequency}")
```

**`data.history()` ONLY supports `'1d'` and `'1m'` frequencies.** There is no native support for 5m, 15m, 1h, 4h, weekly, or monthly.

### 1.3 Built-in Aggregation Infrastructure

From `data_portal.py:248-252`:
```python
self._daily_aggregator = DailyHistoryAggregator(
    self.trading_calendar.first_minutes,
    _dispatch_minute_reader,
    self.trading_calendar,
)
```

From `resample.py`:
- `DailyHistoryAggregator` - Converts minute data to daily on-the-fly
- `MinuteResampleSessionBarReader` - Wraps minute reader to provide session bars
- `minute_frame_to_session_frame()` - Explicit minute-to-session conversion

**Key Insight:** Zipline's architecture expects you to store data at the LOWEST frequency needed, then aggregate to higher timeframes during strategy execution.

---

## 2. Re-Evaluation of Documented "Limitations"

### 2.1 Weekly/Monthly Data

**Previous Assessment:** "NOT compatible with Zipline bundles"

**Correct Assessment:** ✅ TRUE LIMITATION - BY DESIGN

**Root Cause:**
- `BcolzDailyBarWriter` requires continuous session data
- Weekly data = 1 bar per ~5 sessions → Missing 4 sessions per bar
- Monthly data = 1 bar per ~21 sessions → Missing 20 sessions per bar
- The writer's validation `len(table) != len(asset_sessions)` fails

**Correct Architecture:**
1. Store DAILY data in bundles
2. Aggregate to weekly/monthly ON-DEMAND in strategy code
3. Use aggregation utilities from `lib/utils.py`

**Example Pattern:**
```python
def get_weekly_bars(data, asset, weeks=10):
    """Aggregate daily bars to weekly."""
    daily_bars = weeks * 5  # Approximate trading days per week
    hist = data.history(asset, ['open', 'high', 'low', 'close', 'volume'],
                        daily_bars, '1d')

    # Resample to weekly (ending Friday)
    weekly = hist.resample('W-FRI').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }).dropna()

    return weekly
```

### 2.2 4-Hour Timeframe

**Previous Assessment:** "Requires aggregation from 1h data"

**Correct Assessment:** ✅ TRUE - But simpler than assumed

**Root Cause:**
- No yfinance 4h interval exists
- Minute bars can store 1h data (bars at :00 of each hour)
- 4h is simply 4 consecutive 1h bars

**Correct Architecture:**
1. Ingest 1h data into minute bundles (already working)
2. Aggregate 4 hourly bars to 1 four-hour bar in strategy

**Example Pattern:**
```python
def get_4h_bars(data, asset, bars=10):
    """Aggregate 1h bars to 4h."""
    # Get 4x the number of hourly bars needed
    hourly_count = bars * 4
    hist = data.history(asset, ['open', 'high', 'low', 'close', 'volume'],
                        hourly_count, '1m')

    # Resample from hourly to 4-hourly
    four_hour = hist.resample('4H').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }).dropna()

    return four_hour
```

### 2.3 5m/15m/30m/1h Timeframes

**Previous Assessment:** Working for equities, issues with crypto

**Correct Assessment:** ✅ WORKING - After minutes_per_day fix

**Analysis:**
From `bcolz_minute_bars.py:67-76`:
```python
def _calc_minute_index(market_opens, minutes_per_day):
    minutes = np.zeros(len(market_opens) * minutes_per_day, dtype="datetime64[ns]")
    deltas = np.arange(0, minutes_per_day, dtype="timedelta64[m]")
    ...
```

The minute bar writer creates a fixed-size index based on `minutes_per_day`. For 5m/15m/30m/1h data:
- Data is stored at specific minute offsets (e.g., 09:30, 09:35, 09:40 for 5m)
- Intermediate positions are zeros
- Reader retrieves data at requested minute timestamps

**The Fix Applied:**
```python
CALENDAR_MINUTES_PER_DAY: Dict[str, int] = {
    'XNYS': 390,      # NYSE: 6.5 hours
    'CRYPTO': 1440,   # 24/7: 24 hours
    'FOREX': 1440,    # 24/5: 24 hours per trading day
}
```

This ensures the minute index correctly spans 24 hours for crypto/forex markets.

### 2.4 1-Minute Data

**Previous Assessment:** "Limited to 7 days"

**Correct Assessment:** ✅ DATA SOURCE LIMITATION (Not Zipline)

**Root Cause:**
- yfinance API only provides 7 days of 1m data
- This is an API limitation, NOT a Zipline limitation
- Zipline's minute bar infrastructure fully supports 1m data for any duration

**Correct Architecture:**
- For 1m data: Accept 7-day limitation from yfinance
- Alternative: Use paid data providers (Polygon, IB) for longer 1m history
- For most research purposes: Use 5m data (60 days) as minimum practical resolution

---

## 3. Timeframe Storage Matrix

| Timeframe | Storage Format | Data Source Limit | Bundle Frequency | Strategy Aggregation |
|-----------|----------------|-------------------|------------------|---------------------|
| 1m | Minute bars | 7 days (yfinance) | `minute` | None needed |
| 5m | Minute bars | 60 days | `minute` | None needed |
| 15m | Minute bars | 60 days | `minute` | None needed |
| 30m | Minute bars | 60 days | `minute` | None needed |
| 1h | Minute bars | 730 days | `minute` | None needed |
| **4h** | Minute bars (1h) | 730 days | `minute` | Resample 1h → 4h |
| daily | Daily bars | Unlimited | `daily` | None needed |
| **weekly** | Daily bars | Unlimited | `daily` | Resample daily → weekly |
| **monthly** | Daily bars | Unlimited | `daily` | Resample daily → monthly |

---

## 4. Revised Implementation Plan

### 4.1 What We Already Have (Working)

1. ✅ Daily data ingestion (all asset classes)
2. ✅ 1h minute data ingestion (all asset classes - after minutes_per_day fix)
3. ✅ 5m/15m/30m minute data ingestion (equities verified, crypto/forex should work)
4. ✅ `CALENDAR_MINUTES_PER_DAY` configuration
5. ✅ `get_minutes_per_day()` helper function

### 4.2 What Needs to Change

#### A. Remove Weekly/Monthly Ingestion Attempts

**Current Code (Incorrect):**
```python
# In scripts/ingest_data.py - Validation that rejects weekly/monthly
if timeframe in ['weekly', 'monthly']:
    raise ValueError(f"Timeframe '{timeframe}' cannot be stored in Zipline bundles...")
```

**Corrected Approach:**
- Keep the rejection message but make it more helpful
- Point users to aggregation utilities instead

#### B. Add Multi-Timeframe Aggregation Module

Create `lib/timeframe.py`:

```python
"""
Multi-Timeframe Aggregation Utilities for Zipline Strategies

Zipline's data.history() only supports '1d' and '1m' frequencies.
These utilities aggregate to higher timeframes on-demand.
"""

import pandas as pd
from typing import Union, List
from zipline.api import symbol


def aggregate_to_timeframe(df: pd.DataFrame, target_tf: str) -> pd.DataFrame:
    """
    Aggregate OHLCV DataFrame to target timeframe.

    Parameters
    ----------
    df : pd.DataFrame
        OHLCV data with DatetimeIndex
    target_tf : str
        Target timeframe: '4h', 'weekly', 'monthly'

    Returns
    -------
    pd.DataFrame
        Aggregated OHLCV data
    """
    tf_map = {
        '4h': '4H',
        '4H': '4H',
        'weekly': 'W-FRI',
        'W': 'W-FRI',
        'monthly': 'M',
        'M': 'M'
    }

    if target_tf not in tf_map:
        raise ValueError(f"Unsupported target timeframe: {target_tf}")

    return df.resample(tf_map[target_tf]).agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }).dropna()


class MultiTimeframeData:
    """
    Helper class for accessing multiple timeframe data in strategies.

    Usage in initialize():
        context.mtf = MultiTimeframeData()

    Usage in handle_data():
        weekly_close = context.mtf.get_weekly(data, asset, 'close', 10)
    """

    def get_4h(self, data, asset, field: str, bar_count: int) -> pd.Series:
        """Get 4-hour bars by aggregating hourly data."""
        # Get 4x hourly bars
        hist = data.history(asset, field, bar_count * 4, '1m')
        return hist.resample('4H').agg(self._get_agg_func(field)).dropna()

    def get_weekly(self, data, asset, field: str, bar_count: int) -> pd.Series:
        """Get weekly bars by aggregating daily data."""
        # Get ~5 daily bars per week
        hist = data.history(asset, field, bar_count * 5, '1d')
        return hist.resample('W-FRI').agg(self._get_agg_func(field)).dropna()

    def get_monthly(self, data, asset, field: str, bar_count: int) -> pd.Series:
        """Get monthly bars by aggregating daily data."""
        # Get ~21 daily bars per month
        hist = data.history(asset, field, bar_count * 21, '1d')
        return hist.resample('M').agg(self._get_agg_func(field)).dropna()

    @staticmethod
    def _get_agg_func(field: str):
        agg_map = {
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'price': 'last',
            'volume': 'sum'
        }
        return agg_map.get(field, 'last')
```

#### C. Update Documentation

Update the error message for weekly/monthly to be educational:

```python
if timeframe in ['weekly', 'monthly']:
    print(f"""
╔══════════════════════════════════════════════════════════════════════╗
║  TIMEFRAME NOTE: {timeframe} data cannot be stored in Zipline bundles     ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║  Zipline's BcolzDailyBarWriter requires one bar per trading session. ║
║  {timeframe.capitalize()} data has gaps that violate this constraint.           ║
║                                                                      ║
║  RECOMMENDED APPROACH:                                               ║
║  1. Ingest DAILY data:                                               ║
║     python scripts/ingest_data.py --source yahoo --assets equities   ║
║                                       --symbols SPY --timeframe daily║
║                                                                      ║
║  2. In your strategy, use the MultiTimeframeData helper:             ║
║                                                                      ║
║     from lib.timeframe import MultiTimeframeData                     ║
║                                                                      ║
║     def initialize(context):                                         ║
║         context.mtf = MultiTimeframeData()                           ║
║                                                                      ║
║     def handle_data(context, data):                                  ║
║         weekly_close = context.mtf.get_weekly(data, symbol('SPY'),   ║
║                                               'close', 10)           ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
""")
    sys.exit(1)
```

---

## 5. Timeframe Support Summary

| Timeframe | Storage | Strategy Access | Notes |
|-----------|---------|----------------|-------|
| 1m | ✅ Minute bundle | `data.history(asset, 'close', N, '1m')` | 7-day yfinance limit |
| 5m | ✅ Minute bundle | `data.history(asset, 'close', N, '1m')` | 60-day limit |
| 15m | ✅ Minute bundle | `data.history(asset, 'close', N, '1m')` | 60-day limit |
| 30m | ✅ Minute bundle | `data.history(asset, 'close', N, '1m')` | 60-day limit |
| 1h | ✅ Minute bundle | `data.history(asset, 'close', N, '1m')` | 730-day limit |
| 4h | ⚠️ Store 1h | `mtf.get_4h(data, asset, 'close', N)` | Aggregate in strategy |
| daily | ✅ Daily bundle | `data.history(asset, 'close', N, '1d')` | Unlimited |
| weekly | ⚠️ Store daily | `mtf.get_weekly(data, asset, 'close', N)` | Aggregate in strategy |
| monthly | ⚠️ Store daily | `mtf.get_monthly(data, asset, 'close', N)` | Aggregate in strategy |

---

## 6. Files to Create/Modify

### New Files

1. **`lib/timeframe.py`** - Multi-timeframe aggregation utilities
2. **`strategies/_template/mtf_strategy.py`** - Template showing multi-timeframe usage

### Modified Files

1. **`scripts/ingest_data.py`** - Update error messages for weekly/monthly
2. **`tasks/v1.0.6/TODO.md`** - Update with corrected understanding
3. **`lib/utils.py`** - Ensure aggregation functions are consistent with new module

---

## 7. Testing Checklist

### Ingestion Tests (Already Passing)

- [x] Daily equities: `yahoo_equities_daily`
- [x] Daily crypto: `yahoo_crypto_daily`
- [x] Daily forex: `yahoo_forex_daily`
- [x] 1h equities: `yahoo_equities_1h`
- [x] 5m crypto: `yahoo_crypto_5m`
- [x] 1h crypto: `yahoo_crypto_1h`
- [x] 1h forex: `yahoo_forex_1h`

### Aggregation Tests (To Be Added)

- [ ] 4h aggregation from 1h data
- [ ] Weekly aggregation from daily data
- [ ] Monthly aggregation from daily data
- [ ] Multi-timeframe strategy backtest

---

## 8. Conclusion

The original "limitations" were mischaracterized:

| Item | Original Assessment | Correct Assessment |
|------|--------------------|--------------------|
| Weekly/Monthly | "Limitation" | ✅ By design - aggregate in strategy |
| 4h | "Needs implementation" | ✅ Aggregate 1h in strategy |
| 1m | "7-day limit" | ✅ Data source limit, not Zipline |
| Crypto/Forex minute | "Incompatible" | ✅ Fixed with minutes_per_day |

Zipline's architecture is intentionally simple: store at daily or minute granularity, aggregate on-demand. This is more flexible than storing every possible timeframe.

---

**Next Steps:** Await user instructions before implementation.
