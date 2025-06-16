# ISUM Implementation Plan

## Overview

This document outlines the implementation plan for the `isum` CLI tool - a minimal, high-performance Rust
implementation of ISCC checksum generation. The tool provides core functionality with faster startup times and
lower resource usage compared to the Python-based `iscc-sum`.

## High-Level Architecture

- **Binary**: `src/main.rs` - CLI entry point
- **Core Logic**: Leverage existing `src/lib.rs` and processor modules
- **Dependencies**: clap (CLI parsing), existing project dependencies
- **Output**: Unix-style checksum format compatible with standard tools

## Implementation Checkpoints

### Checkpoint 1: CLI Foundation and Argument Parsing

**Goal**: Set up basic CLI structure with argument parsing

**Tasks**:

- [x] Add `clap` dependency to `Cargo.toml` for CLI parsing
- [x] Create basic CLI structure in `src/main.rs`
- [x] Implement command-line argument parsing:
  - [x] Positional `FILE` arguments (multiple files support)
  - [x] `--help` flag with usage information
  - [x] `--version` flag showing crate version
  - [x] `--narrow` flag for narrow format selection
- [x] Set up error handling structure with proper exit codes
- [x] Implement basic input validation

### Checkpoint 2: File Processing Infrastructure

**Goal**: Implement efficient file reading and stdin support

**Tasks**:

- [x] Create file processing logic:
  - [x] Support for multiple file arguments
  - [x] Handle non-existent files gracefully
  - [x] Implement 2MB chunk reading for efficiency
- [x] Implement stdin reading when no files specified:
  - [x] Detect when no FILE arguments provided
  - [x] Read binary data from stdin
  - [x] Use same chunking strategy as file reading
- [x] Ensure proper error handling and reporting

### Checkpoint 3: ISCC Checksum Generation

**Goal**: Integrate with existing library code to generate checksums

**Tasks**:

- [x] Import and use `IsccSumProcessor` from library
- [x] Implement checksum generation logic:
  - [x] Create processor instance
  - [x] Feed file data in chunks
  - [x] Finalize and retrieve checksum
- [x] Handle both extended (default) and narrow formats:
  - [x] Set appropriate width based on `--narrow` flag
  - [x] Ensure correct header bytes for each format
- [x] Validate generated checksums match expected format
- [x] Add unit tests for checksum generation

### Checkpoint 4: Output Formatting

**Goal**: Implement correct output format matching specification

**Tasks**:

- [x] Create output formatter:
  - [x] Format: `<ISCC_CHECKSUM> *<FILENAME>`
  - [x] Ensure proper base32 encoding (RFC4648, no padding)
  - [x] Always include binary mode indicator (`*`)
- [x] Handle special cases:
  - [x] Stdin input: use `-` as filename
  - [x] Paths with special characters
  - [x] Unicode filenames
- [x] Ensure output is deterministic
- [x] Write output to stdout with proper line endings

### Checkpoint 5: Error Handling and Edge Cases

**Goal**: Robust error handling and user-friendly error messages

**Tasks**:

- [x] Implement comprehensive error handling:
  - [x] File not found errors
  - [ ] Permission denied errors
  - [x] I/O errors during reading
  - [ ] Invalid UTF-8 in filenames
- [x] Set correct exit codes:
  - [x] 0 for success
  - [x] 1 for any error
- [x] Write error messages to stderr
- [ ] Handle edge cases:
  - [ ] Empty files
  - [ ] Very large files
  - [ ] Symbolic links
  - [ ] Special files (devices, pipes)

### Checkpoint 6: Performance Optimization

**Goal**: Ensure minimal overhead and fast execution

**Tasks**:

- [ ] Profile the implementation:
  - [ ] Measure startup time
  - [ ] Check memory usage
  - [ ] Identify bottlenecks
- [ ] Optimize critical paths:
  - [ ] Minimize allocations
  - [ ] Use efficient I/O buffering
  - [ ] Leverage parallel processing if beneficial
- [ ] Benchmark against Python implementation
- [ ] Ensure release builds are optimized

### Checkpoint 7: Testing and Documentation

**Goal**: Comprehensive testing and user documentation

**Tasks**:

- [ ] Write unit tests:
  - [ ] CLI argument parsing
  - [ ] File processing logic
  - [ ] Output formatting
  - [ ] Error scenarios
- [ ] Create integration tests:
  - [ ] Test with various file types
  - [ ] Verify output matches Python implementation
  - [ ] Test stdin processing
  - [ ] Multi-file processing
- [ ] Add example usage to help text
- [ ] Update README with isum information
- [ ] Document any implementation decisions

### Checkpoint 8: Cross-Platform Compatibility

**Goal**: Ensure tool works on Linux, macOS, and Windows

**Tasks**:

- [ ] Test on all target platforms:
  - [ ] Linux (various distributions)
  - [ ] macOS (Intel and Apple Silicon)
  - [ ] Windows (native and WSL)
- [ ] Handle platform-specific issues:
  - [ ] Path separators
  - [ ] Line endings
  - [ ] Binary mode handling
- [ ] Ensure consistent behavior across platforms
- [ ] Update CI to test all platforms

### Checkpoint 9: Release Preparation

**Goal**: Prepare for distribution and installation

**Tasks**:

- [ ] Configure release builds:
  - [ ] Enable all optimizations
  - [ ] Strip debug symbols
  - [ ] Minimize binary size
- [ ] Set up binary distribution:
  - [ ] Configure GitHub releases
  - [ ] Create platform-specific binaries
  - [ ] Consider static linking for portability
- [ ] Test installation methods:
  - [ ] Direct binary download
  - [ ] Package manager integration (future)
- [ ] Create changelog entry

## Implementation Order

1. ✅ Start with Checkpoints 1-3 to get basic functionality working
2. ✅ Add Checkpoint 4 for proper output
3. ⚠️ Implement Checkpoint 5 for robustness (basic error handling done)
4. ❌ Follow with Checkpoints 6-7 for quality
5. ❌ Complete with Checkpoints 8-9 for release

## Current Status

The `isum` CLI tool is **functionally complete** with all core features implemented:

- Working CLI with proper argument parsing
- File and stdin processing with efficient chunking
- ISCC checksum generation for both 256-bit and 128-bit formats
- Correct Unix-style output formatting
- Basic error handling with proper exit codes

Remaining work focuses on quality assurance, testing, and release preparation.

## Success Criteria

- [x] Tool compiles without warnings
- [ ] All tests pass with 100% coverage of new code
- [ ] Performance is measurably better than Python version
- [ ] Output exactly matches Python implementation
- [ ] Works on all target platforms
- [ ] Binary size is reasonable (< 10MB)
- [x] Zero dependencies beyond what's already in the project

## Risk Mitigation

1. **Compatibility Risk**: Test extensively against Python implementation
2. **Performance Risk**: Profile early and often
3. **Platform Risk**: Use GitHub Actions for multi-platform CI
4. **Maintenance Risk**: Keep implementation minimal and well-documented

## Future Enhancements (Out of Scope)

- Checksum verification (`-c/--check`)
- BSD-style output (`--tag`)
- Component units output (`--units`)
- Similarity matching (`--similar`)
- Advanced output options
- Progress bars or verbose modes

These features are explicitly excluded from the initial implementation to maintain simplicity and focus on core
functionality.
