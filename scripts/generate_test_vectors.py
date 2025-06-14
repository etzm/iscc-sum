#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Generate test vectors for code_iscc_sum."""

import json
import tempfile

from iscc_sum.code_iscc_sum_ref import code_iscc_sum

# Test cases with different data patterns
test_cases = [
    # Empty file
    ("test_0000_empty_64", b"", False, True),
    ("test_0001_empty_128", b"", True, True),
    # Small files
    ("test_0002_hello_64", b"Hello, ISCC!", False, True),
    ("test_0003_hello_128", b"Hello, ISCC!", True, True),
    # Single byte
    ("test_0004_single_byte_64", b"\x00", False, True),
    ("test_0005_single_byte_128", b"\xff", True, True),
    # Binary pattern
    ("test_0006_binary_64", b"\xff\x00\xff\x00", False, True),
    ("test_0007_binary_128", b"\xff\x00\xff\x00", True, True),
    # Without units
    ("test_0008_no_units_64", b"Test without units", False, False),
    ("test_0009_no_units_128", b"Test without units", True, False),
    # Larger file (1KB of pattern)
    ("test_0010_pattern_64", b"ISCC" * 256, False, True),
    ("test_0011_pattern_128", b"ISCC" * 256, True, True),
]

test_vectors = {}

for test_name, data, wide, add_units in test_cases:
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode="wb", delete=False) as f:
        f.write(data)
        f.flush()

        # Generate ISCC
        result = code_iscc_sum(f.name, wide=wide, add_units=add_units)

        # Format for test vector
        inputs = [f"stream:{data.hex()}", wide, add_units]

        test_vectors[test_name] = {"inputs": inputs, "outputs": result}

# Pretty print the test vectors
print(json.dumps({"code_iscc_sum": test_vectors}, indent=2, sort_keys=True))
