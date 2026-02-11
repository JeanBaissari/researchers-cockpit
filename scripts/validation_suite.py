#!/usr/bin/env python3
"""
Comprehensive Validation Suite for The Researcher's Cockpit.

Runs a complete validation workflow to verify system integrity:
1. Data validation (OHLCV quality, bundle integrity)
2. Configuration validation (settings, strategy parameters)
3. Component validation (metrics, plots, backtest execution)
4. Integration validation (end-to-end workflows)

Usage:
    python scripts/validation_suite.py                  # Run all validations
    python scripts/validation_suite.py --quick          # Run quick checks only
    python scripts/validation_suite.py --data-only      # Run data validation only
    python scripts/validation_suite.py --component=metrics  # Run specific component
    python scripts/validation_suite.py --report         # Generate detailed report
"""

import sys
from pathlib import Path
import os

# Bootstrap: Add project root to path
_project_root_bootstrap = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_project_root_bootstrap))

from lib.paths import get_project_root

# Use canonical path resolution
project_root = get_project_root()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import click
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional
import json

from lib.logging import configure_logging, get_logger, LogContext
from lib.validation import (
    validate_before_ingest,
    validate_bundle,
    validate_backtest_results,
    ValidationConfig,
    ValidationResult,
    ValidationSeverity,
)
from lib.config.core import load_settings
from lib.bundles import list_bundles

# Configure logging
configure_logging(level="INFO", console=False, file=False)
logger = get_logger(__name__)


# =============================================================================
# VALIDATION COMPONENTS
# =============================================================================


class ValidationSuite:
    """Comprehensive validation suite for The Researcher's Cockpit."""

    def __init__(self, verbose: bool = False):
        """
        Initialize validation suite.

        Args:
            verbose: Enable verbose output
        """
        self.verbose = verbose
        self.results: Dict[str, ValidationResult] = {}
        self.start_time = datetime.now()

    def run_all(self) -> bool:
        """
        Run all validation checks.

        Returns:
            True if all checks passed, False otherwise
        """
        click.echo("=" * 80)
        click.echo("RESEARCHER'S COCKPIT - COMPREHENSIVE VALIDATION SUITE")
        click.echo("=" * 80)
        click.echo()

        with LogContext(phase="validation_suite"):
            # Run all validation components
            self.run_configuration_validation()
            self.run_data_validation()
            self.run_bundle_validation()
            self.run_component_validation()
            self.run_integration_validation()

            # Generate summary
            return self.generate_summary()

    def run_configuration_validation(self) -> bool:
        """Validate configuration files and settings."""
        click.echo("─" * 80)
        click.echo("1. CONFIGURATION VALIDATION")
        click.echo("─" * 80)

        with LogContext(phase="config_validation"):
            try:
                # Validate settings.yaml
                settings = load_settings()
                click.echo("  ✓ config/settings.yaml loaded successfully")

                # Check for common sections (flexible - not all may exist)
                common_sections = ["data", "backtest", "logging"]
                found_sections = 0
                for section in common_sections:
                    if section in settings:
                        click.echo(f"  ✓ Section '{section}' present")
                        found_sections += 1

                if found_sections > 0:
                    click.echo(f"  ✓ Configuration has {found_sections} common sections")
                else:
                    click.echo("  ⚠ Configuration appears empty", err=True)

                logger.info("Configuration validation passed")
                return True

            except Exception as e:
                logger.error(f"Configuration validation failed: {e}")
                click.echo(f"  ✗ Configuration validation failed: {e}", err=True)
                return False

    def run_data_validation(self) -> bool:
        """Validate sample OHLCV data."""
        click.echo("\n─" * 80)
        click.echo("2. DATA VALIDATION")
        click.echo("─" * 80)

        with LogContext(phase="data_validation"):
            try:
                # Create sample data for validation
                dates = pd.date_range("2024-01-01", "2024-01-10", freq="1d", tz="UTC")
                df = pd.DataFrame(
                    {
                        "open": [
                            100.0,
                            101.0,
                            102.0,
                            103.0,
                            104.0,
                            105.0,
                            106.0,
                            107.0,
                            108.0,
                            109.0,
                        ],
                        "high": [
                            101.0,
                            102.0,
                            103.0,
                            104.0,
                            105.0,
                            106.0,
                            107.0,
                            108.0,
                            109.0,
                            110.0,
                        ],
                        "low": [
                            99.0,
                            100.0,
                            101.0,
                            102.0,
                            103.0,
                            104.0,
                            105.0,
                            106.0,
                            107.0,
                            108.0,
                        ],
                        "close": [
                            100.5,
                            101.5,
                            102.5,
                            103.5,
                            104.5,
                            105.5,
                            106.5,
                            107.5,
                            108.5,
                            109.5,
                        ],
                        "volume": [1000000] * 10,
                    },
                    index=dates,
                )

                # Validate equity data
                result = validate_before_ingest(
                    df=df,
                    asset_name="SAMPLE_EQUITY",
                    timeframe="1d",
                    asset_type="equity",
                )

                self.results["data_validation_equity"] = result

                if result.passed:
                    click.echo("  ✓ Equity data validation passed")
                    if self.verbose:
                        click.echo(f"    Checks: {len(result.checks)}")
                else:
                    click.echo(
                        f"  ✗ Equity data validation failed: {len(result.error_checks)} errors"
                    )
                    if self.verbose:
                        for check in result.error_checks:
                            click.echo(f"    - {check.message}")

                logger.info(f"Data validation: {result.passed}")
                return result.passed

            except Exception as e:
                logger.error(f"Data validation failed: {e}")
                click.echo(f"  ✗ Data validation failed: {e}", err=True)
                return False

    def run_bundle_validation(self) -> bool:
        """Validate existing bundles."""
        click.echo("\n─" * 80)
        click.echo("3. BUNDLE VALIDATION")
        click.echo("─" * 80)

        with LogContext(phase="bundle_validation"):
            try:
                # List available bundles
                bundles = list_bundles()

                if not bundles:
                    click.echo("  ℹ No bundles found (this is OK for fresh installations)")
                    logger.info("No bundles to validate")
                    return True

                # Filter out default bundles that are just registered but not ingested
                default_bundles = {"quandl", "quantopian-quandl", "csvdir"}
                bundles_to_validate = [b for b in bundles if b not in default_bundles]

                if not bundles_to_validate:
                    click.echo(
                        f"  ℹ Found {len(bundles)} registered bundle(s) but none ingested yet"
                    )
                    click.echo(
                        "  ℹ This is OK for fresh installations or systems using csvdir directly"
                    )
                    logger.info("No ingested bundles to validate")
                    return True

                click.echo(f"  Found {len(bundles_to_validate)} ingested bundle(s) to validate")

                # Validate each bundle
                all_passed = True
                for bundle_name in bundles_to_validate:
                    if self.verbose:
                        click.echo(f"  Validating bundle: {bundle_name}")

                    result = validate_bundle(bundle_name)
                    self.results[f"bundle_{bundle_name}"] = result

                    if result.passed:
                        if self.verbose:
                            click.echo(f"    ✓ {bundle_name} passed")
                    else:
                        click.echo(f"    ✗ {bundle_name} failed: {len(result.error_checks)} errors")
                        all_passed = False

                if all_passed:
                    click.echo(f"  ✓ All {len(bundles_to_validate)} bundles validated successfully")
                else:
                    click.echo(f"  ✗ Some bundles failed validation")

                logger.info(f"Bundle validation: {all_passed}")
                return all_passed

            except Exception as e:
                logger.error(f"Bundle validation failed: {e}")
                click.echo(f"  ✗ Bundle validation failed: {e}", err=True)
                return False

    def run_component_validation(self) -> bool:
        """Validate individual components."""
        click.echo("\n─" * 80)
        click.echo("4. COMPONENT VALIDATION")
        click.echo("─" * 80)

        with LogContext(phase="component_validation"):
            try:
                # Test metrics module
                from lib.metrics.performance import calculate_sharpe_ratio, calculate_sortino_ratio

                # Create sample returns
                returns = pd.Series([0.01, -0.005, 0.02, -0.01, 0.015, 0.0, -0.02, 0.01])

                sharpe = calculate_sharpe_ratio(returns)
                sortino = calculate_sortino_ratio(returns)

                click.echo(f"  ✓ Metrics module: Sharpe={sharpe:.4f}, Sortino={sortino:.4f}")

                # Test logging module
                from lib.logging import configure_logging

                configure_logging(level="INFO", console=False, file=False)
                click.echo("  ✓ Logging module functional")

                # Test config module
                from lib.config.core import load_settings

                settings = load_settings()
                click.echo("  ✓ Config module functional")

                logger.info("Component validation passed")
                return True

            except Exception as e:
                logger.error(f"Component validation failed: {e}")
                click.echo(f"  ✗ Component validation failed: {e}", err=True)
                return False

    def run_integration_validation(self) -> bool:
        """Validate integration workflows."""
        click.echo("\n─" * 80)
        click.echo("5. INTEGRATION VALIDATION")
        click.echo("─" * 80)

        with LogContext(phase="integration_validation"):
            try:
                # Test complete validation workflow
                dates = pd.date_range("2024-01-01", "2024-01-10", freq="1d", tz="UTC")

                # 1. Pre-ingestion validation
                df = pd.DataFrame(
                    {
                        "open": [
                            100.0,
                            101.0,
                            102.0,
                            103.0,
                            104.0,
                            105.0,
                            106.0,
                            107.0,
                            108.0,
                            109.0,
                        ],
                        "high": [
                            101.0,
                            102.0,
                            103.0,
                            104.0,
                            105.0,
                            106.0,
                            107.0,
                            108.0,
                            109.0,
                            110.0,
                        ],
                        "low": [
                            99.0,
                            100.0,
                            101.0,
                            102.0,
                            103.0,
                            104.0,
                            105.0,
                            106.0,
                            107.0,
                            108.0,
                        ],
                        "close": [
                            100.5,
                            101.5,
                            102.5,
                            103.5,
                            104.5,
                            105.5,
                            106.5,
                            107.5,
                            108.5,
                            109.5,
                        ],
                        "volume": [1000000] * 10,
                    },
                    index=dates,
                )

                pre_result = validate_before_ingest(df, "TEST", "1d", "equity")

                # 2. Post-backtest validation
                returns_series = pd.Series(
                    [
                        0.0,
                        0.005,
                        0.0049751,
                        0.004950495,
                        0.00492610837,
                        0.00490196078,
                        0.00487804878,
                        0.00485436893,
                        0.00483091787,
                        0.00480769231,
                    ],
                    index=dates,
                )

                transactions_df = pd.DataFrame(
                    {
                        "dt": dates[:5],
                        "sid": [1, 1, 1, 1, 1],
                        "amount": [10, 10, 10, 10, 10],
                        "price": [100.0, 101.0, 102.0, 103.0, 104.0],
                    }
                )

                positions_df = pd.DataFrame(
                    {
                        "amount": [10, 20, 30, 40, 50, 50, 50, 50, 50, 50],
                        "last_sale_price": [
                            100.0,
                            101.0,
                            102.0,
                            103.0,
                            104.0,
                            105.0,
                            106.0,
                            107.0,
                            108.0,
                            109.0,
                        ],
                    },
                    index=dates,
                )

                # Create backtest results dict with metrics
                backtest_results = {
                    "total_return": 0.045,
                    "sharpe_ratio": 1.5,
                    "max_drawdown": -0.05,
                }

                post_result = validate_backtest_results(
                    backtest_results, returns_series, transactions_df, positions_df
                )

                self.results["integration_pre"] = pre_result
                self.results["integration_post"] = post_result

                if pre_result.passed and post_result.passed:
                    click.echo("  ✓ End-to-end validation workflow passed")
                    logger.info("Integration validation passed")
                    return True
                else:
                    click.echo("  ✗ Integration validation failed")
                    if not pre_result.passed:
                        click.echo(f"    Pre-ingestion: {len(pre_result.error_checks)} errors")
                    if not post_result.passed:
                        click.echo(f"    Post-backtest: {len(post_result.error_checks)} errors")
                    logger.warning("Integration validation failed")
                    return False

            except Exception as e:
                logger.error(f"Integration validation failed: {e}")
                click.echo(f"  ✗ Integration validation failed: {e}", err=True)
                return False

    def generate_summary(self) -> bool:
        """Generate validation summary."""
        click.echo("\n" + "=" * 80)
        click.echo("VALIDATION SUMMARY")
        click.echo("=" * 80)

        # Count results
        total_results = len(self.results)
        passed_results = sum(1 for r in self.results.values() if r.passed)
        failed_results = total_results - passed_results

        # Calculate totals
        total_checks = sum(len(r.checks) for r in self.results.values())
        total_errors = sum(len(r.error_checks) for r in self.results.values())
        total_warnings = sum(len(r.warning_checks) for r in self.results.values())

        # Display summary
        click.echo(f"Total validation runs: {total_results}")
        click.echo(f"Passed: {passed_results}")
        click.echo(f"Failed: {failed_results}")
        click.echo(f"\nTotal checks performed: {total_checks}")
        click.echo(f"Errors found: {total_errors}")
        click.echo(f"Warnings found: {total_warnings}")

        # Execution time
        elapsed = (datetime.now() - self.start_time).total_seconds()
        click.echo(f"\nExecution time: {elapsed:.2f}s")

        # Overall status
        click.echo("\n" + "=" * 80)
        if failed_results == 0:
            click.echo("✓ ALL VALIDATION CHECKS PASSED")
            click.echo("=" * 80)
            logger.info("Validation suite completed successfully")
            return True
        else:
            click.echo("✗ SOME VALIDATION CHECKS FAILED")
            click.echo("=" * 80)
            logger.warning(f"Validation suite completed with {failed_results} failures")
            return False

    def generate_report(self, output_path: Optional[Path] = None) -> None:
        """
        Generate detailed validation report.

        Args:
            output_path: Path to save report (default: results/validation_report.json)
        """
        if output_path is None:
            output_path = get_project_root() / "results" / "validation_report.json"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_results": len(self.results),
                "passed": sum(1 for r in self.results.values() if r.passed),
                "failed": sum(1 for r in self.results.values() if not r.passed),
                "total_checks": sum(len(r.checks) for r in self.results.values()),
                "total_errors": sum(len(r.error_checks) for r in self.results.values()),
                "total_warnings": sum(len(r.warning_checks) for r in self.results.values()),
            },
            "results": {
                name: {
                    "passed": result.passed,
                    "checks": len(result.checks),
                    "errors": len(result.error_checks),
                    "warnings": len(result.warning_checks),
                    "error_messages": [c.message for c in result.error_checks],
                    "warning_messages": [c.message for c in result.warning_checks],
                }
                for name, result in self.results.items()
            },
        }

        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)

        click.echo(f"\nDetailed report saved to: {output_path}")
        logger.info(f"Validation report saved to {output_path}")


# =============================================================================
# CLI COMMAND
# =============================================================================


@click.command()
@click.option("--quick", is_flag=True, help="Run quick checks only (skip integration tests)")
@click.option("--data-only", is_flag=True, help="Run data validation only")
@click.option("--bundles-only", is_flag=True, help="Run bundle validation only")
@click.option("--component", type=str, help="Run specific component validation")
@click.option("--report", is_flag=True, help="Generate detailed validation report")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def main(quick, data_only, bundles_only, component, report, verbose):
    """
    Run comprehensive validation suite for The Researcher's Cockpit.

    Examples:
        python scripts/validation_suite.py                  # Run all validations
        python scripts/validation_suite.py --quick          # Quick checks only
        python scripts/validation_suite.py --data-only      # Data validation only
        python scripts/validation_suite.py --bundles-only   # Bundle validation only
        python scripts/validation_suite.py --report         # Generate report
        python scripts/validation_suite.py --verbose        # Verbose output
    """
    suite = ValidationSuite(verbose=verbose)

    try:
        if data_only:
            success = suite.run_data_validation()
        elif bundles_only:
            success = suite.run_bundle_validation()
        elif component:
            # Run specific component
            if component == "config":
                success = suite.run_configuration_validation()
            elif component == "data":
                success = suite.run_data_validation()
            elif component == "bundles":
                success = suite.run_bundle_validation()
            elif component == "components":
                success = suite.run_component_validation()
            elif component == "integration":
                success = suite.run_integration_validation()
            else:
                click.echo(f"Unknown component: {component}", err=True)
                sys.exit(1)
        else:
            # Run all validations
            success = suite.run_all()

        # Generate report if requested
        if report:
            suite.generate_report()

        # Exit with appropriate code
        sys.exit(0 if success else 1)

    except Exception as e:
        logger.error(f"Validation suite failed with error: {e}", exc_info=True)
        click.echo(f"\n✗ Validation suite failed with error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
