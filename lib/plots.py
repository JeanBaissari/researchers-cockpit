"""
Visualization module for The Researcher's Cockpit.

Provides comprehensive plotting functions for backtest results analysis.
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
    import matplotlib.dates as mdates
    import matplotlib.pyplot as plt
    import seaborn as sns
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
    monthly_returns = (1 + returns).resample('M').prod() - 1
    
    # Create year-month matrix
    monthly_returns.index = pd.to_datetime(monthly_returns.index)
    monthly_returns['year'] = monthly_returns.index.year
    monthly_returns['month'] = monthly_returns.index.month
    
    pivot_data = monthly_returns.pivot_table(
        values=monthly_returns.name if monthly_returns.name else 'returns',
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
    ax.set_xticklabels([month_labels[i-1] if i <= 12 else '' for i in ax.get_xticks()], rotation=0)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()


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
    from .metrics import _extract_trades
    
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
    
    from .metrics import calculate_rolling_metrics
    
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


def _plot_optimization_heatmap(
    results_df: pd.DataFrame,
    param_grid: dict,
    objective: str,
    save_dir: Path
) -> None:
    """
    Plot optimization heatmap for 2-parameter grid search.
    
    Args:
        results_df: DataFrame with optimization results
        param_grid: Parameter grid dictionary
        objective: Objective metric name
        save_dir: Directory to save plot
    """
    if not MATPLOTLIB_AVAILABLE:
        return
    
    if len(param_grid) != 2:
        return
    
    param_names = list(param_grid.keys())
    test_obj_col = f'test_{objective}'
    
    if test_obj_col not in results_df.columns:
        return
    
    # Create pivot table
    pivot_data = results_df.pivot_table(
        values=test_obj_col,
        index=param_names[0],
        columns=param_names[1],
        aggfunc='mean'
    )
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    sns.heatmap(
        pivot_data,
        annot=True,
        fmt='.3f',
        cmap='RdYlGn',
        center=0,
        cbar_kws={'label': f'Test {objective.capitalize()}'},
        ax=ax,
        linewidths=0.5,
        linecolor='gray'
    )
    
    ax.set_xlabel(param_names[1], fontsize=12)
    ax.set_ylabel(param_names[0], fontsize=12)
    ax.set_title(f'Optimization Heatmap - {objective.capitalize()}', fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(save_dir / f'heatmap_{objective}.png', dpi=150, bbox_inches='tight')
    plt.close()


def _plot_monte_carlo_distribution(
    simulation_results: dict,
    save_dir: Path
) -> None:
    """
    Plot Monte Carlo simulation distribution.
    
    Args:
        simulation_results: Dictionary with simulation results
        save_dir: Directory to save plot
    """
    if not MATPLOTLIB_AVAILABLE:
        return
    
    if 'simulation_paths' not in simulation_results:
        return
    
    paths_df = simulation_results['simulation_paths']
    final_values = paths_df.iloc[-1].values if len(paths_df) > 0 else []
    
    if len(final_values) == 0:
        return
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    ax.hist(final_values, bins=50, alpha=0.7, color='#2E86AB', edgecolor='black')
    ax.axvline(np.mean(final_values), color='red', linestyle='--', linewidth=2, label='Mean')
    
    # Add confidence intervals
    if 'confidence_intervals' in simulation_results:
        ci = simulation_results['confidence_intervals']
        for key, value in ci.items():
            ax.axvline(value, color='green', linestyle='--', linewidth=1, alpha=0.7, label=f'{key}')
    
    ax.set_xlabel('Final Portfolio Value ($)', fontsize=12)
    ax.set_ylabel('Frequency', fontsize=12)
    ax.set_title('Monte Carlo Simulation - Final Value Distribution', fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(save_dir / 'distribution.png', dpi=150, bbox_inches='tight')
    plt.close()

