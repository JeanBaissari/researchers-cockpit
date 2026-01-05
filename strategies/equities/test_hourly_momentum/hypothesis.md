# Test Hourly Momentum Strategy

## Purpose
This is a test strategy to verify multi-timeframe data ingestion and usage.
It uses hourly (1h) data to make trading decisions.

## Hypothesis
Hourly SMA crossover can capture intraday momentum while reducing noise
compared to minute-level data.

## Entry Rules
- Buy when fast SMA crosses above slow SMA

## Exit Rules
- Sell when fast SMA crosses below slow SMA
- Stop loss at 5%

## Parameters
- Fast SMA: 5 hourly bars
- Slow SMA: 20 hourly bars

## Notes
This is a test strategy for validating the multi-timeframe data ingestion system.
The primary goal is to verify that:
1. Hourly data can be ingested with `python scripts/ingest_data.py --timeframe 1h`
2. Bundles are named correctly (yahoo_equities_1h)
3. Data limits are properly enforced
