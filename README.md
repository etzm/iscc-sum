# iscc-sum

[![CI](https://github.com/iscc/iscc-sum/actions/workflows/ci.yml/badge.svg)](https://github.com/iscc/iscc-sum/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/iscc-sum.svg)](https://pypi.org/project/iscc-sum/)
[![Crates.io](https://img.shields.io/crates/v/iscc_sum.svg)](https://crates.io/crates/iscc_sum)

High-performance ISCC Data-Code and Instance-Code hashing tool, implemented in Rust with Python bindings.

## Installation

### Python Package

Install from PyPI:

```bash
pip install iscc-sum
```

### Rust CLI Tool

Install from crates.io:

```bash
cargo install iscc_sum
```

Or download pre-built binaries from the [releases page](https://github.com/iscc/iscc-sum/releases).

## Usage

### Command Line

```bash
# Using the installed command
iscc-sum

# Using Python module
python -m iscc_sum
```

### Python API

```python
from iscc_sum import hello_from_bin

print(hello_from_bin())  # prints: hello iscc-sum
```

## Development

### Prerequisites

- Rust (latest stable)
- Python 3.10+
- UV (for Python dependency management)
- Maturin (for building Python wheels)

### Setup

```bash
# Clone the repository
git clone https://github.com/iscc/iscc-sum.git
cd iscc-sum

# Install all dependencies including dev dependencies
uv sync --all-extras

# Build Rust extension for Python
uv run maturin develop

# Run tests
cargo test        # Rust tests
uv run pytest     # Python tests
```

### Building

```bash
# Build Rust binary
cargo build --release

# Build Python wheels
maturin build --release
```

## License

This project is licensed under either of

- Apache License, Version 2.0 ([LICENSE-APACHE](LICENSE-APACHE) or http://www.apache.org/licenses/LICENSE-2.0)
- MIT license ([LICENSE-MIT](LICENSE-MIT) or http://opensource.org/licenses/MIT)

at your option.
