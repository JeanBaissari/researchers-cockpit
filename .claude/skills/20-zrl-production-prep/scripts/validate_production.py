#!/usr/bin/env python3
"""Validate strategy production readiness.

Usage:
    python validate_production.py --strategy path/to/strategy.py
    python validate_production.py --strategy strategy.py --config config.yaml
    python validate_production.py --strategy strategy.py --strict
"""

import argparse
import ast
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import importlib.util
import yaml
import json


@dataclass
class ValidationResult:
    """Result of a validation check."""
    category: str
    check_name: str
    passed: bool
    message: str
    severity: str = "error"  # error, warning, info
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationReport:
    """Complete validation report."""
    strategy_path: str
    results: List[ValidationResult] = field(default_factory=list)
    
    @property
    def passed(self) -> bool:
        """Check if all critical validations passed."""
        return all(r.passed for r in self.results if r.severity == "error")
    
    @property
    def error_count(self) -> int:
        return sum(1 for r in self.results if not r.passed and r.severity == "error")
    
    @property
    def warning_count(self) -> int:
        return sum(1 for r in self.results if not r.passed and r.severity == "warning")
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'strategy_path': self.strategy_path,
            'passed': self.passed,
            'error_count': self.error_count,
            'warning_count': self.warning_count,
            'results': [
                {
                    'category': r.category,
                    'check_name': r.check_name,
                    'passed': r.passed,
                    'message': r.message,
                    'severity': r.severity,
                    'details': r.details
                }
                for r in self.results
            ]
        }


class ProductionValidator:
    """Validate strategy for production readiness."""
    
    REQUIRED_FUNCTIONS = ['initialize', 'handle_data']
    RECOMMENDED_FUNCTIONS = ['before_trading_start', 'analyze']
    
    RISK_PATTERNS = [
        'set_max_position_size',
        'set_max_order_size',
        'set_max_leverage',
    ]
    
    LOGGING_PATTERNS = [
        'log.info', 'log.warning', 'log.error',
        'logger.info', 'logger.warning', 'logger.error',
        'logging.info', 'logging.warning'
    ]
    
    def __init__(self, strategy_path: str, config_path: str = None, strict: bool = False):
        self.strategy_path = Path(strategy_path)
        self.config_path = Path(config_path) if config_path else None
        self.strict = strict
        self.report = ValidationReport(strategy_path=str(self.strategy_path))
        self.source_code = ""
        self.ast_tree = None
        self.config = {}
    
    def validate(self) -> ValidationReport:
        """Run all validation checks."""
        # Load source
        if not self._load_source():
            return self.report
        
        # Load config if provided
        if self.config_path:
            self._load_config()
        
        # Run checks
        self._check_file_exists()
        self._check_required_functions()
        self._check_recommended_functions()
        self._check_error_handling()
        self._check_logging()
        self._check_risk_controls()
        self._check_hardcoded_values()
        self._check_docstrings()
        self._check_type_hints()
        self._check_external_dependencies()
        self._check_config_usage()
        
        if self.config:
            self._check_config_completeness()
        
        return self.report
    
    def _load_source(self) -> bool:
        """Load and parse source code."""
        try:
            self.source_code = self.strategy_path.read_text()
            self.ast_tree = ast.parse(self.source_code)
            return True
        except FileNotFoundError:
            self.report.results.append(ValidationResult(
                category="file",
                check_name="file_exists",
                passed=False,
                message=f"Strategy file not found: {self.strategy_path}",
                severity="error"
            ))
            return False
        except SyntaxError as e:
            self.report.results.append(ValidationResult(
                category="syntax",
                check_name="syntax_valid",
                passed=False,
                message=f"Syntax error: {e}",
                severity="error"
            ))
            return False
    
    def _load_config(self):
        """Load configuration file."""
        try:
            if self.config_path.suffix in ['.yaml', '.yml']:
                self.config = yaml.safe_load(self.config_path.read_text())
            elif self.config_path.suffix == '.json':
                self.config = json.loads(self.config_path.read_text())
        except Exception as e:
            self.report.results.append(ValidationResult(
                category="config",
                check_name="config_loadable",
                passed=False,
                message=f"Failed to load config: {e}",
                severity="warning"
            ))
    
    def _check_file_exists(self):
        """Verify strategy file exists."""
        self.report.results.append(ValidationResult(
            category="file",
            check_name="file_exists",
            passed=True,
            message="Strategy file exists",
            severity="error"
        ))
    
    def _check_required_functions(self):
        """Check for required functions."""
        functions = self._get_function_names()
        
        for func in self.REQUIRED_FUNCTIONS:
            passed = func in functions
            self.report.results.append(ValidationResult(
                category="structure",
                check_name=f"has_{func}",
                passed=passed,
                message=f"Required function '{func}' {'found' if passed else 'missing'}",
                severity="error"
            ))
    
    def _check_recommended_functions(self):
        """Check for recommended functions."""
        functions = self._get_function_names()
        
        for func in self.RECOMMENDED_FUNCTIONS:
            passed = func in functions
            self.report.results.append(ValidationResult(
                category="structure",
                check_name=f"has_{func}",
                passed=passed,
                message=f"Recommended function '{func}' {'found' if passed else 'not found'}",
                severity="warning" if self.strict else "info"
            ))
    
    def _check_error_handling(self):
        """Check for try/except blocks."""
        try_count = sum(1 for node in ast.walk(self.ast_tree) 
                       if isinstance(node, ast.Try))
        
        passed = try_count >= 1
        self.report.results.append(ValidationResult(
            category="resilience",
            check_name="error_handling",
            passed=passed,
            message=f"Found {try_count} try/except blocks",
            severity="warning",
            details={'try_except_count': try_count}
        ))
    
    def _check_logging(self):
        """Check for logging usage."""
        has_logging = any(pattern in self.source_code 
                         for pattern in self.LOGGING_PATTERNS)
        
        self.report.results.append(ValidationResult(
            category="observability",
            check_name="logging",
            passed=has_logging,
            message="Logging " + ("found" if has_logging else "not found"),
            severity="warning"
        ))
    
    def _check_risk_controls(self):
        """Check for risk control setup."""
        risk_controls_found = []
        
        for pattern in self.RISK_PATTERNS:
            if pattern in self.source_code:
                risk_controls_found.append(pattern)
        
        passed = len(risk_controls_found) > 0
        self.report.results.append(ValidationResult(
            category="risk",
            check_name="risk_controls",
            passed=passed,
            message=f"Found {len(risk_controls_found)} risk controls",
            severity="error" if self.strict else "warning",
            details={'controls_found': risk_controls_found}
        ))
    
    def _check_hardcoded_values(self):
        """Check for hardcoded trading values (anti-pattern)."""
        issues = []
        
        for node in ast.walk(self.ast_tree):
            if isinstance(node, ast.Call):
                # Check for hardcoded amounts in order functions
                func_name = self._get_call_name(node)
                if func_name in ['order', 'order_value', 'order_target', 
                                 'order_target_percent', 'order_target_value']:
                    for arg in node.args[1:]:  # Skip asset argument
                        if isinstance(arg, ast.Constant) and isinstance(arg.value, (int, float)):
                            if arg.value > 100:  # Likely a hardcoded share count
                                issues.append(f"Hardcoded value {arg.value} in {func_name}")
        
        passed = len(issues) == 0
        self.report.results.append(ValidationResult(
            category="quality",
            check_name="no_hardcoded_values",
            passed=passed,
            message=f"Found {len(issues)} potential hardcoded values",
            severity="warning",
            details={'issues': issues[:5]}  # Limit details
        ))
    
    def _check_docstrings(self):
        """Check for function docstrings."""
        functions = [node for node in ast.walk(self.ast_tree) 
                    if isinstance(node, ast.FunctionDef)]
        
        documented = sum(1 for f in functions if ast.get_docstring(f))
        total = len(functions)
        
        coverage = documented / total if total > 0 else 0
        passed = coverage >= 0.5  # At least 50% documented
        
        self.report.results.append(ValidationResult(
            category="quality",
            check_name="docstrings",
            passed=passed,
            message=f"Documentation coverage: {coverage:.0%} ({documented}/{total})",
            severity="info",
            details={'documented': documented, 'total': total}
        ))
    
    def _check_type_hints(self):
        """Check for type hints on functions."""
        functions = [node for node in ast.walk(self.ast_tree) 
                    if isinstance(node, ast.FunctionDef)]
        
        typed = sum(1 for f in functions 
                   if f.returns is not None or any(a.annotation for a in f.args.args))
        total = len(functions)
        
        coverage = typed / total if total > 0 else 0
        passed = coverage >= 0.3  # At least 30% with hints
        
        self.report.results.append(ValidationResult(
            category="quality",
            check_name="type_hints",
            passed=passed,
            message=f"Type hint coverage: {coverage:.0%} ({typed}/{total})",
            severity="info",
            details={'typed': typed, 'total': total}
        ))
    
    def _check_external_dependencies(self):
        """Check for external dependencies."""
        imports = []
        
        for node in ast.walk(self.ast_tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        
        # Standard safe imports
        safe_imports = {'zipline', 'pandas', 'numpy', 'scipy', 'datetime', 
                       'collections', 'itertools', 'functools', 'math'}
        
        external = [imp for imp in imports 
                   if not any(imp.startswith(s) for s in safe_imports)]
        
        self.report.results.append(ValidationResult(
            category="dependencies",
            check_name="external_deps",
            passed=True,  # Informational
            message=f"Found {len(external)} external dependencies",
            severity="info",
            details={'external_imports': external}
        ))
    
    def _check_config_usage(self):
        """Check if configuration is externalized."""
        config_patterns = ['config.get', 'config[', 'context.config', 
                          'os.environ', 'os.getenv']
        
        uses_config = any(pattern in self.source_code for pattern in config_patterns)
        
        self.report.results.append(ValidationResult(
            category="configuration",
            check_name="config_externalized",
            passed=uses_config,
            message="Configuration " + ("externalized" if uses_config else "may be hardcoded"),
            severity="warning" if self.strict else "info"
        ))
    
    def _check_config_completeness(self):
        """Check if config has required sections."""
        required_sections = ['strategy', 'risk']
        recommended_sections = ['execution', 'monitoring']
        
        for section in required_sections:
            passed = section in self.config
            self.report.results.append(ValidationResult(
                category="configuration",
                check_name=f"config_has_{section}",
                passed=passed,
                message=f"Config section '{section}' {'present' if passed else 'missing'}",
                severity="error"
            ))
        
        for section in recommended_sections:
            passed = section in self.config
            self.report.results.append(ValidationResult(
                category="configuration",
                check_name=f"config_has_{section}",
                passed=passed,
                message=f"Config section '{section}' {'present' if passed else 'missing'}",
                severity="warning"
            ))
    
    def _get_function_names(self) -> List[str]:
        """Get all function names in the module."""
        return [node.name for node in ast.walk(self.ast_tree) 
                if isinstance(node, ast.FunctionDef)]
    
    def _get_call_name(self, node: ast.Call) -> str:
        """Get the name of a function call."""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return node.func.attr
        return ""


def format_report(report: ValidationReport, verbose: bool = False) -> str:
    """Format validation report for display."""
    lines = []
    lines.append("=" * 60)
    lines.append("PRODUCTION READINESS VALIDATION REPORT")
    lines.append("=" * 60)
    lines.append(f"Strategy: {report.strategy_path}")
    lines.append(f"Status: {'PASSED' if report.passed else 'FAILED'}")
    lines.append(f"Errors: {report.error_count}, Warnings: {report.warning_count}")
    lines.append("-" * 60)
    
    # Group by category
    categories = {}
    for result in report.results:
        if result.category not in categories:
            categories[result.category] = []
        categories[result.category].append(result)
    
    for category, results in sorted(categories.items()):
        lines.append(f"\n[{category.upper()}]")
        for r in results:
            if not verbose and r.passed and r.severity == "info":
                continue
            
            status = "✓" if r.passed else ("!" if r.severity == "warning" else "✗")
            lines.append(f"  {status} {r.check_name}: {r.message}")
            
            if verbose and r.details:
                for k, v in r.details.items():
                    lines.append(f"      {k}: {v}")
    
    lines.append("\n" + "=" * 60)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='Validate strategy production readiness'
    )
    parser.add_argument('--strategy', required=True, help='Path to strategy file')
    parser.add_argument('--config', help='Path to config file')
    parser.add_argument('--strict', action='store_true', help='Strict validation mode')
    parser.add_argument('--output', help='Output file for JSON report')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    validator = ProductionValidator(
        strategy_path=args.strategy,
        config_path=args.config,
        strict=args.strict
    )
    
    report = validator.validate()
    
    # Display report
    print(format_report(report, verbose=args.verbose))
    
    # Save JSON if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(report.to_dict(), f, indent=2)
        print(f"\nJSON report saved to: {args.output}")
    
    # Exit code based on validation
    sys.exit(0 if report.passed else 1)


if __name__ == '__main__':
    main()
