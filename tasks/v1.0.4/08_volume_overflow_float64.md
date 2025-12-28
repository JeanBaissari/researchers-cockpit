#### 8. Volume Overflow Warning for Crypto/Large Volume Assets [PENDING]
**Warning:** `Ignoring N values because they are out of bounds for uint32`

Bitcoin and other high-volume assets exceed uint32 limits (~4.29 billion) for the volume column. Zipline's `BcolzDailyBarWriter` uses `uint32` for volume storage, which is insufficient for crypto markets where daily volumes can exceed this threshold.

**Root Cause Analysis:**
- Zipline was designed for traditional equities where uint32 volume is sufficient
- Crypto markets (especially BTC) regularly trade >10B units daily
- The warning silently drops data points, causing inaccurate volume-based indicators and position sizing calculations

**Rejected Approaches:**
1. ~~Scale volume by 1000~~ — Introduces magic numbers, loses precision, requires tracking/reversal throughout the codebase, fragile for downstream calculations
2. ~~Wait for Zipline update~~ — Passive, blocks progress on a core asset class (crypto) indefinitely
3. ~~Document limitation~~ — Does not fix the issue, compromises data integrity

**Recommended Fix: Use `float64` for Volume at Ingestion Layer**

Modify the data ingestion in `lib/data_loader.py` to convert volume to `float64` dtype before writing to the bundle. This approach:
- Handles values up to ~1.8×10^308 (effectively unlimited for any market)
- Preserves sufficient precision for volume calculations (float64 has 15-17 significant digits)
- Requires no downstream changes to strategies or analysis code
- Aligns with the "fail fast with clear errors" philosophy

**Implementation Details:**

1. **Modify `lib/data_loader.py`:**
   ```python
   def prepare_data_for_ingestion(df):
       # Convert volume to float64 to handle large crypto volumes
       # uint32 max is ~4.29B, insufficient for BTC daily volumes
       if 'volume' in df.columns:
           df['volume'] = df['volume'].astype('float64')
       return df
   ```

2. **Custom BcolzDailyBarWriter configuration (if needed):**
   - If Zipline's writer enforces uint32, create a wrapper that intercepts volume data
   - Store original float64 volume in auxiliary column or separate bundle metadata
   - Alternative: Fork the writer to accept float64 volume dtype

3. **Validation in ingestion pipeline:**
   ```python
   def validate_volume_data(df, asset_name):
       max_vol = df['volume'].max()
       if max_vol > np.iinfo(np.uint32).max:
           logger.info(f"{asset_name}: Volume exceeds uint32 ({max_vol:.2e}), using float64 storage")
       # Verify no NaN/Inf after conversion
       assert not df['volume'].isna().any(), "Volume contains NaN after conversion"
       assert not np.isinf(df['volume']).any(), "Volume contains Inf values"
   ```

4. **Alternative: Notional Volume Conversion**
   If float64 integration proves complex, convert to dollar volume (`price × volume`) during ingestion:
   - More meaningful for position sizing calculations
   - Stays within reasonable bounds for most assets
   - Store conversion factor in bundle metadata for reversibility

**Integration Points:**
- `lib/data_loader.py`: Primary fix location, modify volume dtype handling
- `config/data_sources.yaml`: Add optional `volume_dtype: float64` configuration per source
- `lib/backtest.py`: No changes needed if ingestion handles conversion
- `.agent/backtest_runner.md`: Document that crypto bundles use float64 volume

**Testing Requirements:**
- Unit test: Ingest BTC data with volume > uint32 max, verify no warnings/data loss
- Integration test: Backtest using volume-based indicators (e.g., VWAP) confirms correct values
- Regression test: Existing equity strategies produce identical results

**Success Criteria:**
- Zero `out of bounds for uint32` warnings during crypto data ingestion
- Volume-based calculations (VWAP, volume filters) return accurate values for high-volume assets
- No downstream code changes required in strategies or analysis modules