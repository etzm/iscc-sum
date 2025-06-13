# -*- coding: utf-8 -*-
import io
import json

import pytest

from iscc_sum.code_instance_ref import gen_instance_code


def load_test_vectors():
    # type: () -> list[tuple[str, list, dict]]
    """Load test vectors from JSON file."""
    with open("tests/test_vectors.json") as f:
        data = json.load(f)
    test_data = []
    for test_name, test_values in data["gen_instance_code"].items():
        # Convert hex stream to BytesIO
        inputs = test_values["inputs"]
        stream_hex = inputs[0].lstrip("stream:")
        inputs[0] = io.BytesIO(bytes.fromhex(stream_hex))
        test_data.append((test_name, inputs, test_values["outputs"]))
    return test_data


@pytest.mark.parametrize("test_name,inputs,expected", load_test_vectors())
def test_gen_instance_code(test_name, inputs, expected):
    """Test gen_instance_code against test vectors."""
    result = gen_instance_code(*inputs)
    assert result == expected, f"Failed test: {test_name}"


def main():
    test_vectors = load_test_vectors()
    print(f"Loaded {len(test_vectors)} test vectors")
    for test_name, inputs, expected in test_vectors:
        print(f"\nRunning {test_name}")
        result = gen_instance_code(*inputs)
        if result == expected:
            print("PASSED")
        else:
            print("FAILED")
            print(f"Expected: {expected}")
            print(f"Got:      {result}")


if __name__ == "__main__":
    main()
