"""
Forex Trading Calendar (24/5)

This module provides a 24/5 trading calendar for forex markets.
Forex markets trade 24 hours on weekdays but close on weekends.
"""

from datetime import time
from typing import List

import pandas as pd
from exchange_calendars import ExchangeCalendar


class ForexCalendar(ExchangeCalendar):
    """
    Forex Trading Calendar (24/5 - Weekdays Only)

    Forex markets trade 24 hours on weekdays but close on weekends.
    Trading opens Sunday 5pm EST and closes Friday 5pm EST.

    Note: We use Mon-Fri weekmask because exchange_calendars handles
    sessions on a daily basis. The Sunday open is effectively the start
    of the Monday session in trading terms.

    For minute data: 24 hours * 60 minutes = 1440 minutes per day.
    
    Attributes:
        name: Calendar identifier ('FOREX')
        tz: Timezone (America/New_York)
        open_times: Tuple of (date, time) pairs for market open
        close_times: Tuple of (date, time) pairs for market close
        weekmask: Days of the week that are trading days (Mon-Fri)
    """

    name = "FOREX"
    tz = "America/New_York"
    open_times = ((None, time(0, 0)),)
    close_times = ((None, time(23, 59, 59)),)
    weekmask = "Mon Tue Wed Thu Fri"

    @classmethod
    def open_time_default(cls) -> time:
        """
        Default market open time.
        
        Returns:
            Midnight (00:00:00)
        """
        return time(0, 0)

    @classmethod
    def close_time_default(cls) -> time:
        """
        Default market close time.
        
        Returns:
            End of day (23:59:59)
        """
        return time(23, 59, 59)

    @property
    def regular_holidays(self) -> pd.DatetimeIndex:
        """
        Forex observes major holidays when global banking is closed.
        
        Returns:
            DatetimeIndex of holidays (currently empty, can be extended)
            
        Note:
            Forex typically observes: New Year's Day, Christmas, and major US holidays.
            To add holidays, use: pd.DatetimeIndex([...]) with specific dates
        """
        return pd.DatetimeIndex([])

    @property
    def special_closes(self) -> List:
        """
        No special closing times.
        
        Returns:
            Empty list
        """
        return []


__all__ = ['ForexCalendar']





