"""
Test v1.12.0 NO WRAPPERS compliance for lib/bundles/.

Verifies that lib/bundles/ uses Zipline bundle APIs directly without wrappers.
"""

import ast
import inspect
from pathlib import Path
from typing import List, Set

import pytest


def get_bundle_module_files() -> List[Path]:
    """Get all Python files in lib/bundles/."""
    bundle_dir = Path(__file__).parent.parent.parent / "lib" / "bundles"
    return list(bundle_dir.rglob("*.py"))


def extract_imports_from_file(file_path: Path) -> Set[str]:
    """Extract all import statements from a Python file."""
    imports = set()

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=str(file_path))

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module)
                    for alias in node.names:
                        imports.add(f"{node.module}.{alias.name}")
    except Exception:
        pass  # Skip files that can't be parsed

    return imports


def extract_function_calls_from_file(file_path: Path) -> Set[str]:
    """Extract function calls from a Python file."""
    calls = set()

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=str(file_path))

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    calls.add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    # Get full attribute path (e.g., "zipline.data.bundles.register")
                    parts = []
                    current = node.func
                    while isinstance(current, ast.Attribute):
                        parts.append(current.attr)
                        current = current.value
                    if isinstance(current, ast.Name):
                        parts.append(current.id)
                        calls.add(".".join(reversed(parts)))
    except Exception:
        pass

    return calls


class TestV1120Compliance:
    """Test v1.12.0 NO WRAPPERS compliance."""

    def test_all_zipline_imports_are_direct(self):
        """Verify all Zipline imports are direct (no wrapper modules)."""
        bundle_files = get_bundle_module_files()
        direct_zipline_imports = set()
        indirect_imports = set()

        for file_path in bundle_files:
            # Skip __init__.py and test files
            if file_path.name == "__init__.py" or "test" in file_path.name.lower():
                continue

            imports = extract_imports_from_file(file_path)

            # Check for direct Zipline imports
            for imp in imports:
                if imp.startswith("zipline."):
                    direct_zipline_imports.add(imp)
                # Check for indirect imports through lib modules
                elif imp.startswith("lib.") and "zipline" in str(file_path.read_text()):
                    # This is a heuristic - check if file actually uses zipline
                    content = file_path.read_text()
                    if "from zipline" in content or "import zipline" in content:
                        # File has direct imports, which is good
                        pass
                    else:
                        indirect_imports.add(f"{file_path.name}: {imp}")

        # All Zipline imports should be direct
        assert len(indirect_imports) == 0, (
            f"Found indirect Zipline imports (violates v1.12.0): {indirect_imports}"
        )

        # Should have at least some direct Zipline imports
        assert len(direct_zipline_imports) > 0, "No direct Zipline imports found in lib/bundles/"

    def test_no_registry_module_references(self):
        """Verify no references to deleted registry module."""
        bundle_files = get_bundle_module_files()
        registry_references = []

        for file_path in bundle_files:
            if file_path.name == "__init__.py" or "test" in file_path.name.lower():
                continue

            content = file_path.read_text()

            # Check for registry imports (should be removed in v1.12.0)
            if "from ..registry import" in content or "from .registry import" in content:
                registry_references.append(f"{file_path}: registry import")
            if "load_bundle_registry" in content and "def load_bundle_registry" not in content:
                # Reference to function but not definition (should be removed)
                registry_references.append(f"{file_path}: load_bundle_registry reference")

        assert len(registry_references) == 0, (
            f"Found references to deleted registry module (v1.12.0 violation): "
            f"{registry_references}"
        )

    def test_no_guard_module_references(self):
        """Verify no references to deleted guard module."""
        bundle_files = get_bundle_module_files()
        guard_references = []

        for file_path in bundle_files:
            if file_path.name == "__init__.py" or "test" in file_path.name.lower():
                continue

            content = file_path.read_text()

            # Check for guard imports (should be removed in v1.12.0)
            if "from ..guard import" in content or "from .guard import" in content:
                guard_references.append(f"{file_path}: guard import")

        assert len(guard_references) == 0, (
            f"Found references to deleted guard module (v1.12.0 violation): {guard_references}"
        )

    def test_zipline_api_usage_is_direct(self):
        """Verify Zipline APIs are used directly, not through wrappers."""
        bundle_files = get_bundle_module_files()
        direct_api_usage = []
        wrapper_patterns = []

        # Expected direct Zipline API patterns (check for these in file content)
        expected_direct_api_patterns = [
            "from zipline.data.bundles import",
            "zipline.data.bundles.register",
            "zipline.data.bundles.ingest",
            "zipline.data.bundles.load",
            "zipline.data.bundles.bundles",
            "zipline.data.bundles.unregister",
            "zipline.utils.calendar_utils.get_calendar",
            "zipline.data.bundles.csvdir.csvdir_equities",
        ]

        for file_path in bundle_files:
            if file_path.name == "__init__.py" or "test" in file_path.name.lower():
                continue

            content = file_path.read_text()

            # Check for direct Zipline API usage in file content
            for pattern in expected_direct_api_patterns:
                if pattern in content:
                    direct_api_usage.append(f"{file_path.name}: {pattern}")

            # Check for wrapper patterns (functions that wrap Zipline APIs)
            # This is a heuristic - look for function definitions that might be wrappers
            try:
                tree = ast.parse(content, filename=str(file_path))
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # Check if function name suggests it's a wrapper
                        if any(
                            pattern in node.name.lower()
                            for pattern in ["wrap", "abstract", "facade"]
                        ):
                            wrapper_patterns.append(f"{file_path.name}: {node.name}")
            except SyntaxError:
                pass  # Skip files with syntax errors

        # Should have direct API usage
        assert len(direct_api_usage) > 0, (
            f"No direct Zipline API usage found in lib/bundles/. "
            f"Expected patterns: {expected_direct_api_patterns}"
        )

        # Should not have obvious wrapper patterns
        # (This is a soft check - some functions may legitimately have these names)
        if wrapper_patterns:
            # Log but don't fail - these might be false positives
            print(f"Warning: Potential wrapper patterns found: {wrapper_patterns}")

    def test_access_functions_use_direct_apis(self):
        """Verify access.py uses Zipline APIs directly."""
        from lib.bundles import access

        # Check that load_bundle uses direct Zipline API
        source = inspect.getsource(access.load_bundle)
        assert "from zipline.data.bundles import" in source, (
            "load_bundle should import directly from zipline.data.bundles"
        )
        assert "load(" in source or "bundles[" in source, (
            "load_bundle should use Zipline's load() or bundles dict directly"
        )

        # Check that list_bundles uses direct Zipline API
        source = inspect.getsource(access.list_bundles)
        assert "from zipline.data.bundles import" in source, (
            "list_bundles should import directly from zipline.data.bundles"
        )
        assert "bundles.keys()" in source or "list(bundles" in source, (
            "list_bundles should use Zipline's bundles dict directly"
        )

    def test_management_functions_use_direct_apis(self):
        """Verify management.py uses Zipline APIs directly."""
        from lib.bundles import management

        # Check that ingest_bundle uses direct Zipline API
        source = inspect.getsource(management.ingest_bundle)
        assert "from zipline.data.bundles import" in source or "zipline.data.bundles" in source, (
            "ingest_bundle should use Zipline APIs directly"
        )
        assert "ingest(" in source, "ingest_bundle should call Zipline's ingest() directly"

    def test_yahoo_registration_uses_direct_apis(self):
        """Verify yahoo/registration.py uses Zipline APIs directly."""
        from lib.bundles.yahoo import registration

        # Check that register_yahoo_bundle uses direct Zipline API
        source = inspect.getsource(registration.register_yahoo_bundle)
        assert "from zipline.data.bundles import" in source or "zipline.data.bundles" in source, (
            "register_yahoo_bundle should use Zipline APIs directly"
        )
        assert "@register(" in source or "register(" in source, (
            "register_yahoo_bundle should use Zipline's @register decorator directly"
        )

        # Check that auto_register function doesn't use deleted registry
        source = inspect.getsource(registration.auto_register_yahoo_bundle_if_exists)
        assert "from ..registry import" not in source, (
            "auto_register_yahoo_bundle_if_exists should not import deleted registry module"
        )
        assert "load_bundle_registry" not in source, (
            "auto_register_yahoo_bundle_if_exists should not use deleted load_bundle_registry function"
        )
