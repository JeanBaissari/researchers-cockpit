# Strategy Catalog

> Comprehensive index of all strategies with performance metrics, validation status, and trade statistics.

---

## Purpose

This catalog provides a centralized index of all trading strategies in the Researcher's Cockpit with their performance metrics, validation status, and current development stage. It serves as the single source of truth for strategy inventory and performance tracking.

---

## Scope

**What this covers:**
- Complete list of all strategies (development to live)
- Performance metrics (Sharpe, drawdown, win rate, etc.)
- Validation status (walk-forward, Monte Carlo)
- Data context (bundles, timeframes, date ranges)
- Strategy versioning and parameter sets

**What this does NOT cover:**
- Strategy implementation details (see strategy directories)
- Detailed backtest reports (see `results/` directories)
- Strategy creation process (see `.claude/skills/04-zrl-strategy-scaffold`)

---

## Quick Summary

| Strategy | Asset | Status | Sharpe | MaxDD | Win Rate | Last Updated |
|----------|-------|--------|--------|-------|----------|--------------|

## Detailed Performance Metrics

### Risk-Adjusted Returns

| Strategy | Sharpe | Sortino | Calmar | Omega | Information Ratio |
|----------|--------|---------|--------|-------|-------------------|

### Drawdown Analysis

| Strategy | Max DD | Avg DD | DD Duration (days) | Recovery Time (days) |
|----------|--------|--------|-------------------|---------------------|

### Trade Statistics

| Strategy | Total Trades | Win Rate (%) | Profit Factor | Avg Win/Loss | Avg Holding (days) |
|----------|--------------|--------------|---------------|--------------|-------------------|

### Consistency Metrics

| Strategy | Monthly Std Dev | % Positive Months | Skewness | Kurtosis |
|----------|-----------------|-------------------|----------|----------|

### Exposure Analysis

| Strategy | Avg Exposure (%) | Max Leverage | Beta |
|----------|------------------|--------------|------|

## Validation Status

| Strategy | Walk-Forward Efficiency | Overfit Probability | OOS Sharpe | Monte Carlo p-value | Validation Date |
|----------|------------------------|---------------------|------------|---------------------|-----------------|

## Data Context

| Strategy | Bundle Name | Timeframe | Backtest Start | Backtest End | IS/OOS Split | Data Quality |
|----------|-------------|-----------|----------------|--------------|--------------|--------------|

## Strategy Versioning

| Strategy | Version | Parameter Set ID | Hypothesis Doc | Last Optimization | Notes |
|----------|---------|------------------|----------------|-------------------|-------|

---


## How to Use This Catalog

**Adding a new strategy:**
1. Create strategy in `strategies/{asset_class}/{name}/`
2. Run backtest with `python scripts/run_backtest.py --strategy {name}`
3. Update this catalog with performance metrics
4. Run validation (walk-forward, Monte Carlo)
5. Update validation status

**Updating metrics:**
```bash
# After backtest completion
python scripts/generate_report.py --strategy {name}
# Metrics will be in results/{name}/latest/metrics.json
```

**Strategy status workflow:**
```
development → backtested → validated → paper → live
```

---

## Metrics Reference

### Status Definitions

| Status | Description |
|--------|-------------|
| `development` | Strategy under active development, not validated |
| `backtested` | Initial backtest complete, pending validation |
| `validated` | Passed walk-forward and Monte Carlo validation |
| `paper` | Running in paper trading mode |
| `live` | Deployed in live trading |
| `deprecated` | No longer maintained |

### Metric Descriptions

| Metric | Description | Target |
|--------|-------------|--------|
| **Sharpe Ratio** | Risk-adjusted return (annualized) | > 1.0 |
| **Sortino Ratio** | Downside risk-adjusted return | > 1.5 |
| **Calmar Ratio** | Annual return / Max drawdown | > 1.0 |
| **Omega Ratio** | Probability-weighted gains/losses | > 1.0 |
| **Information Ratio** | Active return / Tracking error | > 0.5 |
| **Max Drawdown** | Largest peak-to-trough decline | < 20% |
| **Profit Factor** | Gross profit / Gross loss | > 1.5 |
| **Win Rate** | Winning trades / Total trades | > 50% |
| **Walk-Forward Efficiency** | OOS performance / IS performance | > 0.5 |
| **Overfit Probability** | Likelihood of curve-fitting | < 30% |

---

## Related Documentation

- [Creating Strategies](../.claude/skills/04-zrl-strategy-scaffold.md) - Strategy scaffolding skill
- [Strategy Template](../strategies/_template/) - Template for new strategies
- [Backtest API](api/backtest.md) - Running backtests
- [Metrics API](api/metrics.md) - Performance metrics
- [Optimization API](api/optimize.md) - Parameter optimization

---

**Last Updated:** 2026-02-09
**Version:** v1.12.0
**Status:** NO WRAPPERS Architecture
