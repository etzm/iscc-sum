# Unit tests for iscc-sum CLI

import pytest
from click.testing import CliRunner

from iscc_sum.cli import cli, get_version


def test_version():
    # type: () -> None
    """Test that version command works."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "iscc-sum" in result.output
    assert get_version() in result.output


def test_help():
    # type: () -> None
    """Test that help command works and contains expected content."""
    runner = CliRunner()

    # Test with --help
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Compute ISCC" in result.output
    assert "Exit status:" in result.output

    # Test with -h
    result = runner.invoke(cli, ["-h"])
    assert result.exit_code == 0
    assert "Compute ISCC" in result.output


def test_no_arguments():
    # type: () -> None
    """Test behavior when no arguments are provided (should read from stdin)."""
    runner = CliRunner()
    result = runner.invoke(cli, [])
    assert result.exit_code == 2
    assert "reading from stdin not yet implemented" in result.output


def test_single_file_argument():
    # type: () -> None
    """Test processing a single file."""
    runner = CliRunner()
    result = runner.invoke(cli, ["test.txt"])
    assert result.exit_code == 0
    assert "Processing: test.txt" in result.output


def test_multiple_file_arguments():
    # type: () -> None
    """Test processing multiple files."""
    runner = CliRunner()
    result = runner.invoke(cli, ["file1.txt", "file2.txt", "file3.txt"])
    assert result.exit_code == 0
    assert "Processing: file1.txt" in result.output
    assert "Processing: file2.txt" in result.output
    assert "Processing: file3.txt" in result.output


def test_check_mode():
    # type: () -> None
    """Test verification mode with -c/--check."""
    runner = CliRunner()

    # Test with -c
    result = runner.invoke(cli, ["-c", "checksums.txt"])
    assert result.exit_code == 2
    assert "verification mode not yet implemented" in result.output

    # Test with --check
    result = runner.invoke(cli, ["--check", "checksums.txt"])
    assert result.exit_code == 2
    assert "verification mode not yet implemented" in result.output


def test_tag_option():
    # type: () -> None
    """Test BSD-style output with --tag."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--tag", "test.txt"])
    assert result.exit_code == 0
    # For now just checking it doesn't error


def test_zero_option():
    # type: () -> None
    """Test NUL-terminated output with -z/--zero."""
    runner = CliRunner()

    # Test with -z
    result = runner.invoke(cli, ["-z", "test.txt"])
    assert result.exit_code == 0

    # Test with --zero
    result = runner.invoke(cli, ["--zero", "test.txt"])
    assert result.exit_code == 0


def test_narrow_option():
    # type: () -> None
    """Test narrow format with --narrow."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--narrow", "test.txt"])
    assert result.exit_code == 0


def test_units_option():
    # type: () -> None
    """Test component units output with --units."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--units", "test.txt"])
    assert result.exit_code == 0


def test_similar_option():
    # type: () -> None
    """Test similarity matching with --similar."""
    runner = CliRunner()

    # Test with less than 2 files
    result = runner.invoke(cli, ["--similar", "test.txt"])
    assert result.exit_code == 2
    assert "--similar requires at least 2 files" in result.output

    # Test with 2 files
    result = runner.invoke(cli, ["--similar", "file1.txt", "file2.txt"])
    assert result.exit_code == 2
    assert "similarity mode not yet implemented" in result.output


def test_similar_with_threshold():
    # type: () -> None
    """Test similarity matching with custom threshold."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--similar", "--threshold", "20", "file1.txt", "file2.txt"])
    assert result.exit_code == 2
    assert "similarity mode not yet implemented" in result.output


def test_conflicting_options():
    # type: () -> None
    """Test that conflicting options are rejected."""
    runner = CliRunner()

    # Test --similar with --check
    result = runner.invoke(cli, ["--similar", "--check", "file1.txt", "file2.txt"])
    assert result.exit_code == 2
    assert "--similar cannot be used with -c/--check" in result.output


def test_verification_options():
    # type: () -> None
    """Test verification-specific options."""
    runner = CliRunner()

    # Test --quiet
    result = runner.invoke(cli, ["-c", "--quiet", "checksums.txt"])
    assert result.exit_code == 2

    # Test --status
    result = runner.invoke(cli, ["-c", "--status", "checksums.txt"])
    assert result.exit_code == 2

    # Test --warn
    result = runner.invoke(cli, ["-c", "--warn", "checksums.txt"])
    assert result.exit_code == 2

    # Test --strict
    result = runner.invoke(cli, ["-c", "--strict", "checksums.txt"])
    assert result.exit_code == 2


def test_stdin_placeholder():
    # type: () -> None
    """Test that stdin placeholder '-' is recognized."""
    runner = CliRunner()
    result = runner.invoke(cli, ["-"])
    assert result.exit_code == 2
    assert "reading from stdin not yet implemented" in result.output


def test_get_version_with_missing_package():
    # type: () -> None
    """Test get_version when package metadata is not available."""
    import sys
    from importlib.metadata import PackageNotFoundError
    from unittest.mock import patch

    # Mock the version function to raise PackageNotFoundError
    with patch("iscc_sum.cli.version") as mock_version:
        mock_version.side_effect = PackageNotFoundError("iscc-sum")
        version = get_version()
        assert version == "0.1.0-alpha.1"


def test_exception_handling():
    # type: () -> None
    """Test generic exception handling in CLI."""
    from unittest.mock import patch

    runner = CliRunner()

    # Mock _handle_checksum_generation to raise an exception
    with patch("iscc_sum.cli._handle_checksum_generation") as mock_handler:
        mock_handler.side_effect = Exception("Test error message")
        result = runner.invoke(cli, ["test.txt"])
        assert result.exit_code == 2
        assert "iscc-sum: Test error message" in result.output


def test_main_entry_point():
    # type: () -> None
    """Test the __main__ entry point."""
    import subprocess
    import sys

    # Run the module as a script
    result = subprocess.run([sys.executable, "-m", "iscc_sum.cli", "--version"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "iscc-sum" in result.stdout
