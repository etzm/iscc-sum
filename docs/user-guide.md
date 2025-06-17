# ISCC-SUM User Guide

This guide covers the `iscc-sum` command-line tool for generating and verifying ISCC (International Standard
Content Code) checksums according to ISO 24138:2024.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Basic Usage](#basic-usage)
- [Output Formats](#output-formats)
- [Checksum Verification](#checksum-verification)
- [Similarity Matching](#similarity-matching)
- [Advanced Options](#advanced-options)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)

## Installation

The recommended way to install the `iscc-sum` CLI tool is using [uv](https://docs.astral.sh/uv/):

```bash
uv tool install iscc-sum
```

**Note:** To install uv, run: `curl -LsSf https://astral.sh/uv/install.sh | sh` (or see
[other installation methods](https://docs.astral.sh/uv/getting-started/installation/))

Alternatively, you can install using pip:

```bash
pip install iscc-sum
```

Verify the installation:

```bash
iscc-sum --version
```

## Quick Start

Generate an ISCC checksum for a file:

```bash
iscc-sum myfile.txt
```

Output:

```
ISCC:KACYPXW445FTYNJ3CYSXHAFJMA2HUWULUNRFE3BLHRSCXYH2XHGQY *myfile.txt
```

## Basic Usage

### Generate Checksums for Multiple Files

```bash
iscc-sum file1.txt file2.pdf file3.jpg
```

### Read from Standard Input

```bash
echo "Hello, World!" | iscc-sum
```

Or:

```bash
cat document.txt | iscc-sum
```

### Generate Checksums for All Files in a Directory

```bash
iscc-sum *.txt
```

### Process Directory Recursively

Generate checksums for all files in a directory and its subdirectories:

```bash
iscc-sum /path/to/directory
```

### Tree Mode - Single Checksum for Directory

Generate a single checksum representing all files in a directory tree:

```bash
iscc-sum --tree /path/to/project
# ISCC:KACYPXW445FTYNJ3CYSXHAFJMA2HUWULUNRFE3BLHRSCXYH2XHGQY */path/to/project/
```

Note the trailing slash indicating this is a directory checksum.

## Output Formats

### Default Format

The default output format matches GNU coreutils checksum tools:

```bash
iscc-sum file.txt
# ISCC:KACYPXW445FTYNJ3CYSXHAFJMA2HUWULUNRFE3BLHRSCXYH2XHGQY *file.txt
```

### BSD-Style Format

Use `--tag` for BSD-style output:

```bash
iscc-sum --tag file.txt
# ISCC (file.txt) = ISCC:KACYPXW445FTYNJ3CYSXHAFJMA2HUWULUNRFE3BLHRSCXYH2XHGQY
```

### Narrow Format (128-bit)

Use `--narrow` for shorter, 128-bit checksums:

```bash
iscc-sum --narrow file.txt
# ISCC:KACYPXW445FTYNJ3CYSXHAFJMA2HU *file.txt
```

### Zero-Terminated Output

Use `-z` or `--zero` for NUL-terminated lines (useful for scripts):

```bash
iscc-sum -z file1.txt file2.txt | od -c
```

### Display Component Units

Use `--units` to show the Data-Code and Instance-Code components:

```bash
iscc-sum --units file.txt
# ISCC:KACYPXW445FTYNJ3CYSXHAFJMA2HUWULUNRFE3BLHRSCXYH2XHGQY *file.txt
#   ISCC:EAAW4BQTJSTJSHAI27AJSAGMGHNUKSKRTK3E6OZ5CXUS57SWQZXJQ
#   ISCC:IABXF3ZHYL6O6PM5P2HGV677CS3RBHINZSXEJCITE3WNOTQ2CYXRA
```

## Checksum Verification

### Verify Checksums from a File

Create a checksum file:

```bash
iscc-sum *.txt > checksums.txt
```

Verify the checksums:

```bash
iscc-sum -c checksums.txt
```

Output:

```
file1.txt: OK
file2.txt: OK
file3.txt: OK
```

### Verification Options

#### Quiet Mode

Only show failures:

```bash
iscc-sum -c -q checksums.txt
```

#### Status Mode

Silent operation, check exit code only:

```bash
iscc-sum -c --status checksums.txt
echo $?  # 0 if all OK, 1 if any failures
```

#### Strict Mode

Exit on first format error:

```bash
iscc-sum -c --strict checksums.txt
```

#### Format Warnings

Show warnings about improperly formatted lines:

```bash
iscc-sum -c -w checksums.txt
```

## Similarity Matching

Find files with similar content based on Data-Code hamming distance:

### Basic Similarity Search

```bash
iscc-sum --similar *.txt
```

Output groups files by similarity:

```
document1.txt
  ~8  document2.txt
  ~12 document3.txt
```

### Adjust Similarity Threshold

Default threshold is 12 bits. Lower values find more similar files:

```bash
iscc-sum --similar --threshold 6 *.txt
```

### Combine with Other Options

```bash
iscc-sum --similar --tag --threshold 10 *.pdf
```

## Advanced Options

### Complete Option Reference

| Option        | Short | Description                                             |
| ------------- | ----- | ------------------------------------------------------- |
| `--help`      |       | Show help message and exit                              |
| `--version`   |       | Show version number and exit                            |
| `--check`     | `-c`  | Read checksums and verify files                         |
| `--narrow`    |       | Generate shorter 128-bit checksums                      |
| `--tag`       |       | Use BSD-style output format                             |
| `--units`     |       | Show Data-Code and Instance-Code components             |
| `--zero`      | `-z`  | End lines with NUL instead of newline                   |
| `--similar`   |       | Find files with similar Data-Codes                      |
| `--threshold` |       | Hamming distance threshold for similarity (default: 12) |
| `--tree`      | `-t`  | Process directory as single unit with combined checksum |
| `--quiet`     | `-q`  | Only show failures during verification                  |
| `--status`    |       | Silent mode, exit code indicates success                |
| `--warn`      | `-w`  | Show warnings about format errors                       |
| `--strict`    |       | Exit on first format error                              |

## Examples

### Example 1: Generate Checksums for a Project

Generate checksums for all source files:

```bash
iscc-sum src/**/*.py > project-checksums.txt
```

### Example 2: Verify Archive Integrity

Before archiving:

```bash
iscc-sum --tag archive/* > archive.checksums
```

After extraction:

```bash
iscc-sum -c archive.checksums
```

### Example 3: Find Duplicate Images

Find similar images in a directory:

```bash
iscc-sum --similar --threshold 8 photos/*.jpg
```

### Example 4: Create Directory Checksum

Create a single checksum for an entire project:

```bash
iscc-sum --tree my-project > project.checksum
```

Verify the project hasn't changed:

```bash
iscc-sum -c project.checksum
```

### Example 5: Pipeline Processing

Process files in a pipeline:

```bash
find . -name "*.doc" -print0 | xargs -0 iscc-sum > documents.checksums
```

### Example 6: Verify Downloads

Create checksum for download:

```bash
curl -s https://example.com/file.pdf | iscc-sum
```

Save and verify:

```bash
curl -s https://example.com/file.pdf -o file.pdf
echo "ISCC:KACYPXW445FTYNJ3CYSXHAFJMA2HUWULUNRFE3BLHRSCXYH2XHGQY *file.pdf" | iscc-sum -c
```

## Troubleshooting

### Common Issues

#### "No such file or directory"

Ensure the file path is correct and the file exists:

```bash
ls -la filename.txt
iscc-sum filename.txt
```

#### "Permission denied"

Check file permissions:

```bash
ls -l filename.txt
sudo iscc-sum filename.txt  # If needed
```

#### Checksum Mismatch

When verification fails:

1. Check if the file was modified
2. Verify the checksum file format is correct
3. Ensure no extra whitespace in checksum file

#### Large File Performance

For very large files, `iscc-sum` processes data in 2MB chunks to maintain performance. Progress is shown
automatically for files over 100MB.

### Exit Codes

- `0`: Success
- `1`: Verification failure (one or more files failed)
- `2`: Error (I/O error, format error, etc.)

### Getting Help

For more help:

```bash
iscc-sum --help
```

Report issues at: https://github.com/bio-codes/iscc-sum/issues
