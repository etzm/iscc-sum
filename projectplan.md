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

### Rust Treewalk Implementation

- ✅ Complete Rust port of treewalk.py
- ✅ Full negation pattern support
- ✅ ISCC-specific filtering
- ✅ 63 Rust tests with comprehensive coverage

## Next Milestone: Repository Dogfooding Script

Create a dogfooding script that uses our own iscc_sum library to hash and verify the repository.

### Checkpoint 1: Basic Dogfood Script Implementation

**Goal**: Create the core script with hash generation functionality.

- [x] Create `scripts/dogfood.py` with CLI structure using click
- [x] Implement `generate` command:
  - [x] Use `treewalk_iscc` to iterate over repository files
  - [x] Create `IsccSumProcessor` instance
  - [x] Process all files and accumulate ISCC hash
  - [x] Collect metadata (units, total_size, file_count)
  - [x] Save results to `.iscc.json` in repository root
- [x] ~Add tests for the generate functionality~ (Not needed for scripts/)

### Checkpoint 2: Verification Command

**Goal**: Add verification capability to check repository integrity.

- [x] Implement `verify` command:
  - [x] Load existing `.iscc.json` from repository root
  - [x] Recalculate ISCC hash using current repository state
  - [x] Compare data-code units between stored and calculated
  - [x] Calculate and display hamming distance if mismatch
  - [x] Return appropriate exit codes (0 for match, 1 for mismatch)
- [x] ~Add tests for verification scenarios~ (Not needed for scripts/)

### Checkpoint 3: Integration with Build System

**Goal**: Integrate the dogfood script into the development workflow.

- [x] Add `dogfood` command to pyproject.toml poe tasks:
  - [x] Create task to run `python scripts/dogfood.py generate`
  - [x] Add dogfood to the `all` combined command
- [x] ~Add `.iscc.json` to `.gitignore`~ (Decided to track in git for CI)
- [x] Test the full workflow:
  - [x] Run via `uv run poe dogfood`
  - [x] Verify .iscc.json generation
  - [x] Test verification with and without changes
- [ ] Update documentation if needed

## Review - Repository Dogfooding Script

**Summary of changes:**

- Created `scripts/dogfood.py` with two commands: `generate` and `verify`
- The `generate` command:
  - Uses `treewalk_iscc` to walk the repository in deterministic order
  - Creates a single `IsccSumProcessor` to hash all files
  - Saves the complete result structure from `IsccSumProcessor.result()` to `.iscc.json`
  - Includes metadata: file count, repository path, datahash, filesize, and units
- The `verify` command:
  - Loads the stored `.iscc.json` file
  - Recalculates the repository ISCC
  - Compares ISCCs and shows hamming distance for data-code if different
  - Returns exit code 0 for match, 1 for mismatch
- Added `dogfood` poe task that runs `python scripts/dogfood.py generate`
- Integrated dogfood into the `all` combined command
- Decided to track `.iscc.json` in git (not gitignored) for CI verification

The dogfooding script successfully demonstrates practical usage of our library while providing a useful
integrity checking tool for the repository.
