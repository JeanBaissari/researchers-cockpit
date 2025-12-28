# Detailed Solution Plan for Issues \#10 & \#11

## Overview

These two issues (Centralized Logging & Data Integrity Checks) are foundational infrastructure concerns that, if solved properly, will improve debugging, auditability, and reliability across the entire research workflow.

---

## Issue \#10: Centralized Logging

### Problem Analysis

* Inconsistent logging (mix of print() and logging.\*)  
* No unified log format across modules  
* Difficult to trace workflow execution (Hypothesis → Strategy → Backtest → Analyze → Optimize → Validate)  
* No correlation between pipeline stages  
* No log persistence for audit trails

### Architectural Solution

#### 1\. Logging Configuration Module

Create lib/logging\_config.py:  
lib/  
├── \_\_init\_\_.py          \# Import and auto-configure logging  
├── logging\_config.py    \# Central logging setup  
└── ...  
Design Principles:

* Structured logging: Use JSON format for machine-parseable logs alongside human-readable console output  
* Context propagation: Add strategy\_name, run\_id, phase (hypothesis/backtest/optimize/validate) to every log entry  
* Level separation: DEBUG for development, INFO for normal runs, WARNING+ for production  
* File rotation: Prevent unbounded log growth

#### 2\. Logger Hierarchy

cockpit                           \# Root logger  
├── cockpit.data                  \# Data ingestion, bundles  
│   ├── cockpit.data.loader       \# lib/data\_loader.py  
│   └── cockpit.data.cache        \# Cache operations  
├── cockpit.strategy              \# Strategy execution  
│   └── cockpit.strategy.backtest \# lib/backtest.py  
├── cockpit.metrics               \# lib/metrics.py  
├── cockpit.validation            \# lib/validate.py  
├── cockpit.report                \# lib/report.py  
└── cockpit.agent                 \# AI agent operations  
Rationale: Hierarchical loggers allow selective verbosity (e.g., cockpit.data=DEBUG while keeping cockpit.strategy=INFO)

#### 3\. Implementation Steps

Step 1: Create lib/logging\_config.py

* Define configure\_logging(strategy\_name=None, run\_id=None, level="INFO", log\_dir="logs/")  
* Support console handler (human-readable) \+ file handler (JSON structured)  
* Include custom formatter with timestamps, module, level, and context fields

Step 2: Create context manager for pipeline phases  
*\# Usage in workflow:*  
*with* LogContext(*phase*\="backtest", *strategy*\="btc\_sma\_cross", *run\_id*\="20241220\_143000"):  
   run\_backtest(...)  *\# All logs within include phase/strategy/run\_id*  
Step 3: Auto-configure in lib/\_\_init\_\_.py

* Import configure\_logging and call with defaults  
* Allow override via config/settings.yaml:

 logging:  
level: INFO  
console: true  
file: true  
log\_dir: logs/  
format: structured  *\# or "simple"*

Step 4: Migrate all modules

* Replace all print() with appropriate logger.debug/info/warning/error  
* Add module-level logger: logger \= logging.getLogger(\_\_name\_\_)  
* Document logging conventions in a CONTRIBUTING.md or docs/development.md

Step 5: Integration with workflow stages

* Each stage from workflow.md (Hypothesis → Strategy → Backtest → Analyze → Optimize → Validate → Document) should log:  
* Stage entry/exit with timestamps  
* Key decisions and metrics  
* Errors with full context

#### 4\. Log Output Structure

Console (human-readable):  
2024-12-20 14:30:00 | INFO | \[btc\_sma\_cross\] Backtest started | run\_id=20241220\_143000  
2024-12-20 14:30:05 | INFO | \[btc\_sma\_cross\] Loaded 1825 bars from yahoo\_crypto\_daily  
2024-12-20 14:30:45 | INFO | \[btc\_sma\_cross\] Backtest complete | sharpe=1.23 | trades=47  
File (JSON structured for analysis):  
{"timestamp": "2024-12-20T14:30:00Z", "level": "INFO", "logger": "cockpit.strategy.backtest", "strategy": "btc\_sma\_cross", "run\_id": "20241220\_143000", "phase": "backtest", "message": "Backtest started"}

#### 5\. Log Retention Policy

* logs/ directory with date-based rotation  
* Keep last 30 days of logs  
* Strategy-specific logs in results/{strategy}/logs/ (persisted with results)  
* Auto-cleanup script in scripts/maintenance.py

---

## Issue \#11: Data Integrity Checks

### Problem Analysis

* verify\_integrity=False bypasses Zipline's built-in checks  
* Data quality issues (gaps, outliers, missing bars) go unnoticed  
* Downstream failures in backtest are harder to diagnose  
* Violates principle of early failure detection

### Architectural Solution

#### 1\. Multi-Layer Validation Strategy

Layer 1: Pre-Ingestion (Source Validation)

* Validate data from API before bundling  
* Check for required columns, data types, reasonable ranges

Layer 2: Ingestion (Zipline Bundle Creation)

* Enable verify\_integrity=True by default  
* Add configurable tolerance levels

Layer 3: Pre-Backtest (Runtime Validation)

* Verify bundle exists and is not corrupted  
* Check date coverage matches backtest range

Layer 4: Post-Backtest (Results Validation)

* Validate output files exist and are non-empty  
* Check metrics are within valid ranges

#### 2\. Implementation Steps

Step 1: Create lib/data\_validation.py  
class DataValidator:  
   def validate\_ohlcv(*self*, *df*: pd.DataFrame) \-\> ValidationResult:  
       """Validates OHLCV data before ingestion."""  
       checks \= \[  
           self.\_check\_required\_columns(df),  
           self.\_check\_no\_nulls(df),  
           self.\_check\_ohlc\_consistency(df),  *\# high \>= low, close within range*  
           self.\_check\_volume\_positive(df),  
           self.\_check\_date\_continuity(df, calendar),  
           self.\_check\_no\_duplicate\_dates(df),  
           self.\_check\_price\_outliers(df),  *\# \>3 sigma moves flagged*  
       \]  
       *return* ValidationResult(checks)  
Step 2: Modify lib/data\_loader.py

* Call DataValidator.validate\_ohlcv() before asset\_db\_writer.write()  
* Log warnings for non-critical issues (gaps on weekends)  
* Raise exceptions for critical issues (negative prices, future dates)

Step 3: Add configuration in config/settings.yaml  
data\_validation:  
 enabled: true  *\# Master switch*  
 strict\_mode: false  *\# If true, fail on any warning*  
  checks:  
   verify\_integrity: true  *\# Zipline's built-in check*  
   check\_gaps: true  
   gap\_tolerance\_days: 3  *\# Allow up to 3 consecutive missing days*  
   check\_outliers: true  
   outlier\_threshold\_sigma: 5  
   check\_future\_dates: true  
   check\_negative\_values: true  
  per\_asset\_class:  
   crypto:  
     gap\_tolerance\_days: 0  *\# Crypto trades 24/7*  
   forex:  
     gap\_tolerance\_days: 2  *\# Weekends expected*  
   equities:  
     gap\_tolerance\_days: 4  *\# Holidays expected*  
Step 4: Add CLI flag support  
\# Default: validation enabled per config  
python scripts/ingest\_data.py \--source yahoo \--assets crypto

\# Override: skip validation (for debugging)  
python scripts/ingest\_data.py \--source yahoo \--assets crypto \--skip-validation

\# Override: strict mode (fail on any issue)  
python scripts/ingest\_data.py \--source yahoo \--assets crypto \--strict  
Step 5: Create validation report in ingestion output  
data/bundles/yahoo\_crypto\_daily/  
├── ... (bundle files)  
└── validation\_report.json  
Report contents:  
{  
 "validated\_at": "2024-12-20T14:30:00Z",  
 "assets\_validated": \["BTC-USD", "ETH-USD"\],  
 "issues": \[  
   {"asset": "BTC-USD", "type": "gap", "dates": \["2024-12-25"\], "severity": "warning"}  
 \],  
 "passed": true  
}  
Step 6: Pre-backtest bundle check in lib/backtest.py

* Before running backtest, verify bundle exists  
* Check validation\_report.json if present  
* Warn if validation was skipped or has issues

#### 3\. Integration with Workflow

From workflow.md Phase 3 (Backtest Execution):  
Add validation gate:  
Data Bundle Check → Validation Check → Backtest Execution → Results Validation  
Agent behavior update:

* Agent checks bundle validation status before backtest  
* If validation failed or was skipped, agent warns user  
* Agent can proceed with user confirmation or auto-fail based on config

#### 4\. Error Reporting

Use the centralized logging from Issue \#10:  
logger.warning(  
   "Data gap detected",  
   *extra*\={  
       "asset": "BTC-USD",  
       "missing\_dates": \["2024-12-25"\],  
       "strategy": context.strategy\_name,  
       "phase": "pre-ingestion"  
   }  
)  
---

## Integration: How These Solutions Work Together

### Unified Configuration

Extend config/settings.yaml:  
*\# Existing settings...*

logging:  
 level: INFO  
 console: true  
 file: true  
 log\_dir: logs/  
 structured: true

data\_validation:  
 enabled: true  
 strict\_mode: false  
 *\# ... (as detailed above)*

### Workflow Integration Points

| Phase (from workflow.md) | Logging | Validation |
| :---- | :---- | :---- |
| Hypothesis Formation | Log creation | N/A |
| Strategy Creation | Log template copy, param loading | N/A |
| Data Ingestion | Log source, assets, bars loaded | Full OHLCV validation |
| Backtest Execution | Log start, bundle, metrics | Bundle existence \+ validation status |
| Analysis | Log visualizations generated | Metrics range validation |
| Optimization | Log grid search progress, best params | Results validation |
| Validation | Log walk-forward, Monte Carlo | Consistency checks |
| Documentation | Log report generation | N/A |

### Pipeline Integration Points

From pipeline.md, ensure each pattern includes validation:   
Quick Validation Pattern:

1. Create hypothesis  
1. Generate strategy  
1. \[NEW\] Verify data bundle (log warning if validation issues)  
1. Backtest  
1. Review (all logged)

Full Research Cycle:

1. Document hypothesis  
1. Implement strategy  
1. \[NEW\] Validate data quality before backtest  
1. Backtest (structured logging throughout)  
1. Deep analysis (logged)  
1. Optimization (progress logged)  
1. \[NEW\] Validate optimization results  
1. Final documentation

---

## Migration Plan

### Phase 1: Logging Foundation (Week 1\)

1. Create lib/logging\_config.py  
1. Update lib/\_\_init\_\_.py  
1. Add to config/settings.yaml  
1. Migrate 3 core modules: data\_loader.py, backtest.py, metrics.py

### Phase 2: Full Logging Migration (Week 2\)

1. Migrate remaining modules  
1. Add LogContext for phase tracking  
1. Update scripts to use logging  
1. Add log cleanup to maintenance

### Phase 3: Validation Foundation (Week 3\)

1. Create lib/data\_validation.py  
1. Integrate with data\_loader.py  
1. Add configuration support  
1. Create CLI flags

### Phase 4: Validation Integration (Week 4\)

1. Add pre-backtest checks  
1. Add post-backtest validation  
1. Update agent instructions  
1. Add validation to existing strategies

### Phase 5: Documentation & Testing (Week 5\)

1. Update workflow.md with validation steps  
1. Update pipeline.md with logging references  
1. Add tests for logging configuration  
1. Add tests for validation edge cases

---

## Success Criteria

1. All modules use structured logging — No print() statements remain  
1. Every workflow phase is traceable — Can reconstruct full research session from logs  
1. Data issues caught early — Validation runs before backtest, not after failure  
1. Configurable strictness — Researchers can choose warning-only or fail-fast  
1. No workflow disruption — Existing strategies continue to work  
1. Audit trail — Every backtest has associated logs in results directory

