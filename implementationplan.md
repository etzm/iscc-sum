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

### Checkpoint 2: Basic Checksum Generation

**Goal**: Implement core checksum generation functionality

**Tasks**:

- [ ] Implement file reading with 2MB chunk size
- [ ] Add stdin reading support when no files specified
- [ ] Integrate with `IsccSumProcessor` from Rust bindings
- [ ] Implement default output format: `<ISCC_CHECKSUM> *<FILENAME>`
- [ ] Implement BSD-style output format with `--tag` option
- [ ] Handle `--narrow` option for 128-bit format
- [ ] Implement `--zero` option for NUL-terminated lines
- [ ] Add progress indication for large files (if needed)
- [ ] Handle file access errors gracefully
- [ ] Write tests for checksum generation with various file types

### Checkpoint 3: Extended Output with Units

**Goal**: Add support for displaying individual component codes

**Tasks**:

- [ ] Implement `--units` option parsing
- [ ] Extract Data-Code and Instance-Code from composite ISCC
- [ ] Format unit output with proper indentation
- [ ] Ensure units are displayed in ISCC format (with "ISCC:" prefix)
- [ ] Test unit extraction for both narrow and extended formats
- [ ] Verify unit display works with all output formats (default, BSD, zero-terminated)

### Checkpoint 4: Checksum Verification Mode

**Goal**: Implement full checksum verification functionality

**Tasks**:

- [ ] Parse checksum files (both default and BSD formats)
- [ ] Auto-detect checksum format in verification files
- [ ] Implement file verification logic
- [ ] Add `-q/--quiet` option (suppress OK messages)
- [ ] Add `--status` option (silent mode, exit code only)
- [ ] Add `-w/--warn` option for format warnings
- [ ] Add `--strict` option (exit on format errors)
- [ ] Track verification statistics (OK, FAILED, etc.)
- [ ] Display verification summary
- [ ] Handle missing files in checksum lists
- [ ] Support both narrow and extended format verification
- [ ] Write comprehensive tests for verification scenarios

### Checkpoint 5: Similarity Matching Feature

**Goal**: Implement the unique similarity matching functionality

**Tasks**:

- [ ] Implement `--similar` option (validate conflicts with `-c/--check`)
- [ ] Add `--threshold` option with default value of 12
- [ ] Extract Data-Code bits from ISCC for comparison
- [ ] Implement hamming distance calculation on Data-Code bits
- [ ] Group files by similarity (reference file + similar files)
- [ ] Sort similar files by hamming distance
- [ ] Format similarity output with distance indicators
- [ ] Handle edge cases (single file, no similar files)
- [ ] Optimize for large file sets (efficient comparison algorithm)
- [ ] Test with various file types and similarity thresholds
- [ ] Ensure proper handling of narrow vs extended format bits

### Checkpoint 6: Performance Optimization

**Goal**: Ensure the tool performs efficiently for large-scale usage

**Tasks**:

- [ ] Profile the application for performance bottlenecks
- [ ] Implement parallel processing for multiple files (if beneficial)
- [ ] Optimize file I/O operations
- [ ] Add caching for repeated file access (if needed)
- [ ] Minimize memory usage for large file processing
- [ ] Benchmark against reference implementations
- [ ] Test with very large files (GB+ size)
- [ ] Test with thousands of small files

### Checkpoint 7: Cross-Platform Compatibility

**Goal**: Ensure the tool works correctly on all target platforms

**Tasks**:

- [ ] Test on Linux (various distributions)
- [ ] Test on macOS (Intel and Apple Silicon)
- [ ] Test on Windows (handle path separators, line endings)
- [ ] Verify stdin handling across platforms
- [ ] Test with various shell environments (bash, zsh, PowerShell)
- [ ] Handle Unicode filenames correctly
- [ ] Test with special characters in filenames
- [ ] Verify proper binary mode handling on all platforms

### Checkpoint 8: Integration and Polish

**Goal**: Final integration, documentation, and release preparation

**Tasks**:

- [ ] Create comprehensive CLI tests using Click's testing utilities
- [ ] Add integration tests comparing output with reference implementation
- [ ] Write user documentation (man page format)
- [ ] Create example scripts demonstrating common use cases
- [ ] Add shell completion support (bash, zsh, fish)
- [ ] Integrate with existing CI/CD pipeline
- [ ] Ensure 100% test coverage requirement is met
- [ ] Performance comparison with Rust CLI (when available)
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

1. Full compliance with `docs/cli-spec.md`
2. 100% test coverage
3. Cross-platform compatibility (Linux, macOS, Windows)
4. Performance comparable to standard checksum tools
5. Clear, helpful error messages
6. Intuitive user experience matching GNU coreutils conventions
