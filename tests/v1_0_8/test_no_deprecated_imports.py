"""
Test that no deprecated imports exist in v1.0.8 codebase.

This test ensures that all legacy wrapper files have been removed and
no code uses deprecated import paths.
"""

import pytest
import subprocess
from pathlib import Path

project_root = Path(__file__).parent.parent.parent


class TestDeprecatedFilesRemoved:
    """Test that deprecated wrapper files no longer exist."""
    
    def test_data_loader_removed(self):
        """Test that lib/data_loader.py has been removed."""
        deprecated_file = project_root / 'lib' / 'data_loader.py'
        assert not deprecated_file.exists(), "lib/data_loader.py should be removed"
    
    def test_data_validation_removed(self):
        """Test that lib/data_validation.py has been removed."""
        deprecated_file = project_root / 'lib' / 'data_validation.py'
        assert not deprecated_file.exists(), "lib/data_validation.py should be removed"
    
    def test_data_integrity_removed(self):
        """Test that lib/data_integrity.py has been removed."""
        deprecated_file = project_root / 'lib' / 'data_integrity.py'
        assert not deprecated_file.exists(), "lib/data_integrity.py should be removed"
    
    def test_logging_config_removed(self):
        """Test that lib/logging_config.py has been removed."""
        deprecated_file = project_root / 'lib' / 'logging_config.py'
        assert not deprecated_file.exists(), "lib/logging_config.py should be removed"
    
    def test_optimize_wrapper_removed(self):
        """Test that lib/optimize.py wrapper has been removed."""
        # Note: lib/optimize/ package should exist, but not lib/optimize.py wrapper
        wrapper_file = project_root / 'lib' / 'optimize.py'
        package_dir = project_root / 'lib' / 'optimize'
        assert not wrapper_file.exists(), "lib/optimize.py wrapper should be removed"
        assert package_dir.exists(), "lib/optimize/ package should exist"
    
    def test_validate_wrapper_removed(self):
        """Test that lib/validate.py wrapper has been removed."""
        # Note: lib/validate/ package should exist, but not lib/validate.py wrapper
        wrapper_file = project_root / 'lib' / 'validate.py'
        package_dir = project_root / 'lib' / 'validate'
        assert not wrapper_file.exists(), "lib/validate.py wrapper should be removed"
        assert package_dir.exists(), "lib/validate/ package should exist"
    
    def test_extension_wrapper_removed(self):
        """Test that lib/extension.py has been removed."""
        deprecated_file = project_root / 'lib' / 'extension.py'
        assert not deprecated_file.exists(), "lib/extension.py should be removed"
        
        # lib/calendars/ package should exist
        calendars_package = project_root / 'lib' / 'calendars'
        assert calendars_package.exists(), "lib/calendars/ package should exist"


class TestNoDeprecatedImportsInScripts:
    """Test that scripts don't use deprecated imports."""
    
    def test_no_data_loader_imports_in_scripts(self):
        """Test that scripts don't import from lib.data_loader."""
        scripts_dir = project_root / 'scripts'
        if not scripts_dir.exists():
            pytest.skip("scripts/ directory not found")
        
        for script in scripts_dir.glob('*.py'):
            content = script.read_text()
            assert 'from lib.data_loader' not in content, \
                f"{script.name} uses deprecated 'from lib.data_loader'"
            assert 'import lib.data_loader' not in content, \
                f"{script.name} uses deprecated 'import lib.data_loader'"
    
    def test_no_data_validation_imports_in_scripts(self):
        """Test that scripts don't import from lib.data_validation."""
        scripts_dir = project_root / 'scripts'
        if not scripts_dir.exists():
            pytest.skip("scripts/ directory not found")
        
        for script in scripts_dir.glob('*.py'):
            content = script.read_text()
            assert 'from lib.data_validation' not in content, \
                f"{script.name} uses deprecated 'from lib.data_validation'"
            assert 'import lib.data_validation' not in content, \
                f"{script.name} uses deprecated 'import lib.data_validation'"
    
    def test_no_logging_config_imports_in_scripts(self):
        """Test that scripts don't import from lib.logging_config."""
        scripts_dir = project_root / 'scripts'
        if not scripts_dir.exists():
            pytest.skip("scripts/ directory not found")
        
        for script in scripts_dir.glob('*.py'):
            content = script.read_text()
            assert 'from lib.logging_config' not in content, \
                f"{script.name} uses deprecated 'from lib.logging_config'"
            assert 'import lib.logging_config' not in content, \
                f"{script.name} uses deprecated 'import lib.logging_config'"


class TestNoDeprecatedImportsInLib:
    """Test that lib/ modules don't use deprecated imports."""
    
    def test_lib_init_has_no_fallbacks(self):
        """Test that lib/__init__.py has no backward-compat fallbacks."""
        lib_init = project_root / 'lib' / '__init__.py'
        if not lib_init.exists():
            pytest.skip("lib/__init__.py not found")
        
        content = lib_init.read_text()
        
        # Should not have try/except fallback patterns
        assert 'from .data_loader' not in content, \
            "lib/__init__.py should not import from .data_loader"
        assert 'from .data_validation' not in content, \
            "lib/__init__.py should not import from .data_validation"
        assert 'from .data_integrity' not in content, \
            "lib/__init__.py should not import from .data_integrity"
        assert 'from .logging_config' not in content, \
            "lib/__init__.py should not import from .logging_config"
        assert 'from .extension' not in content, \
            "lib/__init__.py should not import from .extension"
    
    def test_no_deprecated_imports_in_lib_modules(self):
        """Test that no lib/ module imports deprecated paths."""
        lib_dir = project_root / 'lib'
        if not lib_dir.exists():
            pytest.skip("lib/ directory not found")
        
        deprecated_patterns = [
            'from lib.data_loader',
            'import lib.data_loader',
            'from lib.data_validation',
            'import lib.data_validation',
            'from lib.data_integrity',
            'import lib.data_integrity',
            'from lib.logging_config',
            'import lib.logging_config',
        ]
        
        # Check all Python files in lib/
        for py_file in lib_dir.rglob('*.py'):
            if py_file.name == '__pycache__':
                continue
            
            content = py_file.read_text()
            for pattern in deprecated_patterns:
                assert pattern not in content, \
                    f"{py_file.relative_to(project_root)} uses deprecated '{pattern}'"


class TestNoDeprecatedImportsInTests:
    """Test that tests don't use deprecated imports."""
    
    def test_no_deprecated_imports_in_new_tests(self):
        """Test that v1_0_8 tests don't use deprecated imports."""
        tests_dir = project_root / 'tests' / 'v1_0_8'
        if not tests_dir.exists():
            pytest.skip("tests/v1_0_8/ directory not found")
        
        deprecated_patterns = [
            'from lib.data_loader',
            'import lib.data_loader',
            'from lib.data_validation',
            'import lib.data_validation',
            'from lib.data_integrity',
            'import lib.data_integrity',
            'from lib.logging_config',
            'import lib.logging_config',
        ]
        
        for test_file in tests_dir.glob('test_*.py'):
            content = test_file.read_text()
            for pattern in deprecated_patterns:
                assert pattern not in content, \
                    f"{test_file.name} uses deprecated '{pattern}'"


class TestStrategyTemplateClean:
    """Test that strategy template uses modern imports."""
    
    def test_template_no_deprecated_imports(self):
        """Test that strategy template doesn't use deprecated imports."""
        template_file = project_root / 'strategies' / '_template' / 'strategy.py'
        if not template_file.exists():
            pytest.skip("Strategy template not found")
        
        content = template_file.read_text()
        
        # Should use modern imports
        deprecated_patterns = [
            'from lib.data_loader',
            'import lib.data_loader',
            'from lib.data_validation',
            'import lib.data_validation',
        ]
        
        for pattern in deprecated_patterns:
            assert pattern not in content, \
                f"Strategy template uses deprecated '{pattern}'"
    
    def test_template_no_fallback_path_resolution(self):
        """Test that strategy template doesn't have complex fallback logic."""
        template_file = project_root / 'strategies' / '_template' / 'strategy.py'
        if not template_file.exists():
            pytest.skip("Strategy template not found")
        
        content = template_file.read_text()
        
        # Should not have try/except fallback for lib.utils
        # (This was mentioned in the plan as needing removal)
        fallback_indicators = [
            'if not hasattr(sys.modules.get',
            'manual fallback',
            'lib.utils not available',
        ]
        
        for indicator in fallback_indicators:
            if indicator in content.lower():
                pytest.fail(
                    f"Strategy template still has fallback logic containing: {indicator}"
                )


class TestGrepForDeprecatedPatterns:
    """Use grep to ensure no deprecated patterns exist."""
    
    @pytest.mark.slow
    def test_grep_no_data_loader_imports(self):
        """Grep for any remaining data_loader imports."""
        result = subprocess.run(
            ['grep', '-r', 'from lib.data_loader', str(project_root), 
             '--include=*.py', '--exclude-dir=venv', '--exclude-dir=.venv'],
            capture_output=True,
            text=True
        )
        
        # Grep returns 0 if found, 1 if not found
        assert result.returncode == 1, \
            f"Found deprecated 'from lib.data_loader' imports:\n{result.stdout}"
    
    @pytest.mark.slow
    def test_grep_no_data_validation_imports(self):
        """Grep for any remaining data_validation imports."""
        result = subprocess.run(
            ['grep', '-r', 'from lib.data_validation', str(project_root),
             '--include=*.py', '--exclude-dir=venv', '--exclude-dir=.venv'],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 1, \
            f"Found deprecated 'from lib.data_validation' imports:\n{result.stdout}"
    
    @pytest.mark.slow
    def test_grep_no_logging_config_imports(self):
        """Grep for any remaining logging_config imports."""
        result = subprocess.run(
            ['grep', '-r', 'from lib.logging_config', str(project_root),
             '--include=*.py', '--exclude-dir=venv', '--exclude-dir=.venv'],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 1, \
            f"Found deprecated 'from lib.logging_config' imports:\n{result.stdout}"

