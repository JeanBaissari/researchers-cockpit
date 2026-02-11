"""
Test scripts organization after migration to archive.

Verifies that:
1. Migration scripts are in archive directory
2. Migration scripts are not in main scripts directory
3. Archive README exists and documents archived scripts
"""

import pytest
from pathlib import Path


def get_project_root():
    """Get project root directory."""
    return Path(__file__).parent.parent


def test_archive_directory_exists():
    """Test that scripts/archive/ directory exists."""
    project_root = get_project_root()
    archive_dir = project_root / "scripts" / "archive"

    assert archive_dir.exists(), "Archive directory should exist"
    assert archive_dir.is_dir(), "Archive should be a directory"


def test_migration_scripts_in_archive():
    """Test that migration scripts are in archive directory."""
    project_root = get_project_root()
    archive_dir = project_root / "scripts" / "archive"

    archived_scripts = ["migrate_v110.py", "reingest_all.py", "reorganize_csv_for_csvdir.py"]

    for script in archived_scripts:
        script_path = archive_dir / script
        assert script_path.exists(), f"{script} should be in archive directory"


def test_migration_scripts_not_in_main():
    """Test that migration scripts are NOT in main scripts directory."""
    project_root = get_project_root()
    scripts_dir = project_root / "scripts"

    archived_scripts = ["migrate_v110.py", "reingest_all.py", "reorganize_csv_for_csvdir.py"]

    for script in archived_scripts:
        script_path = scripts_dir / script
        assert not script_path.exists(), f"{script} should NOT be in main scripts directory"


def test_archive_readme_exists():
    """Test that archive README exists."""
    project_root = get_project_root()
    readme_path = project_root / "scripts" / "archive" / "README.md"

    assert readme_path.exists(), "Archive README should exist"
    assert readme_path.is_file(), "README should be a file"


def test_archive_readme_documents_scripts():
    """Test that archive README documents all archived scripts."""
    project_root = get_project_root()
    readme_path = project_root / "scripts" / "archive" / "README.md"

    readme_content = readme_path.read_text()

    archived_scripts = ["migrate_v110.py", "reingest_all.py", "reorganize_csv_for_csvdir.py"]

    for script in archived_scripts:
        assert script in readme_content, f"README should document {script}"


def test_archive_readme_explains_archival_reason():
    """Test that README explains why scripts were archived."""
    project_root = get_project_root()
    readme_path = project_root / "scripts" / "archive" / "README.md"

    readme_content = readme_path.read_text()

    # Should explain archival reasons
    assert "Why archived" in readme_content or "archived" in readme_content.lower(), (
        "README should explain why scripts were archived"
    )

    # Should mention v1.12.0
    assert "v1.12.0" in readme_content, (
        "README should mention v1.12.0 (the version when scripts were archived)"
    )


def test_archive_readme_provides_alternatives():
    """Test that README provides current alternatives."""
    project_root = get_project_root()
    readme_path = project_root / "scripts" / "archive" / "README.md"

    readme_content = readme_path.read_text()

    # Should mention current alternatives
    assert "alternative" in readme_content.lower() or "current" in readme_content.lower(), (
        "README should mention current alternatives to archived scripts"
    )

    # Should mention ingest_data.py as alternative
    assert "ingest_data.py" in readme_content, (
        "README should mention ingest_data.py as alternative to reingest_all.py"
    )
