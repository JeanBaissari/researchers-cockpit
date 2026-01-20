"""
Strategy catalog management module.

Manages the strategy catalog with status and performance metrics.
"""

from datetime import datetime
from typing import Optional, Dict, Any

from ..utils import get_project_root, ensure_dir
from ..strategies import get_strategy_path


def update_catalog(
    strategy_name: str,
    status: str,
    metrics: Dict[str, Any],
    asset_class: Optional[str] = None
) -> None:
    """
    Update strategy catalog with strategy status and metrics.
    
    Args:
        strategy_name: Name of strategy
        status: Status ('testing', 'validated', 'abandoned')
        metrics: Dictionary of metrics
        asset_class: Optional asset class hint
    """
    root = get_project_root()
    catalog_file = root / 'docs' / 'strategy_catalog.md'
    
    # Load existing catalog or create new
    if catalog_file.exists():
        catalog_content = catalog_file.read_text()
    else:
        catalog_content = _create_catalog_template()
    
    # Update or add strategy entry
    catalog_content = _update_catalog_entry(
        catalog_content=catalog_content,
        strategy_name=strategy_name,
        status=status,
        metrics=metrics,
        asset_class=asset_class
    )
    
    # Write updated catalog
    ensure_dir(catalog_file.parent)
    catalog_file.write_text(catalog_content)


def _create_catalog_template() -> str:
    """Create catalog template."""
    return """# Strategy Catalog

> Index of all strategies with status and performance metrics.

| Strategy | Asset | Status | Sharpe | Sortino | MaxDD | Last Updated |
|----------|-------|--------|--------|---------|-------|--------------|
"""


def _update_catalog_entry(
    catalog_content: str,
    strategy_name: str,
    status: str,
    metrics: Dict[str, Any],
    asset_class: Optional[str] = None
) -> str:
    """
    Update or add catalog entry.
    
    Args:
        catalog_content: Current catalog markdown content
        strategy_name: Name of strategy
        status: Status string
        metrics: Performance metrics dictionary
        asset_class: Optional asset class
        
    Returns:
        Updated catalog content
    """
    # Extract asset class from strategy name if not provided
    if asset_class is None:
        try:
            strategy_path = get_strategy_path(strategy_name)
            asset_class = strategy_path.parent.name
        except:
            asset_class = 'unknown'
    
    sharpe = metrics.get('sharpe', 0)
    sortino = metrics.get('sortino', 0)
    max_dd = metrics.get('max_drawdown', 0)
    date_str = datetime.now().strftime('%Y-%m-%d')
    
    # Format metrics
    sharpe_str = f"{sharpe:.2f}" if sharpe else "N/A"
    sortino_str = f"{sortino:.2f}" if sortino else "N/A"
    max_dd_str = f"{max_dd:.1%}" if max_dd else "N/A"
    
    # Build entry line
    entry_line = (
        f"| {strategy_name} | {asset_class} | {status} | "
        f"{sharpe_str} | {sortino_str} | {max_dd_str} | {date_str} |"
    )
    
    # Check if entry exists and update
    lines = catalog_content.split('\n')
    found = False
    for i, line in enumerate(lines):
        if line.startswith(f"| {strategy_name} |"):
            lines[i] = entry_line
            found = True
            break
    
    # Add new entry if not found
    if not found:
        table_end = _find_table_end(lines)
        lines.insert(table_end, entry_line)
    
    return '\n'.join(lines)


def _find_table_end(lines: list) -> int:
    """Find the end of the markdown table."""
    table_end = len(lines)
    for i, line in enumerate(lines):
        if line.startswith('|') and 'Strategy' in line:
            continue
        elif line.startswith('|'):
            continue
        else:
            table_end = i
            break
    return table_end















