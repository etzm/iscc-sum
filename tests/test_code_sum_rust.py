# Test the Rust implementation of ISCC-SUM against the reference implementation

import os
import tempfile

import pytest

from iscc_sum._core import IsccSumProcessor, code_iscc_sum
from iscc_sum.code_iscc_sum_ref import code_iscc_sum as code_iscc_sum_ref


def test_iscc_sum_processor_basic():
    # type: () -> None
    """Test basic functionality of IsccSumProcessor."""
    processor = IsccSumProcessor()
    processor.update(b"Hello, World!")
    result = processor.result(wide=False, add_units=True)

    assert "iscc" in result
    assert result["iscc"].startswith("ISCC:")
    assert "datahash" in result
    assert "filesize" in result
    assert result["filesize"] == 13
    assert "units" in result
    assert len(result["units"]) == 2


def test_code_iscc_sum_function():
    # type: () -> None
    """Test the code_iscc_sum function."""
    with tempfile.NamedTemporaryFile(mode="wb", delete=False) as f:
        f.write(b"Test file content")
        temp_path = f.name

    try:
        result = code_iscc_sum(temp_path, wide=False, add_units=True)
        assert "iscc" in result
        assert result["iscc"].startswith("ISCC:")
        assert result["filesize"] == 17
    finally:
        os.unlink(temp_path)


def test_rust_vs_reference_implementation():
    # type: () -> None
    """Compare Rust implementation with Python reference implementation."""
    test_cases = [
        b"Hello, World!",
        b"The quick brown fox jumps over the lazy dog",
        b"a" * 1000,  # Repetitive content
        b"".join([bytes([i % 256]) for i in range(10000)]),  # Varied content
    ]

    for test_data in test_cases:
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode="wb", delete=False) as f:
            f.write(test_data)
            temp_path = f.name

        try:
            # Get results from both implementations
            rust_result = code_iscc_sum(temp_path, wide=False, add_units=True)
            ref_result = code_iscc_sum_ref(temp_path, wide=False, add_units=True)

            # Compare results
            assert rust_result["iscc"] == ref_result["iscc"], f"ISCC mismatch for data length {len(test_data)}"
            assert rust_result["datahash"] == ref_result["datahash"], (
                f"Datahash mismatch for data length {len(test_data)}"
            )
            assert rust_result["filesize"] == ref_result["filesize"], (
                f"Filesize mismatch for data length {len(test_data)}"
            )
            assert rust_result["units"] == ref_result["units"], (
                f"Units mismatch for data length {len(test_data)}"
            )

        finally:
            os.unlink(temp_path)


def test_rust_vs_reference_wide():
    # type: () -> None
    """Compare Rust implementation with Python reference for wide codes."""
    test_data = b"Test data for wide ISCC-SUM comparison"

    with tempfile.NamedTemporaryFile(mode="wb", delete=False) as f:
        f.write(test_data)
        temp_path = f.name

    try:
        # Get results from both implementations (wide=True)
        rust_result = code_iscc_sum(temp_path, wide=True, add_units=True)
        ref_result = code_iscc_sum_ref(temp_path, wide=True, add_units=True)

        # Compare results
        assert rust_result["iscc"] == ref_result["iscc"]
        assert rust_result["datahash"] == ref_result["datahash"]
        assert rust_result["filesize"] == ref_result["filesize"]
        assert rust_result["units"] == ref_result["units"]

    finally:
        os.unlink(temp_path)


def test_incremental_processing():
    # type: () -> None
    """Test that incremental processing produces same results as single-pass."""
    test_data = b"This is a longer test string that will be processed in chunks"

    # Single update
    processor1 = IsccSumProcessor()
    processor1.update(test_data)
    result1 = processor1.result(wide=False, add_units=False)

    # Multiple updates
    processor2 = IsccSumProcessor()
    chunk_size = 10
    for i in range(0, len(test_data), chunk_size):
        processor2.update(test_data[i : i + chunk_size])
    result2 = processor2.result(wide=False, add_units=False)

    assert result1["iscc"] == result2["iscc"]
    assert result1["datahash"] == result2["datahash"]
    assert result1["filesize"] == result2["filesize"]
