# Critical Validation Tests

## Test 1: End-to-End Workflow

- Complete journey for one strategy

1. Create strategy from template
2. Write hypothesis
3. Configure parameters
4. Ingest data
5. Run backtest
6. Analyze results
7. Optimize parameters
8. Walk-forward validate
9. Generate report
10. Update catalog

Verify all steps complete without errors

## Test 2: Error Handling

- Test graceful failures:

1. Missing strategy → Clear error message
2. Missing bundle → Suggests ingestion command
3. Invalid parameters → Validation error
4. Insufficient data → Handles gracefully
5. Broken symlink → Auto-fixes or warns
6. Invalid date ranges → Clear validation error
7. Malformed YAML → Syntax error with line number
8. Missing required fields → Specific field error

## Test 3: Data Integrity

- Verify data consistency:

1. Bundle dates match requested range
2. Returns calculated correctly
3. Positions match transactions
4. Metrics match manual calculations
5. Plots reflect data accurately
6. OHLCV data has no gaps or anomalies
7. Volume data is non-negative
8. Price data is within reasonable bounds
9. Dividends/splits applied correctly

## Test 4: Multi-Strategy Workflow

- Test parallel strategy development:

1. Create 3 different strategies
2. Run backtests for all
3. Compare results
4. Generate comparison report
5. Verify no conflicts
6. Test concurrent execution safety
7. Verify isolated state management

## Test 5: Edge Cases

- Test boundary conditions:

1. Very short backtest (1 month)
2. Very long backtest (10 years)
3. Single trade strategy
4. No trades strategy
5. Extreme parameters
6. Missing data periods
7. Market close/open edge times
8. Leap year handling
9. Daylight saving time transitions

## Test 6: Calendar Compatibility

- Verify calendar-specific behavior and scheduling:

### CRYPTO Calendar (24/7 Continuous Trading)
1. No market open/close concept - verify scheduling behavior
2. `time_rules.market_open()` handling (should fail or use alternative)
3. Continuous data access without gaps
4. No holiday observance validation
5. UTC timezone consistency
6. Minute-level data across all hours (00:00-23:59)
7. Rebalance scheduling alternatives (fixed time vs market_open)

### FOREX Calendar (24/5 Weekdays)
1. Sunday 17:00 EST open edge case
2. Friday 17:00 EST close edge case
3. Weekend closure handling (Sat-Sun gap)
4. America/New_York timezone alignment
5. Cross-week data continuity
6. Holiday observance (major banking holidays)
7. Scheduling during Sunday evening open

### Standard Equity Calendars
1. Exchange-specific open/close times (NYSE, NASDAQ, LSE, etc.)
2. Holiday calendar accuracy per exchange
3. Early close handling (half-days)
4. Timezone per exchange (EST, GMT, JST, etc.)
5. Market hours validation

### Cross-Calendar Validations
1. Data bundle calendar compatibility (ingest vs strategy calendar mismatch)
2. Timezone normalization across calendars (UTC, EST, local)
3. Date alignment when comparing strategies across calendars
4. Pipeline execution timing per calendar type
5. Benchmark selection per calendar (SPY for equity, BTC for crypto)
6. Strategy portability across calendar types

### Scheduling Robustness
1. `date_rules.every_day()` behavior on 24/7 vs 24/5 vs equity calendars
2. `time_rules.market_open(minutes=X)` on calendars without "open" concept
3. Weekly/monthly rebalancing across different calendar types
4. Risk check scheduling (stop-loss) on continuous markets

## Test 7: Data Frequency Handling

- Test minute vs daily data with calendar awareness:

1. Minute data ingestion and access per calendar type
2. Daily data ingestion and access per calendar type
3. Mixed frequency strategies (minute signals, daily execution)
4. Resampling operations (minute→daily, daily→weekly)
5. **[CRITICAL FIX NEEDED]** Time-of-day normalization is HARDCODED (09:30 for minute, 00:00 for daily) - must be calendar-aware:
   - CRYPTO: No "market open" - use 00:00 UTC or configurable time
   - FOREX: Use 17:00 EST (Sunday open) or configurable time
   - EQUITY: Use exchange-specific open time (09:30 EST for US, 08:00 GMT for LSE, etc.)
   - **Action Required**: Refactor `lib/backtest.py` line 133 to use calendar-specific normalization
6. Intraday vs EOD signal generation per calendar
7. Performance impact of frequency choice (minute data on 24/7 calendar = massive dataset)
8. Data alignment at different frequencies across calendars
9. Minute-level data quality on 24/7 markets (no gaps, continuous)
10. Frequency-calendar compatibility matrix validation

## Test 8: Commission & Slippage Models

- Verify cost modeling accuracy:

1. Per-share commission calculation
2. Minimum commission enforcement
3. Volume-based slippage impact
4. Price impact modeling
5. Round-trip cost accuracy
6. High-frequency vs low-frequency costs
7. Custom commission models
8. Zero-cost baseline comparison

## Test 9: Risk Management

- Test risk controls:

1. Stop-loss execution timing
2. Position sizing constraints
3. Maximum drawdown limits
4. Leverage constraints
5. Portfolio heat checks
6. Correlation-based limits
7. Volatility-adjusted sizing
8. Emergency liquidation scenarios

## Test 10: Pipeline Integration

- Verify Pipeline API usage:

1. Custom factors computation
2. Universe selection logic
3. Data alignment in pipeline
4. Factor combination operations
5. Pipeline output to strategy flow
6. Performance of complex pipelines
7. Memory efficiency with large universes
8. Pipeline caching behavior

## Test 11: Parameter Optimization

- Test optimization framework:

1. Grid search execution
2. Random search sampling
3. Bayesian optimization convergence
4. Walk-forward window splitting
5. In-sample vs out-of-sample metrics
6. Overfitting detection
7. Parameter stability analysis
8. Multi-objective optimization
9. Parallel optimization runs

## Test 12: Bundle Management

- Verify data bundle operations:

1. Bundle ingestion from CSV
2. Bundle ingestion from API
3. Bundle update/append operations
4. Bundle deletion and cleanup
5. Bundle metadata accuracy
6. Multiple bundle coexistence
7. Bundle version control
8. Corrupted bundle recovery

## Test 13: Performance Metrics

- Validate metric calculations:

1. Sharpe ratio accuracy
2. Sortino ratio calculation
3. Maximum drawdown detection
4. Calmar ratio computation
5. Win rate and profit factor
6. Alpha and beta calculation
7. Information ratio
8. Custom metric integration
9. Benchmark-relative metrics

## Test 14: State Persistence

- Test strategy state management:

1. Context variable persistence
2. State across rebalance calls
3. Historical state tracking
4. State serialization/deserialization
5. Recovery from interruption
6. State isolation between strategies
7. Memory leak prevention

## Test 15: Reporting & Visualization

- Verify output quality:

1. Tearsheet generation completeness
2. Plot accuracy and clarity
3. HTML report formatting
4. PDF export functionality
5. Interactive plot responsiveness
6. Multi-strategy comparison charts
7. Custom plot integration
8. Export to external tools (Excel, etc.)

## Test 16: Asset Class Specifics

- Test asset-specific behavior:

1. Equity-specific features
2. Crypto 24/7 trading logic
3. Forex 24/5 trading logic
4. Futures contract rolling
5. Options expiration handling
6. Currency pair conventions
7. Asset class isolation in multi-asset portfolios

## Test 17: Execution Simulation

- Verify order execution realism:

1. Market order fills
2. Limit order logic
3. Stop order triggers
4. Order rejection scenarios
5. Partial fills handling
6. Order cancellation
7. After-hours execution (crypto/forex)
8. Liquidity constraints

## Test 18: Configuration Management

- Test settings and parameters:

1. YAML parameter loading
2. Environment variable override
3. Default value fallbacks
4. Parameter validation rules
5. Config file inheritance
6. Strategy-specific vs global settings
7. Runtime parameter updates
8. Config versioning

## Test 19: Logging & Debugging

- Verify observability:

1. Log level configuration
2. Strategy execution logging
3. Error stack traces
4. Performance profiling
5. Debug mode verbosity
6. Log file rotation
7. Structured logging format
8. Integration with monitoring tools

## Test 20: Regression Testing

- Prevent breaking changes:

1. Known-good strategy reproduction
2. Metric consistency over versions
3. API backward compatibility
4. Data format stability
5. Performance regression detection
6. Output format consistency
7. Dependency version compatibility
8. Migration path validation
