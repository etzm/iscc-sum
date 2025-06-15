# Tests to achieve 100% coverage for CLI module

from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from iscc_sum.cli import cli


def test_python2_stdin_handling():
    # type: () -> None
    """Test stdin handling for Python 2 compatibility."""
    runner = CliRunner()

    # Create a mock stdin object without buffer attribute (Python 2 style)
    mock_stdin_obj = Mock()
    mock_stdin_obj.read = Mock(side_effect=[b"Test data", b""])
    # Ensure no buffer attribute
    mock_stdin_obj.buffer = Mock(side_effect=AttributeError())

    # Patch sys module to return our mock stdin
    with patch("iscc_sum.cli.sys") as mock_sys:
        mock_sys.stdin = mock_stdin_obj
        mock_sys.exit = Mock(side_effect=SystemExit)

        # Also need to patch hasattr to return False for buffer
        with patch("iscc_sum.cli.hasattr", side_effect=lambda obj, attr: attr != "buffer"):
            result = runner.invoke(cli, ["-"])
            assert result.exit_code == 0
            assert "ISCC:" in result.output


def test_unexpected_exception_during_processing():
    # type: () -> None
    """Test handling of unexpected exceptions during file processing."""
    runner = CliRunner()

    # Mock IsccSumProcessor to raise an unexpected exception
    with patch("iscc_sum.IsccSumProcessor") as mock_processor_class:
        mock_instance = Mock()
        mock_instance.update.side_effect = RuntimeError("Unexpected error")
        mock_processor_class.return_value = mock_instance

        with runner.isolated_filesystem():
            with open("test.txt", "wb") as f:
                f.write(b"Test content")

            result = runner.invoke(cli, ["test.txt"])
            assert result.exit_code == 2
            assert "iscc-sum: test.txt: unexpected error: Unexpected error" in result.output
