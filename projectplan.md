# Storage-Agnostic Treewalk Implementation Plan

## Overview

Implement universal_pathlib (UPath) based versions of treewalk functions to support various storage backends
(S3, GCS, Azure, HTTP, etc.) while preserving the existing high-performance local filesystem implementation.

## Design Principles

1. **No Breaking Changes**: Keep all existing functions unchanged for backward compatibility
2. **Performance First**: Local filesystem operations should use existing optimized code
3. **Consistent API**: New functions should mirror existing ones with minimal differences
4. **Progressive Enhancement**: Each layer builds on the previous (listdir → treewalk → treewalk_ignore →
    treewalk_iscc)
5. **Test Coverage**: 100% test coverage for all new code

## Helpfull resources

For current information about universal pathlib and fsspec use:

Deepwiki: fsspec/filesystem_spec Deepwiki: fsspec/universal_pathlib

## Checkpoint 1: Foundation - UPath-based listdir

Create the base layer for storage-agnostic directory listing with deterministic ordering.

### Tasks:

- [x] Create `listdir_upath(path, **storage_options)` function
    - [x] Accept UPath or string/Path that gets converted to UPath
    - [x] Use `path.iterdir()` instead of `os.scandir()`
    - [x] Filter out symlinks (where backend supports symlink detection)
    - [x] Implement same NFC normalization and UTF-8 sorting
    - [x] Return list of UPath objects instead of DirEntry objects
- [x] Add type annotations with UPath support
- [x] Create comprehensive tests
    - [x] Test with local filesystem using file:// protocol
    - [x] Test with memory filesystem for isolation
    - [x] Test sorting behavior matches original
    - [x] Test symlink filtering where applicable
- [x] Add docstring explaining differences from original

### Checkpoint 1 Review:

**Completed**: All tasks for Checkpoint 1 have been successfully implemented.

**Summary of changes**:

- Added `listdir_upath()` function to `src/iscc_sum/treewalk.py` (lines 41-85)
- Function accepts UPath, string, or Path objects and converts to UPath
- Uses UPath.iterdir() for backend-agnostic directory listing
- Implements same NFC normalization and UTF-8 sorting as original
- Filters out symlinks where backend supports it, gracefully handles when it doesn't
- Returns list of UPath objects instead of DirEntry objects
- Complete PEP 484 style type annotations
- Comprehensive docstring explaining differences from original

**Testing**:

- Created comprehensive test suite in `tests/test_listdir_upath_comprehensive.py`
- 27 tests covering all functionality including error cases
- Tests with local filesystem (file://) and memory filesystem (memory://)
- Verified sorting behavior matches original listdir exactly
- Achieved 100% test coverage

**Key design decisions**:

- Used try/except for symlink detection to handle backends that don't support it
- Maintained exact same sorting algorithm with NFC normalization and secondary sort
- Kept the API similar to original with addition of \*\*storage_options parameter

## Checkpoint 2: Basic Treewalk - UPath Implementation

Implement storage-agnostic recursive directory traversal.

### Tasks:

- [ ] Create `treewalk_upath(path, **storage_options)` function
    - [ ] Accept UPath or string/Path with storage options
    - [ ] Use `listdir_upath` for directory listing
    - [ ] Replace `is_dir()` and `is_file()` checks with UPath methods
    - [ ] Maintain same yielding order (ignore files → regular files → subdirectories)
    - [ ] Yield UPath objects instead of Path objects
- [ ] Handle edge cases
    - [ ] Non-existent paths
    - [ ] Permission errors on remote backends
    - [ ] Network timeouts (with sensible defaults)
- [ ] Create tests
    - [ ] Test traversal order matches original
    - [ ] Test with nested directory structures
    - [ ] Test with memory filesystem
    - [ ] Test error handling

## Checkpoint 3: Ignore Pattern Support - UPath Implementation

Add gitignore-style pattern matching for storage-agnostic traversal.

### Tasks:

- [ ] Create
    `treewalk_ignore_upath(path, ignore_file_name, root_path=None, ignore_spec=None, **storage_options)`
    - [ ] Replace `open()` with `path.read_text()` for reading ignore files
    - [ ] Handle missing ignore files gracefully on remote backends
    - [ ] Ensure relative path calculations work with UPath
    - [ ] Propagate storage_options through recursive calls
- [ ] Optimize for remote backends
    - [ ] Cache ignore file contents to avoid repeated remote reads
    - [ ] Consider batching existence checks where possible
- [ ] Create tests
    - [ ] Test ignore pattern matching
    - [ ] Test cascading ignore rules
    - [ ] Test with various ignore file placements
    - [ ] Test performance with remote backend simulation

## Checkpoint 4: ISCC-Specific Layer - UPath Implementation

Implement ISCC-specific filtering for storage-agnostic traversal.

### Tasks:

- [ ] Create `treewalk_iscc_upath(path, **storage_options)` function
    - [ ] Use `treewalk_ignore_upath` with ".isccignore"
    - [ ] Filter out ".iscc.json" files
    - [ ] Maintain same behavior as original
- [ ] Create tests
    - [ ] Test .iscc.json filtering
    - [ ] Test .isccignore pattern matching
    - [ ] Test complete traversal behavior

## Checkpoint 5: Performance Optimization

Optimize for common remote storage patterns.

### Tasks:

- [ ] Implement caching layer for remote backends
    - [ ] Cache directory listings for repeated traversals
    - [ ] Cache file type checks (is_dir/is_file)
    - [ ] Add cache TTL configuration
- [ ] Add concurrent operations for remote backends
    - [ ] Parallel directory listing where beneficial
    - [ ] Batch existence checks
- [ ] Add progress callback support
    - [ ] Optional callback for long-running remote operations
    - [ ] Include bytes processed, files found metrics
- [ ] Performance benchmarks
    - [ ] Compare local filesystem performance (should be similar)
    - [ ] Measure remote backend overhead
    - [ ] Document performance characteristics

## Checkpoint 6: Integration and Polish

Integrate with existing codebase and add convenience features.

### Tasks:

- [ ] Update module docstring to document new functions
- [ ] Add examples to docstrings showing remote usage
- [ ] Create protocol detection helper
    - [ ] Auto-detect when to use upath vs regular functions
    - [ ] Provide clear migration path
- [ ] Add comprehensive error messages
    - [ ] Clear errors for missing backend dependencies (s3fs, gcsfs, etc.)
    - [ ] Helpful messages for authentication issues
- [ ] Update type stubs if needed
- [ ] Create integration tests
    - [ ] Test that original functions remain unchanged
    - [ ] Test interoperability between old and new functions

## Checkpoint 7: Documentation and Examples

Create comprehensive documentation for the new functionality.

### Tasks:

- [ ] Write detailed documentation
    - [ ] API reference for all new functions
    - [ ] Migration guide from existing functions
    - [ ] Performance considerations
    - [ ] Backend-specific notes
- [ ] Create example scripts
    - [ ] Local to S3 migration example
    - [ ] Cross-cloud hashing example
    - [ ] Performance comparison script
- [ ] Add inline code examples
    - [ ] Show S3 usage with credentials
    - [ ] Show GCS usage
    - [ ] Show Azure usage
- [ ] Document limitations
    - [ ] Symlink support varies by backend
    - [ ] Performance implications
    - [ ] Authentication requirements

## Testing Strategy

### Unit Tests

- Test each function in isolation
- Use memory filesystem for fast, deterministic tests
- Mock only where absolutely necessary (prefer real implementations)

### Integration Tests

- Test with real local filesystem
- Test with fsspec's memory filesystem
- Optional tests with real cloud backends (marked as slow)

### Performance Tests

- Benchmark against original implementation
- Measure overhead for remote operations
- Profile memory usage

## Review Checklist

- [ ] All new functions have \_upath suffix
- [ ] Original functions unchanged
- [ ] 100% test coverage achieved
- [ ] Type annotations complete
- [ ] Documentation comprehensive
- [ ] Performance acceptable
- [ ] No new required dependencies
- [ ] Error handling robust
