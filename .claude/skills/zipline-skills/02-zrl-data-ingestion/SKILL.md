---
name: zrl-data-ingestion
description: This skill should be used when ingesting market data from multiple sources (APIs, databases, files) into Zipline-Reloaded. It provides standardized patterns for data normalization, quality checks, and pipeline integration.
---

# Zipline Data Ingestion

Standardized patterns for ingesting market data from any source into Zipline-Reloaded.

## Purpose

Provide a unified interface for data ingestion from heterogeneous sources while maintaining data quality, proper formatting, and seamless integration with Zipline's data pipeline.

## When to Use

- Integrating new data sources (APIs, databases, files)
- Building automated data pipelines
- Combining multiple data sources into unified bundles
- Adding alternative data to backtests

## Data Source Adapters

### Adapter Pattern

All data sources implement a common interface:

```python
class DataSourceAdapter:
    def fetch(self, symbols: List[str], start: datetime, end: datetime) -> pd.DataFrame:
        """Fetch raw data from source."""
        raise NotImplementedError
    
    def normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize to Zipline format."""
        raise NotImplementedError
    
    def validate(self, df: pd.DataFrame) -> bool:
        """Validate data quality."""
        raise NotImplementedError
```

### Supported Sources

| Source | Adapter | Script |
|--------|---------|--------|
| Yahoo Finance | `YahooAdapter` | `scripts/adapters/yahoo_adapter.py` |
| Alpha Vantage | `AlphaVantageAdapter` | `scripts/adapters/alphavantage_adapter.py` |
| CSV Files | `CSVAdapter` | `scripts/adapters/csv_adapter.py` |
| PostgreSQL | `PostgresAdapter` | `scripts/adapters/postgres_adapter.py` |
| Parquet | `ParquetAdapter` | `scripts/adapters/parquet_adapter.py` |

## Core Workflow

### Step 1: Configure Data Source

```python
from adapters import YahooAdapter

adapter = YahooAdapter(
    rate_limit=5,  # requests per second
    retry_count=3,
    cache_dir='/path/to/cache'
)
```

### Step 2: Fetch and Normalize

```python
# Fetch raw data
raw_df = adapter.fetch(
    symbols=['AAPL', 'MSFT', 'GOOGL'],
    start=datetime(2020, 1, 1),
    end=datetime(2024, 12, 31)
)

# Normalize to Zipline format
normalized_df = adapter.normalize(raw_df)
```

### Step 3: Validate and Export

```python
# Run validation
if adapter.validate(normalized_df):
    # Export to bundle-ready format
    adapter.export(normalized_df, output_dir='/path/to/csvs')
```

## Data Normalization Rules

### Column Mapping

Standard output columns:

| Output Column | Type | Description |
|---------------|------|-------------|
| date | datetime64[ns, UTC] | Trading date |
| symbol | str | Uppercase ticker |
| open | float64 | Opening price |
| high | float64 | High price |
| low | float64 | Low price |
| close | float64 | Closing price |
| volume | int64 | Trading volume |
| adj_close | float64 | Adjusted close (optional) |
| dividend | float64 | Cash dividend (optional) |
| split | float64 | Split ratio (optional) |

### Timezone Handling

All timestamps normalized to UTC:

```python
def normalize_timezone(df: pd.DataFrame) -> pd.DataFrame:
    if df.index.tz is None:
        df.index = df.index.tz_localize('UTC')
    else:
        df.index = df.index.tz_convert('UTC')
    return df
```

### Missing Data Handling

```python
# Forward-fill prices (max 5 days gap)
df['close'] = df['close'].fillna(method='ffill', limit=5)

# Zero-fill volume
df['volume'] = df['volume'].fillna(0).astype(int)
```

## Quality Checks

Execute `scripts/data_quality.py` for comprehensive validation:

```bash
python scripts/data_quality.py /path/to/data --report quality_report.html
```

### Automated Checks

- OHLC relationship validation
- Price continuity (no jumps > 50% without corporate action)
- Volume sanity (no negative, reasonable magnitude)
- Date completeness (aligned with trading calendar)
- Duplicate detection

## Multi-Source Merging

Combine data from multiple sources with priority rules:

```python
from scripts.data_merger import DataMerger

merger = DataMerger(
    primary_source=YahooAdapter(),
    fallback_sources=[AlphaVantageAdapter(), CSVAdapter('/backup/data')],
    conflict_resolution='primary_wins'  # or 'newest', 'average'
)

merged_df = merger.merge(symbols, start, end)
```

## Caching Strategy

Implement tiered caching for efficiency:

```
Level 1: Memory cache (current session)
Level 2: Local disk cache (SQLite/Parquet)
Level 3: Remote cache (S3/GCS for teams)
```

Configure in adapter:

```python
adapter = YahooAdapter(
    cache_config={
        'enabled': True,
        'backend': 'parquet',  # or 'sqlite', 's3'
        'path': '/cache/yahoo',
        'ttl_days': 1  # re-fetch after 1 day
    }
)
```

## Script Reference

### data_quality.py

Comprehensive data quality analysis:

```bash
python scripts/data_quality.py /path/to/data \
    --calendar NYSE \
    --start 2020-01-01 \
    --end 2024-12-31 \
    --report output/quality_report.html
```

### data_merger.py

Merge multiple data sources:

```bash
python scripts/data_merger.py \
    --primary yahoo \
    --fallback csv:/path/to/backup \
    --symbols AAPL,MSFT \
    --output /merged/data
```

### incremental_update.py

Update existing bundle with new data:

```bash
python scripts/incremental_update.py \
    --bundle my-bundle \
    --source yahoo \
    --symbols AAPL,MSFT
```

## Error Handling

| Error Type | Handling | Recovery |
|------------|----------|----------|
| API Rate Limit | Exponential backoff | Retry with delay |
| Missing Symbol | Log warning | Continue with available |
| Network Timeout | Retry 3x | Use cached/fallback |
| Invalid Data | Quarantine | Manual review |

## References

See `references/source_configs.md` for API configuration templates.
See `references/quality_metrics.md` for quality threshold definitions.
