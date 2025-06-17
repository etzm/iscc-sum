# Test edge cases for full code coverage

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from iscc_sum.cli import cli


def test_expand_paths_special_file():
    # type: () -> None
    """Test handling of special files (devices, pipes) in _expand_paths."""
    runner = CliRunner()

    with runner.isolated_filesystem():
        # Create a mock that simulates a special file
        with (
            patch("pathlib.Path.exists") as mock_exists,
            patch("pathlib.Path.is_file") as mock_is_file,
            patch("pathlib.Path.is_dir") as mock_is_dir,
        ):
            mock_exists.return_value = True
            mock_is_file.return_value = False
            mock_is_dir.return_value = False

            result = runner.invoke(cli, ["special_file"])
            assert result.exit_code == 2
            assert "Not a regular file or directory" in result.output


def test_handle_tree_mode_unexpected_error():
    # type: () -> None
    """Test unexpected error handling in tree mode."""
    runner = CliRunner()

    with runner.isolated_filesystem():
        os.makedirs("test_dir")
        Path("test_dir/file.txt").write_text("content")

        # Mock IsccSumProcessor to raise an unexpected error
        with patch("iscc_sum.IsccSumProcessor") as mock_processor:
            mock_processor.side_effect = RuntimeError("Unexpected error in tree mode")

            result = runner.invoke(cli, ["--tree", "test_dir"])
            assert result.exit_code == 2
            assert "unexpected error: Unexpected error in tree mode" in result.output


def test_handle_checksum_generation_io_error():
    # type: () -> None
    """Test IO error handling in normal checksum generation."""
    runner = CliRunner()

    with runner.isolated_filesystem():
        # Create a file
        Path("test.txt").write_text("content")

        # Mock file open to raise IOError
        original_open = open

        def mock_open(path, mode="r", *args, **kwargs):
            if "test.txt" in str(path) and "rb" in str(mode):
                raise IOError("Permission denied")
            return original_open(path, mode, *args, **kwargs)

        with patch("builtins.open", mock_open):
            result = runner.invoke(cli, ["test.txt"])
            assert result.exit_code == 2
            assert "Permission denied" in result.output


def test_handle_similarity_io_error():
    # type: () -> None
    """Test IO error handling in similarity mode."""
    runner = CliRunner()

    with runner.isolated_filesystem():
        # Create files
        Path("file1.txt").write_text("content1")
        Path("file2.txt").write_text("content2")

        # Mock file open to raise IOError for the second file
        original_open = open

        def mock_open(path, mode="r", *args, **kwargs):
            if "file2.txt" in str(path) and "rb" in str(mode):
                raise IOError("File locked")
            return original_open(path, mode, *args, **kwargs)

        with patch("builtins.open", mock_open):
            result = runner.invoke(cli, ["--similar", "file1.txt", "file2.txt"])
            assert result.exit_code == 2
            assert "File locked" in result.output
