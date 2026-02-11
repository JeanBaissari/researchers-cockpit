#!/usr/bin/env python3
"""
Hypothesis lifecycle management CLI for The Researcher's Cockpit.

Manage trading hypotheses from creation through validation/rejection.
Link hypotheses to backtest results and track research progress.

Examples:
    # Create new hypothesis
    python scripts/hypothesis.py create "BTC momentum persistence" --asset-class crypto

    # List hypotheses by status
    python scripts/hypothesis.py list --status testing

    # Update hypothesis status
    python scripts/hypothesis.py update 2026-02_btc_momentum --status validated

    # Link backtest to hypothesis
    python scripts/hypothesis.py link 2026-02_btc_momentum backtest_20260210_143022

    # Search by tag
    python scripts/hypothesis.py search --tags momentum

    # Show hypothesis details
    python scripts/hypothesis.py show 2026-02_btc_momentum
"""

import sys
from pathlib import Path

# Bootstrap: Add project root to path
_project_root_bootstrap = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_project_root_bootstrap))

from lib.paths import get_project_root, ProjectRootNotFoundError

# Use canonical path resolution
project_root = get_project_root()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import click
from datetime import datetime
from typing import Optional, List

from lib.research import (
    HypothesisStatus,
    Hypothesis,
    create_hypothesis,
    save_hypothesis,
    load_hypothesis,
    list_hypotheses,
    link_backtest,
)
from lib.logging import configure_logging, get_logger

# Configure logging (console=False since we use click.echo for user output)
configure_logging(level="INFO", console=False, file=False)
logger = get_logger(__name__)


@click.group()
def cli():
    """Hypothesis management for trading research."""
    pass


@cli.command()
@click.argument("title")
@click.option(
    "--asset-class",
    required=True,
    type=click.Choice(["crypto", "forex", "equities"]),
    help="Asset class for hypothesis",
)
@click.option("--description", default="", help="Detailed hypothesis description")
@click.option("--symbols", multiple=True, help="Symbols to test (can specify multiple)")
@click.option("--timeframe", default="daily", help="Timeframe for testing (e.g., daily, 1h, 5m)")
@click.option("--tags", multiple=True, help="Tags for categorization (can specify multiple)")
def create(
    title: str, asset_class: str, description: str, symbols: tuple, timeframe: str, tags: tuple
):
    """
    Create a new hypothesis with DRAFT status.

    Example:
        python scripts/hypothesis.py create "BTC momentum persistence" --asset-class crypto --tags momentum --tags crypto
    """
    try:
        logger.info(f"Creating hypothesis: {title}")

        # Create hypothesis
        hyp = create_hypothesis(
            title=title,
            asset_class=asset_class,
            description=description,
            symbols=list(symbols) if symbols else [],
            timeframe=timeframe,
            tags=list(tags) if tags else [],
        )

        # Save to file
        file_path = save_hypothesis(hyp)

        click.echo(f"✓ Created hypothesis: {hyp.id}")
        click.echo(f"  Status: {hyp.status.value}")
        # Try to get relative path, fall back to absolute if not in project
        try:
            rel_path = file_path.relative_to(get_project_root())
            click.echo(f"  File: {rel_path}")
        except ValueError:
            click.echo(f"  File: {file_path}")
        click.echo(f"  Next: Edit {file_path.name} to add rationale and expected metrics")

        logger.info(f"Created hypothesis {hyp.id} at {file_path}")

    except Exception as e:
        logger.error(f"Failed to create hypothesis: {e}", exc_info=True)
        click.echo(f"✗ Error creating hypothesis: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--status",
    type=click.Choice(["draft", "testing", "validated", "rejected"]),
    help="Filter by status",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "list", "detailed"]),
    default="table",
    help="Output format",
)
def list(status: Optional[str], output_format: str):
    """
    List hypotheses with optional status filter.

    Example:
        python scripts/hypothesis.py list --status testing
    """
    try:
        # Convert status string to enum
        status_filter = HypothesisStatus(status) if status else None

        # Load hypotheses
        hypotheses = list_hypotheses(status_filter)

        if not hypotheses:
            click.echo("No hypotheses found.")
            if status:
                click.echo(f"Try: python scripts/hypothesis.py list (without --status)")
            return

        # Display based on format
        if output_format == "table":
            _display_table(hypotheses)
        elif output_format == "list":
            _display_list(hypotheses)
        else:  # detailed
            _display_detailed(hypotheses)

        click.echo(f"\nTotal: {len(hypotheses)} hypothesis(es)")

    except Exception as e:
        logger.error(f"Failed to list hypotheses: {e}", exc_info=True)
        click.echo(f"✗ Error listing hypotheses: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("hypothesis_id")
@click.option(
    "--status",
    type=click.Choice(["draft", "testing", "validated", "rejected"]),
    help="Update hypothesis status",
)
@click.option("--strategy", help="Set strategy name")
@click.option("--conclusion", help="Set conclusion (for validated/rejected)")
@click.option("--learnings", help="Set key learnings")
@click.option("--actual-sharpe", type=float, help="Actual Sharpe ratio from testing")
@click.option("--actual-drawdown", type=float, help="Actual max drawdown from testing")
def update(
    hypothesis_id: str,
    status: Optional[str],
    strategy: Optional[str],
    conclusion: Optional[str],
    learnings: Optional[str],
    actual_sharpe: Optional[float],
    actual_drawdown: Optional[float],
):
    """
    Update hypothesis fields.

    Example:
        python scripts/hypothesis.py update 2026-02_btc_momentum --status validated --conclusion "Hypothesis confirmed"
    """
    try:
        # Load hypothesis
        hyp = load_hypothesis(hypothesis_id)

        # Update fields
        updated_fields = []
        if status:
            hyp.status = HypothesisStatus(status)
            updated_fields.append(f"status → {status}")
        if strategy:
            hyp.strategy_name = strategy
            updated_fields.append(f"strategy → {strategy}")
        if conclusion:
            hyp.conclusion = conclusion
            updated_fields.append("conclusion updated")
        if learnings:
            hyp.learnings = learnings
            updated_fields.append("learnings updated")
        if actual_sharpe is not None:
            hyp.actual_sharpe = actual_sharpe
            updated_fields.append(f"actual_sharpe → {actual_sharpe}")
        if actual_drawdown is not None:
            hyp.actual_max_drawdown = actual_drawdown
            updated_fields.append(f"actual_max_drawdown → {actual_drawdown}")

        # Update timestamp
        hyp.updated = datetime.now().strftime("%Y-%m-%d")

        # Save
        file_path = save_hypothesis(hyp)

        click.echo(f"✓ Updated hypothesis: {hypothesis_id}")
        for field in updated_fields:
            click.echo(f"  - {field}")

        logger.info(f"Updated hypothesis {hypothesis_id}: {updated_fields}")

    except FileNotFoundError:
        click.echo(f"✗ Error: Hypothesis '{hypothesis_id}' not found", err=True)
        click.echo(f"  Run: python scripts/hypothesis.py list", err=True)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to update hypothesis: {e}", exc_info=True)
        click.echo(f"✗ Error updating hypothesis: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("hypothesis_id")
@click.argument("backtest_id")
def link(hypothesis_id: str, backtest_id: str):
    """
    Link a backtest to a hypothesis.

    Example:
        python scripts/hypothesis.py link 2026-02_btc_momentum backtest_20260210_143022
    """
    try:
        # Link backtest
        link_backtest(hypothesis_id, backtest_id)

        click.echo(f"✓ Linked backtest {backtest_id} to hypothesis {hypothesis_id}")

        logger.info(f"Linked backtest {backtest_id} to hypothesis {hypothesis_id}")

    except FileNotFoundError:
        click.echo(f"✗ Error: Hypothesis '{hypothesis_id}' not found", err=True)
        click.echo(f"  Run: python scripts/hypothesis.py list", err=True)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to link backtest: {e}", exc_info=True)
        click.echo(f"✗ Error linking backtest: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--tags", multiple=True, help="Filter by tags (can specify multiple)")
@click.option(
    "--asset-class",
    type=click.Choice(["crypto", "forex", "equities"]),
    help="Filter by asset class",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "list", "detailed"]),
    default="table",
    help="Output format",
)
def search(tags: tuple, asset_class: Optional[str], output_format: str):
    """
    Search hypotheses by tags or asset class.

    Example:
        python scripts/hypothesis.py search --tags momentum --tags crypto
    """
    try:
        # Load all hypotheses
        hypotheses = list_hypotheses()

        # Filter by tags
        if tags:
            tags_set = set(tags)
            hypotheses = [h for h in hypotheses if tags_set.intersection(h.tags)]

        # Filter by asset class
        if asset_class:
            hypotheses = [h for h in hypotheses if h.asset_class == asset_class]

        if not hypotheses:
            click.echo("No hypotheses found matching criteria.")
            return

        # Display based on format
        if output_format == "table":
            _display_table(hypotheses)
        elif output_format == "list":
            _display_list(hypotheses)
        else:  # detailed
            _display_detailed(hypotheses)

        click.echo(f"\nTotal: {len(hypotheses)} hypothesis(es)")

    except Exception as e:
        logger.error(f"Failed to search hypotheses: {e}", exc_info=True)
        click.echo(f"✗ Error searching hypotheses: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("hypothesis_id")
def show(hypothesis_id: str):
    """
    Show detailed hypothesis information.

    Example:
        python scripts/hypothesis.py show 2026-02_btc_momentum
    """
    try:
        # Load hypothesis
        hyp = load_hypothesis(hypothesis_id)

        # Display details
        click.echo(f"\n{'=' * 80}")
        click.echo(f"Hypothesis: {hyp.id}")
        click.echo(f"{'=' * 80}")
        click.echo(f"\nTitle: {hyp.title}")
        click.echo(f"Status: {hyp.status.value}")
        click.echo(f"Created: {hyp.created}")
        click.echo(f"Updated: {hyp.updated}")

        click.echo(f"\n--- Hypothesis Details ---")
        click.echo(f"Asset Class: {hyp.asset_class}")
        click.echo(f"Symbols: {', '.join(hyp.symbols) if hyp.symbols else 'Not specified'}")
        click.echo(f"Timeframe: {hyp.timeframe}")
        if hyp.description:
            click.echo(f"Description: {hyp.description}")

        click.echo(f"\n--- Rationale ---")
        click.echo(f"Why: {hyp.why if hyp.why else 'Not specified'}")
        click.echo(
            f"Prior Evidence: {hyp.prior_evidence if hyp.prior_evidence else 'Not specified'}"
        )
        click.echo(
            f"Expected Sharpe: {hyp.expected_sharpe if hyp.expected_sharpe else 'Not specified'}"
        )
        click.echo(
            f"Expected Max Drawdown: {hyp.expected_max_drawdown if hyp.expected_max_drawdown else 'Not specified'}"
        )

        click.echo(f"\n--- Testing ---")
        click.echo(f"Strategy: {hyp.strategy_name if hyp.strategy_name else 'Not specified'}")
        if hyp.backtest_ids:
            click.echo(f"Backtests ({len(hyp.backtest_ids)}):")
            for backtest_id in hyp.backtest_ids:
                click.echo(f"  - {backtest_id}")
        else:
            click.echo("Backtests: None linked")
        if hyp.parameter_ranges:
            click.echo(f"Parameter Ranges: {hyp.parameter_ranges}")

        click.echo(f"\n--- Results ---")
        click.echo(f"Actual Sharpe: {hyp.actual_sharpe if hyp.actual_sharpe else 'Not tested'}")
        click.echo(
            f"Actual Max Drawdown: {hyp.actual_max_drawdown if hyp.actual_max_drawdown else 'Not tested'}"
        )
        if hyp.conclusion:
            click.echo(f"Conclusion: {hyp.conclusion}")
        if hyp.learnings:
            click.echo(f"Learnings: {hyp.learnings}")

        if hyp.tags:
            click.echo(f"\n--- Tags ---")
            click.echo(f"{', '.join(hyp.tags)}")

        click.echo(f"\n{'=' * 80}\n")

    except FileNotFoundError:
        click.echo(f"✗ Error: Hypothesis '{hypothesis_id}' not found", err=True)
        click.echo(f"  Run: python scripts/hypothesis.py list", err=True)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to show hypothesis: {e}", exc_info=True)
        click.echo(f"✗ Error showing hypothesis: {e}", err=True)
        sys.exit(1)


# Display helpers


def _display_table(hypotheses: List[Hypothesis]):
    """Display hypotheses in table format."""
    click.echo(f"\n{'ID':<30} {'Status':<12} {'Asset Class':<12} {'Title':<40}")
    click.echo("-" * 100)
    for hyp in sorted(hypotheses, key=lambda h: h.updated, reverse=True):
        title_short = hyp.title[:37] + "..." if len(hyp.title) > 40 else hyp.title
        click.echo(f"{hyp.id:<30} {hyp.status.value:<12} {hyp.asset_class:<12} {title_short:<40}")


def _display_list(hypotheses: List[Hypothesis]):
    """Display hypotheses in simple list format."""
    for hyp in sorted(hypotheses, key=lambda h: h.updated, reverse=True):
        click.echo(f"- {hyp.id} [{hyp.status.value}] {hyp.title}")


def _display_detailed(hypotheses: List[Hypothesis]):
    """Display hypotheses with detailed information."""
    for i, hyp in enumerate(sorted(hypotheses, key=lambda h: h.updated, reverse=True)):
        if i > 0:
            click.echo()
        click.echo(f"ID: {hyp.id}")
        click.echo(f"  Title: {hyp.title}")
        click.echo(f"  Status: {hyp.status.value}")
        click.echo(f"  Asset Class: {hyp.asset_class}")
        click.echo(f"  Created: {hyp.created}, Updated: {hyp.updated}")
        if hyp.tags:
            click.echo(f"  Tags: {', '.join(hyp.tags)}")
        if hyp.backtest_ids:
            click.echo(f"  Backtests: {len(hyp.backtest_ids)}")


if __name__ == "__main__":
    try:
        cli()
    except ProjectRootNotFoundError as e:
        click.echo(f"✗ Error: Cannot find project root: {e}", err=True)
        click.echo("  Set PROJECT_ROOT environment variable to override.", err=True)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Script failed: {e}", exc_info=True)
        click.echo(f"✗ Unexpected error: {e}", err=True)
        sys.exit(1)
