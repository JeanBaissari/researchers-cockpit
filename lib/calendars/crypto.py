"""
Crypto Trading Calendar (24/7)

This module provides a 24/7 trading calendar for cryptocurrency markets.
Crypto markets trade continuously without holidays or market closures.
"""

from datetime import time
from typing import List

import pandas as pd
from exchange_calendars import ExchangeCalendar
from exchange_calendars.calendar_helpers import UTC


class CryptoCalendar(ExchangeCalendar):
    """
    24/7 Trading Calendar for Cryptocurrency Markets

    Crypto markets trade continuously without holidays or market closures.
    This calendar reflects that reality with no off days.

    For minute data: 24 hours * 60 minutes = 1440 minutes per day.
    
    Attributes:
        name: Calendar identifier ('CRYPTO')
        tz: Timezone (UTC)
        open_times: Tuple of (date, time) pairs for market open
        close_times: Tuple of (date, time) pairs for market close
        weekmask: Days of the week that are trading days
    """

    name = "CRYPTO"
    tz = UTC
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
    def regular_holidays(self) -> pd.DatetimeIndex:
        """
        Crypto markets don't observe holidays.
        
        Returns:
            Empty DatetimeIndex
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


__all__ = ['CryptoCalendar']

