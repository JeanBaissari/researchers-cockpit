# Caching Utilities

> Cache and manage data efficiently during backtests.

## CachedObject

```python
class zipline.utils.cache.CachedObject(value, expires)
```

Simple struct for cached values with expiration.

| Parameter | Type | Description |
|-----------|------|-------------|
| `value` | object | Object to cache |
| `expires` | datetime-like | Expiration timestamp |

### unwrap()

```python
cached.unwrap(dt)
```

Get the cached value if not expired, otherwise raises `Expired`.

### Example

```python
from zipline.utils.cache import CachedObject
from pandas import Timestamp, Timedelta

expires = Timestamp('2024-01-01', tz='UTC')
obj = CachedObject(my_data, expires)

# Valid access
obj.unwrap(expires - Timedelta('1 day'))  # Returns my_data

# Expired access
obj.unwrap(expires + Timedelta('1 day'))  # Raises Expired
```

---

## ExpiringCache

```python
class zipline.utils.cache.ExpiringCache(cache=None, cleanup=None)
```

Cache of multiple CachedObjects with automatic expiration handling.

| Parameter | Type | Description |
|-----------|------|-------------|
| `cache` | dict-like | Storage backend (default: dict) |
| `cleanup` | callable | Called on expiry before deletion |

### Methods

| Method | Description |
|--------|-------------|
| `set(key, value, expires)` | Store a value |
| `get(key, dt)` | Retrieve value if valid |

### Example

```python
from zipline.utils.cache import ExpiringCache
from pandas import Timestamp, Timedelta

cache = ExpiringCache()
expires = Timestamp('2024-01-01', tz='UTC')

cache.set('my_key', expensive_computation(), expires)

# Later access
try:
    value = cache.get('my_key', current_dt)
except KeyError:
    # Expired or not found
    value = expensive_computation()
```

---

## dataframe_cache

```python
class zipline.utils.cache.dataframe_cache(
    path=None,
    lock=None,
    clean_on_failure=True,
    serialization='pickle'
)
```

Disk-backed cache for DataFrames. Can be used as context manager.

| Parameter | Type | Description |
|-----------|------|-------------|
| `path` | str | Directory for cache files |
| `lock` | Lock | Thread/process lock |
| `clean_on_failure` | bool | Delete on exception |
| `serialization` | str | 'msgpack' or 'pickle:N' |

### Usage

```python
from zipline.utils.cache import dataframe_cache

# As context manager
with dataframe_cache('/tmp/my_cache') as cache:
    cache['prices'] = prices_df
    cache['factors'] = factors_df
    
    # Access later
    prices = cache['prices']
    
    # Load all at once
    all_data = cache[:]

# Direct usage
cache = dataframe_cache('/tmp/my_cache')
cache['data'] = df
```

---

## working_file

```python
class zipline.utils.cache.working_file(final_path, *args, **kwargs)
```

Context manager for atomic file writes via temporary file.

| Parameter | Type | Description |
|-----------|------|-------------|
| `final_path` | str | Destination path |
| `*args` | | Passed to NamedTemporaryFile |
| `**kwargs` | | Passed to NamedTemporaryFile |

File is moved to `final_path` only if no exceptions occur.

### Example

```python
from zipline.utils.cache import working_file

with working_file('/data/output.csv', mode='w') as f:
    df.to_csv(f)
# File automatically moved to /data/output.csv on success
# Temp file deleted on failure
```

---

## working_dir

```python
class zipline.utils.cache.working_dir(final_path, *args, **kwargs)
```

Context manager for atomic directory creation.

| Parameter | Type | Description |
|-----------|------|-------------|
| `final_path` | str | Destination directory |

Directory is copied to `final_path` only if no exceptions occur.

### Example

```python
from zipline.utils.cache import working_dir

with working_dir('/data/bundle') as tmpdir:
    # Write files to tmpdir
    write_prices(f'{tmpdir}/prices.bcolz')
    write_assets(f'{tmpdir}/assets.db')
# Directory copied to /data/bundle on success
```

---

## Best Practices

1. **Use ExpiringCache** for session-level caching in algorithms
2. **Use dataframe_cache** for bundle ingestion intermediates
3. **Use working_file/dir** for atomic writes during data processing
4. **Set appropriate expirations** to avoid stale data

---

## See Also

- [Data Bundles](../08_data_bundles/bundles.md)
- [Pipeline Engine](../06_pipeline/pipeline_engine.md)
