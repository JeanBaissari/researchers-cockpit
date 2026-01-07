# Hypothesis: Breakout Intraday Strategy

## 1. The Belief
The Breakout Intraday strategy exploits market inefficiencies by capturing momentum continuation when price breaks through previous day high/low levels in trending forex markets. This leverages the psychological significance of daily price boundaries and institutional order flow concentrations, particularly during the London trading session. Phase 11 enhancements (session filtering and ATR-based range detection) further mitigate weaknesses in low-quality or range-bound markets.

## 2. The Reasoning
The strategy is founded on the observation that price movements often accelerate after breaking significant previous day high/low levels due to concentrated institutional order flow and psychological factors. The London trading session provides optimal liquidity and statistically superior trending behavior, leading to higher win rates. Historically, the strategy suffered from:
- **Session Quality Variation:** Trading all sessions equally led to lower win rates (35-45%) and false breakouts, especially in Asian and New York sessions. London-only mode addresses this by restricting trading to higher-quality sessions.
- **Range-Bound Market Whipsaws:** Consolidating markets frequently triggered both high and low breakouts, resulting in double losses. ATR-based range detection prevents trading during these periods, reducing whipsaw losses.

## 3. The Conditions
The strategy is suitable for:
- **Market Suitability**: Trending Markets, High Volatility, London Session.
- **Volatility Regime Suitability**: High to medium volatility (poor in low volatility consolidation).
- **Session Filter (Phase 11 Enhancement)**: Restricts trading to London session (07:00-16:00 UTC) and London/NY overlap (13:00-16:00 UTC) when `london_only_mode` is enabled.
- **Range Detection Filter (Phase 11 Enhancement)**: Prevents trading during range-bound markets. If `(prev_day_high - prev_day_low) / ATR(14) < 1.5`, market is consolidating and signals are skipped.
- **Daily Trade Limit**: Maximum 2 trades per day.
- **Exit Conditions**: Trailing Stop Exit (activates after 10 pips profit, trails by 10 pips), End-of-Day Exit (mandatory close at 23:00 UTC), and optional Opposite Signal Exit.

## 4. The Falsification
This hypothesis would be proven wrong if, after comprehensive backtesting with Phase 11 enhancements:
- The Expected Sharpe Ratio is consistently below 1.0.
- The Maximum Drawdown exceeds 8%.
- The Win Rate falls below 45%.
- The Profit Factor is consistently below 1.2.
- The strategy fails to maintain low correlation with broader market movements.
- The Phase 11 enhancements (london_only_mode and enable_range_detection) do not significantly improve win rate (by 5-10%) and reduce whipsaw losses (by 20-30%) compared to a baseline.

