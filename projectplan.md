# iscc-sum Project Plan

## Completed Tasks

### Initial Setup and Infrastructure

- ✅ Project setup with maturin and basic Rust/Python structure
- ✅ Basic CLI implementation with both Python and Rust versions
- ✅ Core hashing algorithms (Data-Code, Instance-Code) in Rust
- ✅ Python bindings via PyO3
- ✅ Comprehensive test suite with 100% coverage
- ✅ Reference implementations for verification
- ✅ Benchmarking framework

### Tree Mode Feature

- ✅ Tree mode specification (treewalk-spec.md)
- ✅ Python implementation of treewalk algorithms
- ✅ Tree mode verification support
- ✅ Test vectors for treewalk functionality
- ✅ Deterministic tie-breaking for duplicate normalized names

## Next Milestone: Rust Treewalk Implementation

A compatible RUST port of @src/iscc_sum/treewalk.py

### Review - Checkpoint 1

**Summary of changes:**

- Added `unicode-normalization = "0.1"` dependency to Cargo.toml for NFC normalization support
- Created `src/treewalk.rs` module with initial error types and structure
- Added module declaration to `src/lib.rs`
- Set up TreewalkError enum with IoError and InvalidPath variants
- Created unit test module structure with basic error conversion test

All tasks in Checkpoint 1 have been completed. The infrastructure is ready for implementing the core treewalk
algorithms.

### Checkpoint 1: Core Infrastructure Setup

**Goal**: Set up the foundation for the Rust treewalk module with necessary dependencies and basic structure.

- [x] Add dependencies to Cargo.toml:
  - [x] `globset` for pattern matching (already in use, verify version)
  - [x] `unicode-normalization` for NFC normalization
  - [x] `walkdir` (optional - evaluate if needed vs custom implementation)
- [x] Create `src/treewalk.rs` module file with module documentation
- [x] Add module declaration to `src/lib.rs`
- [x] Set up basic error types for treewalk operations
- [x] Create unit test module structure in `src/treewalk.rs`

### Checkpoint 2: Core Listdir Implementation

**Goal**: Implement the foundational directory listing with deterministic ordering.

- [ ] Implement `listdir` function with NFC normalization:
  - [ ] Read directory entries using std::fs
  - [ ] Filter out symlinks for security
  - [ ] Apply NFC normalization to entry names
  - [ ] Sort by normalized UTF-8 bytes with original bytes as tie-breaker
  - [ ] Return structured entry information (name, is_dir, is_file)
- [ ] Add comprehensive unit tests for `listdir`:
  - [ ] Test basic sorting
  - [ ] Test Unicode normalization cases
  - [ ] Test duplicate normalized names handling
  - [ ] Test symlink filtering
  - [ ] Test error handling (permissions, non-existent paths)

### Checkpoint 3: Base Treewalk Algorithm

**Goal**: Implement the core recursive tree traversal with ignore file prioritization.

- [ ] Implement `treewalk` function:
  - [ ] Use `listdir` for deterministic entry ordering
  - [ ] Separate entries into files and directories
  - [ ] Yield ignore files first (.\*ignore pattern)
  - [ ] Yield regular files second
  - [ ] Recursively process subdirectories
  - [ ] Handle path resolution and normalization
- [ ] Implement efficient path handling:
  - [ ] Use PathBuf for cross-platform compatibility
  - [ ] Implement relative path calculation from root
  - [ ] Handle Windows drive roots correctly
- [ ] Add unit tests for `treewalk`:
  - [ ] Test ignore file prioritization
  - [ ] Test recursive traversal order
  - [ ] Test empty directories
  - [ ] Test deeply nested structures
  - [ ] Test permission errors during traversal
- [ ] Add integration tests using test vectors from spec

### Checkpoint 4: Treewalk-Ignore Extension

**Goal**: Add gitignore-style pattern matching with cascading rules.

- [ ] Implement pattern parsing and matching:
  - [ ] Create `IgnoreSpec` wrapper around globset
  - [ ] Parse ignore files with proper error handling
  - [ ] Handle gitignore-specific syntax (comments, negation, etc.)
- [ ] Implement `treewalk_ignore` function:
  - [ ] Load and parse ignore files at each directory level
  - [ ] Accumulate patterns from root to current directory
  - [ ] Apply pattern matching to filter entries
  - [ ] Handle directory exclusion to prevent traversal
  - [ ] Maintain pattern precedence rules
- [ ] Add comprehensive tests:
  - [ ] Test basic pattern matching
  - [ ] Test pattern precedence and overrides
  - [ ] Test directory exclusion
  - [ ] Test negation patterns
  - [ ] Test edge cases (empty ignore files, invalid patterns)
- [ ] Performance optimization:
  - [ ] Cache compiled patterns
  - [ ] Optimize pattern matching for large ignore files
  - [ ] Benchmark against Python pathspec implementation

### Checkpoint 5: Treewalk-ISCC Extension

**Goal**: Implement ISCC-specific filtering on top of treewalk-ignore.

- [ ] Implement `treewalk_iscc` function:
  - [ ] Use treewalk_ignore with `.isccignore` files
  - [ ] Add automatic filtering of `.iscc.json` files
  - [ ] Ensure proper layering of filters
- [ ] Add tests for ISCC-specific behavior:
  - [ ] Test .isccignore processing
  - [ ] Test .iscc.json filtering
  - [ ] Test interaction between filters
  - [ ] Verify conformance with specification
- [ ] Integration tests with existing ISCC hashing

### Checkpoint 9: Documentation and Polish

**Goal**: Ensure the implementation is production-ready with proper documentation.

- [ ] Complete documentation:
  - [ ] API documentation with examples
- [ ] Code quality:
  - [ ] Run clippy and fix all warnings
  - [ ] Ensure consistent error messages
  - [ ] Review and if necessary refactor for clarity
- [ ] Final testing:
  - [ ] Run full test suite
  - [ ] Verify spec compliance
