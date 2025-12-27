# Strategy Hypothesis: SPY SMA Crossover

> **REQUIRED:** Every strategy MUST have a hypothesis.md file. This document articulates what market behavior you're exploiting and why you believe it exists.

---

## The Belief

**What specific market behavior are we exploiting?**

SPY (S&P 500 ETF) exhibits persistent trends following moving average crossovers. When a fast moving average (10-day) crosses above a slow moving average (30-day), it signals the beginning of an uptrend that persists for several days to weeks. Conversely, when the fast SMA crosses below the slow SMA, it signals a downtrend.

This is a classic trend-following strategy that exploits momentum in the broad market.

---

## The Reasoning

**Why does this behavior exist?**

1. **Institutional Rebalancing**: Large institutions rebalance portfolios based on trend signals, creating self-reinforcing momentum
2. **Retail FOMO**: Retail investors chase trends after breakouts, amplifying moves
3. **Market Structure**: The S&P 500 is composed of large-cap stocks that tend to trend rather than mean-revert
4. **Liquidity**: High liquidity in SPY allows trends to persist without immediate reversal

---

## The Conditions

**When should this work? When should it fail?**

**Works well in:**
- Trending markets (strong directional moves)
- Bull markets with consistent upward momentum
- Periods of low volatility with clear trends

**Fails in:**
- Choppy, sideways markets (whipsaws)
- High volatility periods with frequent reversals
- Bear markets with sharp downturns (late entries)
- Range-bound markets without clear direction

---

## The Falsification

**What result would prove this hypothesis wrong?**

- If Sharpe Ratio < 0.5 across 3+ years of data, the edge doesn't exist
- If maximum drawdown > 30%, risk-adjusted returns are unacceptable
- If win rate < 40%, the strategy generates more losses than wins
- If the strategy consistently underperforms buy-and-hold SPY

---

## Implementation Notes

**How is this hypothesis translated into code?**

- Use 10-day fast SMA and 30-day slow SMA
- Enter long position on golden cross (fast > slow crossover)
- Exit position on death cross (fast < slow crossover)
- Rebalance daily at market open + 30 minutes
- Apply 5% stop loss for risk management

---

## Expected Outcomes

**What results would validate this hypothesis?**

- Sharpe Ratio > 0.7
- Maximum Drawdown < 20%
- Win Rate > 45%
- Positive returns in trending market periods
- Reasonable trade frequency (not too many whipsaws)

---

## References

**What research, papers, or observations support this hypothesis?**

- Classic technical analysis: Moving average crossovers are one of the oldest trend-following signals
- Momentum investing literature: Jegadeesh and Titman (1993) documented momentum effects
- Market microstructure: Large-cap ETFs like SPY exhibit persistent trends due to institutional flows

---

## Revision History

| Date | Change | Author |
|------|--------|--------|
| 2025-12-20 | Initial hypothesis for MVP testing | System |
