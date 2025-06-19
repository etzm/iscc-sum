# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 0.1.0 (2025-06-19)


### Features

* add -o/--output option for cross-platform checksum files ([1dbe7be](https://github.com/bio-codes/iscc-sum/commit/1dbe7be96511659193f53a45fc7b8b02c3fc19f7))
* add CLI with file and stdin processing support ([2708824](https://github.com/bio-codes/iscc-sum/commit/27088248f119ddbec906f5cf600ed2c1f4b3d5eb))
* add comprehensive cross-platform compatibility tests ([348710a](https://github.com/bio-codes/iscc-sum/commit/348710ac3dc06822fdca39f7e96a4d40e7ce7dfb))
* Add comprehensive test suite for isum CLI tool ([9a7102a](https://github.com/bio-codes/iscc-sum/commit/9a7102a23f7d6b04d6fa18e3e9cd7f1b7877858b))
* add comprehensive treewalk test vectors with cross-platform support ([c1ebd9a](https://github.com/bio-codes/iscc-sum/commit/c1ebd9a50f15b1d8b335e27278df3a4dcc07be0f))
* Add comprehensive unit tests for ISCC checksum generation ([015e736](https://github.com/bio-codes/iscc-sum/commit/015e736e604ee4ea1af4718e1165cfad82467a12))
* add content-defined chunking (CDC) module and update project configuration ([edcb308](https://github.com/bio-codes/iscc-sum/commit/edcb3089378d45fb5a415c0a01c401cd9ee07451))
* add data code draft with CDC chunking and minhash implementation ([914bc7b](https://github.com/bio-codes/iscc-sum/commit/914bc7b6b9a516e66ea6d1fefe877dce3302d183))
* add DataCodeProcessor for incremental data hashing ([1707774](https://github.com/bio-codes/iscc-sum/commit/170777474fb6ae2d4c98161d6ad78179e2c3616f))
* add InstanceCodeProcessor for BLAKE3-based instance hashing ([b6dc272](https://github.com/bio-codes/iscc-sum/commit/b6dc272b9616ee8f91bebb367edab66ef28b1f6e))
* add ISCC-CODE SUM reference implementation with comprehensive tests ([051123c](https://github.com/bio-codes/iscc-sum/commit/051123c0d1521e0cd31dc590b5ab4a9f1dc9842f))
* add minhash module for ISCC Data-Code similarity detection ([c5377b8](https://github.com/bio-codes/iscc-sum/commit/c5377b8b6943bf3eddfe12b39ab542f67c197379))
* add performance benchmarking script ([d6104e2](https://github.com/bio-codes/iscc-sum/commit/d6104e24a133f6d4dfc0a101ce29455e6ce6900a))
* add py.typed marker for type hint support ([0cf7acf](https://github.com/bio-codes/iscc-sum/commit/0cf7acf7aa470419b9e016a42f1c7580cd43a747))
* add Python wrapper for code_iscc_sum with fsspec support ([4018dff](https://github.com/bio-codes/iscc-sum/commit/4018dff43c9f48bb9ebbf9d05039c04d7a41f5dd))
* add recursive directory processing with exclude and depth options ([2b41afc](https://github.com/bio-codes/iscc-sum/commit/2b41afcd9e7ab80f2afa4195c073b81299c91e43))
* add recursive directory processing with walkdir and error handling ([b97ab1c](https://github.com/bio-codes/iscc-sum/commit/b97ab1ce6501704a982dc2a5e346aa714caf88e3))
* add release build support for benchmarking ([0a9dea4](https://github.com/bio-codes/iscc-sum/commit/0a9dea4c7717e28c79f1c29063d05f3f3b9d8665))
* add repository ISCC dogfooding with datasize field ([d9ead34](https://github.com/bio-codes/iscc-sum/commit/d9ead3477678c89fefdb69faed5d1fb1d5e9c0e8))
* add Rust treewalk module infrastructure ([7edbfac](https://github.com/bio-codes/iscc-sum/commit/7edbfac0f4ea575aa20a507685caab84bdd89fdf))
* add tree mode verification support ([fc21243](https://github.com/bio-codes/iscc-sum/commit/fc212432563715a2185a31a0d4f518677f0cd253))
* add treewalk module with deterministic directory traversal and ignore file support ([60936d8](https://github.com/bio-codes/iscc-sum/commit/60936d83a42f14a20c871509dd7f8746b4e9739a))
* complete CLI units option implementation (Checkpoint 3) ([c8aab04](https://github.com/bio-codes/iscc-sum/commit/c8aab04a3f93d3fe5110996499d365200f2df992))
* Enhance error handling and edge case support for file processing ([1b83007](https://github.com/bio-codes/iscc-sum/commit/1b8300702481b05259874b213ffcb15c1c9e1fe6))
* implement basic checksum generation for iscc-sum CLI ([c6eda49](https://github.com/bio-codes/iscc-sum/commit/c6eda4946b5e88246596d4b193548718ca36fd11))
* implement basic CLI structure with Click framework ([e36ef32](https://github.com/bio-codes/iscc-sum/commit/e36ef32dc649418e0b5f58a3041ef40a8af099ad))
* implement checksum verification mode for iscc-sum CLI ([6e26b78](https://github.com/bio-codes/iscc-sum/commit/6e26b780909678ffd7d586a2f182fc8626bdb194))
* implement ISCC Data-Code and Instance-Code functionality ([934355d](https://github.com/bio-codes/iscc-sum/commit/934355d3cd3259987c89230a24d6968c2400ccdb))
* implement ISCC-SUM functionality in Rust ([09235dc](https://github.com/bio-codes/iscc-sum/commit/09235dc12c54986b71f8cda625f017d2e81ec0c5))
* implement listdir function with NFC normalization for Rust treewalk ([7539771](https://github.com/bio-codes/iscc-sum/commit/7539771b1355e9292a94173820a0555b580b4100))
* implement negation pattern support in Rust treewalk ([d6669db](https://github.com/bio-codes/iscc-sum/commit/d6669db78fb64bc85ba77a27512b1e6bc19be3d1))
* implement Rust treewalk base algorithm (Checkpoint 3) ([4fd0319](https://github.com/bio-codes/iscc-sum/commit/4fd03192f425a926e968d71a860716bb6e5a379c))
* implement similarity matching functionality for iscc-sum CLI ([6a30f53](https://github.com/bio-codes/iscc-sum/commit/6a30f53ea7d928e72c8b7ab83b7be318d3286557))
* implement tree mode option for directory processing ([0c0b933](https://github.com/bio-codes/iscc-sum/commit/0c0b93379c5d7bc5119e9cad7c3ae9deae0d8e3d))
* implement treewalk_ignore with gitignore-style pattern matching ([11d9340](https://github.com/bio-codes/iscc-sum/commit/11d934010b653e0e8989d5cb4409a6579ede7742))
* implement treewalk_iscc function in Rust ([a5e49bd](https://github.com/bio-codes/iscc-sum/commit/a5e49bd70403ba4a847d3d2ebf6fa2e25dcfb348))
* improve Python bindings developer UX ([cadcf06](https://github.com/bio-codes/iscc-sum/commit/cadcf069c8adeb6ac85ce387c9a88038f3244d84))
* optimize performance with release profile and buffered I/O ([0dc3edf](https://github.com/bio-codes/iscc-sum/commit/0dc3edf97020692c349842e02e0165fda57c7875))
* return typed IsccSumResult class from Rust instead of plain dict ([8954a80](https://github.com/bio-codes/iscc-sum/commit/8954a80d6693f8f1e53c6c4f9b104c7d2a079bbb))


### Bug Fixes

* add chmod step to make downloaded binary executable in CI ([e7607be](https://github.com/bio-codes/iscc-sum/commit/e7607be5108e25f48ed9fa8993de9d6b7c74aa78))
* add Python setup to Rust binary build workflow for Windows ([1e28e49](https://github.com/bio-codes/iscc-sum/commit/1e28e49a987792c13dcd3e8fc52893c435f47f00))
* Add Rust toolchain setup for cross-compilation in Python wheel builds ([d58f45c](https://github.com/bio-codes/iscc-sum/commit/d58f45cadd875f65ce3acab2ca319b45fb701a6c))
* correct typo in constants module import and filename ([041045b](https://github.com/bio-codes/iscc-sum/commit/041045ba846841658df578f84d711dea256ae57a))
* ensure Python 3.10+ is available for PyO3 builds in CI ([8087334](https://github.com/bio-codes/iscc-sum/commit/8087334ba8d678e8c79d134871a91ea976d7cc33))
* Ensure Windows compatibility for treewalk module ([6494dfd](https://github.com/bio-codes/iscc-sum/commit/6494dfd725bf73c42cb1469dce1cbce1bf256922))
* handle Windows paths correctly in directory expansion ([6156b4c](https://github.com/bio-codes/iscc-sum/commit/6156b4c55aa6fa4113d1a52b8d1e7d76294283ec))
* implement deterministic tie-breaking for duplicate normalized names ([731ddef](https://github.com/bio-codes/iscc-sum/commit/731ddeff5a540d3661c838a3c398a33ac90c0cf7))
* make Unicode normalization tests compatible with macOS filesystem behavior ([afdbafa](https://github.com/bio-codes/iscc-sum/commit/afdbafa01e757b1e16c097f4e8cecef77b6ff9a0))
* normalize line endings to fix Windows CI doctest failures ([1220041](https://github.com/bio-codes/iscc-sum/commit/122004133d0d907657df9a7af341e46f30094d68))
* resolve CI failures - formatting and virtual environment issues ([8f38052](https://github.com/bio-codes/iscc-sum/commit/8f380525ca7099f2cfb28b35021bbe4e4b906433))
* resolve CI failures and CLI naming conflict ([db4caa6](https://github.com/bio-codes/iscc-sum/commit/db4caa62607e60a659224771c01b31420c0cc0f2))
* update treewalk test vectors to properly test Unicode normalization ([1559804](https://github.com/bio-codes/iscc-sum/commit/15598044da3ccb605fa26066a6472b4091a74ae3))
* use git config instead of invalid autocrlf parameter in CI ([031d4e0](https://github.com/bio-codes/iscc-sum/commit/031d4e0f893ef9e0b734d6dd8f40eb79a64bf918))

## [0.1.0] - 2025-06-19

### Summary

First stable release of iscc-sum, a high-performance ISCC Data-Code and Instance-Code hashing tool built in Rust
with Python bindings. This release achieves 50-130x performance improvements over the pure python reference
implementation while maintaining full compatibility with the ISCC standard.

### Added

#### Core Features

- **ISCC Data-Code generation**: Content-defined chunking (CDC) algorithm for content similarity detection
    - Wide format (128-bit, default) for enhanced security and similarity matching
    - Narrow format (64-bit) for ISO 24138:2024 compliance via `--narrow` flag
- **ISCC Instance-Code generation**: BLAKE3-based cryptographic hash for file integrity verification
- **ISCC-SUM composite code**: Combined Data-Code and Instance-Code with self-describing header
- **High-performance processing**: 950-1050 MB/s throughput using SIMD optimizations and parallel processing

#### Command-Line Interface

- **Full-featured CLI** (`iscc-sum`) with Unix-style interface
    - Generate checksums for files, directories, and stdin
    - Verify checksums from files (`-c, --check`)
    - Find similar files based on data (`--similar`)
    - Process directories as single objects (`-t, --tree`)
    - BSD-style output format (`--tag`)
    - NUL-terminated output (`--zero`)
    - Show individual code components (`--units`)

#### Python API

- **High-level API** for easy integration
    - `code_iscc_sum()` function supporting local files and fsspec URIs
    - Streaming processors for large file handling
    - Dictionary-compatible result objects
- **Universal path support** via fsspec integration
    - Process files from S3, HTTP/HTTPS, and other remote sources
    - Transparent handling of different storage backends

#### Platform Support

- **Cross-platform compatibility**: Linux, macOS, and Windows
- **Python version support**: 3.10, 3.11, 3.12, and 3.13
- **Pre-built wheels** for all major platforms

#### Developer Experience

- **100% test coverage** requirement with comprehensive test suite
- **Integrated tooling** via poethepoet task automation
- **Type annotations** with mypy type checking
- **Security scanning** with Bandit
- **Automated CI/CD** pipeline with Release Please

### Performance

- **50-130x faster** than pure Python reference implementations
- **950-1050 MB/s** processing speed on modern hardware
- **Parallel processing** using Rayon for multi-core utilization

### Standards Compliance

- **ISO 24138:2024 compatible** when using `--narrow` flag
- **Reference implementation compatibility** for all code formats
- **Deterministic output** across platforms

### Known Limitations

- This is an early release focused on core functionality
- Advanced ISCC features (Text-Code, Meta-Code) are out of scope for now
- Rust crate not published to crates.io in this release

### Dependencies

- blake3 >=1.0.5 - Cryptographic hashing
- click >=8.0.0 - CLI framework
- pathspec >=0.12.1 - Gitignore-style pattern matching
- universal-pathlib >=0.2.6 - Cross-platform path handling
- xxhash >=3.5.0 - High-speed hashing for CDC

### Acknowledgments

This project implements the ISCC (International Standard Content Code) as defined in ISO 24138:2024. The
performance improvements are achieved through Rust's zero-cost abstractions and careful algorithm optimization
while maintaining full compatibility with the standard.
