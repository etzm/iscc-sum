# ISUM - Rust CLI Specification (Minimal)

## Command Synopsis

```
isum [OPTION]... [FILE|DIR]...
```

## Description

The `isum` command is a minimal, high-performance Rust implementation of ISCC (International Standard Content
Code) checksum generation. It provides the same core functionality as the Python-based `iscc-sum` tool but with
faster startup times and lower resource usage.

When given directories as arguments, `isum` recursively processes all regular files within them in a
deterministic order to ensure consistent output across platforms.

## Options

### Basic Options

- `--help` - Display help message and exit
- `--version` - Output version information and exit
- `--narrow` - Generate narrow format (2×64-bit) conformant with ISO 24138:2024 (default: 2×128-bit extended
  format)

### Directory Processing Options

- `-r, --recursive` - Process directories recursively (default when directory argument is provided)
- `--no-recursive` - Process only files in the specified directory, not subdirectories
- `--exclude <PATTERN>` - Exclude files matching the given glob pattern (can be specified multiple times)
- `--max-depth <N>` - Maximum directory depth to traverse (default: unlimited)

## Output Format

### Default Format

```
<ISCC_CHECKSUM> *<FILENAME>
```

- `<ISCC_CHECKSUM>`: ISCC code starting with "ISCC:" followed by base32 encoded value
- `*`: Binary mode indicator (always present)
- `<FILENAME>`: Path to the file

Example:

```
ISCC:KACYPXW445FTYNJ3CYSXHAFJMA2HUWULUNRFE3BLHRSCXYH2M5AEGQY *document.pdf
```

## Checksum Structure

### Extended Format (default, 256-bit)

- Header: 2 bytes
  - Byte 1: Main type (0101) | Sub type (0111)
  - Byte 2: Version (0000) | Length (0000)
- Data-Code: 128 bits (16 bytes)
- Instance-Code: 128 bits (16 bytes)
- Total: 34 bytes → ~54 characters base32

### Narrow Format (--narrow, 128-bit)

- Header: 2 bytes
  - Byte 1: Main type (0101) | Sub type (0101)
  - Byte 2: Version (0000) | Length (0000)
- Data-Code: 64 bits (8 bytes)
- Instance-Code: 64 bits (8 bytes)
- Total: 18 bytes → ~29 characters base32

## Exit Status

- `0` - Success (files processed successfully)
- `1` - Error (I/O error or invalid input)

## Examples

```bash
# Single file
isum document.pdf

# Multiple files  
isum *.txt

# Process directory recursively
isum /path/to/directory

# Process directory non-recursively
isum --no-recursive /path/to/directory

# Exclude certain files
isum --exclude "*.tmp" --exclude ".git/*" /path/to/directory

# Limit traversal depth
isum --max-depth 2 /path/to/directory

# Narrow format
isum --narrow document.pdf

# Process stdin (when no FILE specified)
cat document.pdf | isum
```

## Implementation Notes

1. Process all files as binary data
2. Use 2MB chunks for file reading
3. Support reading from stdin when no FILE is specified
4. Output MUST be deterministic for the same input
5. Base32 encoding MUST use RFC4648 alphabet without padding
6. Use existing Rust library code in `src/lib.rs`
7. Keep implementation simple and focused on core functionality
8. Directory traversal MUST produce identical results across platforms:
   - Sort entries case-sensitively by filename (using UTF-8 byte order)
   - Process regular files only (skip symlinks, devices, etc.)
   - Continue processing remaining files if individual files fail
   - Output files in the order they are processed

## Features NOT Included in Minimal Version

- Checksum verification (`-c/--check`)
- BSD-style output (`--tag`)
- Component units output (`--units`)
- Similarity matching (`--similar`)
- NUL-terminated output (`--zero`)
- Quiet/status modes
- Warning/strict modes

These features may be added in future versions but are excluded to keep the initial implementation simple and
focused. Users requiring these advanced features should use the full-featured Python-based `iscc-sum` tool.
