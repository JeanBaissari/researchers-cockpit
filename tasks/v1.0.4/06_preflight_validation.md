#### 6. Crypto Strategy - No Trades with Long SMA Periods [PENDING]
**Impact:** Crypto backtest runs but shows 0% return

With 50/200 SMA periods, the strategy needs 200+ days of history before generating signals. Combined with a short backtest period, no trades are executed.

**Root Cause:** The system lacks warmup period validation, allowing backtests to run with insufficient data for indicator initialization.

**Fix (Robust Approach):**

1. **Pre-flight validation in `lib/backtest.py`:**
   - Before executing any backtest, validate: `(backtest_end - backtest_start).days > required_warmup_days`
   - Extract `required_warmup_days` from strategy parameters or calculate dynamically
   - Fail fast with clear error: `"Insufficient data: strategy requires {X} days warmup, but only {Y} days provided"`
   - This integrates with the existing backtest execution flow in `lib/backtest.py`

2. **Add `warmup_days` parameter to strategy config:**
   - Update `strategies/_template/parameters.yaml` to include:
     ```yaml
     backtest:
       warmup_days: 200  # Calculated as max(indicator_periods)
     ```
   - The `run_backtest.py` script should extend data loading to include warmup period before `backtest_start`
   - Only the evaluation period (after warmup) counts for performance metrics

3. **Dynamic validation in `initialize()`:**
   - In strategy template, add validation logic:
     ```python
     def initialize(context):
         params = load_params()
         required_warmup = max(
             params['strategy'].get('fast_period', 10),
             params['strategy'].get('slow_period', 50)
         )
         context.required_warmup_days = required_warmup
         # Log warning if warmup_days param is less than required
     ```
   - This aligns with the AI Agent behavior documented in workflow.md (step 3: "Validates strategy file exists and is syntactically correct")

4. **Update `.agent/backtest_runner.md`:**
   - Add instruction for agents to verify warmup requirements before execution
   - Include warmup validation in the "Validation Checklist" phase

**Integration Points:**
- `lib/backtest.py`: Add pre-flight validation check
- `scripts/run_backtest.py`: Extend data window by warmup_days before start_date
- `strategies/_template/strategy.py`: Add dynamic warmup calculation in initialize()
- `strategies/_template/parameters.yaml`: Add warmup_days parameter
- `.agent/backtest_runner.md`: Document warmup validation for AI agents