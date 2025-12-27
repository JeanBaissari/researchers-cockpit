# Strategy Hypothesis

> **REQUIRED:** Every strategy MUST have a hypothesis.md file. This document articulates what market behavior you're exploiting and why you believe it exists.

---

## The Belief

**What specific market behavior are we exploiting?**

Short-term price momentum, when confirmed by medium-term momentum, tends to persist in the direction of the trend. This behavior is driven by investor herding and delayed institutional response to new information.

---

## The Reasoning

**Why does this behavior exist?**

Momentum in financial markets is a well-documented anomaly. It is believed to exist due to:
- **Behavioral biases:** Investors under-react to new information initially, leading to a gradual price adjustment. Once the trend is established, fear of missing out (FOMO) and herd mentality can amplify the trend.
- **Market structure:** Institutional investors often have mandates or investment processes that cause them to react slowly to price movements, contributing to trend continuation.
- **Feedback loops:** Price increases attract more buyers, pushing prices higher, and vice versa.

---

## The Conditions

**When should this work? When should it fail?**

**Works well in:**
- Strong trending markets (up or down).
- Markets with clear leadership and follow-through.

**Fails in:**
- Choppy, sideways, or mean-reverting markets.
- Periods of high uncertainty or sudden regime shifts.

---

## The Falsification

**What result would prove this hypothesis wrong?**

- If Sharpe Ratio < 0.75 over a 5-year backtest, the edge doesn't exist
- If maximum drawdown > 25%, risk-adjusted returns are unacceptable
- The strategy consistently underperforms a simple buy-and-hold benchmark during trending periods.

---

## Implementation Notes

**How is this hypothesis translated into code?**

This strategy uses the Zipline Pipeline API to calculate 10-day and 30-day momentum factors.
A 'buy' signal is generated when 10-day momentum crosses above 30-day momentum.
A 'sell' signal is generated when 10-day momentum crosses below 30-day momentum.
Positions are held until a crossover in the opposite direction occurs.

---

## Expected Outcomes

**What results would validate this hypothesis?**

- Sharpe Ratio > 1.0 (annualized)
- Maximum Drawdown < 20%
- Positive alpha relative to a relevant benchmark (e.g., SPY)
- Consistent positive returns in trending market environments.

---

## References

**What research, papers, or observations support this hypothesis?**

- [Optional: List any relevant sources or prior research.]

---

## Revision History

| Date | Change | Author |
|------|--------|--------|
| 2025-12-26 | Initial hypothesis for Pipeline Momentum Strategy | Jean Baissari |
