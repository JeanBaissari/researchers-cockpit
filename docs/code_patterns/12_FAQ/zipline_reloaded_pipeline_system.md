# **Pipeline System**

The Pipeline System is a core component of Zipline Reloaded that enables efficient calculation of cross-sectional (multi-asset) values based on historical market data. It provides a declarative API for expressing complex computations on large datasets while handling the logic for time management, asset universe selection, and efficient execution.

If you're looking for information about how pipeline integrates with the overall backtesting process, see . For details on data access for pipelines, see .

## **Overview**

The Pipeline System allows users to express what computations they want performed, rather than how to perform them. Users define a pipeline consisting of various calculations (terms) to perform on market data, and the system handles the efficient execution of these computations.

Pipeline System Architecture

Sources: engine.py:1-57 . engine.py:210-247 ,

## **Key Components**

### **Terms**

Terms are the building blocks of pipeline computations. All terms derive from the Term base class, which defines common functionality for pipeline expressions.

Pipeline Term Hierarchy

Sources: term.py:51-168 , ,

### **Term Types**

The Pipeline system has three main types of terms:

| Term Type | Output Type | Description | Common Uses |
| ----- | ----- | ----- | ----- |
| Factor | Numeric (float64) | Produces numeric values for each asset/date pair | Moving averages, ratios, rankings |
| Filter | Boolean | Produces boolean values for each asset/date pair | Screening assets, combining conditions |
| Classifier | Categorical | Produces categorical or integer values for each asset/date pair | Sector/industry classification, grouping |

Each term type provides different methods suitable for their data type:

* Factors offer methods like rank(), demean(), zscore(), and winsorize()  
* Filters offer methods like top(), bottom(), and boolean operations (&, |, \~)  
* Classifiers enable grouping and categorical operations

Sources: , ,

### **Pipeline**

A Pipeline is a container that holds a collection of term computations and an optional screen (which determines which assets should be included in the results).

Sources: engine.py:86-97 ,

### **PipelineEngine**

The PipelineEngine is responsible for executing pipelines. The main implementation is SimplePipelineEngine, which calculates each term independently.

Pipeline Execution Flow

Sources: engine.py:210-372 , engine.py:566-709

## **Pipeline Execution Process**

When executing a pipeline, the engine follows these steps:

1. Determine domain: Identify the trading calendar and assets for the pipeline using resolve\_domain  
2. Build dependency graph: Create an ExecutionPlan with all terms and their dependencies  
3. Compute root mask: Calculate which assets exist on which dates using \_compute\_root\_mask  
4. Initialize workspace: Set up initial data structures with \_populate\_initial\_workspace  
5. Compute execution order: Determine the order to calculate terms with execution\_order  
6. Execute terms: Calculate each term in order using compute\_chunk, storing results in the workspace  
7. Format results: Extract and format the final results with \_to\_narrow

The execution process is optimized to minimize memory usage by tracking reference counts for each term and removing data from the workspace when it's no longer needed.

Sources: engine.py:1-57 , engine.py:361-429 , engine.py:566-709

## **Common Operations**

### **Factor Operations**

Factors offer various operations for transforming numerical data:

1. Statistical Operations:  
   * rank(method='ordinal'): Assign a rank to each asset each day  
   * demean(groupby=None): Subtract the mean from each asset's value  
   * zscore(groupby=None): Standardize values to mean 0, std 1  
   * winsorize(min\_percentile, max\_percentile): Cap outliers at percentile boundaries  
2. Windowed Operations:  
   * SimpleMovingAverage(window\_length): Calculate the rolling mean  
   * EWMA(window\_length, decay\_rate): Exponential weighted moving average  
   * EWMSTD(window\_length, decay\_rate): Exponential weighted moving standard deviation  
   * MaxDrawdown(window\_length): Maximum peak-to-trough drawdown  
3. Comparison Operations:  
   * Comparison operators: \>, \<, \>=, \<=, \==, \!=  
   * Mathematical operators: \+, \-, \*, /, \*\*

Sources: , ,

### **Filter Operations**

Filters provide operations for selecting assets:

1. Asset Selection:  
   * top(n): Select the top n assets  
   * bottom(n): Select the bottom n assets  
   * percentile\_between(min\_percentile, max\_percentile): Select assets within percentile range  
2. Boolean Operations:  
   * Boolean operators: & (and), | (or), \~ (not)  
   * all(\*filters): True when all inputs are True  
   * any(\*filters): True when any input is True  
   * at\_least\_n(n, \*filters): True when at least n inputs are True

Sources: ,

## **Pipeline Execution in Practice**

The typical workflow for using pipelines involves:

1. Define factors, filters, and classifiers that express your computation  
2. Create a pipeline with these terms and an optional screen  
3. Run the pipeline using an engine, specifying a date range  
4. Analyze or use the results in your algorithm

Example of pipeline execution:

*\# Assume we've already created some factors and filters*    
my\_pipeline \= Pipeline(    
    columns={    
        'momentum': MomentumFactor(),    
        'value': ValueFactor(),    
    },    
    screen=market\_cap\_filter & liquidity\_filter    
)    
    
*\# Run the pipeline*    
results \= pipeline\_engine.run\_pipeline(    
    pipeline=my\_pipeline,    
    start\_date=start\_date,    
    end\_date=end\_date  

)

The output is a multi-indexed pandas DataFrame with dates and assets as indices, and the requested factor values as columns.

Sources: engine.py:334-361

## **Advanced Features**

### **Chunked Pipeline Execution**

For long date ranges, the run\_chunked\_pipeline method can significantly reduce memory usage by processing the pipeline in smaller time chunks:

results \= engine.run\_chunked\_pipeline(    
    pipeline=my\_pipeline,    
    start\_date=start\_date,    
    end\_date=end\_date,    
    chunksize=20  *\# Process 20 days at a time*  

)

This is particularly useful for production systems or when working with limited memory.

### **Multiple Outputs from Custom Factors**

Custom factors can produce multiple outputs by specifying the outputs parameter:

class OpenCloseSumAndDiff(CustomFactor):    
    inputs \= \[USEquityPricing.open, USEquityPricing.close\]    
    outputs \= \['sum\_', 'diff'\]    
        
    def compute(self, today, assets, out, open, close):    
        out.sum\_\[:\] \= open.sum(axis=0) \+ close.sum(axis=0)  

        out.diff\[:\] \= open.sum(axis=0) \- close.sum(axis=0)

This allows for more efficient computation when multiple related values need to be calculated.

### **Domain-Specific Pipelines**

Pipelines can be specialized to specific domains (e.g., US equities, Japanese equities) to ensure proper calendar and asset handling:

*\# Create a pipeline specific to US equities*    
us\_pipeline \= Pipeline(    
    columns={...},    
    domain=US\_EQUITIES  

)

## **Best Practices**

1. Reuse terms when possible to avoid redundant calculations  
2. Use chunked execution for long date ranges to reduce memory usage  
3. Apply screens early in your factor pipeline to reduce computation  
4. Make terms window-safe when they need to be used in windowed expressions  
5. Leverage built-in operations rather than writing custom factors when possible  
6. Use appropriate domains to ensure correct calendar and asset handling  
7. Monitor reference counts for complex pipelines to optimize memory usage

Sources: engine.py:271-310 , ,

## **Integration with Zipline**

The Pipeline System is integrated with Zipline via the TradingAlgorithm class, which provides methods for defining and running pipelines:

* attach\_pipeline(pipeline, name): Register a pipeline  
* pipeline\_output(name): Run an attached pipeline  
* before\_trading\_start: Common place to execute pipelines

This integration allows algorithms to access cross-sectional data specific to the current simulation date.

Sources: engine.py:1-57

Wiki pages you might want to explore:

* [Overview (stefan-jansen/zipline-reloaded)](https://deepwiki.com/stefan-jansen/zipline-reloaded/1-overview)  
* [Pipeline System (stefan-jansen/zipline-reloaded)](https://deepwiki.com/stefan-jansen/zipline-reloaded/6-pipeline-system)

