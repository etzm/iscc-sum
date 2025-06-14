"""Test Rust DataCodeProcessor against Python reference implementation."""

import io

import pytest

from iscc_sum._core import DataCodeProcessor
from iscc_sum.code_data_ref import DataHasher as RefDataHasher


def test_data_code_processor_simple():
    # type: () -> None
    """Test DataCodeProcessor with simple data."""
    # Test with Rust implementation
    processor = DataCodeProcessor()
    processor.update(b"Hello, World!")
    result = processor.result()
    rust_digest = result["digest"]

    # Test with Python reference implementation
    ref_hasher = RefDataHasher()
    ref_hasher.push(b"Hello, World!")
    ref_digest = ref_hasher.digest()

    assert rust_digest == ref_digest
    assert len(rust_digest) == 32  # 256 bits


def test_data_code_processor_incremental():
    # type: () -> None
    """Test DataCodeProcessor incremental updates."""
    # Test with Rust implementation
    processor = DataCodeProcessor()
    processor.update(b"Hello, ")
    processor.update(b"World!")
    result = processor.result()
    rust_digest = result["digest"]

    # Test with Python reference implementation
    ref_hasher = RefDataHasher()
    ref_hasher.push(b"Hello, ")
    ref_hasher.push(b"World!")
    ref_digest = ref_hasher.digest()

    assert rust_digest == ref_digest


def test_data_code_processor_empty():
    # type: () -> None
    """Test DataCodeProcessor with empty data."""
    # Test with Rust implementation
    processor = DataCodeProcessor()
    result = processor.result()
    rust_digest = result["digest"]

    # Test with Python reference implementation
    ref_hasher = RefDataHasher()
    ref_digest = ref_hasher.digest()

    assert rust_digest == ref_digest


def test_data_code_processor_large():
    # type: () -> None
    """Test DataCodeProcessor with large data."""
    # Create test data
    data = b"a" * 10000

    # Test with Rust implementation
    processor = DataCodeProcessor()
    processor.update(data)
    result = processor.result()
    rust_digest = result["digest"]

    # Test with Python reference implementation
    ref_hasher = RefDataHasher()
    ref_hasher.push(data)
    ref_digest = ref_hasher.digest()

    assert rust_digest == ref_digest


def test_data_code_processor_multiple_calls():
    # type: () -> None
    """Test DataCodeProcessor with multiple update calls."""
    # Test with Rust implementation
    processor = DataCodeProcessor()
    for i in range(100):
        processor.update(b"test data chunk ")
    result = processor.result()
    rust_digest = result["digest"]

    # Test with Python reference implementation
    ref_hasher = RefDataHasher()
    for i in range(100):
        ref_hasher.push(b"test data chunk ")
    ref_digest = ref_hasher.digest()

    assert rust_digest == ref_digest
