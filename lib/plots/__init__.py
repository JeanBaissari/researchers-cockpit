"""
Visualization package for The Researcher's Cockpit.

Provides comprehensive plotting functions for backtest results analysis.
"""

# Standard library imports
from pathlib import Path
from typing import Optional

# Third-party imports
import pandas as pd

# Import all plotting functions from submodules
from .equity import plot_equity_curve, plot_drawdown
from .returns import plot_monthly_returns
from .trade import plot_trade_analysis
from .rolling import plot_rolling_metrics
from .optimization import _plot_optimization_heatmap, _plot_monte_carlo_distribution

__all__ = [
    # Equity visualization
    'plot_equity_curve',
    'plot_drawdown',
    # Returns visualization
    'plot_monthly_returns',
    # Trade visualization
    'plot_trade_analysis',
    # Rolling metrics visualization
    'plot_rolling_metrics',
    # Orchestration
    'plot_all',
    # Optimization visualization (internal)
    '_plot_optimization_heatmap',
    '_plot_monte_carlo_distribution',
]


def plot_all(
    returns: pd.Series,
    save_dir: Path,
    portfolio_value: Optional[pd.Series] = None,
    transactions: Optional[pd.DataFrame] = None,
    strategy_name: str = 'Strategy'
) -> None:
    """
    Generate all standard plots and save to directory.
    
    Args:
        returns: Series of daily returns
        portfolio_value: Optional Series of portfolio values
        transactions: Optional DataFrame of transactions
        save_dir: Directory to save plots
        strategy_name: Strategy name for titles
    """
    save_dir = Path(save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)
    
    # Equity curve
    plot_equity_curve(
        returns,
        portfolio_value=portfolio_value,
        save_path=save_dir / 'equity_curve.png',
        title=f'{strategy_name} - Equity Curve'
    )
    
    # Drawdown
    plot_drawdown(
        returns,
        save_path=save_dir / 'drawdown.png',
        title=f'{strategy_name} - Drawdown Chart'
    )
    
    # Monthly returns
    plot_monthly_returns(
        returns,
        save_path=save_dir / 'monthly_returns.png',
        title=f'{strategy_name} - Monthly Returns'
    )
    
    # Rolling metrics
    plot_rolling_metrics(
        returns,
        save_path=save_dir / 'rolling_metrics.png',
        title=f'{strategy_name} - Rolling Metrics'
    )
    
    # Trade analysis (if transactions provided)
    if transactions is not None and len(transactions) > 0:
        plot_trade_analysis(
            transactions,
            save_path=save_dir / 'trade_analysis.png',
            title=f'{strategy_name} - Trade Analysis'
        )

