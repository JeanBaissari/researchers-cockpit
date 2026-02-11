# Documentation Configuration API

## Purpose

This module provides programmatic access to documentation standards and configuration, enabling automated validation and enforcement of documentation quality across the project.

## Scope

Covers:
- Loading documentation configuration from `config/settings.yaml`
- Accessing documentation zones, required sections, and index files
- Validating documentation structure against standards
- Enforcing docs-maintainer agent standards programmatically

Does not cover:
- Actual documentation content generation
- Markdown rendering or parsing
- Git-based documentation workflows

## Repo Paths

- Configuration: `config/settings.yaml` (documentation section)
- Module: `lib/config/documentation.py`
- Agent definition: `.claude/agents/docs_maintainer.md`
- Tests: `tests/config/test_documentation.py`

## API Reference

### load_documentation_config()

Load documentation configuration from settings.

```python
from lib.config import load_documentation_config

config = load_documentation_config()
# Returns dict with sections: organization, zones, required_sections, indexing, cleanup
```

### get_doc_zones()

Get documentation zone paths as absolute Path objects.

```python
from lib.config import get_doc_zones

zones = get_doc_zones()
# Returns: {'api': Path('/path/to/docs/api'), 'code_patterns': Path(...), ...}
```

### get_required_sections()

Get list of required sections for new documentation.

```python
from lib.config import get_required_sections

sections = get_required_sections()
# Returns: ['purpose', 'scope', 'repo_paths', 'examples', 'related_docs']
```

### get_index_files()

Get documentation index file paths.

```python
from lib.config import get_index_files

indexes = get_index_files()
# Returns: {
#   'global_index': Path('/path/to/docs/README.md'),
#   'section_indexes': [Path(...), Path(...), ...]
# }
```

### validate_doc_structure(doc_path)

Validate that a documentation file has all required sections.

```python
from pathlib import Path
from lib.config import validate_doc_structure

result = validate_doc_structure(Path('docs/api/example.md'))
# Returns: {
#   'valid': True,
#   'missing_sections': [],
#   'found_sections': ['purpose', 'scope', 'repo_paths', 'examples', 'related_docs']
# }
```

### should_archive_instead_of_delete()

Check if docs should be archived instead of deleted.

```python
from lib.config import should_archive_instead_of_delete

should_archive = should_archive_instead_of_delete()
# Returns: True (default behavior)
```

## Examples

### Example 1: Validate New Documentation

```python
from pathlib import Path
from lib.config import validate_doc_structure, get_required_sections

doc_path = Path('docs/api/new_feature.md')
result = validate_doc_structure(doc_path)

if not result['valid']:
    print(f"Missing sections: {', '.join(result['missing_sections'])}")
    print(f"Required sections: {', '.join(get_required_sections())}")
else:
    print("Documentation structure is valid!")
```

### Example 2: Check Documentation Zones

```python
from lib.config import get_doc_zones

zones = get_doc_zones()

# Check if a zone exists
if zones['api'].exists():
    print(f"API documentation zone: {zones['api']}")

# List all zones
for zone_name, zone_path in zones.items():
    print(f"{zone_name}: {zone_path}")
```

### Example 3: Automated Documentation Checks

```python
from pathlib import Path
from lib.config import validate_doc_structure, get_doc_zones

def check_all_docs_in_zone(zone_name: str):
    """Validate all markdown files in a documentation zone."""
    zones = get_doc_zones()
    zone_path = zones[zone_name]

    results = {}
    for doc_file in zone_path.rglob('*.md'):
        if doc_file.name != 'README.md':  # Skip indexes
            result = validate_doc_structure(doc_file)
            if not result['valid']:
                results[doc_file.name] = result['missing_sections']

    if results:
        print(f"Invalid docs in {zone_name}:")
        for filename, missing in results.items():
            print(f"  {filename}: missing {', '.join(missing)}")
    else:
        print(f"All docs in {zone_name} are valid!")

# Check API documentation
check_all_docs_in_zone('api')
```

### Example 4: Pre-Commit Hook Integration

```python
#!/usr/bin/env python
"""Pre-commit hook to validate documentation structure."""

import sys
from pathlib import Path
from lib.config import validate_doc_structure, get_doc_zones

def main():
    """Validate all staged documentation files."""
    zones = get_doc_zones()
    doc_dirs = [str(zone) for zone in zones.values()]

    # Get staged files (would use git commands in real hook)
    staged_docs = [
        Path('docs/api/example.md'),  # Example
    ]

    invalid_docs = []
    for doc_path in staged_docs:
        # Only validate docs in known zones
        if any(str(doc_path).startswith(d) for d in doc_dirs):
            result = validate_doc_structure(doc_path)
            if not result['valid']:
                invalid_docs.append((doc_path, result['missing_sections']))

    if invalid_docs:
        print("ERROR: Invalid documentation structure detected:")
        for doc_path, missing in invalid_docs:
            print(f"  {doc_path}: missing {', '.join(missing)}")
        return 1

    return 0

if __name__ == '__main__':
    sys.exit(main())
```

## Configuration

The documentation configuration is stored in `config/settings.yaml` under the `documentation` section:

```yaml
documentation:
  organization:
    prefer_granular: true
    require_indexing: true
    enforce_architecture_alignment: true
    prevent_stale_references: true

  zones:
    api: docs/api/
    code_patterns: docs/code_patterns/
    troubleshooting: docs/troubleshooting/
    verification: docs/verification/
    archive: docs/archive/

  required_sections:
    - purpose
    - scope
    - repo_paths
    - examples
    - related_docs

  indexing:
    global_index: docs/README.md
    section_indexes:
      - docs/api/README.md
      - docs/code_patterns/README.md
      # ... more indexes

  cleanup:
    archive_instead_of_delete: true
    mark_archived_docs: true
    link_to_canonical: true
```

## Related Docs

- [Documentation Standards](../README.md) - Main documentation index
- [docs-maintainer Agent](./.claude/agents/docs_maintainer.md) - Agent definition
- [Documentation Map](../doc_map.md) - Visual navigation guide
- [lib/config Package](./config.md) - Configuration module overview

## Standards Alignment

This API enforces the standards defined in `.claude/agents/docs_maintainer.md`:

1. **Granular docs** - Configuration validates small, focused files
2. **Discoverability** - Requires indexing in README files
3. **No stale paths** - Prevents referencing non-existent files
4. **Architecture alignment** - Enforces v1.12.0+ NO WRAPPERS standards
5. **Where-to-look** - Requires concrete paths in documentation
