# CSV Ingestion Best Practices
## Lessons from v1.0.9 Pipeline Validation

---

## Bundle Naming Convention

### Standard Format
```bash
{source}_{asset_class}_{timeframe}
# Examples:
csv_forex_1m       # Generic forex 1-minute bundle
csv_forex_1h       # Generic forex 1-hour bundle
csv_forex_daily    # Generic forex daily bundle
```

### Symbol-Specific Format
```bash
{source}_{symbol}_{timeframe}
# Examples:
csv_eurusd_1m      # EURUSD 1-minute data
csv_nzdjpy_1h      # NZDJPY 1-hour data
csv_btcusd_5m      # BTCUSD 5-minute data
```

### ✅ DO:
- Use lowercase for all bundle names
- Be consistent with timeframe suffixes
- Use symbol-specific names when bundle contains single symbol
- Re-use the same bundle name when re-ingesting (with `--force`)

### ❌ DON'T:
- Don't manually append timeframe suffix when using `--bundle-name` (script does this automatically)
- Don't create new bundle names for the same data (causes registry pollution)
- Don't use special characters or spaces in bundle names

---

## Data Frequency Matching

### Critical Rule
**Strategy data frequency MUST match bundle data frequency**

### Examples

#### ✅ CORRECT:
```yaml
# Strategy uses 1-minute bars
data.history(asset, 'price', 100, '1m')

# Bundle ingested with 1-minute data
python scripts/ingest_data.py --timeframe 1m ...
```

#### ❌ WRONG:
```yaml
# Strategy uses 1-minute bars
data.history(asset, 'price', 100, '1m')

# Bundle ingested with 1-hour data
python scripts/ingest_data.py --timeframe 1h ...  # ✗ Shape mismatch errors!
```

### Pre-Flight Check
Before running a backtest, verify:
1. What frequency does the strategy request? (check `data.history()` calls)
2. What frequency was the bundle ingested with? (check bundle registry)
3. Do they match?

---

## Ingestion Time Estimates

### CSV File Size → Ingestion Time

| Data Frequency | File Size | Approximate Rows | Ingestion Time |
|----------------|-----------|------------------|----------------|
| 1m (minute)    | 150MB     | ~2M rows         | 20-30 min      |
| 5m             | 30MB      | ~400K rows       | 5-8 min        |
| 15m            | 10MB      | ~130K rows       | 2-4 min        |
| 1h (hour)      | 2.5MB     | ~30K rows        | 1-2 min        |
| Daily          | 100KB     | ~1K rows         | < 30 sec       |

**Note:** Times assume:
- Modern CPU (4+ cores)
- SSD storage
- 8GB+ RAM
- Single symbol per bundle

### Progress Indicators
Current implementation has limited progress output during:
- Large CSV parsing (no output until complete)
- Validation phase (no output)
- Data writing phase (progress bars for bcolz writing)

**Expected behavior:** No output for several minutes during large CSV processing is normal.

---

## Calendar Selection for FOREX/CRYPTO

### FOREX Trading
```bash
# 24/5 trading (Monday 00:00 UTC to Friday 23:59 UTC)
--calendar FOREX
```

**IMPORTANT:** FOREX data requires:
- Pre-session filtering (removes Sunday late hours: 00:00-04:59 UTC)
- Sunday consolidation (merges Sunday bars into Friday)
- Gap filling (forward-fills holidays like Good Friday)

### CRYPTO Trading
```bash
# 24/7 trading (continuous)
--calendar CRYPTO
```

**IMPORTANT:** CRYPTO data requires:
- No pre-session filtering
- No weekend consolidation
- Gap filling for exchange maintenance windows

### Equity Trading
```bash
# Standard US market hours
--calendar XNYS   # NYSE
--calendar XNAS   # NASDAQ
```

---

## Common Pitfalls

### 1. Wrong Data Frequency
**Symptom:** Shape mismatch errors during backtest
```
Error: shape mismatch: value array of shape (4556,1) could not
broadcast to indexing result of shape (4560,1)
```

**Cause:** Strategy requests 1m bars but bundle has 1h data

**Fix:** Re-ingest with matching frequency or modify strategy

### 2. API Limits Applied to CSV
**Symptom:** Bundle only contains last 2 years despite having 5+ years of CSV data

**Cause:** (FIXED in v1.0.9) CSV ingestion incorrectly applied Yahoo Finance API limits

**Fix:** Already fixed in `lib/bundles/api.py:141`

### 3. Bundle Name Duplication
**Symptom:** Bundle names like `csv_eurusd_1h_1h_1h`

**Cause:** (FIXED in v1.0.9) Re-ingestion with `--bundle-name` that already had suffix

**Fix:** Already fixed in `scripts/ingest_data.py:59`

### 4. Missing Gap Filling
**Symptom:** `AssertionError: Got 383 rows, expected 384 rows. Missing sessions: [Good Friday]`

**Cause:** (FIXED in v1.0.9) Gap filling only applied to daily path, not aggregated intraday path

**Fix:** Already fixed in `lib/bundles/csv_bundle.py:475` and `yahoo_bundle.py:362`

---

## Recommended Workflow

### Step 1: Verify CSV Data
```bash
# Check file exists and has correct format
ls -lh data/processed/{timeframe}/
head -n 5 data/processed/{timeframe}/{SYMBOL}_{timeframe}_*.csv

# Expected columns: Date, Open, High, Low, Close, Volume
# Expected date format: 2020-01-02 05:00:00
```

### Step 2: Choose Correct Timeframe
```bash
# Match the strategy's data.history() calls
grep "data.history" strategies/{asset_class}/{strategy}/strategy.py

# If you see '1m' → use --timeframe 1m
# If you see '1h' → use --timeframe 1h
# If you see '1d' → use --timeframe daily
```

### Step 3: Ingest with Appropriate Settings
```bash
# Standard ingestion
python scripts/ingest_data.py \
  --source csv \
  --assets forex \
  --symbols EURUSD \
  --timeframe 1m \
  --bundle-name csv_eurusd_1m \
  --calendar FOREX \
  --force

# Notes:
# - Use --force to overwrite existing bundle
# - Bundle name should NOT include timeframe suffix (added automatically)
# - Calendar should match asset class
```

### Step 4: Verify Bundle Registry
```bash
# Check bundle was registered correctly
cat ~/.zipline/bundle_registry.json | python -m json.tool | grep -A 10 "csv_eurusd_1m"

# Verify:
# - start_date covers your desired backtest period
# - end_date is recent
# - data_frequency matches timeframe ('minute' for 1m/1h, 'daily' for daily)
# - calendar_name is correct ('FOREX', 'CRYPTO', etc.)
```

### Step 5: Update Strategy Parameters
```yaml
# strategies/{asset_class}/{strategy}/parameters.yaml
backtest:
  bundle: csv_eurusd_1m          # ← Match bundle name exactly
  data_frequency: minute         # ← Match bundle data_frequency
```

### Step 6: Run Backtest
```bash
python scripts/run_backtest.py \
  --strategy {strategy_name} \
  --asset-class {asset_class} \
  --bundle csv_eurusd_1m \
  --start 2024-01-01 \
  --end 2025-12-31
```

---

## Cleanup Commands

### Remove Old Bundles
```bash
# Remove from registry
# (Manual edit required - no automated cleanup yet)
nano ~/.zipline/bundle_registry.json

# Remove bundle data files
rm -rf ~/.zipline/data/csv_eurusd_1h_1h      # Old bundle
rm -rf ~/.zipline/data/csv_eurusd_1h_1h_1h  # Old bundle
```

### List All Bundles
```bash
# Show all registered bundles
cat ~/.zipline/bundle_registry.json | python -m json.tool | grep '"csv_' | sort

# Show bundle data directories
ls -lh ~/.zipline/data/
```

---

## Troubleshooting

### Ingestion Takes Too Long (> 30 min)
- Check CPU usage: `ps aux | grep ingest_data.py`
- If CPU < 50%: Process may be I/O bound (slow disk)
- If CPU > 90%: Normal for large CSVs, wait for completion
- Check for errors: `tail -f /tmp/claude/...output`

### No Progress Output
- Normal for large CSV parsing phase
- Output appears after validation completes
- Can take 10-20 minutes before first output for 150MB+ files

### Bundle Not Found
```bash
# Verify bundle is registered
cat ~/.zipline/bundle_registry.json | grep "{bundle_name}"

# If missing, re-ingest with --force
```

### Calendar Not Found
```bash
# Error: "InvalidCalendarName: The requested ExchangeCalendar, CSV, does not exist"
# Cause: Old bug where bundle used 'CSV' instead of actual calendar name
# Fix: Re-ingest bundle (bug fixed in v1.0.9)
```

---

## Performance Tips

### For Faster Ingestion
1. Use SSD storage for `~/.zipline/data/`
2. Ensure CSV files are on local disk (not network drive)
3. Close other applications to free RAM
4. Use smaller date ranges for testing (e.g., 1 year instead of 5)

### For Faster Backtests
1. Use higher timeframes when possible (1h instead of 1m)
2. Limit backtest date range for initial testing
3. Reduce warmup period in parameters.yaml
4. Disable verbose logging during production runs

---

## Best Practices Summary

✅ **DO:**
- Match strategy frequency to bundle frequency
- Use consistent bundle naming convention
- Re-use bundle names with `--force` flag
- Verify CSV format before ingesting
- Clean up old bundles periodically
- Document which bundles are production vs test

❌ **DON'T:**
- Mix data frequencies (1m strategy with 1h bundle)
- Create multiple bundles for same symbol/timeframe
- Forget to use --force when re-ingesting
- Assume CSV limits apply (they don't!)
- Run multiple ingestions simultaneously

---

**Last Updated:** 2026-01-15
**Version:** v1.0.9
