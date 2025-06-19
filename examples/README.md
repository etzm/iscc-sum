# ISCC-SUM Examples

This directory contains example scripts demonstrating common use cases for the `iscc-sum` command-line tool. All scripts are written in Python for cross-platform compatibility.

## Scripts Overview

### 1. backup-verification.py

A Python script for creating and verifying backup checksums.

**Usage:**
```bash
# Create checksums for all files in a directory
./backup-verification.py create /path/to/backup

# Verify checksums to ensure backup integrity
./backup-verification.py verify /path/to/backup
```

**Features:**
- Generates checksums for all files in a directory tree
- Stores checksums in a hidden `.iscc-checksums` file
- Verifies file integrity after restore or transfer
- Reports any changed or missing files

### 2. duplicate-finder.py

A Python script that uses the similarity matching feature to find duplicate or near-duplicate files.

**Usage:**
```bash
# Find similar files in a directory
./duplicate-finder.py ./photos

# Find very similar files (threshold: 8 bits)
./duplicate-finder.py ./photos 8

# Find similar images only
./duplicate-finder.py ./photos 12 .jpg .png .gif
```

**Features:**
- Groups files by content similarity
- Shows hamming distance between files
- Identifies exact duplicates (distance = 0)
- Filters by file extension

### 3. integrity-monitor.py

A Python script for monitoring file system integrity, useful for detecting unauthorized changes.

**Usage:**
```bash
# Initialize monitoring for /etc directory
./integrity-monitor.py /etc

# Check for changes (run periodically via cron)
./integrity-monitor.py /etc
```

**Features:**
- Tracks file additions, modifications, and deletions
- Maintains a state file of known-good checksums
- Logs all integrity checks and changes
- Interactive state update after changes

**Scheduled Task Example:**

Linux/macOS (cron):
```bash
# Add to crontab to check daily at 3 AM
0 3 * * * /usr/bin/python3 /path/to/integrity-monitor.py /etc
```

Windows (Task Scheduler):
```powershell
# Create scheduled task
schtasks /create /tn "ISCC Integrity Check" /tr "python C:\path\to\integrity-monitor.py C:\Important" /sc daily /st 03:00
```

### 4. verify-downloads.py

A Python script for verifying downloaded files using ISCC checksums.

**Usage:**
```bash
# Generate checksum for sharing
./verify-downloads.py generate myfile.pdf

# Download and verify in one step
./verify-downloads.py download https://example.com/file.zip ISCC:KAC...

# Verify an existing file
./verify-downloads.py verify file.zip ISCC:KAC...
```

**Features:**
- Generates checksums for file distribution
- Downloads and verifies files automatically
- Verifies existing files against known checksums
- Handles corrupted downloads gracefully

## Running the Examples

1. Ensure `iscc-sum` is installed:

   Using uv (recommended):
   ```bash
   uv tool install iscc-sum
   ```
   
   Or using pip:
   ```bash
   pip install iscc-sum
   ```

2. Run scripts with Python:
```bash
python backup-verification.py create ./mydata
python duplicate-finder.py ./photos
python integrity-monitor.py /etc
python verify-downloads.py generate myfile.pdf
```

On Unix-like systems, you can also make scripts executable:
```bash
chmod +x *.py
./backup-verification.py create ./mydata
```

## Use Case Scenarios

### Scenario 1: Archiving Important Data

Before archiving data to external storage:
```bash
./backup-verification.py create /home/user/important-data
```

After restoring from archive:
```bash
./backup-verification.py verify /home/user/important-data
```

### Scenario 2: Managing Photo Collections

Find duplicate photos to save space:
```bash
./duplicate-finder.py ~/Pictures 0  # Find exact duplicates
```

Find similar photos (different resolutions/compressions):
```bash
./duplicate-finder.py ~/Pictures 8 .jpg .jpeg
```

### Scenario 3: System Security Monitoring

Set up monitoring for system directories:

Linux/macOS:
```bash
sudo python integrity-monitor.py /etc
sudo python integrity-monitor.py /usr/local/bin
```

Windows (as Administrator):
```powershell
python integrity-monitor.py C:\Windows\System32\drivers\etc
python integrity-monitor.py C:\Program Files\ImportantApp
```

### Scenario 4: Distributing Files Securely

Publisher generates checksum:
```bash
./verify-downloads.py generate release-v1.0.tar.gz
# Share: ISCC:KACYPXW445FTYNJ3CYSXHAFJMA2HUWULUNRFE3BLHRSCXYH2XHGQY
```

Users verify download:
```bash
./verify-downloads.py download \
  https://example.com/release-v1.0.tar.gz \
  ISCC:KACYPXW445FTYNJ3CYSXHAFJMA2HUWULUNRFE3BLHRSCXYH2XHGQY
```

## Integration Ideas

### Git Hooks

Create `.git/hooks/pre-commit` (works on all platforms with Python):
```python
#!/usr/bin/env python3
import subprocess
import datetime

# Get staged files
result = subprocess.run(['git', 'diff', '--cached', '--name-only'], 
                       capture_output=True, text=True)
files = result.stdout.strip().split('\n')
files = [f for f in files if f]  # Remove empty strings

if files:
    # Generate checksums
    date = datetime.datetime.now().strftime('%Y%m%d')
    subprocess.run(['iscc-sum'] + files, 
                  stdout=open(f'.checksums-{date}', 'w'))
```

### CI/CD Pipeline

Verify artifacts in CI:
```yaml
- name: Verify build artifacts
  run: |
    echo "ISCC:EXPECTED_CHECKSUM *build/app.zip" | iscc-sum -c
```

### Docker Integration

Add to Dockerfile for layer verification:
```dockerfile
RUN echo "ISCC:CHECKSUM *app.tar.gz" | iscc-sum -c || exit 1
```

## Performance Tips

1. **Large Directories**: Use `find` with `-type f` to exclude directories
2. **Network Shares**: Generate checksums locally, then copy checksum file
3. **Parallel Processing**: Split large file sets and process in parallel
4. **Incremental Updates**: Use integrity-monitor.sh approach for large datasets

## Contributing

Feel free to submit additional examples via pull requests to:
https://github.com/bio-codes/iscc-sum