"""
Rolling metrics visualization functions.

Provides rolling Sharpe and Sortino ratio plotting.
"""

# Standard library imports
from pathlib import Path
from typing import Optional

# Third-party imports
import pandas as pd

try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.dates as mdates
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


def plot_rolling_metrics(
    returns: pd.Series,
    window: int = 63,
    save_path: Optional[Path] = None,
    title: Optional[str] = None
) -> None:
    """
    Plot rolling Sharpe and Sortino ratios.
    
    Args:
        returns: Series of daily returns
        window: Rolling window size in days (default: 63)
        save_path: Optional path to save figure
        title: Optional plot title
    """
    if not MATPLOTLIB_AVAILABLE:
        return
    
    from ..metrics import calculate_rolling_metrics
    
    rolling = calculate_rolling_metrics(returns, window=window)
    
    if len(rolling) == 0:
        return
    
    fig, axes = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
    
    # Rolling Sharpe
    axes[0].plot(rolling.index, rolling['rolling_sharpe'], linewidth=1.5, color='#2E86AB', label='Sharpe')
    axes[0].axhline(0, color='black', linestyle='--', linewidth=1, alpha=0.5)
    axes[0].axhline(1, color='green', linestyle='--', linewidth=1, alpha=0.5, label='Sharpe = 1')
    axes[0].set_ylabel('Rolling Sharpe Ratio', fontsize=12)
    axes[0].set_title(f'Rolling Metrics ({window}-day window)', fontsize=13, fontweight='bold')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # Rolling Sortino
    axes[1].plot(rolling.index, rolling['rolling_sortino'], linewidth=1.5, color='#E63946', label='Sortino')
    axes[1].axhline(0, color='black', linestyle='--', linewidth=1, alpha=0.5)
    axes[1].axhline(1, color='green', linestyle='--', linewidth=1, alpha=0.5, label='Sortino = 1')
    axes[1].set_xlabel('Date', fontsize=12)
    axes[1].set_ylabel('Rolling Sortino Ratio', fontsize=12)
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    axes[1].xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    plt.xticks(rotation=45)
    
    if title:
        fig.suptitle(title, fontsize=14, fontweight='bold', y=1.02)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()

