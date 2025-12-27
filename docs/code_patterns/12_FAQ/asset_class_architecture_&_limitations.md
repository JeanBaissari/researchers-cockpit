Based on my analysis of the Zipline Reloaded codebase, here's how to structure code for handling multiple asset classes with different trading calendars and enable scalable strategy testing:

## **Asset Class Architecture and Limitations**

Important Note: Zipline Reloaded currently supports only two native asset types: Equity and Future. Forex and crypto are not currently supported as distinct asset classes. \_assets.pyx:266-276

To add forex or crypto support, you would need to extend the asset type system by creating new asset subclasses similar to how Equity and Future extend the base Asset class.

## **Handling Multiple Asset Classes with Different Trading Calendars**

### **1\. Data Ingestion with Bundle Registration**

The bundle system allows you to register data bundles with specific trading calendars: core.py:1-60

You can create custom ingest functions for different asset classes: csvdir.py:22-58

### **2\. Calendar Alignment with ReindexBarReader**

When assets trade on different calendars, Zipline uses ReindexBarReader to align them to a common superset calendar: resample.py:590-617

The reindex readers fill missing data with NaN for prices and 0 for volume when the target calendar has sessions that don't exist in the source calendar: resample.py:670-698

### **3\. Dispatching by Asset Type**

The AssetDispatchBarReader routes data requests to the appropriate reader based on asset type: dispatch\_bar\_reader.py:22-56

The dispatch mechanism groups assets by type and delegates to type-specific readers: dispatch\_bar\_reader.py:100-131

Example pattern from tests showing NYSE (equities) and us\_futures calendars working together: test\_dispatch\_bar\_reader.py:40-90

## **Triggering Strategies by Different Trading Sessions**

### **1\. Schedule Function with Calendar Support**

Use schedule\_function() to trigger strategies at specific times on different trading calendars: algorithm.py:881-953

### **2\. Time Rules for Market Sessions**

The AfterOpen and BeforeClose rules calculate trigger times based on each calendar's session times: events.py:345-398 events.py:401-452

Note the special handling for us\_futures calendar which has different execution times: events.py:376-383

### **3\. Getting Specific Trading Calendars**

Use get\_calendar() to access different exchange calendars: calendar\_utils.py:28-32

Each asset can check if its exchange is open at a given time: \_assets.pyx:250-262

## **Scalable Parameter Testing Patterns**

### **1\. The @parameter\_space Decorator**

For testing strategies with multiple parameter combinations, use the @parameter\_space decorator: core.py:1074-1149

This decorator tests the cross-product of all parameter combinations without creating separate test cases for each.

Example usage for testing across multiple calendars and parameter combinations: test\_downsampling.py:94-150

### **2\. Passing Parameters via run\_algorithm**

The run\_algorithm() function accepts an initialize function where you can set strategy parameters: run\_algo.py:304-394

### **3\. Context-Based Parameter Storage**

Store strategy parameters in the context object during initialization, making them accessible throughout the algorithm lifecycle and easily parameterizable for testing.

## **Recommended Pattern for Multi-Asset, Multi-Calendar Setup**

1. Create separate bundles for each asset class/calendar combination  
2. Use AssetDispatchBarReader with ReindexBarReader wrappers to align different calendars  
3. Schedule functions with appropriate calendar parameters for session-specific triggers  
4. Store parameters in context during initialization for easy testing  
5. Use @parameter\_space for comprehensive parameter sweep testing

## **Notes**

* Zipline Reloaded leverages the exchange\_calendars library for calendar implementations, supporting many global exchanges  
* To add forex/crypto support, you'd need to: (1) create new Asset subclasses, (2) update the database schema, (3) implement appropriate data loaders, and (4) register trading calendars for these markets  
* The calendar alignment system assumes the target calendar is a superset of the source calendar  
* For session-specific strategies (ASIAN, LONDON, etc.), you can register functions with schedule\_function() using the appropriate exchange calendar (e.g., "XHKG" for Hong Kong, "XLON" for London)

