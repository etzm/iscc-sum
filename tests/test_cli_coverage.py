# Tests to achieve 100% coverage for CLI module

from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from iscc_sum.cli import cli


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
