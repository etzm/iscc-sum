# Basic tests for iscc-sum

import iscc_sum


def test_import():
    # type: () -> None
    """Test that the module can be imported."""
    assert hasattr(iscc_sum, "hello_from_bin")
    assert hasattr(iscc_sum, "main")


def test_hello_message():
    # type: () -> None
    """Test the hello message from Rust."""
    result = iscc_sum.hello_from_bin()
    assert isinstance(result, str)
    assert result == "hello iscc-sum"
    assert "iscc-sum" in result.lower()


def test_main_function_exists():
    # type: () -> None
    """Test that main function is callable."""
    assert callable(iscc_sum.main)
