# Strategy Catalog

> Comprehensive index of all strategies with performance metrics, validation status, and trade statistics.

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
