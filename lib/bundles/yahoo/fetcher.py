"""
Yahoo Finance data fetcher for The Researcher's Cockpit.

Handles yfinance API calls, retry logic, and symbol resolution.
Extracted from yahoo_bundle.py as part of v1.0.11 refactoring.
"""

import logging
from typing import List, Optional

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


def fetch_yahoo_data(
    symbol: str,
    start_date: Optional[str],
    end_date: Optional[str],
    interval: str,
    show_progress: bool = False
) -> pd.DataFrame:
    """
    Fetch data from Yahoo Finance for a single symbol.

    Args:
        symbol: Symbol to fetch (e.g., 'SPY', 'BTC-USD')
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        interval: yfinance interval ('1m', '5m', '1h', '1d', etc.)
        show_progress: Whether to print progress messages

    Returns:
        DataFrame with OHLCV data and DatetimeIndex

    Raises:
        ValueError: If no data returned for symbol
    """
    try:
        ticker = yf.Ticker(symbol)

        # Convert date strings to datetime if provided
        yf_start = pd.Timestamp(start_date).to_pydatetime() if start_date else None
        yf_end = pd.Timestamp(end_date).to_pydatetime() if end_date else None

        # Fetch data from yfinance
        hist = ticker.history(start=yf_start, end=yf_end, interval=interval)

        if hist.empty:
            raise ValueError(f"No data returned for {symbol} at {interval} timeframe")

        if show_progress:
            print(f"  {symbol}: Fetched {len(hist)} bars ({hist.index[0]} to {hist.index[-1]})")

        return hist

    except Exception as e:
        logger.exception(f"Error fetching data for {symbol}")
        raise ValueError(f"Failed to fetch data for {symbol}: {e}") from e


def fetch_multiple_symbols(
    symbols: List[str],
    start_date: Optional[str],
    end_date: Optional[str],
    interval: str,
    show_progress: bool = False
) -> dict:
    """
    Fetch data for multiple symbols from Yahoo Finance.

    Args:
        symbols: List of symbols to fetch
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        interval: yfinance interval
        show_progress: Whether to print progress

    Returns:
        Dictionary mapping symbol -> DataFrame

    Raises:
        RuntimeError: If no symbols could be fetched
    """
    results = {}
    failed = []

    for symbol in symbols:
        try:
            data = fetch_yahoo_data(symbol, start_date, end_date, interval, show_progress)
            results[symbol] = data
        except Exception as e:
            failed.append(symbol)
            if show_progress:
                print(f"  Warning: Skipping {symbol} - {e}")

    if not results:
        raise RuntimeError(
            f"Failed to fetch data for all symbols. "
            f"Attempted: {symbols}, Failed: {failed}"
        )

    if failed and show_progress:
        print(f"  Successfully fetched {len(results)}/{len(symbols)} symbols")

    return results
