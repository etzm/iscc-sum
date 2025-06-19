# -*- coding: utf-8 -*-
"""Tests for ISCC-CODE SUM reference implementation."""

import io
import json
import tempfile

import pytest

from iscc_sum.code_iscc_sum_ref import code_iscc_sum, encode_base32


def load_test_vectors():
    # type: () -> list[tuple[str, list, dict]]
    """Load test vectors from JSON file."""
    with open("tests/test_vectors.json") as f:
        data = json.load(f)
    test_data = []
    for test_name, test_values in data["code_iscc_sum"].items():
        # Convert hex stream to file
        inputs = test_values["inputs"].copy()
        stream_hex = inputs[0].lstrip("stream:")

        # Create a temporary file with the test data
        with tempfile.NamedTemporaryFile(mode="wb", delete=False) as temp_file:
            if stream_hex:
                temp_file.write(bytes.fromhex(stream_hex))
            temp_file.flush()
            inputs[0] = temp_file.name

        test_data.append((test_name, inputs, test_values["outputs"]))
    return test_data


@pytest.mark.parametrize("test_name,inputs,expected", load_test_vectors())
def test_code_iscc_sum_vectors(test_name, inputs, expected):
    """Test code_iscc_sum against test vectors."""
    result = code_iscc_sum(*inputs)

    # Compare all fields that are present in expected
    for key in expected:
        assert key in result, f"Missing key '{key}' in result for test: {test_name}"
        assert result[key] == expected[key], f"Mismatch in '{key}' for test: {test_name}"


def test_code_iscc_sum_basic():
    """Test basic code_iscc_sum functionality with small file."""
    # Create a temporary file with test content
    with tempfile.NamedTemporaryFile(mode="wb", delete=False) as f:
        test_data = b"Hello, ISCC-SUM!"
        f.write(test_data)
        f.flush()

        # Test basic functionality
        result = code_iscc_sum(f.name)

        # Verify result structure
        assert "iscc" in result
        assert "datahash" in result
        assert "filesize" in result
        assert "units" in result

        # Verify ISCC format
        assert result["iscc"].startswith("ISCC:")
        assert len(result["iscc"]) > 5

        # Verify filesize
        assert result["filesize"] == len(test_data)

        # Verify units are included
        assert len(result["units"]) == 2
        assert all(unit.startswith("ISCC:") for unit in result["units"])


def test_code_iscc_sum_wide():
    """Test code_iscc_sum with wide=True parameter."""
    with tempfile.NamedTemporaryFile(mode="wb", delete=False) as f:
        test_data = b"Test data for wide ISCC"
        f.write(test_data)
        f.flush()

        # Test with wide=False (default)
        result_narrow = code_iscc_sum(f.name, wide=False)

        # Test with wide=True
        result_wide = code_iscc_sum(f.name, wide=True)

        # Wide ISCC should be longer than narrow
        assert len(result_wide["iscc"]) > len(result_narrow["iscc"])

        # Both should have same filesize and datahash
        assert result_wide["filesize"] == result_narrow["filesize"]
        assert result_wide["datahash"] == result_narrow["datahash"]


def test_code_iscc_sum_no_units():
    """Test code_iscc_sum with add_units=False parameter."""
    with tempfile.NamedTemporaryFile(mode="wb", delete=False) as f:
        test_data = b"Test without units"
        f.write(test_data)
        f.flush()

        # Test with add_units=False
        result = code_iscc_sum(f.name, add_units=False)

        # Verify result structure
        assert "iscc" in result
        assert "datahash" in result
        assert "filesize" in result
        assert "units" not in result  # Units should not be included


def test_code_iscc_sum_empty_file():
    """Test code_iscc_sum with empty file."""
    with tempfile.NamedTemporaryFile(mode="wb", delete=False) as f:
        # Empty file
        f.flush()

        result = code_iscc_sum(f.name)

        # Should still produce valid result
        assert result["iscc"].startswith("ISCC:")
        assert result["filesize"] == 0
        assert len(result["units"]) == 2


def test_code_iscc_sum_large_file():
    """Test code_iscc_sum with file larger than IO_READ_SIZE."""
    with tempfile.NamedTemporaryFile(mode="wb", delete=False) as f:
        # Write data larger than IO_READ_SIZE (2MB)
        chunk_size = 1024 * 1024  # 1MB
        test_data = b"x" * chunk_size

        # Write 3MB of data
        for _ in range(3):
            f.write(test_data)
        f.flush()

        result = code_iscc_sum(f.name)

        # Verify result
        assert result["iscc"].startswith("ISCC:")
        assert result["filesize"] == 3 * chunk_size
        assert len(result["units"]) == 2


def test_code_iscc_sum_with_fsspec_url():
    """Test code_iscc_sum with fsspec URL path."""
    # Create a temporary file
    with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".txt") as f:
        test_data = b"Testing fsspec URL support"
        f.write(test_data)
        f.flush()

        # Use file:// URL
        file_url = f"file://{f.name}"
        result = code_iscc_sum(file_url)

        # Verify result
        assert result["iscc"].startswith("ISCC:")
        assert result["filesize"] == len(test_data)


def test_encode_base32_basic():
    """Test encode_base32 function with basic input."""
    # Test with simple bytes
    data = b"Hello"
    encoded = encode_base32(data)

    # Should be uppercase base32 without padding
    assert encoded == "JBSWY3DP"
    assert "=" not in encoded


def test_encode_base32_empty():
    """Test encode_base32 with empty input."""
    encoded = encode_base32(b"")
    assert encoded == ""


def test_encode_base32_padding_removal():
    """Test encode_base32 removes padding correctly."""
    # Test data that would normally have padding
    data = b"H"  # Single byte would normally encode to "JA======"
    encoded = encode_base32(data)
    assert encoded == "JA"
    assert "=" not in encoded

    # Test with data that needs different amounts of padding
    test_cases = [
        (b"He", "JBSQ"),
        (b"Hel", "JBSWY"),
        (b"Hell", "JBSWY3A"),
    ]

    for data, expected in test_cases:
        encoded = encode_base32(data)
        assert encoded == expected
        assert "=" not in encoded


def test_code_iscc_sum_combinations():
    """Test various parameter combinations for code_iscc_sum."""
    with tempfile.NamedTemporaryFile(mode="wb", delete=False) as f:
        test_data = b"Testing all parameter combinations"
        f.write(test_data)
        f.flush()

        # Test all combinations of wide and add_units
        combinations = [
            (False, True),
            (False, False),
            (True, True),
            (True, False),
        ]

        results = []
        for wide, add_units in combinations:
            result = code_iscc_sum(f.name, wide=wide, add_units=add_units)
            results.append(result)

            # Basic assertions for each combination
            assert result["iscc"].startswith("ISCC:")
            assert result["filesize"] == len(test_data)
            assert ("units" in result) == add_units

        # Wide results should have longer ISCC codes
        assert len(results[2]["iscc"]) > len(results[0]["iscc"])  # wide=True vs wide=False
        assert len(results[3]["iscc"]) > len(results[1]["iscc"])  # wide=True vs wide=False


def test_code_iscc_sum_exact_io_read_size():
    """Test code_iscc_sum with file exactly matching IO_READ_SIZE."""
    with tempfile.NamedTemporaryFile(mode="wb", delete=False) as f:
        # Write exactly IO_READ_SIZE bytes (2MB)
        test_data = b"x" * 2097152
        f.write(test_data)
        f.flush()

        result = code_iscc_sum(f.name)

        # Verify result
        assert result["iscc"].startswith("ISCC:")
        assert result["filesize"] == 2097152
        assert len(result["units"]) == 2


def test_code_iscc_sum_binary_content():
    """Test code_iscc_sum with binary content including null bytes."""
    with tempfile.NamedTemporaryFile(mode="wb", delete=False) as f:
        # Write binary data including null bytes and all byte values
        test_data = bytes(range(256)) * 100  # All possible byte values
        f.write(test_data)
        f.flush()

        result = code_iscc_sum(f.name)

        # Verify result
        assert result["iscc"].startswith("ISCC:")
        assert result["filesize"] == len(test_data)
        assert len(result["units"]) == 2
