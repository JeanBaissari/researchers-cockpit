# Strategy Hypothesis

> **REQUIRED:** Every strategy MUST have a hypothesis.md file. This document articulates what market behavior you're exploiting and why you believe it exists.

---

## The Belief

**What specific market behavior are we exploiting?**

[Describe the market inefficiency, pattern, or edge you're testing. Be specific.]

Example: "BTC price trends persist for 15-30 days after a moving average crossover. The momentum created by retail FOMO and institutional rebalancing creates predictable directional moves."

---

## The Reasoning

**Why does this behavior exist?**

[Explain the market mechanics, participant behavior, or structural factors that create this opportunity.]

Example:
- Retail FOMO creates momentum after breakouts
- Institutional rebalancing creates mean reversion boundaries
- Market microstructure creates predictable patterns

---

## The Conditions

**When should this work? When should it fail?**

[Describe market conditions, regimes, or environments where this strategy should perform well or poorly.]

**Works well in:**
- Trending markets
- High volatility environments
- [Add specific conditions]

**Fails in:**
- Choppy, sideways markets
- Low liquidity periods
- [Add specific conditions]

---

## The Falsification

**What result would prove this hypothesis wrong?**

[Define clear criteria for rejecting the hypothesis.]

Example:
- If Sharpe < 0.5 across 3+ years of data, the edge doesn't exist
- If maximum drawdown > 30%, risk-adjusted returns are unacceptable
- If win rate < 40%, the strategy is not viable

---

## Implementation Notes

**How is this hypothesis translated into code?**

[Brief description of the strategy implementation approach.]

Example:
- Use fast SMA (10-day) and slow SMA (30-day) crossovers
- Enter on golden cross, exit on death cross
- Apply 200-day trend filter to avoid trading in bear markets

---

## Expected Outcomes

**What results would validate this hypothesis?**

[Define success criteria.]

- Sharpe Ratio > 1.0
- Maximum Drawdown < 20%
- Win Rate > 50%
- Consistent performance across different market regimes

---

## References

**What research, papers, or observations support this hypothesis?**

[Optional: List any relevant sources or prior research.]

---

## Revision History

| Date | Change | Author |
|------|--------|--------|
| YYYY-MM-DD | Initial hypothesis | [Your name] |

