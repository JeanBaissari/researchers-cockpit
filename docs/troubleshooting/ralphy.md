# Ralphy: Connection Stalls and Task Failures

## "Connection stalled" or exit code 1 with no test output

**Symptom:** Task fails with `C: Connection stalled [34s]` or `Command failed with exit code 1` and the "output" shown is the prompt sent to the AI, not pytest/lint output.

**Cause:** The failure is from the **Cursor/agent process** (timeout or disconnect), not from your repo (tests or commands). Ralphy reports whatever exit code the engine returns.

**What to do:**

1. **Re-run the same task** — Often succeeds on retry.
2. **Run the command locally** — e.g. `pytest tests/ --cov=lib --cov-report=html -q`. If it passes, the task is effectively done; you can mark it complete in `.ralphy/progress.txt` and move on.
3. **Shorten the task** — If a task asks the agent to "implement, test, lint, commit", split it into "run one command" tasks so each run is quick and less likely to stall.
4. **Reduce parallel load** — If using `--parallel`, try without it so each session has more time.

## Coverage command fails with "unrecognized arguments: --cov"

**Cause:** `pytest-cov` is not installed.

**Fix:** `pip install pytest-cov` or add `pytest-cov>=4.1.0` to `requirements.txt` and reinstall.

## Task keeps getting retried (deferred)

**Cause:** Task text may be vague or the "done when" is hard for the agent to satisfy (e.g. "improve coverage" without a single command).

**Fix:** In the PRD, make the task:
- **One command** to run, and **done when** that command exits 0 (or a file exists).
- Explicit: "Do NOT refactor. Just run X and report."
