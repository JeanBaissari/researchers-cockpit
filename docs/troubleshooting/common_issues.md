# Common Issues (Solved in v1.0.6)

This guide documents issues that were identified and **solved** in v1.0.6. Understanding these helps prevent similar problems and explains the system's design decisions.

---

## 1. Minute Backtest NaT Error (SOLVED)

### Error Message
```
'NaTType' object has no attribute 'normalize'
```

### Root Cause
Intraday bundles (1m, 5m, 1h, etc.) were only writing minute bars, leaving the daily bar reader empty with NaT sentinel values.

### How v1.0.6 Fixed It
The `ingest_bundle()` function now automatically generates **both minute AND daily bars** for intraday timeframes:
- Minute bars: Written to `BcolzMinuteBarWriter`
- Daily bars: Aggregated from minute data and written to `BcolzDailyBarWriter`

### Best Practice
- Always use v1.0.6+ for intraday data ingestion
- If you have old bundles, re-ingest them:

```bash
python scripts/reingest_all.py --timeframe 1h
```

---

## 2. FOREX Session Handling (SOLVED)

### Issue
FOREX 1h ingestion failed or produced misaligned data with pre-session bars.

### Root Cause
FOREX sessions open at 05:00 UTC (midnight America/New_York). yfinance returns bars at 00:00-04:59 UTC labeled with "today" but belonging to the previous session.

### How v1.0.6 Fixed It
1. **Pre-session bar filtering**: Bars at 00:00-04:59 UTC are filtered before writing
2. **Auto-exclude current day**: For FOREX minute data, `end_date` is automatically set to yesterday

### Best Practice
- Let the system handle FOREX sessions automatically
- Use `--end` flag only if you need a specific historical end date
- FOREX daily data is unaffected by this issue

---

## 3. 24/7 Calendar Support (VERIFIED WORKING)

### Issue
Minute bar ingestion failed for crypto bundles with 24/7 calendars.

### Root Cause
`BcolzMinuteBarWriter` creates a minute index based on `minutes_per_day`. Without the correct value (1440 for 24/7 markets), the index didn't span the full 24 hours.

### How v1.0.6 Fixed It
Bundle registration now passes `minutes_per_day=1440` for CRYPTO and FOREX calendars:

```python
CALENDAR_MINUTES_PER_DAY = {
    'XNYS': 390,    # NYSE: 9:30 AM - 4:00 PM
    'CRYPTO': 1440, # 24/7 markets
    'FOREX': 1440,  # 24h Mon-Fri
}
```

### Verification
Use `bundle_info.py` to verify correct bar counts:

```bash
python scripts/bundle_info.py yahoo_crypto_1h --verbose
```

### Best Practice
- Use `CRYPTO` calendar for 24/7 assets
- Use `FOREX` calendar for Mon-Fri 24h assets
- Use `XNYS` for standard US equities

---

## 4. Bundle Registry Integrity (SOLVED)

### Issue
Corrupted metadata fields in `~/.zipline/bundle_registry.json`:
- `end_date: "daily"` instead of valid date
- Missing required fields

### Root Cause
Historical bug where timeframe values were incorrectly written to date fields.

### How v1.0.6 Fixed It
- Fixed `_register_bundle_metadata()` to properly validate and store dates
- Created `validate_bundles.py` script for ongoing registry validation

### Detection and Repair
```bash
# Check for issues
python scripts/validate_bundles.py

# Auto-repair
python scripts/validate_bundles.py --fix
```

### Best Practice
- Run validation after bulk ingestion operations
- The system now validates automatically during ingestion

---

## 5. Data Frequency Auto-Detection (WORKING)

### Issue
Backtest defaulted to 'daily' frequency regardless of bundle type.

### How v1.0.6 Fixed It
The backtest runner now auto-detects data frequency from bundle registry metadata when `--data-frequency` is not specified.

### Manual Override
If needed, you can still specify explicitly:

```bash
python scripts/run_backtest.py --strategy my_strategy \
    --bundle yahoo_equities_1h \
    --data-frequency minute
```

### Best Practice
- Let auto-detection work unless testing specific scenarios
- Bundle registry stores `data_frequency` field for each bundle

---

## 6. Strategy Symbol Validation (WORKING)

### Issue
Cryptic Zipline errors when strategy referenced symbols not present in bundle.

### How v1.0.6 Fixed It
Pre-backtest validation now checks that `strategy.asset_symbol` from `parameters.yaml` exists in the bundle:

```python
validate_strategy_symbols('spy_sma_cross', 'yahoo_equities_daily')
# Raises ValueError if SPY not in bundle
```

### Error Message (Clear)
```
Strategy 'spy_sma_cross' requires symbol 'SPY' but bundle 'yahoo_crypto_daily'
contains: [BTC-USD, ETH-USD].
Either re-ingest the bundle with the correct symbol:
  python scripts/ingest_data.py --source yahoo --symbols SPY --bundle-name yahoo_crypto_daily
Or update the strategy's parameters.yaml to use an available symbol.
```

### Verification
Check bundle symbols before running:

```bash
python scripts/bundle_info.py yahoo_equities_daily
```

---

## Quick Diagnostic Commands

```bash
# List all bundles with status
python scripts/bundle_info.py --list

# Check specific bundle health
python scripts/bundle_info.py yahoo_equities_1h --verbose

# Validate all bundles
python scripts/validate_bundles.py

# Re-ingest problematic bundles
python scripts/reingest_all.py --dry-run  # Preview first
python scripts/reingest_all.py            # Then execute

# Run tests to verify system health
python -m pytest tests/test_multi_timeframe.py -v
```

---

## Version History

| Version | Key Fixes |
|---------|-----------|
| v1.0.6 | Multi-timeframe support, NaT fix, FOREX filtering, 24/7 calendar |
| v1.0.5 | Path resolution, timezone handling, bundle registry |
| v1.0.4 | Metrics calculation edge cases |
| v1.0.3 | UTC standardization, custom calendars |

---

## See Also

- [Data Ingestion Troubleshooting](data_ingestion.md)
- [Backtesting Troubleshooting](backtesting.md)
- [Auto-Repair Removal](auto_repair_removal.md) - Understanding validation behavior changes
- [API Reference](../api/README.md)
