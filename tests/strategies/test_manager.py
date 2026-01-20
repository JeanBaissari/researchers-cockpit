"""
Tests for strategy management utilities.

Tests for:
- get_strategy_path()
- create_strategy()
- create_strategy_from_template()
- check_and_fix_symlinks()
"""

# Standard library imports
import sys
import shutil
from pathlib import Path

# Third-party imports
import pytest

# Local imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from lib.strategies import (
    get_strategy_path,
    create_strategy,
    create_strategy_from_template,
    check_and_fix_symlinks,
)
from lib.paths import get_project_root


class TestGetStrategyPath:
    """Tests for get_strategy_path() function."""

    @pytest.mark.unit
    def test_get_strategy_path_with_asset_class(self, project_root_path):
        """Test getting strategy path with specific asset class."""
        # Create a test strategy directory
        test_strategy = 'test_sma_cross'
        test_asset = 'equities'
        strategy_path = project_root_path / 'strategies' / test_asset / test_strategy
        strategy_path.mkdir(parents=True, exist_ok=True)
        
        try:
            result = get_strategy_path(test_strategy, test_asset)
            assert result == strategy_path
            assert result.exists()
        finally:
            # Cleanup
            if strategy_path.exists():
                shutil.rmtree(strategy_path)

    @pytest.mark.unit
    def test_get_strategy_path_without_asset_class(self, project_root_path):
        """Test getting strategy path without asset class (searches all)."""
        # Create a test strategy in crypto
        test_strategy = 'test_btc_strategy'
        test_asset = 'crypto'
        strategy_path = project_root_path / 'strategies' / test_asset / test_strategy
        strategy_path.mkdir(parents=True, exist_ok=True)
        
        try:
            result = get_strategy_path(test_strategy)
            assert result == strategy_path
            assert result.exists()
        finally:
            # Cleanup
            if strategy_path.exists():
                shutil.rmtree(strategy_path)

    @pytest.mark.unit
    def test_get_strategy_path_not_found(self, project_root_path):
        """Test get_strategy_path raises FileNotFoundError for non-existent strategy."""
        with pytest.raises(FileNotFoundError) as exc_info:
            get_strategy_path('nonexistent_strategy_xyz123')
        
        assert 'nonexistent_strategy_xyz123' in str(exc_info.value)
        assert 'not found' in str(exc_info.value).lower()

    @pytest.mark.unit
    def test_get_strategy_path_wrong_asset_class(self, project_root_path):
        """Test get_strategy_path with wrong asset class."""
        # Create strategy in crypto
        test_strategy = 'test_forex_strategy'
        strategy_path = project_root_path / 'strategies' / 'crypto' / test_strategy
        strategy_path.mkdir(parents=True, exist_ok=True)
        
        try:
            # Try to find in wrong asset class
            with pytest.raises(FileNotFoundError):
                get_strategy_path(test_strategy, 'forex')
        finally:
            # Cleanup
            if strategy_path.exists():
                shutil.rmtree(strategy_path)


class TestCreateStrategy:
    """Tests for create_strategy() function."""

    @pytest.mark.unit
    def test_create_strategy_from_template(self, project_root_path):
        """Test creating strategy from template."""
        test_strategy = 'test_new_strategy'
        test_asset = 'equities'
        strategy_path = project_root_path / 'strategies' / test_asset / test_strategy
        
        # Ensure template exists
        template_path = project_root_path / 'strategies' / '_template'
        if not template_path.exists():
            pytest.skip("Template directory does not exist")
        
        try:
            result = create_strategy(test_strategy, test_asset, from_template=True)
            assert result == strategy_path
            assert result.exists()
            assert (result / 'strategy.py').exists() or (result / 'parameters.yaml').exists()
        finally:
            # Cleanup
            if strategy_path.exists():
                shutil.rmtree(strategy_path)

    @pytest.mark.unit
    def test_create_strategy_without_template(self, project_root_path):
        """Test creating strategy without template."""
        test_strategy = 'test_empty_strategy'
        test_asset = 'equities'
        strategy_path = project_root_path / 'strategies' / test_asset / test_strategy
        
        try:
            result = create_strategy(test_strategy, test_asset, from_template=False)
            assert result == strategy_path
            assert result.exists()
        finally:
            # Cleanup
            if strategy_path.exists():
                shutil.rmtree(strategy_path)

    @pytest.mark.unit
    def test_create_strategy_already_exists(self, project_root_path):
        """Test create_strategy raises ValueError if strategy already exists."""
        test_strategy = 'test_existing_strategy'
        test_asset = 'equities'
        strategy_path = project_root_path / 'strategies' / test_asset / test_strategy
        strategy_path.mkdir(parents=True, exist_ok=True)
        
        try:
            with pytest.raises(ValueError) as exc_info:
                create_strategy(test_strategy, test_asset)
            assert 'already exists' in str(exc_info.value).lower()
        finally:
            # Cleanup
            if strategy_path.exists():
                shutil.rmtree(strategy_path)

    @pytest.mark.unit
    def test_create_strategy_template_not_found(self, project_root_path, monkeypatch):
        """Test create_strategy raises FileNotFoundError if template doesn't exist."""
        test_strategy = 'test_no_template_strategy'
        test_asset = 'equities'
        strategy_path = project_root_path / 'strategies' / test_asset / test_strategy
        
        # Mock template path to not exist
        original_get_root = get_project_root
        def mock_get_root():
            root = original_get_root()
            # Temporarily rename template if it exists
            template = root / 'strategies' / '_template'
            if template.exists():
                temp_name = root / 'strategies' / '_template_backup'
                if temp_name.exists():
                    shutil.rmtree(temp_name)
                template.rename(temp_name)
            return root
        
        monkeypatch.setattr('lib.strategies.manager.get_project_root', mock_get_root)
        
        try:
            with pytest.raises(FileNotFoundError) as exc_info:
                create_strategy(test_strategy, test_asset, from_template=True)
            assert 'template' in str(exc_info.value).lower()
        finally:
            # Restore template if it was renamed
            root = get_project_root()
            template_backup = root / 'strategies' / '_template_backup'
            if template_backup.exists():
                template = root / 'strategies' / '_template'
                if template.exists():
                    shutil.rmtree(template)
                template_backup.rename(template)
            
            # Cleanup strategy if created
            if strategy_path.exists():
                shutil.rmtree(strategy_path)


class TestCreateStrategyFromTemplate:
    """Tests for create_strategy_from_template() function."""

    @pytest.mark.unit
    def test_create_strategy_from_template_basic(self, project_root_path):
        """Test creating strategy from template with asset symbol."""
        test_strategy = 'test_template_strategy'
        test_asset = 'equities'
        asset_symbol = 'SPY'
        strategy_path = project_root_path / 'strategies' / test_asset / test_strategy
        
        # Ensure template exists
        template_path = project_root_path / 'strategies' / '_template'
        if not template_path.exists():
            pytest.skip("Template directory does not exist")
        
        try:
            result = create_strategy_from_template(
                name=test_strategy,
                asset_class=test_asset,
                asset_symbol=asset_symbol
            )
            
            assert result == strategy_path
            assert result.exists()
            
            # Check that parameters.yaml was updated
            params_path = result / 'parameters.yaml'
            if params_path.exists():
                import yaml
                with open(params_path, 'r') as f:
                    params = yaml.safe_load(f)
                assert 'strategy' in params
                assert params['strategy']['asset_symbol'] == asset_symbol
            
            # Check that results directory and symlink were created
            results_dir = project_root_path / 'results' / test_strategy
            assert results_dir.exists()
            results_link = result / 'results'
            assert results_link.exists() or results_link.is_symlink()
        finally:
            # Cleanup
            if strategy_path.exists():
                shutil.rmtree(strategy_path)
            results_dir = project_root_path / 'results' / test_strategy
            if results_dir.exists():
                shutil.rmtree(results_dir)

    @pytest.mark.unit
    def test_create_strategy_from_template_already_exists(self, project_root_path):
        """Test create_strategy_from_template raises ValueError if strategy exists."""
        test_strategy = 'test_existing_template_strategy'
        test_asset = 'equities'
        strategy_path = project_root_path / 'strategies' / test_asset / test_strategy
        strategy_path.mkdir(parents=True, exist_ok=True)
        
        try:
            with pytest.raises(ValueError) as exc_info:
                create_strategy_from_template(
                    name=test_strategy,
                    asset_class=test_asset,
                    asset_symbol='SPY'
                )
            assert 'already exists' in str(exc_info.value).lower()
        finally:
            # Cleanup
            if strategy_path.exists():
                shutil.rmtree(strategy_path)


class TestCheckAndFixSymlinks:
    """Tests for check_and_fix_symlinks() function."""

    @pytest.mark.unit
    def test_check_and_fix_symlinks_no_broken_links(self, project_root_path):
        """Test check_and_fix_symlinks with no broken links."""
        test_strategy = 'test_symlink_strategy'
        test_asset = 'equities'
        strategy_path = project_root_path / 'strategies' / test_asset / test_strategy
        strategy_path.mkdir(parents=True, exist_ok=True)
        results_base = project_root_path / 'results' / test_strategy
        results_base.mkdir(parents=True, exist_ok=True)
        
        # Create valid symlink
        results_link = strategy_path / 'results'
        if results_link.exists() or results_link.is_symlink():
            results_link.unlink()
        results_link.symlink_to(results_base)
        
        try:
            fixed = check_and_fix_symlinks(test_strategy, test_asset)
            # Should return empty list if no broken links
            assert isinstance(fixed, list)
        finally:
            # Cleanup
            if results_link.exists() or results_link.is_symlink():
                results_link.unlink()
            if strategy_path.exists():
                shutil.rmtree(strategy_path)
            if results_base.exists():
                shutil.rmtree(results_base)

    @pytest.mark.unit
    def test_check_and_fix_symlinks_broken_strategy_link(self, project_root_path):
        """Test check_and_fix_symlinks fixes broken strategy results symlink."""
        test_strategy = 'test_broken_symlink_strategy'
        test_asset = 'equities'
        strategy_path = project_root_path / 'strategies' / test_asset / test_strategy
        strategy_path.mkdir(parents=True, exist_ok=True)
        results_base = project_root_path / 'results' / test_strategy
        results_base.mkdir(parents=True, exist_ok=True)
        
        # Create broken symlink (points to non-existent path)
        results_link = strategy_path / 'results'
        broken_target = project_root_path / 'nonexistent' / 'path'
        results_link.symlink_to(broken_target)
        
        try:
            fixed = check_and_fix_symlinks(test_strategy, test_asset)
            assert len(fixed) > 0
            assert results_link in fixed
            # Symlink should now be fixed
            assert results_link.exists() or results_link.is_symlink()
        finally:
            # Cleanup
            if results_link.exists() or results_link.is_symlink():
                results_link.unlink()
            if strategy_path.exists():
                shutil.rmtree(strategy_path)
            if results_base.exists():
                shutil.rmtree(results_base)

    @pytest.mark.unit
    def test_check_and_fix_symlinks_strategy_not_found(self, project_root_path):
        """Test check_and_fix_symlinks raises FileNotFoundError for non-existent strategy."""
        with pytest.raises(FileNotFoundError):
            check_and_fix_symlinks('nonexistent_strategy_xyz', 'equities')
