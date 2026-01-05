# Data Ingestion Troubleshooting

Best practices and working features for data ingestion.

---

## Timeframe Support Matrix

### Supported Timeframes

| Timeframe | yfinance Limit | Bundle Type | Status |
|-----------|----------------|-------------|--------|
| `1m` | 7 days | minute | Working |
| `5m` | 60 days | minute | Working |
| `15m` | 60 days | minute | Working |
| `30m` | 60 days | minute | Working |
| `1h` | 730 days | minute | Working |
| `daily` | Unlimited | daily | Working |

### NOT Supported (By Design)

| Timeframe | Reason | Workaround |
|-----------|--------|------------|
| `weekly` | Zipline requires one bar per session | Use daily + aggregation |
| `monthly` | Zipline requires one bar per session | Use daily + aggregation |
| `4h` | yfinance doesn't support natively | Use 1h + aggregation |

### Using Aggregation for Unsupported Timeframes

```python
from lib.utils import aggregate_ohlcv, create_multi_timeframe_data

# Aggregate 1h to 4h
df_4h = aggregate_ohlcv(df_1h, '4h')

# Create multiple views
mtf_data = create_multi_timeframe_data(df_1h, '1h', ['4h', 'daily'])
```

---

## Calendar Selection Guide

| Asset Class | Calendar | Minutes/Day | Trading Days |
|-------------|----------|-------------|--------------|
| US Equities | `XNYS` | 390 | Mon-Fri, NYSE hours |
| Cryptocurrency | `CRYPTO` | 1440 | 24/7/365 |
| Forex | `FOREX` | 1440 | Mon-Fri, 24h |

### Auto-Detection

The system auto-selects calendars based on asset class:

```bash
# Auto-selects XNYS
python scripts/ingest_data.py --source yahoo --assets equities --symbols SPY

# Auto-selects CRYPTO
python scripts/ingest_data.py --source yahoo --assets crypto --symbols BTC-USD

# Auto-selects FOREX
python scripts/ingest_data.py --source yahoo --assets forex --symbols EURUSD=X
```

### Manual Override

```bash
python scripts/ingest_data.py --source yahoo --assets equities \
    --symbols SPY --calendar CRYPTO  # Override if needed
```

---

## Gap-Filling Behavior

### When Gaps Are Filled

The system automatically fills data gaps for:
- **FOREX**: Maximum 5 consecutive days
- **CRYPTO**: Maximum 3 consecutive days

### How Gaps Are Filled

- **OHLC prices**: Forward-filled (last known price)
- **Volume**: Set to 0 (signals synthetic bar, no real trades)

### Identifying Synthetic Bars

```python
# Synthetic bars have volume = 0
synthetic_bars = df[df['volume'] == 0]
print(f"Found {len(synthetic_bars)} synthetic bars")
```

---

## Bundle Naming Convention

Standard format: `{source}_{asset_class}_{timeframe}`

| Example | Source | Asset | Timeframe |
|---------|--------|-------|-----------|
| `yahoo_equities_daily` | yahoo | equities | daily |
| `yahoo_crypto_1h` | yahoo | crypto | 1h |
| `yahoo_forex_5m` | yahoo | forex | 5m |

### Custom Names

```bash
python scripts/ingest_data.py --source yahoo --assets equities \
    --symbols SPY,AAPL --bundle-name my_custom_bundle
```

---

## Re-Ingestion Procedures

### When to Re-Ingest

- After updating to v1.0.6 from earlier versions
- When bundle shows incorrect bar counts
- When validation reports issues

### Re-Ingest Single Bundle

```bash
python scripts/ingest_data.py --source yahoo --assets equities \
    --symbols SPY,AAPL -t 1h --force
```

### Re-Ingest Multiple Bundles

```bash
# Preview what will be re-ingested
python scripts/reingest_all.py --dry-run

# Re-ingest all hourly bundles
python scripts/reingest_all.py --timeframe 1h

# Re-ingest all crypto bundles
python scripts/reingest_all.py --assets crypto

# Re-ingest specific bundles
python scripts/reingest_all.py --bundles yahoo_equities_1h,yahoo_crypto_5m
```

---

## Data Limit Handling

### yfinance Data Limits

| Timeframe | Max Days | Notes |
|-----------|----------|-------|
| 1m | 7 | Last 7 calendar days only |
| 5m | 60 | ~2 months of data |
| 15m | 60 | ~2 months of data |
| 30m | 60 | ~2 months of data |
| 1h | 730 | ~2 years of data |
| daily | Unlimited | Full historical data |

### Auto-Adjustment

The system automatically adjusts date ranges for limited timeframes:

```bash
# Requested: 2020-01-01 to 2024-01-01 with 5m timeframe
# Actual: Last 60 days from today (data limit)
python scripts/ingest_data.py --source yahoo --assets equities \
    --symbols SPY -t 5m --start 2020-01-01 --end 2024-01-01
```

A warning is logged when dates are adjusted.

---

## Volume Handling

### Large Volume Values

Some crypto assets have volumes exceeding uint32 max (4.29 billion). The system:
1. Uses float64 for volume storage
2. Logs warnings when volume exceeds uint32 limits

### Zero Volume Days

Zero volume on trading days may indicate:
- Market holiday (legitimate)
- Synthetic gap-filled bar
- Data source issue

---

## Common Commands

### List Available Timeframes

```bash
python scripts/ingest_data.py --list-timeframes
```

### Check Bundle Contents

```bash
python scripts/bundle_info.py yahoo_equities_daily
```

### Validate All Bundles

```bash
python scripts/validate_bundles.py
```

### Force Re-Registration

```bash
python scripts/ingest_data.py --source yahoo --assets equities \
    --symbols SPY -t daily --force
```

---

## Error Messages and Solutions

### "symbols parameter is required"

**Solution:** Provide symbols list:
```bash
python scripts/ingest_data.py --source yahoo --assets equities --symbols SPY,AAPL
```

### "Timeframe 'weekly' not compatible with Zipline bundles"

**Solution:** Use daily data and aggregate in your strategy:
```python
from lib.utils import aggregate_ohlcv
df_weekly = aggregate_ohlcv(df_daily, 'weekly')
```

### "No data returned for symbol"

**Causes:**
- Symbol doesn't exist
- Symbol delisted
- yfinance rate limit

**Solution:**
1. Verify symbol exists on Yahoo Finance
2. Try again after a few minutes (rate limit)
3. Check internet connection

### "Calendar not found"

**Solution:** Ensure custom calendars are registered:
```python
from lib.extension import register_custom_calendars
register_custom_calendars(['CRYPTO', 'FOREX'])
```

---

## See Also

- [Common Issues](common_issues.md)
- [Data Loader API](../api/data_loader.md)
- [Utils API](../api/utils.md)
