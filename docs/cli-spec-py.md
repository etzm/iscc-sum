# ISCC-SUM CLI Specification

## Command Synopsis

```
iscc-sum [OPTION]... [FILE]...
```

## Description

The `iscc-sum` command computes ISCC (International Standard Content Code) checksums for files. Each checksum
consists of a 2-byte self-describing header followed by a composite of Data-Code and Instance-Code (BLAKE3)
components. All files are processed as binary data.

Unlike traditional checksum tools that only verify exact matches, `iscc-sum` enables similarity detection
between files through the Data-Code component. Files with similar content will have similar Data-Codes, allowing
similarity matching based on hamming distance.

## Options

### Core Options (GNU coreutils compatible)

- `-c, --check` - Read checksums from FILEs and verify them
- `--tag` - Create a BSD-style checksum output
- `-z, --zero` - End each output line with NUL, not newline
- `--help` - Display help message and exit
- `--version` - Output version information and exit

### Verification Options

- `-q, --quiet` - Don't print OK for successfully verified files
- `--status` - Don't output anything, status code shows success
- `-w, --warn` - Warn about improperly formatted checksum lines
- `--strict` - Exit non-zero for improperly formatted checksum lines

### ISCC-Specific Options

- `--narrow` - Generate narrow format (2×64-bit) conformant with ISO 24138:2024 (default: 2×128-bit extended
  format)
- `--units` - Include individual Data-Code and Instance-Code units in output (verification mode: ignored)

### Similarity Matching Options

- `--similar` - Group files by similarity based on Data-Code hamming distance
  - Cannot be used with `-c/--check`
  - Requires at least 2 files to compare
- `--threshold <N>` - Maximum hamming distance for similarity matching (default: 12)
  - Hamming distance is calculated on Data-Code bits: 128 bits (extended) or 64 bits (narrow)

## Output Format

### Default Format (untagged)

```
<ISCC_CHECKSUM> *<FILENAME>
```

- `<ISCC_CHECKSUM>`: ISCC code starting with "ISCC:" followed by base32 encoded value
- `*`: Binary mode indicator (always present as iscc-sum only processes binary data)
- `<FILENAME>`: Path to the file

Example:

```
ISCC:KACYPXW445FTYNJ3CYSXHAFJMA2HUWULUNRFE3BLHRSCXYH2M5AEGQY *document.pdf
```

### BSD-Tagged Format (--tag)

```
ISCC-SUM (<FILENAME>) = <ISCC_CHECKSUM>
```

Example:

```
ISCC-SUM (document.pdf) = ISCC:KACYPXW445FTYNJ3CYSXHAFJMA2HUWULUNRFE3BLHRSCXYH2M5AEGQY
```

### Extended Output with Units (--units)

When `--units` is specified, output additional lines with component codes:

```
<ISCC_CHECKSUM> *<FILENAME>
  Data-Code: <DATA_CODE_ISCC>
  Instance-Code: <INSTANCE_CODE_ISCC>
```

### Similarity Matching Output (--similar)

Files are grouped by similarity with the first file in each group as reference:

```
<ISCC_CHECKSUM> *<REFERENCE_FILE>
  0: <ISCC_CHECKSUM> *<IDENTICAL_FILE>
  5: <ISCC_CHECKSUM> *<SIMILAR_FILE>
  12: <ISCC_CHECKSUM> *<SIMILAR_FILE>

<ISCC_CHECKSUM> *<ANOTHER_REFERENCE_FILE>
  3: <ISCC_CHECKSUM> *<SIMILAR_FILE>
```

Numbers indicate hamming distance between Data-Code components.

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

- `0` - Success (all checksums matched when verifying; files processed successfully)
- `1` - Verification failure (one or more checksums didn't match)
- `2` - I/O or format error

## Examples

### Generate checksums

```bash
# Single file
iscc-sum document.pdf

# Multiple files  
iscc-sum *.txt

# BSD-style output
iscc-sum --tag document.pdf

# Narrow format (ISO 24138:2024)
iscc-sum --narrow document.pdf

# With component units
iscc-sum --units document.pdf
```

### Verify checksums

```bash
# Verify from checksum file
iscc-sum -c checksums.txt

# Quiet verification (only show failures)
iscc-sum -c --quiet checksums.txt

# Silent verification (exit code only)
iscc-sum -c --status checksums.txt
```

### Find similar files

```bash
# Group similar files
iscc-sum --similar *.jpg

# Use custom similarity threshold (hamming distance)
iscc-sum --similar --threshold 20 documents/*.pdf

# Find similar files recursively (using shell globstar)
iscc-sum --similar **/*.png
```

**Note**: File patterns are expanded by the shell. Use `**/*` with shells that support globstar (bash with
`shopt -s globstar`, zsh) for recursive directory traversal.

## Implementation Notes

1. The tool MUST process all files as binary data (no text encoding/decoding)
2. File reading SHOULD use 2MB chunks for efficiency
3. The tool MUST support reading from stdin when no FILE is specified
4. Output MUST be deterministic for the same input
5. The base32 encoding MUST use RFC4648 alphabet without padding
6. The tool SHOULD auto-detect checksum format when verifying
7. Unlike traditional checksum tools, iscc-sum has no text mode - all files are processed as binary
8. Hamming distance MUST be calculated on the decoded bits of the Data-Code component only (excluding the 2-byte
   header)
9. File patterns are handled by shell expansion; the tool does not implement glob matching
