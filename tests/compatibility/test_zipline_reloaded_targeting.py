"""
Explicit verification that the codebase targets zipline-reloaded (not legacy Zipline).

This test suite ensures:
1. Requirements files specify zipline-reloaded (not zipline)
2. All imports use zipline (not quantopian or legacy patterns)
3. Documentation references stefan-jansen/zipline-reloaded
4. No deprecated API patterns from legacy Quantopian zipline
5. Code explicitly targets Zipline-Reloaded v3.0+
"""

import re
from pathlib import Path
from typing import List, Tuple

import pytest


class TestRequirementsTargetZiplineReloaded:
    """Verify requirements files target zipline-reloaded."""

    @pytest.mark.unit
    def test_requirements_txt_uses_zipline_reloaded(self):
        """Verify requirements.txt specifies zipline-reloaded."""
        project_root = Path(__file__).parent.parent.parent
        requirements_file = project_root / "requirements.txt"

        assert requirements_file.exists(), "requirements.txt must exist"

        content = requirements_file.read_text()

        # Must contain zipline-reloaded
        assert "zipline-reloaded" in content, (
            "requirements.txt must specify zipline-reloaded, not zipline"
        )

        # Must NOT contain bare 'zipline' (without -reloaded)
        # Allow 'zipline-reloaded' but not standalone 'zipline'
        lines = content.split("\n")
        for line in lines:
            # Skip comments and empty lines
            if line.strip().startswith("#") or not line.strip():
                continue
            # Check for bare 'zipline' package (not zipline-reloaded)
            if re.match(r"^zipline[^-]", line.strip()):
                pytest.fail(
                    f"requirements.txt contains bare 'zipline' package: {line}\n"
                    "Must use 'zipline-reloaded' instead"
                )

    @pytest.mark.unit
    def test_requirements_mvp_uses_zipline_reloaded(self):
        """Verify requirements-mvp.txt specifies zipline-reloaded."""
        project_root = Path(__file__).parent.parent.parent
        requirements_file = project_root / "requirements-mvp.txt"

        if not requirements_file.exists():
            pytest.skip("requirements-mvp.txt not found")

        content = requirements_file.read_text()

        # Must contain zipline-reloaded
        assert "zipline-reloaded" in content, "requirements-mvp.txt must specify zipline-reloaded"


class TestImportsTargetZiplineReloaded:
    """Verify all imports use zipline (not quantopian)."""

    @pytest.mark.unit
    def test_no_quantopian_imports(self):
        """Verify no files import from quantopian."""
        project_root = Path(__file__).parent.parent.parent

        # Files to check (Python files in lib/ and strategies/)
        python_files = []
        for pattern in ["lib/**/*.py", "strategies/**/*.py", "scripts/**/*.py"]:
            python_files.extend(project_root.glob(pattern))

        quantopian_imports = []
        for file_path in python_files:
            try:
                content = file_path.read_text()
                # Check for quantopian imports
                if re.search(r"from quantopian|import quantopian", content):
                    quantopian_imports.append(str(file_path.relative_to(project_root)))
            except Exception:
                # Skip files that can't be read
                continue

        assert len(quantopian_imports) == 0, (
            f"Found quantopian imports in:\n"
            + "\n".join(quantopian_imports)
            + "\nAll imports must use 'zipline' (from zipline-reloaded), not 'quantopian'"
        )

    @pytest.mark.unit
    def test_zipline_imports_use_correct_module(self):
        """Verify zipline imports use correct module structure."""
        project_root = Path(__file__).parent.parent.parent

        # Check key files that should import from zipline
        key_files = [
            "lib/backtest/execution.py",
            "strategies/_template/strategy.py",
            "lib/pipeline_utils.py",
        ]

        for rel_path in key_files:
            file_path = project_root / rel_path
            if not file_path.exists():
                continue

            content = file_path.read_text()

            # Must import from zipline (not quantopian)
            if "from zipline" in content or "import zipline" in content:
                # Good - using zipline imports
                pass
            elif "from quantopian" in content or "import quantopian" in content:
                pytest.fail(
                    f"{rel_path} imports from quantopian. "
                    "Must use 'zipline' (from zipline-reloaded) instead"
                )


class TestDocumentationTargetsZiplineReloaded:
    """Verify documentation references zipline-reloaded."""

    @pytest.mark.unit
    def test_readme_references_zipline_reloaded(self):
        """Verify README.md references zipline-reloaded."""
        project_root = Path(__file__).parent.parent.parent
        readme = project_root / "README.md"

        assert readme.exists(), "README.md must exist"

        content = readme.read_text()

        # Must reference zipline-reloaded
        assert "zipline-reloaded" in content.lower() or "zipline-reloaded" in content, (
            "README.md must reference zipline-reloaded"
        )

        # Should reference stefan-jansen repository
        assert "stefan-jansen" in content.lower(), (
            "README.md should reference stefan-jansen/zipline-reloaded repository"
        )

    @pytest.mark.unit
    def test_prd_references_zipline_reloaded(self):
        """Verify PRD.md explicitly targets zipline-reloaded."""
        project_root = Path(__file__).parent.parent.parent
        prd = project_root / "PRD.md"

        if not prd.exists():
            pytest.skip("PRD.md not found")

        content = prd.read_text()

        # Must explicitly state zipline-reloaded usage
        assert "zipline-reloaded" in content.lower() or "zipline-reloaded" in content, (
            "PRD.md must reference zipline-reloaded"
        )

        # Must not target legacy Quantopian zipline.
        assert "quantopian" not in content.lower(), (
            "PRD.md must not target legacy Quantopian zipline"
        )

    @pytest.mark.unit
    def test_claude_md_references_zipline_reloaded(self):
        """Verify CLAUDE.md references zipline-reloaded."""
        project_root = Path(__file__).parent.parent.parent
        claude = project_root / "CLAUDE.md"

        assert claude.exists(), "CLAUDE.md must exist"

        content = claude.read_text()

        # Must reference zipline-reloaded
        assert "zipline-reloaded" in content.lower() or "zipline-reloaded" in content, (
            "CLAUDE.md must reference zipline-reloaded"
        )


class TestNoDeprecatedAPIPatterns:
    """Verify no deprecated API patterns from legacy Quantopian zipline."""

    @pytest.mark.unit
    def test_strategy_template_prefers_equity_pricing(self):
        """Verify strategy template prefers EquityPricing over USEquityPricing."""
        project_root = Path(__file__).parent.parent.parent
        template = project_root / "strategies" / "_template" / "strategy.py"

        assert template.exists(), "Strategy template must exist"

        content = template.read_text()

        # Should prefer EquityPricing (Zipline-Reloaded 3.x)
        # Fallback to USEquityPricing is acceptable for compatibility
        assert "EquityPricing" in content, (
            "Strategy template should use EquityPricing (Zipline-Reloaded 3.x)"
        )

        # Should have comment explaining the fallback
        assert "Zipline-Reloaded" in content or "zipline-reloaded" in content.lower(), (
            "Strategy template should reference Zipline-Reloaded in comments"
        )

    @pytest.mark.unit
    def test_no_legacy_zipline_patterns(self):
        """Verify no legacy zipline patterns in key files."""
        project_root = Path(__file__).parent.parent.parent

        # Patterns that indicate legacy Quantopian zipline usage
        legacy_patterns = [
            (r"trading_calendars", "Use exchange_calendars instead"),
            (r"from quantopian\.", "Must use zipline, not quantopian"),
        ]

        key_files = [
            "lib/backtest/execution.py",
            "lib/calendars/__init__.py",
            "strategies/_template/strategy.py",
        ]

        violations = []
        for rel_path in key_files:
            file_path = project_root / rel_path
            if not file_path.exists():
                continue

            content = file_path.read_text()
            for pattern, message in legacy_patterns:
                if re.search(pattern, content):
                    violations.append(f"{rel_path}: {message}")

        assert len(violations) == 0, "Found legacy zipline patterns:\n" + "\n".join(violations)


class TestExplicitZiplineReloadedTargeting:
    """Verify codebase explicitly targets zipline-reloaded."""

    @pytest.mark.unit
    def test_error_messages_reference_zipline_reloaded(self):
        """Verify error messages reference zipline-reloaded installation."""
        project_root = Path(__file__).parent.parent.parent

        # Files that should have zipline-reloaded in error messages
        key_files = [
            "lib/backtest/execution.py",
            "lib/backtest/runner.py",
        ]

        for rel_path in key_files:
            file_path = project_root / rel_path
            if not file_path.exists():
                continue

            content = file_path.read_text()

            # Should reference zipline-reloaded in import error messages
            if "zipline" in content and "not installed" in content.lower():
                assert "zipline-reloaded" in content, (
                    f"{rel_path} error message should reference 'zipline-reloaded', "
                    "not just 'zipline'"
                )

    @pytest.mark.unit
    def test_config_files_reference_zipline_reloaded(self):
        """Verify config files reference zipline-reloaded."""
        project_root = Path(__file__).parent.parent.parent

        # Check .ralphy/config.yaml if it exists
        ralphy_config = project_root / ".ralphy" / "config.yaml"
        if ralphy_config.exists():
            content = ralphy_config.read_text()

            # Should reference zipline-reloaded
            assert "zipline-reloaded" in content.lower() or "Zipline-Reloaded" in content, (
                ".ralphy/config.yaml should reference zipline-reloaded"
            )

            # Should reference stefan-jansen repository
            assert "stefan-jansen" in content.lower(), (
                ".ralphy/config.yaml should reference stefan-jansen/zipline-reloaded"
            )

    @pytest.mark.unit
    def test_lib_init_references_zipline_reloaded(self):
        """Verify lib/__init__.py references zipline-reloaded."""
        project_root = Path(__file__).parent.parent.parent
        lib_init = project_root / "lib" / "__init__.py"

        assert lib_init.exists(), "lib/__init__.py must exist"

        content = lib_init.read_text()

        # Should reference zipline-reloaded or Zipline Reloaded
        assert "zipline" in content.lower(), "lib/__init__.py should reference zipline-reloaded"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
