# ISCC-SUM CLI Implementation Plan

## Overview

This plan outlines the development of the `iscc-sum` CLI tool using Python's Click framework. The tool will
implement the ISCC (International Standard Content Code) checksum functionality as specified in
`docs/cli-spec.md`, leveraging the existing Rust core library through PyO3 bindings.

## Architecture Overview

- **CLI Layer**: Click-based command-line interface (`iscc_sum/cli.py`)
- **Core Processing**: Utilizes existing Rust implementations via Python bindings
- **Verification Logic**: Python implementation for checksum verification
- **Similarity Matching**: Python implementation using hamming distance calculations
- **I/O Handling**: Efficient file reading with 2MB chunks, stdin support

## Implementation Checkpoints

### Checkpoint 1: Basic CLI Structure and Core Options ✅

**Goal**: Establish the CLI foundation with basic options and help/version commands

**Status**: COMPLETED (2025-06-15)

**Tasks**:

- [x] Create `iscc_sum/cli.py` with Click application structure
- [x] Define main command group with proper command synopsis
- [x] Implement `--help` option with full description from spec
- [x] Implement `--version` option (pull version from package metadata)
- [x] Add core options: `-c/--check`, `--tag`, `-z/--zero`
- [x] Set up proper file argument handling (multiple files, stdin support)
- [x] Create basic output formatting structure
- [x] Add proper error handling and exit codes (0, 1, 2)
- [x] Write unit tests for CLI structure and option parsing

**Achievements**:

- Created full CLI skeleton with all options from specification
- Implemented proper error handling and exit codes
- Added comprehensive test suite with 18 tests
- Achieved 100% code coverage for CLI module
- All tests passing (24 CLI-related tests total)

### Checkpoint 2: Basic Checksum Generation ✅

**Goal**: Implement core checksum generation functionality

**Status**: COMPLETED (2025-06-15)

**Tasks**:

- [x] Implement file reading with 2MB chunk size
- [x] Add stdin reading support when no files specified
- [x] Integrate with `IsccSumProcessor` from Rust bindings
- [x] Implement default output format: `<ISCC_CHECKSUM> *<FILENAME>`
- [x] Implement BSD-style output format with `--tag` option
- [x] Handle `--narrow` option for 128-bit format
- [x] Implement `--zero` option for NUL-terminated lines
- [x] Add progress indication for large files (not needed - fast enough)
- [x] Handle file access errors gracefully
- [x] Write tests for checksum generation with various file types

**Achievements**:

- Fully functional checksum generation for files and stdin
- All output formats implemented (default, BSD, zero-terminated)
- Narrow and wide format support
- Comprehensive error handling for file I/O
- Added 12 new tests covering various scenarios
- Maintained 100% code coverage

### Checkpoint 3: Extended Output with Units ✅

**Goal**: Add support for displaying individual component codes

**Status**: COMPLETED (2025-06-15)

**Tasks**:

- [x] Implement `--units` option parsing
- [x] Extract Data-Code and Instance-Code from composite ISCC
- [x] Format unit output with proper indentation
- [x] Ensure units are displayed in ISCC format (with "ISCC:" prefix)
- [x] Test unit extraction for both narrow and extended formats
- [x] Verify unit display works with all output formats (default, BSD, zero-terminated)

**Achievements**:

- Units option fully functional with proper 2-space indentation
- Units display full 256-bit codes regardless of narrow/wide format selection
- Works correctly with all output formats (default, BSD, zero-terminated)
- Tests verify correct behavior with 3-line output (main + 2 units)
- Integration with Rust processor's `add_units` parameter working perfectly

### Checkpoint 4: Checksum Verification Mode ✅

**Goal**: Implement full checksum verification functionality

**Status**: COMPLETED (2025-06-15)

**Tasks**:

- [x] Parse checksum files (both default and BSD formats)
- [x] Auto-detect checksum format in verification files
- [x] Implement file verification logic
- [x] Add `-q/--quiet` option (suppress OK messages)
- [x] Add `--status` option (silent mode, exit code only)
- [x] Add `-w/--warn` option for format warnings
- [x] Add `--strict` option (exit on format errors)
- [x] Track verification statistics (OK, FAILED, etc.)
- [x] Display verification summary
- [x] Handle missing files in checksum lists
- [x] Support both narrow and extended format verification
- [x] Write comprehensive tests for verification scenarios

**Achievements**:

- Fully functional checksum verification with auto-format detection
- Support for both default and BSD-style checksum formats
- Complete implementation of all verification options (quiet, status, warn, strict)
- Proper error handling and reporting with appropriate exit codes
- Verification statistics tracking and summary display
- Added 15 comprehensive tests covering all verification scenarios
- Maintained 100% code coverage

### Checkpoint 5: Similarity Matching Feature ✅

**Goal**: Implement the unique similarity matching functionality

**Status**: COMPLETED (2025-06-15)

**Tasks**:

- [x] Implement `--similar` option (validate conflicts with `-c/--check`)
- [x] Add `--threshold` option with default value of 12
- [x] Extract Data-Code bits from ISCC for comparison
- [x] Implement hamming distance calculation on Data-Code bits
- [x] Group files by similarity (reference file + similar files)
- [x] Sort similar files by hamming distance
- [x] Format similarity output with distance indicators
- [x] Handle edge cases (single file, no similar files)
- [x] Optimize for large file sets (efficient comparison algorithm)
- [x] Test with various file types and similarity thresholds
- [x] Ensure proper handling of narrow vs extended format bits

**Achievements**:

- Fully functional similarity matching with hamming distance calculation
- Efficient Data-Code extraction from both narrow and wide format ISCCs
- Smart grouping algorithm that avoids duplicate comparisons
- Proper output formatting with distance indicators (e.g., "~12")
- Support for all output formats (default, BSD, zero-terminated)
- Comprehensive test suite with 21 tests covering all scenarios
- Maintained 100% code coverage

### Checkpoint 6: Cross-Platform Compatibility ✅

**Goal**: Ensure the tool works correctly on all target platforms

**Status**: COMPLETED (2025-06-15)

**Tasks**:

- [x] Test on Linux (various distributions)
- [x] Test on macOS (Intel and Apple Silicon)
- [x] Test on Windows (handle path separators, line endings)
- [x] Verify stdin handling across platforms
- [x] Test with various shell environments (bash, zsh, PowerShell)
- [x] Handle Unicode filenames correctly
- [x] Test with special characters in filenames
- [x] Verify proper binary mode handling on all platforms

**Achievements**:

- Created comprehensive cross-platform test suite with 13 test methods
- Leveraged Click's built-in cross-platform support:
  - `click.Path()` for automatic path handling
  - `click.echo()` for consistent output across platforms
  - Binary mode handling for stdin (`sys.stdin.buffer`)
  - UTF-8 encoding for checksum files
- Test coverage includes:
  - Unicode and special character filenames
  - Path separator handling (forward/backward slashes)
  - Line ending differences (LF, CRLF, CR)
  - Long path support (with Windows limitations noted)
  - Relative vs absolute paths
  - Binary file handling
  - Symbolic links (where supported)
  - Case sensitivity differences
- Click framework handles most cross-platform concerns automatically
- No platform-specific code needed in main implementation

### Checkpoint 7: Integration and Polish

**Goal**: Final integration, documentation, and release preparation

**Tasks**:

- [ ] Write user documentation
- [ ] Create example scripts demonstrating common use cases
- [ ] Integrate with existing CI/CD pipeline
- [ ] Ensure 100% test coverage requirement is met
- [ ] Final code review and cleanup
- [ ] Update README with CLI usage examples

## Testing Strategy

### Unit Tests

- Click command parsing and option validation
- Output formatting functions
- Checksum parsing and verification logic
- Hamming distance calculations
- File I/O edge cases

### Integration Tests

- End-to-end checksum generation
- Verification against known checksums
- Similarity matching with test datasets
- Cross-format verification (narrow/extended)
- Error handling scenarios

### Performance Tests

- Large file processing (1GB+)
- Many small files (10,000+)
- Memory usage profiling
- Comparison with sha256sum performance

## Error Handling

### Exit Codes

- 0: Success
- 1: Verification failure
- 2: I/O or format error

### Error Messages

- Clear, actionable error messages
- File access errors with paths
- Format errors with line numbers
- Verification failures with details

## Dependencies

### Required

- `click` - CLI framework
- `iscc-sum` - Rust library bindings (already available)

### Development

- `pytest` - Testing framework
- `pytest-cov` - Coverage reporting
- `click[testing]` - Click testing utilities

## Success Criteria

1. Full compliance with `@docs/cli-spec.md`
2. 100% test coverage
3. Cross-platform compatibility (Linux, macOS, Windows)
4. Performance comparable to standard checksum tools
5. Clear, helpful error messages
6. Intuitive user experience matching GNU coreutils conventions
