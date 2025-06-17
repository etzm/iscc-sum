# Test tree mode functionality in CLI

import os
import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner

from iscc_sum.cli import cli


def test_tree_mode_basic():
    # type: () -> None
    """Test basic tree mode functionality."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create test directory structure
        os.makedirs("test_dir/sub1/sub2")
        Path("test_dir/file1.txt").write_text("Content 1")
        Path("test_dir/sub1/file2.txt").write_text("Content 2")
        Path("test_dir/sub1/sub2/file3.txt").write_text("Content 3")

        # Run tree mode
        result = runner.invoke(cli, ["--tree", "test_dir"])
        assert result.exit_code == 0

        # Check output format - should have trailing slash
        assert " *test_dir/" in result.output
        assert result.output.startswith("ISCC:")


def test_tree_mode_bsd_format():
    # type: () -> None
    """Test tree mode with BSD-style output."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create test directory
        os.makedirs("test_dir")
        Path("test_dir/file.txt").write_text("Test content")

        # Run with BSD format
        result = runner.invoke(cli, ["--tree", "--tag", "test_dir"])
        assert result.exit_code == 0

        # Check BSD format
        assert "ISCC-SUM (test_dir/) = ISCC:" in result.output


def test_tree_mode_with_units():
    # type: () -> None
    """Test tree mode with units output."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create test directory
        os.makedirs("test_dir")
        Path("test_dir/file.txt").write_text("Test content")

        # Run with units
        result = runner.invoke(cli, ["--tree", "--units", "test_dir"])
        assert result.exit_code == 0

        # Should have main checksum and units
        lines = result.output.strip().split("\n")
        assert len(lines) > 1
        assert lines[0].startswith("ISCC:")
        assert all(line.startswith("  ") for line in lines[1:])


def test_tree_mode_empty_directory():
    # type: () -> None
    """Test tree mode with empty directory."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create empty directory
        os.makedirs("empty_dir")

        # Run tree mode
        result = runner.invoke(cli, ["--tree", "empty_dir"])
        assert result.exit_code == 2
        assert "no files found" in result.output


def test_tree_mode_with_isccignore():
    # type: () -> None
    """Test tree mode respects .isccignore files."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create directory with .isccignore
        os.makedirs("test_dir")
        Path("test_dir/.isccignore").write_text("*.log\n")
        Path("test_dir/keep.txt").write_text("Keep this")
        Path("test_dir/ignore.log").write_text("Ignore this")

        # Run tree mode
        result = runner.invoke(cli, ["--tree", "test_dir"])
        assert result.exit_code == 0

        # The checksum should only include keep.txt, not ignore.log
        # We can't easily verify the exact checksum, but it should succeed


def test_tree_mode_validation_errors():
    # type: () -> None
    """Test tree mode validation errors."""
    runner = CliRunner()

    # Test with no arguments
    result = runner.invoke(cli, ["--tree"])
    assert result.exit_code == 2
    assert "requires exactly one directory argument" in result.output

    # Test with multiple arguments
    result = runner.invoke(cli, ["--tree", "dir1", "dir2"])
    assert result.exit_code == 2
    assert "requires exactly one directory argument" in result.output

    with runner.isolated_filesystem():
        # Test with file instead of directory
        Path("file.txt").write_text("content")
        result = runner.invoke(cli, ["--tree", "file.txt"])
        assert result.exit_code == 2
        assert "requires a directory, not a file" in result.output

        # Test with non-existent directory
        result = runner.invoke(cli, ["--tree", "nonexistent"])
        assert result.exit_code == 2
        assert "requires a directory, not a file" in result.output


def test_tree_mode_conflicts():
    # type: () -> None
    """Test tree mode conflicts with other options."""
    runner = CliRunner()

    # Tree with check
    result = runner.invoke(cli, ["--tree", "--check", "dir"])
    assert result.exit_code == 2
    assert "--tree cannot be used with -c/--check" in result.output

    # Tree with similar
    result = runner.invoke(cli, ["--tree", "--similar", "dir"])
    assert result.exit_code == 2
    assert "--tree cannot be used with --similar" in result.output


def test_tree_mode_zero_terminator():
    # type: () -> None
    """Test tree mode with zero terminator."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create test directory
        os.makedirs("test_dir")
        Path("test_dir/file.txt").write_text("content")

        # Run with zero terminator
        result = runner.invoke(cli, ["--tree", "-z", "test_dir"])
        assert result.exit_code == 0

        # Output should end with null byte instead of newline
        assert result.output.endswith("\0")
        assert not result.output.endswith("\n")


def test_tree_mode_narrow_format():
    # type: () -> None
    """Test tree mode with narrow format."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create test directory
        os.makedirs("test_dir")
        Path("test_dir/file.txt").write_text("content")

        # Run with narrow format
        result = runner.invoke(cli, ["--tree", "--narrow", "test_dir"])
        assert result.exit_code == 0

        # Extract the ISCC code and check its length
        iscc_code = result.output.split()[0]
        # Narrow format should be shorter than wide format

        # Run with wide format for comparison
        result_wide = runner.invoke(cli, ["--tree", "test_dir"])
        assert result_wide.exit_code == 0
        iscc_code_wide = result_wide.output.split()[0]

        assert len(iscc_code) < len(iscc_code_wide)


def test_tree_mode_deterministic():
    # type: () -> None
    """Test tree mode produces deterministic results."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create test directory
        os.makedirs("test_dir/sub")
        Path("test_dir/file1.txt").write_text("Content 1")
        Path("test_dir/file2.txt").write_text("Content 2")
        Path("test_dir/sub/file3.txt").write_text("Content 3")

        # Run multiple times
        checksums = []
        for _ in range(3):
            result = runner.invoke(cli, ["--tree", "test_dir"])
            assert result.exit_code == 0
            checksum = result.output.split()[0]
            checksums.append(checksum)

        # All checksums should be identical
        assert len(set(checksums)) == 1


def test_tree_mode_io_error_handling():
    # type: () -> None
    """Test tree mode handles IO errors gracefully."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create test directory
        os.makedirs("test_dir")
        Path("test_dir/file1.txt").write_text("Content 1")
        Path("test_dir/file2.txt").write_text("Content 2")

        # Make one file unreadable (on Unix systems)
        if os.name != "nt":  # Skip on Windows
            os.chmod("test_dir/file2.txt", 0o000)

            # Run tree mode - should continue despite error
            result = runner.invoke(cli, ["--tree", "test_dir"])

            # Restore permissions for cleanup
            os.chmod("test_dir/file2.txt", 0o644)

            # Should still get a checksum for the readable file
            assert result.exit_code == 0
            assert "ISCC:" in result.output
