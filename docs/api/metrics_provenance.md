# Metrics Provenance: Zipline-Reloaded vs lib/metrics/

> Clear mapping of which metrics come from Zipline-Reloaded (performance DataFrame / metrics tracker) and which are calculated by the project's `lib/metrics/` package.

**Source:** [stefan-jansen/zipline-reloaded](https://github.com/stefan-jansen/zipline-reloaded)  
**Version:** Zipline-Reloaded v3.0+  
**Last Updated:** 2026-01-28

---

## Table of Contents

1. [Overview](#overview)
2. [Provenance Summary](#provenance-summary)
3. [Zipline-Reloaded Metrics](#zipline-reloaded-metrics)
4. [lib/metrics/ Metrics](#libmetrics-metrics)
5. [Overlapping Metrics (Same Name, Different Source)](#overlapping-metrics-same-name-different-source)
6. [Data Flow and When Each Is Used](#data-flow-and-when-each-is-used)
7. [Recommendations](#recommendations)
8. [References](#references)

---

## Overview

In The Researcher's Cockpit, performance numbers can come from two places:

| Source | What It Provides | When It Is Produced |
|--------|------------------|----------------------|
| **Zipline-Reloaded** | Time-series columns in the Performance DataFrame returned by `run_algorithm()`; some risk columns from the metrics tracker | During backtest execution (per bar/session) |
| **lib/metrics/** | Single-value metrics (and rolling/trade metrics) from returns and transactions | After the backtest, when you call `calculate_metrics()`, `calculate_trade_metrics()`, etc. |

**Provenance** here means: for any given metric name (e.g. `sharpe`, `max_drawdown`), whether it is **Zipline-native** (column in `perf`), **lib/metrics/** (from our package), or **both** (same name, different semantics).

---

## Provenance Summary

| Metric / Concept | Zipline-Reloaded | lib/metrics/ | Notes |
|------------------|------------------|--------------|--------|
| **Returns & portfolio** | | | |
| `returns` | ✅ Column (period return) | ❌ Input only | Zipline: `perf['returns']`; lib/metrics uses it as input |
| `portfolio_value` | ✅ Column | ❌ Reconstructed if missing | Zipline: `perf['portfolio_value']`; we can rebuild from transactions |
| `benchmark_period_return` | ✅ Column | ❌ Input only | Zipline: benchmark return per period; lib/metrics uses as `benchmark_returns` |
| **Risk ratios (same name)** | | | |
| `sharpe` | ✅ Column (rolling) | ✅ Full-period | See [Overlapping metrics](#overlapping-metrics-same-name-different-source) |
| `sortino` | ✅ Column (rolling) | ✅ Full-period | Same |
| `max_drawdown` | ✅ Column (rolling) | ✅ Full-period | Same |
| `max_drawdown_duration` | ✅ Column | ✅ Full-period | Same |
| `recovery_time` | ✅ Column | ✅ Full-period (as days) | Same |
| **Benchmark-relative** | | | |
| `alpha` | ✅ Column | ✅ Full-period | Zipline: end-of-sim or rolling; lib/metrics: from returns + benchmark |
| `beta` | ✅ Column | ✅ Full-period | Same |
| **Portfolio/positions/transactions** | | | |
| `positions`, `transactions`, `orders` | ✅ Columns (raw) | ❌ Consumed only | We extract/flatten for CSV and for trade metrics |
| `gross_leverage`, `net_leverage` | ✅ Columns | ❌ | Zipline only |
| **Trade-level** | | | |
| `trade_count`, `win_rate`, `profit_factor`, etc. | ❌ | ✅ | lib/metrics only (from transactions) |
| **Other risk/performance** | | | |
| `calmar`, `omega`, `tail_ratio` | ❌ | ✅ | lib/metrics only |
| Rolling metrics (e.g. rolling Sharpe) | ❌ | ✅ `calculate_rolling_metrics()` | lib/metrics only |
| Custom series (e.g. `record(rsi=…)`) | ✅ Columns | ❌ | Zipline `record()` only |

---

## Zipline-Reloaded Metrics

These are produced **by Zipline-Reloaded** during `run_algorithm()` and appear as columns in the Performance DataFrame (`perf`).

### Produced by Zipline (columns in `perf`)

- **Portfolio / cash:** `portfolio_value`, `starting_value`, `ending_value`, `starting_cash`, `ending_cash`, `pnl`, `returns`, `capital_used`
- **Positions:** `positions`, `gross_leverage`, `net_leverage`, `long_value`, `short_value`, `long_exposure`, `short_exposure`
- **Transactions / orders:** `orders`, `transactions`
- **Benchmark / risk (when metrics set includes them):** `benchmark_period_return`, `algorithm_period_return`, `alpha`, `beta`, `sharpe`, `sortino`, `max_drawdown`, `max_drawdown_duration`, `recovery_time`
- **Other:** `period_label`, `period_close`, `period_open`, `capital_base`, `max_leverage`, `trading_days`, and any series passed to `record()` (e.g. custom indicators)

### Semantics

- **Risk columns (`sharpe`, `sortino`, `max_drawdown`, etc.):** Implemented by Zipline’s metrics tracker; typically **rolling** or **point-in-time** (e.g. drawdown up to that date), not necessarily full-backtest single-number metrics.
- **Availability:** Depends on `metrics_set`. With `metrics_set='none'`, many columns (including `returns`, `portfolio_value`, and risk metrics) may be missing; the project can reconstruct `returns` and `portfolio_value` from transactions when saving results.

**Reference:** Zipline-Reloaded `zipline.finance.metrics` and [docs/api/metrics_inventory.md](metrics_inventory.md).

---

## lib/metrics/ Metrics

These are produced **by the project** when you call functions in `lib/metrics/` (e.g. `calculate_metrics()`, `calculate_trade_metrics()`, `calculate_rolling_metrics()`). They are **not** columns of the Performance DataFrame unless we explicitly add them.

### Entry points

- **`calculate_metrics(returns, transactions=..., benchmark_returns=..., ...)`**  
  Returns a single dict of metrics for the full period (and optionally trade-level metrics if `transactions` is provided).
- **`calculate_trade_metrics(transactions)`**  
  Returns trade-level metrics only (win rate, profit factor, etc.).
- **`calculate_rolling_metrics(returns, window=..., ...)`**  
  Returns a DataFrame of rolling metrics (e.g. rolling Sharpe).

### Metrics produced only by lib/metrics/

| Metric | Module | Description |
|--------|--------|-------------|
| `calmar` | performance | Annual return / \|max drawdown\| |
| `omega` | risk | Omega ratio |
| `tail_ratio` | risk | Tail ratio (e.g. 95th / 5th percentile of returns) |
| `trade_count` | trade | Number of completed trades |
| `win_rate` | trade | Fraction of winning trades |
| `profit_factor` | trade | Gross profit / gross loss |
| `avg_trade_return`, `avg_win`, `avg_loss` | trade | Average trade P&amp;L stats |
| `max_win`, `max_loss` | trade | Largest single win/loss |
| `max_consecutive_losses` | trade | Longest losing streak |
| `avg_trade_duration` | trade | Average holding period |
| `trades_per_month` | trade | Trades per month |
| Rolling series | rolling | e.g. `rolling_sharpe`, `rolling_sortino`, etc. |

### Metrics produced by both (see next section)

- `sharpe`, `sortino`, `max_drawdown`, `max_drawdown_duration`, `recovery_time`, `alpha`, `beta`  
  In lib/metrics they are **full-period** (single value) from the given returns (and benchmark). In Zipline they are **time-series** (rolling or cumulative) in `perf`.

**Reference:** [docs/api/metrics.md](metrics.md) and `lib/metrics/` package.

---

## Overlapping Metrics (Same Name, Different Source)

These names appear both in Zipline’s Performance DataFrame and in the dict returned by `lib/metrics.calculate_metrics()`. The **meaning** differs.

| Metric | Zipline-Reloaded | lib/metrics/ |
|--------|------------------|--------------|
| **sharpe** | Time-series (rolling); one value per bar in `perf['sharpe']` | Single full-period Sharpe from `returns` (and optional risk-free rate) |
| **sortino** | Time-series (rolling) in `perf['sortino']` | Single full-period Sortino |
| **max_drawdown** | Time-series (e.g. running max drawdown) in `perf['max_drawdown']` | Single full-period max drawdown |
| **max_drawdown_duration** | Column (e.g. days) in `perf['max_drawdown_duration']` | Single full-period duration in days |
| **recovery_time** | Column (e.g. days) in `perf['recovery_time']` | Single full-period recovery time (we convert to days) |
| **alpha** | Column (benchmark-relative) in `perf['alpha']` | Single full-period Jensen’s alpha from returns + benchmark |
| **beta** | Column in `perf['beta']` | Single full-period beta |

**When to use which:**

- **Zipline columns:** For time-series plots and bar-by-bar analysis (e.g. `perf['sharpe'].plot()`), and when you want to keep using Zipline’s built-in definitions.
- **lib/metrics:** For reporting a single number for the whole backtest (e.g. “Sharpe 1.2”), for `metrics.json`, and for strategy comparison. Used by `save_results()` → `calculate_and_save_metrics()` and by validation/optimization code.

---

## Data Flow and When Each Is Used

1. **Backtest run**  
   `run_algorithm()` returns `perf` (Performance DataFrame). All Zipline-produced columns (portfolio, returns, risk columns if enabled, custom `record()` columns) are in `perf`.

2. **Saving results**  
   `save_results()` (and `lib/backtest/results_serialization.py`) may:
   - Reconstruct `returns` and `portfolio_value` if missing (e.g. `metrics_set='none'`).
   - Call `lib.metrics.calculate_metrics(returns, transactions=..., benchmark_returns=...)` to get full-period and trade-level metrics.
   - Write the result to `metrics.json`. So **metrics.json** is **lib/metrics/** provenance, not raw Zipline columns.

3. **Reports and analysis**  
   Report code may:
   - Use Zipline columns from `perf` (or from loaded `performance.pkl`) for time-series and benchmark/risk columns.
   - Use `metrics.json` or `calculate_metrics()` for summary numbers and trade stats. So a single report can show both Zipline-origin (e.g. rolling Sharpe from `perf`) and lib/metrics-origin (e.g. full-period Sharpe from `metrics.json`).

4. **Walk-forward / optimization**  
   Validation and optimization typically derive `returns` from `perf` (e.g. `perf['returns']` or from `portfolio_value`), then call `lib.metrics.calculate_metrics(returns, ...)`. So the metrics they use for in/out-of-sample or objective functions are **lib/metrics/**.

---

## Recommendations

1. **Document in reports:** When showing a metric, note whether it is “from Zipline (rolling)” or “from lib/metrics (full-period)” if both exist (e.g. Sharpe, max drawdown).
2. **Prefer lib/metrics for single-value summaries:** For “the” Sharpe, max drawdown, alpha, beta of the run, use `calculate_metrics()` or `metrics.json` so semantics are full-period and consistent.
3. **Use Zipline columns for time-series:** Keep using `perf['sharpe']`, `perf['max_drawdown']`, etc. for plots and intra-backtest analysis.
4. **Trade-level metrics:** Always from lib/metrics (`calculate_trade_metrics()` or `calculate_metrics(..., transactions=...)`); Zipline does not compute win rate, profit factor, etc.

---

## References

### Project docs

- [Performance DataFrame Integration](performance_dataframe_integration.md) — How `perf` is used and persisted.
- [Zipline Metrics Inventory](metrics_inventory.md) — Zipline-Reloaded metrics system and columns.
- [Metrics API](metrics.md) — lib/metrics/ API and returned metrics.

### Code

- `lib/metrics/` — Project metrics implementation (core, performance, risk, trade, rolling, comparison).
- `lib/backtest/results_serialization.py` — Calls `calculate_metrics()` and writes `metrics.json`.

### Zipline-Reloaded

- [Zipline-Reloaded](https://github.com/stefan-jansen/zipline-reloaded)  
- [Zipline Documentation](https://zipline.ml4trading.io)
