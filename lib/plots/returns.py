"""
Returns visualization functions.

Provides monthly returns heatmap plotting.
"""

# Standard library imports
from pathlib import Path
from typing import Optional

# Third-party imports
import pandas as pd

try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    import seaborn as sns
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


def plot_monthly_returns(
    returns: pd.Series,
    save_path: Optional[Path] = None,
    title: Optional[str] = None
) -> None:
    """
    Plot monthly returns heatmap.
    
    Args:
        returns: Series of daily returns
        save_path: Optional path to save figure
        title: Optional plot title
    """
    if not MATPLOTLIB_AVAILABLE:
        return
    
    # Resample to monthly returns
    monthly_returns = (1 + returns).resample('ME').prod() - 1
    
    # Create year-month matrix from the Series
    monthly_returns.index = pd.to_datetime(monthly_returns.index)
    
    # Convert to DataFrame for pivot
    monthly_df = pd.DataFrame({
        'returns': monthly_returns.values,
        'year': monthly_returns.index.year,
        'month': monthly_returns.index.month
    })
    
    pivot_data = monthly_df.pivot_table(
        values='returns',
        index='year',
        columns='month',
        aggfunc='first'
    )
    
    fig, ax = plt.subplots(figsize=(14, max(6, len(pivot_data) * 0.5)))
    
    # Create heatmap
    sns.heatmap(
        pivot_data * 100,  # Convert to percentage
        annot=True,
        fmt='.1f',
        cmap='RdYlGn',
        center=0,
        cbar_kws={'label': 'Monthly Return (%)'},
        ax=ax,
        linewidths=0.5,
        linecolor='gray'
    )
    
    ax.set_xlabel('Month', fontsize=12)
    ax.set_ylabel('Year', fontsize=12)
    ax.set_title(title or 'Monthly Returns Heatmap', fontsize=14, fontweight='bold')
    
    # Set month labels
    month_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    xticks = [int(i) for i in ax.get_xticks()]
    ax.set_xticklabels([month_labels[i-1] if 1 <= i <= 12 else '' for i in xticks], rotation=0)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()

