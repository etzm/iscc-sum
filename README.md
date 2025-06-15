# iscc-sum

[![CI](https://github.com/bio-codes/iscc-sum/actions/workflows/ci.yml/badge.svg)](https://github.com/bio-codes/iscc-sum/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/iscc-sum.svg)](https://pypi.org/project/iscc-sum/)
[![Crates.io](https://img.shields.io/crates/v/iscc-sum.svg)](https://crates.io/crates/iscc-sum)

High-performance ISCC Data-Code and Instance-Code hashing tool, implemented in Rust with Python bindings.

## Project Status

> [!CAUTION]
> **Early Release** — This project is in its early development stage.

## Installation

### Python Package

Install from PyPI:

```bash
pip install iscc-sum
```

### Rust CLI Tool

Install from crates.io:

```bash
cargo install iscc-sum
```

Or download pre-built binaries from the [releases page](https://github.com/bio-codes/iscc-sum/releases).

## Usage

### Command Line

```bash
# Using the Rust CLI tool
iscc-sum-rs

# Using Python module (provides iscc-sum command)
python -m iscc_sum
# or if installed:
iscc-sum
```

### Python API

#### Quick Start

Generate ISCC-SUM codes for files:

```pycon
>>> from iscc_sum import code_iscc_sum
>>> 
>>> # Generate ISCC-SUM for a file
>>> result = code_iscc_sum("LICENSE")
>>> result.iscc
'ISCC:KUAA2G6UMXGFJAO6HAZ7YPERUN476'
>>> result.datahash
'1e203833fc3c91a379ff509b431db1f7fd40dea69a6614249f420ec62398957087b1'
>>> result.filesize
11357

```

#### Streaming API

For large files or streaming data, use the processor classes:

```python
from iscc_sum import IsccSumProcessor

processor = IsccSumProcessor()
with open("large_file.bin", "rb") as f:
    while chunk := f.read(1024 * 1024):  # Read in 1MB chunks
        processor.update(chunk)

result = processor.result(wide=False, add_units=True)
print(f"ISCC: {result.iscc}")
print(f"Units: {result.units}")  # Individual Data-Code and Instance-Code
```

## Development

### Prerequisites

- **Rust** (latest stable) - Install from [rustup.rs](https://rustup.rs/)
- **Python 3.10+**
- **UV** (for Python dependency management) - Install from [astral.sh/uv](https://astral.sh/uv)

### Quick Setup

```bash
# Clone the repository

git clone https://github.com/bio-codes/iscc-sum.git
cd iscc-sum

# Install Python dependencies
uv sync --all-extras

# Setup Rust development components
uv run poe setup

# Build Python extension and run all checks
uv run poe all
```

### Development Commands

All development tasks are managed through [poethepoet](https://poethepoet.natn.io/):

```bash
# One-time setup (installs Rust components)
uv run poe setup

# Pre-commit checks (format, lint, test everything)
uv run poe all

# Individual commands
uv run poe format        # Format all code (Rust + Python)
uv run poe test          # Run all tests (Rust + Python)
uv run poe typecheck     # Run Python type checking
uv run poe rust-build    # Build Rust binary
uv run poe build-ext     # Build Python extension

# Check if Rust toolchain is properly installed
uv run poe check-rust
```

### Manual Setup (if needed)

```bash
# Install all dependencies including dev dependencies
uv sync --all-extras

# Install Rust components manually
rustup component add rustfmt clippy

# Build Rust extension for Python
uv run maturin develop

# Run tests manually
cargo test        # Rust tests
uv run pytest     # Python tests
```

### Building

```bash
# Build Rust binary (creates iscc-sum-rs executable)
cargo build --release

# Build Python wheels
maturin build --release
```

## Funding

This project has received funding from the European Commission's Horizon Europe Research and Innovation
programme under grant agreement No. 101129751 as part of the
[BIO-CODES](https://oscars-project.eu/projects/bio-codes-enhancing-ai-readiness-bioimaging-data-content-based-identifiers)
project (Enhancing AI-Readiness of Bioimaging Data with Content-Based Identifiers).

## License

This project is licensed under the Apache License, Version 2.0 - see the [LICENSE](LICENSE) file for details.
