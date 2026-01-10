# Ingest Data

## Overview

Ingest data from external sources (Yahoo, Binance, OANDA) into Zipline data bundles for backtesting, with validation and caching.

## Steps

1. **Configure Data Source** - Set source, assets, symbols, timeframe in config/data_sources.yaml
2. **Fetch Data** - Download data from API with caching (24-hour cache)
3. **Validate Data** - Check OHLCV integrity, gaps, timezone consistency
4. **Create Bundle** - Write to Zipline bundle format (BcolzDailyBarWriter/BcolzMinuteBarWriter)
5. **Register Bundle** - Add to bundle registry for discovery
6. **Verify Bundle** - Validate bundle can be loaded and has expected date range

## Checklist

- [ ] Data source configured in config/data_sources.yaml
- [ ] Data fetched from API (or loaded from cache)
- [ ] Data validated (OHLCV integrity, no gaps, UTC timezone)
- [ ] Bundle created in data/bundles/{bundle_name}/
- [ ] Bundle registered in bundle registry
- [ ] Bundle verified (can be loaded, date range correct)

## Execution Methods

**Script (CLI):**
```bash
# Ingest crypto data from Yahoo
python scripts/ingest_data.py --source yahoo --assets crypto

# Ingest forex data from OANDA
python scripts/ingest_data.py --source oanda --assets forex

# Ingest specific symbol
python scripts/ingest_data.py --source binance --symbol BTC-USDT --timeframe 1h

# Force refresh (bypass cache)
python scripts/ingest_data.py --source yahoo --assets crypto --force
```

**Library (Programmatic):**
```python
from lib.bundles.yahoo_bundle import ingest_yahoo_bundle

bundle_name = ingest_yahoo_bundle(
    symbols=['BTC-USD', 'ETH-USD'],
    start_date='2020-01-01',
    end_date='2023-12-31',
    timeframe='1d'
)
```

## Bundle Naming Convention

```
{source}_{asset_class}_{timeframe}
```

Examples:
- `yahoo_crypto_daily`
- `binance_btc_1h`
- `oanda_forex_1h`
- `yahoo_equities_daily`

## Data Validation

**OHLCV Integrity:**
- High >= Low
- High >= Open, High >= Close
- Low <= Open, Low <= Close
- Volume >= 0

**Timezone Normalization:**
- All timestamps normalized to UTC
- No timezone-naive datetimes

**Gap Detection:**
- Check for missing dates in expected range
- Flag gaps for manual review

## Cache Management

API responses cached for 24 hours:
```
data/cache/
├── yahoo_2024_12_18.parquet
├── binance_2024_12_20.parquet
└── ...
```

Force refresh:
```bash
python scripts/ingest_data.py --source yahoo --assets crypto --force
```

## Common Issues

**API rate limiting:**
```bash
# Error: Rate limit exceeded
# Solution: Wait and retry, or use cached data
```

**Missing data:**
```bash
# Error: No data for symbol BTC-USD
# Solution: Check symbol name, date range, data source availability
```

**Timezone errors:**
```bash
# Error: Timezone mismatch
# Solution: Data automatically normalized to UTC
```

## Notes

- Data is cached for 24 hours to avoid redundant API calls
- Bundles are validated before registration
- Use --force flag to bypass cache when needed
- Check bundle info: `python scripts/bundle_info.py --bundle yahoo_crypto_daily`
- Re-ingest if bundle structure changes: `python scripts/reingest_all.py`

## Related Commands

- run-backtest.md - For using ingested bundles in backtests
- validate-strategy.md - For validating strategies with data
