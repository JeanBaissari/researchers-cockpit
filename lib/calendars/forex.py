"""
Forex Trading Calendar (24/5)

This module provides a 24/5 trading calendar for forex markets.
Forex markets trade 24 hours on weekdays but close on weekends.
"""

from datetime import time
from typing import List

import pandas as pd
from pandas.tseries.holiday import (
    Holiday,
    GoodFriday,
)
from exchange_calendars import ExchangeCalendar
from exchange_calendars.exchange_calendar import HolidayCalendar


class ForexCalendar(ExchangeCalendar):
    """
    Forex Trading Calendar (24/5 including Sundays)

    Forex markets trade 24 hours from Sunday 5pm EST through Friday 5pm EST.
    This calendar uses a 7-day weekmask to accommodate Sunday trading data.

    Key Properties:
    - Trading Days: Sunday through Friday (includes Sunday for data alignment)
    - Open Time: 00:00 (midnight)
    - Close Time: 23:59:59 (end of day)
    - Timezone: America/New_York (EST/EDT)
    - Holidays: Major global bank closures (Christmas, New Year's, Good Friday)

    Note: While FOREX technically closes on Saturday, we use a 7-day weekmask
    to prevent session mismatch errors when CSV data includes Sunday dates
    (markets open Sunday evening). This eliminates the need for SessionManager
    workarounds and aligns with actual FOREX data availability.

    For minute data: 24 hours * 60 minutes = 1440 minutes per day.

    Attributes:
        name: Calendar identifier ('FOREX')
        tz: Timezone (America/New_York)
        open_times: Tuple of (date, time) pairs for market open
        close_times: Tuple of (date, time) pairs for market close
        weekmask: Days of the week that are trading days (Mon-Sun, 7 days)
    """

    name = "FOREX"
    tz = "America/New_York"
    open_times = ((None, time(0, 0)),)
    close_times = ((None, time(23, 59, 59)),)
    weekmask = "Mon Tue Wed Thu Fri Sat Sun"

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
    def regular_holidays(self) -> HolidayCalendar:
        """
        Forex observes major holidays when global banking is closed.

        Returns:
            HolidayCalendar with forex market holidays

        Note:
            Forex typically observes: New Year's Day, Christmas, and Good Friday.
            Major banks globally close on these days, so forex trading is suspended.
        """
        return HolidayCalendar(
            [
                Holiday("Christmas", month=12, day=25),
                Holiday("New Year", month=1, day=1),
                GoodFriday,
            ]
        )

    @property
    def special_closes(self) -> List:
        """
        No special closing times.

        Returns:
            Empty list
        """
        return []


__all__ = ["ForexCalendar"]
