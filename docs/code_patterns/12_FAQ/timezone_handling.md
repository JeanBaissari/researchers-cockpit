## **How Zipline Handles Timestamps**

Yes, Zipline has predetermined timezone conversion: all timestamps are converted to UTC internally.

When data is ingested, Zipline explicitly converts timestamps to UTC and then removes the timezone localization. This happens in the ingest() function: core.py:408-410

The timestamp is first converted to UTC, then the timezone information is removed (making it timezone-naive but representing UTC time).

Additionally, when writing asset data, the \_dt\_to\_epoch\_ns() function ensures all datetime series are converted to UTC before being stored as epoch nanoseconds: asset\_writer.py:388-406

This function handles both timezone-naive timestamps (which get localized to UTC) and timezone-aware timestamps (which get converted to UTC).

For general timestamp normalization, Zipline provides the make\_utc\_aware() utility function: date\_utils.py:45-52

## **Calendar Selection for Ingested Data**

The calendar is specified when registering a data bundle, and it's passed to all the writers during ingestion.

### **How to Specify a Calendar**

When registering a bundle, you specify the calendar using the calendar\_name parameter in the register() function: core.py:253-345

The default calendar is 'NYSE', but you can specify any registered calendar name. For EURUSD forex data, you would likely want to use a continuous trading calendar like "24/5" (24 hours/day, 5 days/week), which is used in Zipline's FX rate tests: test\_fx.py:21-34

### **How Calendar Selection Works in Code**

During bundle ingestion, the calendar is retrieved and passed to all the writers: core.py:397-444

The calendar determines:

* Valid trading sessions (start\_session and end\_session)  
* Which dates are valid for the data  
* How the data is aligned and stored

### **Example: Registering a Calendar Alias**

You can also register calendar aliases for custom exchanges. For example, the CSVDIR bundle maps to NYSE: csvdir.py:254

### **Code Example Structure**

For EURUSD from Yahoo, your bundle registration would look something like this:

from zipline.data.bundles import register    
    
@register(    
    'yahoo-eurusd',    
    calendar\_name='24/5',  *\# or another appropriate forex calendar*    
    start\_session=pd.Timestamp('2020-01-01'),    
    end\_session=pd.Timestamp('2024-12-31')    
)    
def yahoo\_eurusd\_bundle(environ, asset\_db\_writer, minute\_bar\_writer,     
                        daily\_bar\_writer, adjustment\_writer, calendar,    
                        start\_session, end\_session, cache, show\_progress, output\_dir):    
    *\# Your ingestion logic here*    
    *\# The calendar parameter is automatically provided*  

    *\# All timestamps should be in UTC*

## **Notes**

* All timestamps in Zipline are stored in UTC \- this is a fundamental design decision for consistency across different trading calendars and timezones.  
* The calendar doesn't change timezone handling \- it only determines which dates are valid trading sessions. The timezone conversion to UTC happens regardless of the calendar used.  
* For forex data specifically, Zipline has a dedicated FXRateReader interface that expects timestamps localized to UTC: base.py:60-86  
* The FX system uses continuous trading calendars (like "24/5") to handle the fact that forex markets trade nearly 24 hours a day, 5 days a week.

