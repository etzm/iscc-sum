# ISCC-SUM User Guide

This comprehensive guide covers all features of the `iscc-sum` command-line tool for generating and verifying
ISCC (International Standard Content Code) checksums according to ISO 24138:2024.

!!! tip "New to ISCC-SUM?"

    If you're just getting started, check out our [Quick Start Guide](quickstart.md) for a gentle introduction. This
    user guide covers all features in detail for when you need more advanced functionality.

## :package: Installation

The recommended way to install `iscc-sum` is using [UV](https://docs.astral.sh/uv/), a fast Python package
manager:

=== "Linux/macOS"

    ```bash
    # Install UV (if not already installed)
    curl -LsSf https://astral.sh/uv/install.sh | sh

    # Install iscc-sum globally
    uv tool install iscc-sum
    ```

=== "Windows"

    ```powershell
    # Install UV (if not already installed)
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

    # Install iscc-sum globally
    uv tool install iscc-sum
    ```

=== "Alternative: pip"

    ```bash
    pip install iscc-sum
    ```

Verify the installation:

```bash
iscc-sum --version
```

??? question "Installation Troubleshooting"

    **"Command not found" after installation**

    - Close and reopen your terminal to refresh the PATH
    - Check if UV's bin directory is in your PATH:
        - Linux/macOS: `~/.local/bin`
        - Windows: `%USERPROFILE%\.local\bin`

    **Permission errors during installation**

    - Don't use `sudo` with UV
    - UV installs tools in your user directory by default

## :rocket: Core Features

### Basic Checksum Generation

Generate ISCC checksums for your files with simple commands:

#### Single File

```bash
iscc-sum document.pdf
```

Output:

```
ISCC:KACYPXW445FTYNJ3CYSXHAFJMA2HUWULUNRFE3BLHRSCXYH2XHGQY *document.pdf
```

!!! info "Output Format"

    The default output format follows GNU coreutils conventions:

    - `ISCC:...` - The ISCC checksum
    - `*` - Binary mode indicator (always present)
    - `filename` - Path to the file

#### Multiple Files

Process multiple files in one command:

```bash
iscc-sum file1.txt file2.pdf image.jpg
```

Output:

```
ISCC:KACWSO4JFISTQSRVMCWDRBTS5AX5E2XD7H3PRFMBTNGBD6PZQJNQ *file1.txt
ISCC:KACYPXW445FTYNJ3CYSXHAFJMA2HUWULUNRFE3BLHRSCXYH2XHGQY *file2.pdf
ISCC:KACSUH2DZ5SLMG4YGH3LUW7J7ERVQZFMV5LYS4KAHCUSM6EPUAFA *image.jpg
```

#### Directory Processing

Process all files in a directory recursively:

```bash
iscc-sum /path/to/directory
```

This will:

- :file_folder: Recursively find all files
- :arrow_up_down: Process them in deterministic order
- :page_facing_up: Respect `.isccignore` patterns

!!! tip "Deterministic Ordering"

    Directory traversal uses the [TREEWALK-ISCC](specifications/treewalk.md) algorithm, ensuring consistent output
    across different platforms and filesystems.

#### Standard Input

Process data from pipes or redirects:

```bash
echo "Hello, World!" | iscc-sum
```

Or from a file:

```bash
iscc-sum < document.txt
```

### Output Formats

ISCC-SUM supports multiple output formats for different use cases:

#### Default Format

The standard format compatible with GNU coreutils tools:

```bash
iscc-sum file.txt
# ISCC:KACYPXW445FTYNJ3CYSXHAFJMA2HUWULUNRFE3BLHRSCXYH2XHGQY *file.txt
```

#### BSD-Style Format

Use `--tag` for BSD-style output:

```bash
iscc-sum --tag file.txt
# ISCC-SUM (file.txt) = ISCC:KACYPXW445FTYNJ3CYSXHAFJMA2HUWULUNRFE3BLHRSCXYH2XHGQY
```

#### Narrow Format (128-bit)

For ISO 24138:2024 conformant 128-bit checksums:

```bash
iscc-sum --narrow file.txt
# ISCC:KACYPXW445FTYNJ3CYSXHAFJMA2HU *file.txt
```

!!! note "Narrow vs Extended Format"

    - **Narrow** (128-bit): Shorter, ISO standard compliant
    - **Extended** (256-bit): Default, more collision resistant

#### Component Display

Show individual Data-Code and Instance-Code components:

```bash
iscc-sum --units file.txt
```

Output:

```
ISCC:KACYPXW445FTYNJ3CYSXHAFJMA2HUWULUNRFE3BLHRSCXYH2XHGQY *file.txt
  ISCC:EAAW4BQTJSTJSHAI27AJSAGMGHNUKSKRTK3E6OZ5CXUS57SWQZXJQ
  ISCC:IABXF3ZHYL6O6PM5P2HGV677CS3RBHINZSXEJCITE3WNOTQ2CYXRA
```

The components are:

- First line: Combined ISCC checksum
- Second line: Data-Code (content similarity)
- Third line: Instance-Code (exact match)

#### Zero-Terminated Output

For script processing, use NUL-terminated lines:

```bash
iscc-sum -z file1.txt file2.txt | xargs -0 -n1 echo "Processing:"
```

### Cross-Platform Checksum Files

!!! success "New Feature"

    The `-o/--output` option ensures consistent checksum files across platforms.

Create portable checksum files that work on Windows, Linux, and macOS:

```bash
iscc-sum -o checksums.txt *.pdf
```

This ensures:

- :page_facing_up: UTF-8 encoding
- :leftwards_arrow_with_hook: LF line endings (Unix-style)
- :globe_with_meridians: Cross-platform compatibility

## :white_check_mark: Verification Mode

Verify file integrity by checking against saved checksums:

### Creating Checksum Files

Save checksums for later verification:

```bash
# Save to a file (cross-platform safe)
iscc-sum -o project-checksums.txt src/**/*.py

# Or use shell redirection (platform-specific line endings)
iscc-sum *.doc > checksums.txt
```

### Basic Verification

Check if files match their saved checksums:

```bash
iscc-sum -c project-checksums.txt
```

Output:

```
src/main.py: OK
src/utils.py: OK
src/config.py: FAILED
iscc-sum: WARNING: 1 computed checksum did NOT match
```

### Verification Options

#### Quiet Mode

Only show failures:

```bash
iscc-sum -c -q checksums.txt
# Only outputs failed files
```

#### Status Mode

Silent operation, check exit code only:

```bash
iscc-sum -c --status checksums.txt
echo $?  # 0 if all OK, 1 if any failures
```

Perfect for scripts:

```bash
if iscc-sum -c --status checksums.txt; then
    echo "All files verified successfully"
else
    echo "Verification failed!"
fi
```

#### Strict Mode

Exit immediately on format errors:

```bash
iscc-sum -c --strict checksums.txt
```

#### Format Warnings

Show warnings about improperly formatted lines:

```bash
iscc-sum -c -w checksums.txt
```

## :mag: Similarity Detection

!!! abstract "Unique Feature"

    Unlike traditional checksums, ISCC enables finding similar files through its Data-Code component.

### How It Works

ISCC's Data-Code captures content structure, allowing similarity comparison:

- Similar content → Similar Data-Codes
- Measured by [Hamming distance](https://en.wikipedia.org/wiki/Hamming_distance)
- Default threshold: 12 bits difference

### Finding Similar Files

Group files by content similarity:

```bash
iscc-sum --similar *.txt
```

Output:

```
document_v1.txt
  ~08 document_v2.txt
  ~12 document_draft.txt

report_2024.txt
  ~06 report_2024_final.txt
```

The numbers (e.g., `~08`) indicate bit differences - lower means more similar.

### Adjusting Similarity Threshold

Find more similar files with a higher threshold:

```bash
iscc-sum --similar --threshold 20 *.jpg
```

Or find only very similar files:

```bash
iscc-sum --similar --threshold 5 *.pdf
```

!!! tip "Choosing Thresholds"

    - **0-5**: Nearly identical files
    - **6-12**: Likely similar content (default)
    - **13-20**: Probably somewhat similar

### Similarity with Other Options

Combine similarity detection with other formats:

```bash
# BSD-style output with similarity grouping
iscc-sum --similar --tag *.doc

# Narrow format similarity
iscc-sum --similar --narrow --threshold 8 images/*
```

## :file_folder: Tree Mode

Generate a single checksum for an entire directory structure:

```bash
iscc-sum --tree my-project/
```

Output:

```
ISCC:KACYPXW445FTYNJ3CYSXHAFJMA2HUWULUNRFE3BLHRSCXYH2XHGQY *my-project/
```

!!! note "Directory Indicator"

    The trailing slash (`/`) indicates this is a directory checksum, not a file.

### What Tree Mode Captures

Tree mode creates a composite checksum of:

- :page_facing_up: All file contents
- :file_folder: Directory structure
- :arrow_up_down: File ordering
- :no_entry_sign: Respects `.isccignore` patterns

### Use Cases for Tree Mode

=== "Version Snapshots"

    ```bash
    # Create a snapshot before changes
    iscc-sum --tree project/ > snapshot-before.txt

    # After changes, verify what changed
    iscc-sum --tree project/ > snapshot-after.txt
    diff snapshot-before.txt snapshot-after.txt
    ```

=== "Archive Verification"

    ```bash
    # Before archiving
    iscc-sum --tree data/ -o archive-checksum.txt

    # After extraction
    iscc-sum -c archive-checksum.txt
    ```

=== "Cross-System Sync"

    ```bash
    # On source system
    iscc-sum --tree /source/dir/ | ssh user@target "cat > checksum.txt"

    # On target system
    iscc-sum -c checksum.txt
    ```

## :notebook: Practical Examples

### Example: Build Reproducibility

Ensure your build outputs are consistent:

```bash
# Before build
iscc-sum --tree src/ -o src-checksum.txt

# After build
make clean && make

# Verify source unchanged
iscc-sum -c src-checksum.txt

# Check build outputs
iscc-sum --tree build/ -o build-checksum.txt
```

### Example: Finding Duplicate Images

Identify duplicate or near-duplicate images:

```bash
# Find very similar images
iscc-sum --similar --threshold 5 photos/*.jpg > duplicates.txt

# Review groups
grep -B1 "~0[0-5]" duplicates.txt
```

### Example: Cross-Platform File Transfer

Ensure files transfer correctly between systems:

=== "On Source System"

    ```bash
    # Create portable checksum file
    iscc-sum -o transfer-manifest.txt files/*

    # Transfer files and manifest
    rsync -av files/ transfer-manifest.txt remote:/destination/
    ```

=== "On Target System"

    ```bash
    # Verify all files transferred correctly
    cd /destination
    iscc-sum -c transfer-manifest.txt
    ```

### Example: Continuous Integration

Add file integrity checks to your CI pipeline:

```yaml
# .github/workflows/verify.yml
steps:
  - name: Checkout
    uses: actions/checkout@v4
    
  - name: Verify test fixtures
    run: |
      iscc-sum -c tests/fixtures/checksums.txt --status || {
        echo "Test fixtures corrupted!"
        exit 1
      }
```

## :book: Command Reference

### Synopsis

```
iscc-sum [OPTION]... [FILE|DIR]...
```

### Options Reference

| Option           | Short | Description                                   |
| ---------------- | ----- | --------------------------------------------- |
| `--help`         |       | Show help message and exit                    |
| `--version`      |       | Show version number and exit                  |
| **Generation**   |       |                                               |
| `--narrow`       |       | Generate 128-bit checksums (ISO standard)     |
| `--tag`          |       | Use BSD-style output format                   |
| `--units`        |       | Show Data-Code and Instance-Code components   |
| `--zero`         | `-z`  | End lines with NUL instead of newline         |
| `--output FILE`  | `-o`  | Write to FILE with consistent encoding        |
| **Verification** |       |                                               |
| `--check`        | `-c`  | Read checksums and verify files               |
| `--quiet`        | `-q`  | Don't print OK for each file                  |
| `--status`       |       | Don't output anything, exit code only         |
| `--warn`         | `-w`  | Warn about format errors                      |
| `--strict`       |       | Exit on first format error                    |
| **Advanced**     |       |                                               |
| `--similar`      |       | Find files with similar content               |
| `--threshold N`  |       | Hamming distance for similarity (default: 12) |
| `--tree`         | `-t`  | Single checksum for entire directory          |

### Exit Codes

| Code | Meaning                                           |
| ---- | ------------------------------------------------- |
| 0    | Success - all operations completed successfully   |
| 1    | Verification failure - one or more files failed   |
| 2    | Error - I/O error, invalid format, or other issue |

### Performance Tips

!!! tip "Performance Optimization"

    - **Large Files**: Processed in 2MB chunks for memory efficiency
    - **Many Files**: Use directory arguments instead of wildcards for better performance
    - **Network Storage**: Create checksums locally, then transfer for faster processing

## :sos: Troubleshooting

??? bug "Common Issues and Solutions"

    **"No such file or directory"**

    - Check file path spelling and case (especially on Linux/macOS)
    - Use tab completion to verify paths
    - For spaces in names: use quotes or escape with backslash

    **"Permission denied"**

    - Check file permissions: `ls -l filename`
    - For system files, consider if you really need to checksum them
    - Never use `sudo` unless absolutely necessary

    **Checksum mismatches**

    - Verify the file hasn't been modified: check timestamps
    - Ensure consistent line endings (use `-o` option)
    - Check for hidden characters in filenames

    **Performance issues**

    - For many small files, process directory instead of wildcards
    - Use `--tree` mode for full directory comparison
    - Consider `--narrow` format for faster processing

## :link: See Also

- [Quick Start Guide](quickstart.md) - Getting started with ISCC-SUM
- [Developer Guide](developers.md) - Using ISCC-SUM in your Python code
- [Specifications](specifications/) - Technical details and standards
- [GitHub Repository](https://github.com/bio-codes/iscc-sum) - Source code and issue tracking
