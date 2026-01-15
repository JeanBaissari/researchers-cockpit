"""
Data verification module for The Researcher's Cockpit.

Provides data integrity verification for backtest results.
"""

import logging
from typing import Dict, Any

import pandas as pd


# Module-level logger
logger = logging.getLogger(__name__)


def _verify_data_integrity(
    perf: pd.DataFrame,
    transactions_df: pd.DataFrame,
    metrics: Dict[str, Any]
) -> None:
    """
    Run optional data integrity checks.
    
    Args:
        perf: Performance DataFrame
        transactions_df: Transactions DataFrame
        metrics: Calculated metrics
    """
    try:
        from ..data_integrity import (
            verify_metrics_calculation,
            verify_returns_calculation,
            verify_positions_match_transactions
        )
        
        # Verify metrics
        if 'returns' in perf.columns:
            returns = perf['returns'].dropna()
            is_valid, discrepancies = verify_metrics_calculation(
                metrics,
                returns,
                transactions_df if len(transactions_df) > 0 else None
            )
            if not is_valid:
                logger.warning(f"Metrics verification found discrepancies: {discrepancies}")
            
            # Verify returns calculation
            if len(transactions_df) > 0:
                is_valid, error = verify_returns_calculation(returns, transactions_df)
                if not is_valid:
                    logger.warning(f"Returns verification failed: {error}")
        
        # Verify positions match transactions
        if 'positions' in perf.columns and len(transactions_df) > 0:
            positions_df = perf[['positions']].copy()
            is_valid, error = verify_positions_match_transactions(positions_df, transactions_df)
            if not is_valid:
                logger.warning(f"Positions verification failed: {error}")
    except ImportError:
        # Data integrity module not available, skip
        pass
    except Exception as e:
        logger.warning(f"Data integrity check failed: {e}")















