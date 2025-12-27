#!/usr/bin/env python3
"""
Report generation script for The Researcher's Cockpit.

Generates markdown reports from strategy results.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import click
from lib.report import generate_report, update_catalog


@click.command()
@click.option('--strategy', required=True, help='Strategy name (e.g., spy_sma_cross)')
@click.option('--type', 'result_type', default='backtest',
              type=click.Choice(['backtest', 'optimization', 'walkforward']),
              help='Result type (default: backtest)')
@click.option('--output', default=None, help='Output file path (default: reports/{strategy}_report_{date}.md)')
@click.option('--asset-class', default=None, type=click.Choice(['crypto', 'forex', 'equities']),
              help='Asset class hint')
@click.option('--update-catalog', is_flag=True, help='Update strategy catalog after generating report')
@click.option('--status', default='testing',
              type=click.Choice(['testing', 'validated', 'abandoned']),
              help='Strategy status for catalog (default: testing)')
def main(strategy, result_type, output, asset_class, update_catalog_flag, status):
    """
    Generate a markdown report from strategy results.
    
    Examples:
        # Generate backtest report
        python scripts/generate_report.py --strategy spy_sma_cross
        
        # Generate optimization report
        python scripts/generate_report.py --strategy spy_sma_cross --type optimization
        
        # Generate report and update catalog
        python scripts/generate_report.py --strategy spy_sma_cross --update-catalog --status validated
    """
    click.echo(f"Generating {result_type} report for strategy: {strategy}")
    
    try:
        # Generate report
        output_path = generate_report(
            strategy_name=strategy,
            result_type=result_type,
            output_path=Path(output) if output else None,
            asset_class=asset_class
        )
        
        click.echo(f"\n✓ Report generated: {output_path}")
        
        # Update catalog if requested
        if update_catalog_flag:
            # Load metrics from latest results
            from lib.utils import get_project_root
            import json
            
            results_dir = get_project_root() / 'results' / strategy / 'latest'
            metrics_file = results_dir / 'metrics.json'
            
            if metrics_file.exists():
                with open(metrics_file) as f:
                    metrics = json.load(f)
                
                update_catalog(
                    strategy_name=strategy,
                    status=status,
                    metrics=metrics,
                    asset_class=asset_class
                )
                
                click.echo(f"✓ Strategy catalog updated")
            else:
                click.echo(f"⚠ Warning: Metrics file not found, catalog not updated", err=True)
        
        click.echo("\n" + "=" * 60)
        click.echo("REPORT GENERATION COMPLETE")
        click.echo("=" * 60)
        click.echo(f"Strategy: {strategy}")
        click.echo(f"Report: {output_path}")
        click.echo("=" * 60)
        
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

