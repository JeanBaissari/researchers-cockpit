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
from lib.paths import get_project_root
from lib.logging import configure_logging, get_logger, LogContext

# Configure logging (console=False since we use click.echo for user output)
configure_logging(level='INFO', console=False, file=False)
logger = get_logger(__name__)


@click.command()
@click.option('--strategy', required=True, help='Strategy name (e.g., spy_sma_cross)')
@click.option('--type', 'result_type', default='backtest',
              type=click.Choice(['backtest', 'optimization', 'walkforward']),
              help='Result type (default: backtest)')
@click.option('--output', default=None, help='Output file path (default: reports/{strategy}_report_{date}.md)')
@click.option('--asset-class', default=None, type=click.Choice(['crypto', 'forex', 'equities']),
              help='Asset class hint')
@click.option('--update-catalog', 'update_catalog_flag', is_flag=True, help='Update strategy catalog after generating report')
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
    
    # Use LogContext for structured logging
    with LogContext(phase='report_generation', strategy=strategy, result_type=result_type):
        logger.info(f"Generating {result_type} report for strategy: {strategy}")
        
        try:
            # Generate report
            logger.info("Generating report")
            output_path = generate_report(
                strategy_name=strategy,
                result_type=result_type,
                output_path=Path(output) if output else None,
                asset_class=asset_class
            )
            
            logger.info(f"Report generated: {output_path}")
            click.echo(f"\n✓ Report generated: {output_path}")
            
            # Update catalog if requested
            if update_catalog_flag:
                # Load metrics from latest results
                import json
                
                results_dir = get_project_root() / 'results' / strategy / 'latest'
                metrics_file = results_dir / 'metrics.json'
                
                if metrics_file.exists():
                    logger.info("Updating strategy catalog")
                    with open(metrics_file) as f:
                        metrics = json.load(f)
                    
                    update_catalog(
                        strategy_name=strategy,
                        status=status,
                        metrics=metrics,
                        asset_class=asset_class
                    )
                    
                    logger.info("Strategy catalog updated")
                    click.echo(f"✓ Strategy catalog updated")
                else:
                    logger.warning(f"Metrics file not found: {metrics_file}")
                    click.echo(f"⚠ Warning: Metrics file not found, catalog not updated", err=True)
            
            click.echo("\n" + "=" * 60)
            click.echo("REPORT GENERATION COMPLETE")
            click.echo("=" * 60)
            click.echo(f"Strategy: {strategy}")
            click.echo(f"Report: {output_path}")
            click.echo("=" * 60)
        
        except FileNotFoundError as e:
            logger.error(f"Report generation failed - file not found: {e}", exc_info=True)
            click.echo(f"✗ Error: Strategy '{strategy}' results not found", err=True)
            click.echo(f"  Searched in: results/{strategy}/latest/", err=True)
            click.echo(f"  Run backtest first: python scripts/run_backtest.py --strategy {strategy}", err=True)
            sys.exit(1)
        except Exception as e:
            logger.error(f"Report generation failed: {e}", exc_info=True)
            click.echo(f"✗ Error: {e}", err=True)
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == '__main__':
    main()

