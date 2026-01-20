"""
Custom minimal metrics set for Zipline to avoid metrics tracker bugs.

When using metrics_set='none', Zipline doesn't populate standard columns like
'returns' and 'portfolio_value'. This minimal metrics set provides only
essential tracking without the buggy session indexing code.
"""

from zipline.finance import metrics


@metrics.register('minimal-essential')
def minimal_essential_metrics():
    """
    Minimal metrics set that tracks only essential performance data.
    
    Avoids the daily_cumulative_returns bug by not using BenchmarkReturnsAndVolatility.
    Only tracks:
    - Returns (for lib/metrics calculation)
    - Portfolio value (for equity curve)
    - Cash flow (for transaction tracking)
    
    Returns:
        Set of minimal metric objects
    """
    from zipline.finance.metrics.metric import (
        ReturnsStatistic,
        CashFlow,
    )
    
    return {
        ReturnsStatistic(),  # Tracks returns
        CashFlow(),  # Tracks cash flow
        # Note: We don't include BenchmarkReturnsAndVolatility to avoid the bug
    }
