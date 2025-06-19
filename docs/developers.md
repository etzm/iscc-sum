# iscc-sum

[![CI](https://github.com/bio-codes/iscc-sum/actions/workflows/ci.yml/badge.svg)](https://github.com/bio-codes/iscc-sum/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/iscc-sum.svg)](https://pypi.org/project/iscc-sum/)
[![Crates.io](https://img.shields.io/crates/v/iscc-sum.svg)](https://crates.io/crates/iscc-sum)

A blazing-fast ISCC Data-Code and Instance-Code hashing tool built in Rust with Python bindings. Delivers
**50-130x faster** performance than reference implementations, processing data at over 1 GB/s.

Originally created to handle massive microscopic imaging datasets where existing tools were too slow.

## Project Status

!!! danger

    **Early Release** — This project is in its early development stage.

!!! note

    By default, this tool creates ISCC-CODEs of SubType WIDE, introduced for large-scale secure checksum support
    with data similarity matching capabilities. This SubType is not yet part of the ISO 24138:2024 standard but is
    supported by the latest version of the [Iscc-Core](https://github.com/iscc/iscc-core) reference implementation.
    For ISO 24138:2024 conformant ISCC-CODEs, use the `--narrow` flag in the CLI tool.

## Performance

- **950-1050 MB/s** processing speed (vs 7-8 MB/s reference)
- **50-130x faster** than existing implementations
- **Consistent performance** on multi-GB files

Ideal for large-scale data processing: microscopic imaging, video files, scientific datasets.

## Installation

### Python Package

The recommended way to install the iscc-sum CLI tool is using [uv](https://docs.astral.sh/uv/):

```bash
uv tool install iscc-sum
```

**Note:** To install uv, run: `curl -LsSf https://astral.sh/uv/install.sh | sh` (or see
[other installation methods](https://docs.astral.sh/uv/getting-started/installation/))

Alternatively, install from PyPI:

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

### Command Line Interface

The `iscc-sum` command provides checksum generation and verification functionality similar to standard tools
like `md5sum` or `sha256sum`, but using ISCC (International Standard Content Code) checksums.

#### Basic Usage

```bash
# Generate checksum for a file
iscc-sum document.pdf
# Output: ISCC:KACYPXW445FTYNJ3CYSXHAFJMA2HUWULUNRFE3BLHRSCXYH2XHGQY *document.pdf

# Generate checksums for multiple files
iscc-sum *.txt

# Read from standard input
echo "Hello, World!" | iscc-sum
cat document.txt | iscc-sum
```

#### Checksum Verification

```bash
# Create a checksum file
iscc-sum *.txt > checksums.txt

# Verify checksums
iscc-sum -c checksums.txt
# Output:
# file1.txt: OK
# file2.txt: OK

# Verify with quiet mode (only show failures)
iscc-sum -c -q checksums.txt
```

#### Output Formats

```bash
# Default format (GNU style)
iscc-sum file.txt
# ISCC:KACYPXW445FTYNJ3CYSXHAFJMA2HUWULUNRFE3BLHRSCXYH2XHGQY *file.txt

# BSD-style format
iscc-sum --tag file.txt
# ISCC (file.txt) = ISCC:KACYPXW445FTYNJ3CYSXHAFJMA2HUWULUNRFE3BLHRSCXYH2XHGQY

# Narrow format (128-bit)
iscc-sum --narrow file.txt
# ISCC:KACYPXW445FTYNJ3CYSXHAFJMA2HU *file.txt

# Show component codes
iscc-sum --units file.txt
# ISCC:KACYPXW445FTYNJ3CYSXHAFJMA2HUWULUNRFE3BLHRSCXYH2XHGQY *file.txt
#   ISCC:EAAW4BQTJSTJSHAI27AJSAGMGHNUKSKRTK3E6OZ5CXUS57SWQZXJQ
#   ISCC:IABXF3ZHYL6O6PM5P2HGV677CS3RBHINZSXEJCITE3WNOTQ2CYXRA

# Process entire directory as single unit
iscc-sum --tree /path/to/project
# ISCC:KACYPXW445FTYNJ3CYSXHAFJMA2HUWULUNRFE3BLHRSCXYH2XHGQY */path/to/project/
```

#### Similarity Matching

Find files with similar content:

```bash
# Find similar files (default threshold: 12 bits)
iscc-sum --similar *.jpg
# Output:
# photo1.jpg
#   ~8  photo2.jpg
#   ~12 photo3.jpg

# Adjust similarity threshold
iscc-sum --similar --threshold 6 *.pdf
```

#### Complete Options

```bash
iscc-sum --help  # Show all available options

Options:
-c, --check      Read checksums from files and check them
--narrow         Generate shorter 128-bit checksums
--tag            Create a BSD-style checksum
--units          Show Data-Code and Instance-Code components
-z, --zero       End each output line with NUL
--similar        Find files with similar Data-Codes
--threshold      Hamming distance threshold for similarity (default: 12)
-t, --tree       Process directory as single unit with combined checksum
-q, --quiet      Don't print OK for each verified file
--status         Don't output anything, exit code shows success
-w, --warn       Warn about improperly formatted lines
--strict         Exit non-zero for improperly formatted lines
```

#### Examples

See the [examples](examples/) directory for practical scripts demonstrating:

- Backup verification workflows
- Duplicate file detection
- File integrity monitoring
- Download verification

#### Rust CLI Tool

A standalone Rust binary is also available:

```bash
# Install from crates.io
cargo install iscc-sum

# Run the Rust CLI
isum
```

### Python API

#### Quick Start

Generate ISCC-SUM codes for files:

```pycon
>>> from iscc_sum import code_iscc_sum
>>> 
>>> # Generate extended ISCC-SUM for a file
>>> result = code_iscc_sum("LICENSE", wide=True)
>>> result.iscc
'ISCC:K4AA2G6UMXGFJAO6ZOMIFZIYO6LYMOBT7Q6JDI3Z75IJWQY5WH372QA'
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
# Build Rust binary (creates isum executable)
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
