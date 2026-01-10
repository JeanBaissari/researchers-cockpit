# Backup Results

## Overview

Create backups of strategy results for archival and recovery, compressing and timestamping backups.

## Steps

1. **Identify Results** - Find results directories to backup
2. **Create Archive** - Compress results with timestamp
3. **Store Backup** - Save to backups/ or configurable location
4. **Generate Manifest** - Create backup manifest with metadata
5. **Verify Integrity** - Check backup file integrity
6. **List Backups** - Provide command to list available backups
7. **Restore Option** - Enable restore from backup functionality

## Checklist

- [ ] Results directories identified
- [ ] Compressed archive created with timestamp
- [ ] Backup stored in designated location
- [ ] Backup manifest generated
- [ ] Backup integrity verified
- [ ] Backup listed in backup catalog
- [ ] Restore functionality available

## Backup Patterns

**Create backup:**
```python
from pathlib import Path
import tarfile
from datetime import datetime
from lib.paths import get_results_dir

def backup_results(strategy_name: str, backup_dir: Path = None):
    """Create backup of strategy results."""
    if backup_dir is None:
        backup_dir = Path('backups')
    backup_dir.mkdir(exist_ok=True)
    
    results_dir = get_results_dir() / strategy_name
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = backup_dir / f"{strategy_name}_{timestamp}.tar.gz"
    
    with tarfile.open(backup_file, 'w:gz') as tar:
        tar.add(results_dir, arcname=strategy_name)
    
    # Generate manifest
    manifest = {
        'strategy': strategy_name,
        'timestamp': timestamp,
        'backup_file': str(backup_file),
        'size': backup_file.stat().st_size
    }
    
    return backup_file, manifest
```

**List backups:**
```python
def list_backups(backup_dir: Path = None):
    """List available backups."""
    if backup_dir is None:
        backup_dir = Path('backups')
    
    backups = []
    for backup_file in backup_dir.glob('*.tar.gz'):
        stat = backup_file.stat()
        backups.append({
            'file': backup_file.name,
            'size': stat.st_size,
            'modified': datetime.fromtimestamp(stat.st_mtime)
        })
    
    return backups
```

**Restore backup:**
```python
import tarfile
from lib.paths import get_results_dir

def restore_backup(backup_file: Path, strategy_name: str):
    """Restore results from backup."""
    results_dir = get_results_dir() / strategy_name
    results_dir.mkdir(parents=True, exist_ok=True)
    
    with tarfile.open(backup_file, 'r:gz') as tar:
        tar.extractall(results_dir.parent)
    
    return results_dir
```

**Backup manifest:**
```yaml
# backups/manifest.yaml
backups:
  - strategy: btc_sma_cross
    timestamp: 20240220_143000
    backup_file: backups/btc_sma_cross_20240220_143000.tar.gz
    size: 1048576
    created: 2024-02-20T14:30:00
```

## Notes

- Store backups in `backups/` directory (configurable)
- Use compressed format (tar.gz) to save space
- Include timestamp in backup filename
- Generate manifest for backup tracking
- Verify backup integrity after creation
- Keep backups organized by strategy name

## Related Commands

- analyze-results.md - For analyzing backed up results
- health-check.md - For checking backup integrity

