# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
