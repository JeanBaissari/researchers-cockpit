"""
Equity and drawdown visualization functions.

Provides equity curve and drawdown chart plotting.
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


def plot_equity_curve(
    returns: pd.Series,
    portfolio_value: Optional[pd.Series] = None,
    save_path: Optional[Path] = None,
    title: Optional[str] = None
) -> None:
    """
    Plot equity curve from returns or portfolio value.
    
    Args:
        returns: Series of daily returns
        portfolio_value: Optional Series of portfolio values (if provided, used instead of returns)
        save_path: Optional path to save figure
        title: Optional plot title
    """
    if not MATPLOTLIB_AVAILABLE:
        return
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    if portfolio_value is not None:
        ax.plot(portfolio_value.index, portfolio_value.values, linewidth=1.5, color='#2E86AB')
        ax.set_ylabel('Portfolio Value ($)', fontsize=12)
    else:
        cumulative = (1 + returns).cumprod()
        ax.plot(cumulative.index, cumulative.values, linewidth=1.5, color='#2E86AB')
        ax.set_ylabel('Cumulative Return', fontsize=12)
    
    ax.set_xlabel('Date', fontsize=12)
    ax.set_title(title or 'Equity Curve', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()


def plot_drawdown(
    returns: pd.Series,
    save_path: Optional[Path] = None,
    title: Optional[str] = None
) -> None:
    """
    Plot drawdown chart (underwater plot).
    
    Args:
        returns: Series of daily returns
        save_path: Optional path to save figure
        title: Optional plot title
    """
    if not MATPLOTLIB_AVAILABLE:
        return
    
    cumulative = (1 + returns).cumprod()
    running_max = cumulative.cummax()
    drawdown = (cumulative - running_max) / running_max
    
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.fill_between(drawdown.index, drawdown.values, 0, color='#E63946', alpha=0.7)
    ax.plot(drawdown.index, drawdown.values, linewidth=1, color='#A23B72')
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Drawdown', fontsize=12)
    ax.set_title(title or 'Drawdown Chart', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()















