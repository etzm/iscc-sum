# Implementation Plan: Fix Windows Path Display in Directory Expansion

## Checkpoint 1: Remove Deprecated CLI Options

### Tasks:

- [x] Remove `--recursive` option from CLI definition
- [x] Remove `--no-recursive` option from CLI definition
- [x] Remove `--exclude` option from CLI definition
- [x] Remove `--max-depth` option from CLI definition
- [x] Remove all validation logic for these options
- [x] Remove all references to these options in function signatures
- [x] Update docstrings to remove mentions of these options
- [x] Run existing tests to identify which tests need updating
- [x] Update failing tests to remove references to deprecated options
- [x] Verify all tests pass after cleanup

## Checkpoint 2: Add File Discovery and Expansion Logic

### Tasks:

- [x] Create a new function `_expand_paths` that takes file/directory arguments
- [x] For file arguments, yield the file path as-is
- [x] For directory arguments, use `treewalk_iscc` to get all files
- [x] Handle mixed file and directory arguments correctly
- [x] Add proper error handling for invalid paths
- [x] Create unit tests for `_expand_paths` function
- [x] Test with various path combinations (files, dirs, mixed)
- [x] Ensure deterministic ordering is maintained
- [x] Verify tests pass

## Checkpoint 3: Implement Tree Mode Option

### Tasks:

- [x] Add `--tree/-t` option to CLI definition
- [x] Add validation to ensure tree mode only works with single directory argument
- [x] Create `_handle_tree_mode` function to process entire directory as one unit
- [x] Implement checksum output with trailing slash for tree mode
- [x] Handle both standard and BSD format outputs for tree mode
- [x] Add tree mode tests for basic functionality
- [x] Add tree mode tests for error cases
- [x] Test tree mode with both output formats
- [x] Verify all tree mode tests pass

## Checkpoint 4: Update Main Processing Functions

### Tasks:

- [x] Update `_handle_checksum_generation` to use `_expand_paths`
- [x] Add tree mode handling to checksum generation flow
- [x] Update `_handle_similarity` to use `_expand_paths`
- [x] Update `_handle_verification` to support tree mode checksums
- [x] Ensure stdin handling still works correctly
- [x] Update existing integration tests
- [x] Add tests for directory processing
- [x] Add tests for mixed file/directory arguments
- [x] Run full test suite and fix any remaining issues

## Checkpoint 5: Tree Mode Verification Support

### Tasks:

- [x] Update `_parse_checksum_line` to detect tree mode (trailing slash)
- [x] Implement tree mode verification logic in `_handle_verification`
- [x] When verifying tree checksum, use `treewalk_iscc` on the directory
- [x] Process all files and combine into single checksum
- [x] Add tests for tree mode verification
- [x] Test verification with both standard and BSD formats
- [x] Test error cases (missing directory, changed files)
- [x] Ensure proper exit codes for tree verification

## Checkpoint 6: Update Documentation

### Tasks:

- [x] Update `docs/cli-spec-py.md` to remove deprecated options
- [x] Add `--tree` option documentation to `docs/cli-spec-py.md`
- [x] Update examples to show tree mode usage
- [x] Update directory processing description
- [x] Remove references to exclude patterns and recursion control
- [x] Add tree mode examples to CLI help text
- [x] Update any other relevant documentation files
- [x] Review all documentation for consistency

## Checkpoint 7: Integration and Edge Case Testing

### Tasks:

- [ ] Test with empty directories
- [ ] Test with directories containing only ignored files (.isccignore)
- [ ] Test with symlinks (should be ignored by treewalk)
- [ ] Test with very deep directory structures
- [ ] Test with Unicode filenames
- [ ] Test cross-platform compatibility
- [ ] Add performance tests for large directories
- [ ] Ensure 100% code coverage is maintained
- [ ] Run full test suite with coverage report

## Additional Work Not in Original Plan

### Unicode Normalization Tie-Breaking Fix:

- [x] Updated treewalk-spec.md Section 4.1 to specify deterministic tie-breaking rule
- [x] Updated listdir() implementation to use tuple sorting with original bytes as tie-breaker
- [x] Fixed test expectations in spec to match correct byte ordering
- [x] Added explicit test for unicode normalization tie-breaking behavior
- [x] Verified all tests pass with 100% coverage

### Rust CLI Updates:

- [ ] Remove deprecated options from Rust CLI (`--recursive`, `--no-recursive`, `--exclude`, `--max-depth`)
- [ ] Consider implementing tree mode in Rust CLI for feature parity
- [ ] Update Rust CLI documentation

## Implementation Notes

### Key Considerations:

1. The `treewalk_iscc` function already handles:

   - Deterministic ordering (NFC-normalized UTF-8)
   - .isccignore file processing
   - Filtering of .iscc.json metadata files
   - Symlink exclusion

2. For tree mode:

   - Process all files from `treewalk_iscc` in order
   - Feed each file's content to a single `IsccSumProcessor` instance
   - Output shows directory path with trailing slash

3. Backward compatibility:

   - Since no release yet, we can break compatibility
   - Remove all traces of deprecated options
   - Update all tests and documentation

### Dependencies:

- The existing `treewalk_iscc` function from `iscc_sum.treewalk`
- The existing processor classes from `iscc_sum._core`
- No new external dependencies required
