# Detailed Solution Plan: Conditional Pipeline Attachment

## Problem Analysis

The template strategy unconditionally attaches a Pipeline in initialize(), but:

1. Pipeline API requires country\_code in asset metadata  
1. Non-equity assets (crypto, forex) may not have/need this field  
1. The use\_pipeline parameter exists but isn't being respected

## Architectural Solution

### 1\. Parameter-Driven Pipeline Attachment Pattern

In strategies/\_template/strategy.py's initialize() function:  
Before any pipeline operations:  
1\. Load parameters via load\_params()  
2\. Check context.params\['strategy'\].get('use\_pipeline', False)  
3\. Only if True, proceed with pipeline attachment  
Recommended guard structure:  
def initialize(*context*):  
   params \= load\_params()  
   context.params \= params  
    
   *\# Pipeline attachment \- only when explicitly enabled*  
   *if* params.get('strategy', {}).get('use\_pipeline', False):  
       *\# Validate prerequisites*  
       *if* 'country\_code' not in asset\_metadata\_columns:  
           *raise* ConfigurationError(  
               "Pipeline requires country\_code in asset metadata. "  
               "Either add country\_code to data ingestion or set use\_pipeline: false"  
           )  
       attach\_pipeline(make\_pipeline(), 'my\_pipeline')

### 2\. Parameters.yaml Template Update

Add explicit documentation in \_template/parameters.yaml:   
strategy:  
 *\# Pipeline settings*  
 use\_pipeline: false  *\# Set true only for US equities with proper metadata*  
 *\# When true, requires: country\_code in asset metadata*

### 3\. Defensive Pipeline Factory

Create lib/pipeline\_utils.py:

* can\_use\_pipeline(bundle\_name) → checks if bundle has required metadata  
* safe\_attach\_pipeline(context, pipeline, name) → wraps attachment with validation

### 4\. Asset Class-Specific Templates

Structure strategies/\_template/ to provide asset-class variants:  
strategies/\_template/  
├── base/strategy.py           \# No pipeline (crypto, forex)  
├── equities/strategy.py       \# With pipeline support  
├── hypothesis.md  
└── parameters.yaml

### 5\. Validation Hook in Backtest Runner

In lib/backtest.py or scripts/run\_backtest.py:

* Pre-flight check: if use\_pipeline: true, verify bundle metadata includes country\_code  
* Fail fast with actionable error message before Zipline execution

### 6\. Documentation Updates

In pipeline.md:

* Add section: "Pipeline Prerequisites"  
* Document that Pipeline API is primarily for US equities  
* Explain when to use use\_pipeline: false

In workflow.md:

* Add note in Strategy Creation phase about pipeline compatibility

## Implementation Order

1. Immediate fix: Add conditional check in \_template/strategy.py  
1. Short-term: Add validation in lib/backtest.py pre-flight checks  
1. Medium-term: Create lib/pipeline\_utils.py with safe helpers  
1. Long-term: Consider asset-class-specific template variants

## Why This Approach

* Fail-fast: Catches misconfiguration before cryptic Zipline errors  
* Backwards compatible: Default use\_pipeline: false won't break existing strategies  
* Self-documenting: Parameters clearly indicate pipeline usage  
* Consistent with Zipline patterns: Pipeline attachment is always explicit, never implicit

