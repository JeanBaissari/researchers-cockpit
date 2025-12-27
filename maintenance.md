# Maintenance Guide — Hybrid A: The Researcher's Cockpit

> This document covers everything required to keep the research environment healthy, organized, and efficient over time.

---

## Maintenance Philosophy

Hybrid A is designed for minimal maintenance. The structure is intentionally simple, with few moving parts. Most maintenance is about **hygiene** (keeping things clean) rather than **operations** (keeping things running).

Think of it like maintaining a well-designed kitchen: you don't need to reconfigure the appliances, just keep the counters clean and restock the pantry.

---

## Daily Maintenance

### Time Required: 5 minutes

**1. Clear the Sandbox**

Notebooks in `notebooks/_sandbox/` accumulate. If you haven't touched a sandbox notebook in 3+ days, delete it or promote it to a proper location.

```bash
# See what's in sandbox
ls -la notebooks/_sandbox/

# Clear old experiments
rm notebooks/_sandbox/old_experiment_*.ipynb
```

**2. Check Latest Symlinks**

After running backtests, verify the `latest` symlink points where you expect:

```bash
ls -la results/*/latest
```

If a symlink is broken (points to deleted directory), recreate it:

```bash
cd results/btc_sma_cross
rm latest
ln -s backtest_20241220_091500 latest
```

**3. Review Overnight Runs (if applicable)**

If you scheduled runs overnight, check for errors:

```bash
# Quick error check
grep -r "Error\|Exception" results/*/backtest_*/logs/*.log 2>/dev/null
```

---

## Weekly Maintenance

### Time Required: 30 minutes

**1. Update Strategy Catalog**

The catalog (`docs/strategy_catalog.md`) should reflect current strategy status:

```markdown
| Strategy | Asset | Status | Sharpe | Last Updated |
|----------|-------|--------|--------|--------------|
| btc_sma_cross | Crypto | Validated | 1.23 | 2024-12-18 |
| eth_mean_rev | Crypto | Abandoned | -0.12 | 2024-12-20 |
```

Review each active strategy:
- Has status changed?
- Are metrics current?
- Any strategies stuck in limbo?

**2. Data Bundle Health Check**

Verify bundles are current and uncorrupted:

```bash
# List all bundles
ls -la data/bundles/

# Check bundle dates
for bundle in data/bundles/*/; do
    echo "$bundle: $(stat -c %y "$bundle")"
done
```

If any bundle is >7 days old and you need current data:

```bash
python scripts/ingest_data.py --source yahoo --assets crypto --force
```

**3. Cache Cleanup**

The cache directory can grow unbounded. Clean old cache files:

```bash
# Remove cache files older than 7 days
find data/cache/ -type f -mtime +7 -delete
```

**4. Disk Space Check**

Results accumulate. Check disk usage:

```bash
du -sh results/
du -sh data/
du -sh notebooks/
```

If results are consuming too much space, consider archiving old runs (see Monthly Maintenance).

---

## Monthly Maintenance

### Time Required: 1-2 hours

**1. Archive Old Results**

Results older than 3 months that aren't part of validated strategies can be archived:

```bash
# Create archive directory
mkdir -p archive/results_2024Q3

# Move old results
mv results/*/backtest_202409* archive/results_2024Q3/
mv results/*/optimization_202409* archive/results_2024Q3/

# Compress archive
tar -czvf archive/results_2024Q3.tar.gz archive/results_2024Q3/
rm -rf archive/results_2024Q3/
```

**Keep unarchived:**
- `latest` symlinks (update if target was archived)
- Results referenced in active reports
- Validated strategy results

**2. Strategy Lifecycle Review**

For each strategy, determine its fate:

| Status | Action |
|--------|--------|
| Active/Validated | Keep, ensure latest results are current |
| Testing | Set deadline for resolution |
| Abandoned | Move to `strategies/_archived/` |
| Forgotten | Decide: revive or archive |

Move abandoned strategies:

```bash
mkdir -p strategies/_archived
mv strategies/crypto/failed_experiment strategies/_archived/
```

**3. Dependency Audit**

Check for outdated dependencies:

```bash
pip list --outdated
```

Update carefully:
- Zipline-reloaded updates may change behavior
- Pin versions in requirements.txt after testing

**4. Configuration Review**

Review `config/settings.yaml`:
- Are default date ranges still appropriate?
- Any API keys expiring?
- Capital assumptions still valid?

**5. Documentation Refresh**

Review and update:
- `README.md` — Still accurate?
- `docs/workflow.md` — Reflects current practices?
- `.agent/` instructions — Any new conventions?

---

## Quarterly Maintenance

### Time Required: Half day

**1. Full System Health Check**

Run the complete test suite (if you have one):

```bash
# Run all tests
pytest tests/

# Or manual smoke test
python scripts/run_backtest.py --strategy btc_sma_cross --quick
```

**2. Performance Benchmarking**

Track system performance over time:

```bash
# Time a standard backtest
time python scripts/run_backtest.py --strategy btc_sma_cross
```

Compare to previous quarter. Significant slowdowns indicate:
- Data bundles have grown
- Dependencies have changed
- Hardware issues

**3. Strategy Portfolio Review**

Big picture questions:
- What percentage of strategies are validated vs. abandoned?
- Are we learning from failures?
- Any strategies need re-optimization with fresh data?

Create quarterly summary:

```markdown
# Q4 2024 Research Summary

## Strategies Tested: 12
- Validated: 3 (25%)
- Promising: 2 (17%)
- Abandoned: 7 (58%)

## Key Learnings
- Mean reversion works better in crypto than momentum
- Forex breakout strategies overfit easily

## Focus for Next Quarter
- Test regime-switching approaches
- Expand to equity indices
```

**4. Backup Verification**

Verify backups exist and are restorable:

```bash
# Check backup exists
ls -la ~/backups/zipline-algo/

# Test restore (to temp location)
tar -xzvf ~/backups/zipline-algo/backup_2024Q4.tar.gz -C /tmp/
ls /tmp/zipline-algo/
```

**5. Agent Instruction Review**

Review `.agent/` files:
- Are instructions still accurate?
- Any repeated issues with AI agent behavior?
- New conventions to document?

Update instructions based on lessons learned.

---

## Annual Maintenance

### Time Required: Full day

**1. Major Version Evaluation**

Review major dependency versions:
- Python version (upgrade?)
- Zipline-reloaded (new features?)
- Pandas/NumPy (compatibility?)

Plan any major upgrades for a quiet period.

**2. Full Archive Rotation**

Move everything >12 months old to cold storage:

```bash
mkdir -p archive/2023
mv archive/results_2023* archive/2023/
tar -czvf archive/2023_full.tar.gz archive/2023/
rm -rf archive/2023/
# Move to cold storage (external drive, S3, etc.)
```

**3. System Rebuild Test**

Can you rebuild the environment from scratch?

```bash
# Create fresh environment
python -m venv test_env
source test_env/bin/activate
pip install -r requirements.txt

# Run smoke test
python scripts/run_backtest.py --strategy btc_sma_cross --quick
```

Fix any issues discovered. Update requirements.txt if needed.

**4. Research Retrospective**

Document the year:
- Best performing strategies
- Biggest failures (and why)
- Process improvements made
- Goals for next year

---

## Troubleshooting Common Issues

### Issue: Backtest Fails with "No Data"

**Cause:** Data bundle doesn't contain required dates or symbols.

**Fix:**
```bash
# Check what's in the bundle
python -c "from lib.data_loader import list_bundle_contents; list_bundle_contents('crypto_daily')"

# Re-ingest if needed
python scripts/ingest_data.py --source yahoo --assets crypto --force
```

### Issue: Strategy Import Errors

**Cause:** Strategy file has syntax errors or missing imports.

**Fix:**
```bash
# Check syntax
python -m py_compile strategies/crypto/broken_strategy/strategy.py

# Common missing imports
# Add to strategy.py:
from zipline.api import order_target_percent, record, symbol
```

### Issue: Results Directory Full

**Cause:** Too many backtest runs accumulated.

**Fix:**
```bash
# See disk usage by strategy
du -sh results/*/

# Archive old results (keep latest)
find results/*/backtest_* -maxdepth 0 -type d -mtime +30 | while read dir; do
    strategy=$(dirname "$dir" | xargs basename)
    latest=$(readlink "results/$strategy/latest")
    if [ "$(basename "$dir")" != "$latest" ]; then
        echo "Archiving $dir"
        # rm -rf "$dir"  # Uncomment to actually delete
    fi
done
```

### Issue: Symlinks Broken

**Cause:** Target directory was moved or deleted.

**Fix:**
```bash
# Find broken symlinks
find . -type l ! -exec test -e {} \; -print

# Fix each one
cd results/btc_sma_cross
rm latest
ln -s $(ls -td backtest_* | head -1) latest
```

### Issue: Config Not Loading

**Cause:** YAML syntax error or missing file.

**Fix:**
```bash
# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('config/settings.yaml'))"

# Check for tabs (YAML hates tabs)
grep -P '\t' config/*.yaml
```

### Issue: Notebook Kernel Dies

**Cause:** Out of memory during large backtest.

**Fix:**
- Reduce date range in backtest
- Use script instead of notebook (lower memory overhead)
- Increase system swap space (if available)

### Issue: API Rate Limited

**Cause:** Too many data requests to external API.

**Fix:**
```bash
# Check cache status
ls -la data/cache/

# Use cached data
python scripts/ingest_data.py --source yahoo --assets crypto --use-cache

# Wait and retry (most APIs reset hourly)
```

---

## Backup Strategy

### What to Backup

**Must Backup:**
- `strategies/` — Your intellectual property
- `config/` — Environment configuration
- `.agent/` — Agent instructions
- `docs/` — Documentation
- `lib/` — Custom code

**Optional Backup:**
- `results/` — Can be regenerated, but time-consuming
- `reports/` — Summaries of work done

**Don't Backup:**
- `data/cache/` — Temporary, regenerated on demand
- `data/bundles/` — Can be re-ingested
- `notebooks/_sandbox/` — Experimental, ephemeral

### Backup Commands

```bash
# Full backup
tar -czvf backup_$(date +%Y%m%d).tar.gz \
    strategies/ config/ .agent/ docs/ lib/ \
    --exclude='strategies/_archived' \
    --exclude='*.pyc'

# Minimal backup (strategies only)
tar -czvf strategies_$(date +%Y%m%d).tar.gz strategies/

# Results backup (optional, large)
tar -czvf results_$(date +%Y%m%d).tar.gz results/
```

### Backup Schedule

| Frequency | What | Where |
|-----------|------|-------|
| Daily | Git commit | Remote repository |
| Weekly | Full backup | Local + cloud |
| Monthly | Results archive | Cold storage |

### Git Workflow

```bash
# Daily commit
git add strategies/ lib/ config/ docs/
git commit -m "Research progress $(date +%Y-%m-%d)"
git push origin main

# After major milestones
git tag -a v1.2 -m "Validated BTC SMA strategy"
git push origin --tags
```

---

## Monitoring Checklist

### Daily Quick Check (1 minute)
- [ ] Any overnight errors?
- [ ] Sandbox clean?

### Weekly Check (10 minutes)
- [ ] Strategy catalog updated?
- [ ] Data bundles current?
- [ ] Disk space adequate?

### Monthly Check (30 minutes)
- [ ] Old results archived?
- [ ] Abandoned strategies cleared?
- [ ] Dependencies up to date?
- [ ] Backups verified?

### Quarterly Check (2 hours)
- [ ] Full system health check
- [ ] Performance benchmarking
- [ ] Strategy portfolio review
- [ ] Agent instructions reviewed

---

## Environment Variables

Document any environment variables the system depends on:

```bash
# Required
export ZIPLINE_ROOT=~/.zipline

# Optional (API keys)
export YAHOO_API_KEY=xxx
export BINANCE_API_KEY=xxx
export BINANCE_API_SECRET=xxx
export OANDA_API_KEY=xxx
export OANDA_ACCOUNT_ID=xxx
```

Store these in `~/.bashrc` or `~/.zshrc`, NOT in the repository.

---

## Logs

### Log Locations

```
logs/                           # If using file logging
├── backtest.log               # Backtest execution logs
├── data_ingestion.log         # Data loading logs
└── errors.log                 # Error-only log
```

### Log Rotation

Logs can grow large. Rotate weekly:

```bash
# Simple rotation
mv logs/backtest.log logs/backtest_$(date +%Y%m%d).log
touch logs/backtest.log

# Or configure logrotate (Linux)
```

### Log Retention

- Keep error logs for 90 days
- Keep execution logs for 30 days
- Delete older logs automatically

```bash
find logs/ -name "*.log" -mtime +30 -delete
find logs/ -name "errors*.log" -mtime +90 -delete
```
