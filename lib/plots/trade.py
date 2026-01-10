"""
Trade analysis visualization functions.

Provides trade distribution and analysis plotting.
"""

# Standard library imports
from pathlib import Path
from typing import Optional

# Third-party imports
import numpy as np
import pandas as pd

try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


def plot_trade_analysis(
    transactions: pd.DataFrame,
    save_path: Optional[Path] = None,
    title: Optional[str] = None
) -> None:
    """
    Plot trade distribution analysis (win/loss histogram).
    
    Args:
        transactions: DataFrame with columns: date, sid, amount, price, commission
        save_path: Optional path to save figure
        title: Optional plot title
    """
    if not MATPLOTLIB_AVAILABLE:
        return
    
    # Extract trades from transactions
    from ..metrics import _extract_trades
    
    trades = _extract_trades(transactions)
    
    if len(trades) == 0:
        return
    
    # Calculate trade returns
    trade_returns = []
    for trade in trades:
        if trade['entry_price'] > 0 and trade['exit_price'] > 0:
            if trade['direction'] == 'long':
                trade_return = (trade['exit_price'] - trade['entry_price']) / trade['entry_price']
            else:
                trade_return = (trade['entry_price'] - trade['exit_price']) / trade['entry_price']
            trade_returns.append(trade_return * 100)  # Convert to percentage
    
    if len(trade_returns) == 0:
        return
    
    trade_returns = np.array(trade_returns)
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    # Histogram
    wins = trade_returns[trade_returns > 0]
    losses = trade_returns[trade_returns < 0]
    
    axes[0].hist(wins, bins=20, alpha=0.7, color='#06A77D', label=f'Wins ({len(wins)})')
    axes[0].hist(losses, bins=20, alpha=0.7, color='#E63946', label=f'Losses ({len(losses)})')
    axes[0].axvline(0, color='black', linestyle='--', linewidth=1)
    axes[0].set_xlabel('Trade Return (%)', fontsize=12)
    axes[0].set_ylabel('Frequency', fontsize=12)
    axes[0].set_title('Trade Return Distribution', fontsize=13, fontweight='bold')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # Cumulative trade returns
    cumulative_trades = np.cumsum(trade_returns)
    axes[1].plot(range(len(cumulative_trades)), cumulative_trades, linewidth=2, color='#2E86AB')
    axes[1].axhline(0, color='black', linestyle='--', linewidth=1)
    axes[1].set_xlabel('Trade Number', fontsize=12)
    axes[1].set_ylabel('Cumulative Return (%)', fontsize=12)
    axes[1].set_title('Cumulative Trade Returns', fontsize=13, fontweight='bold')
    axes[1].grid(True, alpha=0.3)
    
    fig.suptitle(title or 'Trade Analysis', fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()





