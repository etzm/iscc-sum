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

### Review - Checkpoint 2

**Summary of changes:**

- Implemented `listdir` function in `src/treewalk.rs` with full NFC normalization support
- Created `DirEntry` struct to represent directory entries with type information
- Added deterministic sorting by normalized UTF-8 bytes with original bytes as tie-breaker
- Implemented symlink filtering for security
- Added comprehensive test suite covering all edge cases
- All tests passing with 100% Python code coverage maintained

All tasks in Checkpoint 2 have been completed successfully.

### Checkpoint 2: Core Listdir Implementation

**Goal**: Implement the foundational directory listing with deterministic ordering.

- [x] Implement `listdir` function with NFC normalization:
  - [x] Read directory entries using std::fs
  - [x] Filter out symlinks for security
  - [x] Apply NFC normalization to entry names
  - [x] Sort by normalized UTF-8 bytes with original bytes as tie-breaker
  - [x] Return structured entry information (name, is_dir, is_file)
- [x] Add comprehensive unit tests for `listdir`:
  - [x] Test basic sorting
  - [x] Test Unicode normalization cases
  - [x] Test duplicate normalized names handling
  - [x] Test symlink filtering
  - [x] Test error handling (permissions, non-existent paths)

### Review - Checkpoint 3

**Summary of changes:**

- Implemented `treewalk` function with recursive directory traversal
- Added `treewalk_recursive` helper function for depth-first traversal
- Implemented correct ordering: ignore files first, regular files second, subdirectories last
- Added comprehensive unit test suite covering:
  - Basic traversal functionality
  - Ignore file prioritization
  - Recursive ordering verification
  - Empty directory handling
  - Deep nesting support
  - Permission error handling (Unix-specific)
  - Unicode file name support
- Fixed cross-platform path separator handling in tests (Windows compatibility)
- All Rust tests passing (19 tests)
- Python test coverage maintained at 100%
- No clippy warnings

All tasks in Checkpoint 3 have been completed successfully.

### Checkpoint 3: Base Treewalk Algorithm

**Goal**: Implement the core recursive tree traversal with ignore file prioritization.

- [x] Implement `treewalk` function:
  - [x] Use `listdir` for deterministic entry ordering
  - [x] Separate entries into files and directories
  - [x] Yield ignore files first (.\*ignore pattern)
  - [x] Yield regular files second
  - [x] Recursively process subdirectories
  - [x] Handle path resolution and normalization
- [x] Implement efficient path handling:
  - [x] Use PathBuf for cross-platform compatibility
  - [x] Implement relative path calculation from root
  - [x] Handle Windows drive roots correctly
- [x] Add unit tests for `treewalk`:
  - [x] Test ignore file prioritization
  - [x] Test recursive traversal order
  - [x] Test empty directories
  - [x] Test deeply nested structures
  - [x] Test permission errors during traversal
- [x] Add integration tests using test vectors from spec

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
