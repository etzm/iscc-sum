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
    test_input = b"Test data from stdin\n"
    result = runner.invoke(cli, [], input=test_input)
    assert result.exit_code == 0
    assert "ISCC:" in result.output
    assert " *-" in result.output  # stdin is shown as "-"


def test_single_file_argument():
    # type: () -> None
    """Test processing a single file."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create a test file
        with open("test.txt", "wb") as f:
            f.write(b"Test content\n")

        result = runner.invoke(cli, ["test.txt"])
        assert result.exit_code == 0
        assert "ISCC:" in result.output
        assert " *test.txt" in result.output


def test_multiple_file_arguments():
    # type: () -> None
    """Test processing multiple files."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create test files
        for i in range(1, 4):
            with open(f"file{i}.txt", "wb") as f:
                f.write(f"Content of file {i}\n".encode())

        result = runner.invoke(cli, ["file1.txt", "file2.txt", "file3.txt"])
        assert result.exit_code == 0
        assert " *file1.txt" in result.output
        assert " *file2.txt" in result.output
        assert " *file3.txt" in result.output
        # Check we have 3 ISCC codes
        assert result.output.count("ISCC:") == 3


def test_check_mode():
    # type: () -> None
    """Test verification mode with -c/--check."""
    runner = CliRunner()

    # Test with -c (file not found)
    result = runner.invoke(cli, ["-c", "checksums.txt"])
    assert result.exit_code == 2
    assert "No such file or directory" in result.output

    # Test with --check (file not found)
    result = runner.invoke(cli, ["--check", "checksums.txt"])
    assert result.exit_code == 2
    assert "No such file or directory" in result.output


def test_tag_option():
    # type: () -> None
    """Test BSD-style output with --tag."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("test.txt", "wb") as f:
            f.write(b"Test content\n")

        result = runner.invoke(cli, ["--tag", "test.txt"])
        assert result.exit_code == 0
        assert "ISCC-SUM (test.txt) = ISCC:" in result.output
        assert " *test.txt" not in result.output  # Should not have default format


def test_zero_option():
    # type: () -> None
    """Test NUL-terminated output with -z/--zero."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("test.txt", "wb") as f:
            f.write(b"Test content\n")

        # Test with -z
        result = runner.invoke(cli, ["-z", "test.txt"])
        assert result.exit_code == 0
        assert "\0" in result.output
        assert "\n" not in result.output

        # Test with --zero
        result = runner.invoke(cli, ["--zero", "test.txt"])
        assert result.exit_code == 0
        assert "\0" in result.output


def test_narrow_option():
    # type: () -> None
    """Test narrow format with --narrow."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("test.txt", "wb") as f:
            f.write(b"Test content\n")

        # Get normal (wide) output
        result_wide = runner.invoke(cli, ["test.txt"])
        assert result_wide.exit_code == 0
        wide_iscc = result_wide.output.split()[0]

        # Get narrow output
        result_narrow = runner.invoke(cli, ["--narrow", "test.txt"])
        assert result_narrow.exit_code == 0
        narrow_iscc = result_narrow.output.split()[0]

        # Narrow should be shorter than wide
        # Wide is ~54 chars (256-bit), narrow is ~29 chars (128-bit)
        assert len(narrow_iscc) < len(wide_iscc)
        assert len(narrow_iscc) < 35  # Should be around 29 chars
        assert len(wide_iscc) > 45  # Should be around 54 chars


def test_units_option():
    # type: () -> None
    """Test component units output with --units."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("test.txt", "wb") as f:
            f.write(b"Test content\n")

        result = runner.invoke(cli, ["--units", "test.txt"])
        assert result.exit_code == 0
        lines = result.output.strip().split("\n")
        assert len(lines) == 3  # Main ISCC + 2 units
        assert "ISCC:" in lines[0]  # Main composite code
        assert "  ISCC:" in lines[1]  # Data-Code (indented)
        assert "  ISCC:" in lines[2]  # Instance-Code (indented)


def test_similar_option():
    # type: () -> None
    """Test similarity matching with --similar."""
    runner = CliRunner()

    # Test with less than 2 files
    result = runner.invoke(cli, ["--similar", "test.txt"])
    assert result.exit_code == 2
    assert "--similar requires at least 2 files" in result.output

    # Test with 2 non-existent files
    result = runner.invoke(cli, ["--similar", "file1.txt", "file2.txt"])
    assert result.exit_code == 2
    assert "No such file or directory" in result.output


def test_similar_with_threshold():
    # type: () -> None
    """Test similarity matching with custom threshold."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--similar", "--threshold", "20", "file1.txt", "file2.txt"])
    assert result.exit_code == 2
    assert "No such file or directory" in result.output


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
    test_input = b"Data from stdin\n"
    result = runner.invoke(cli, ["-"], input=test_input)
    assert result.exit_code == 0
    assert "ISCC:" in result.output
    assert " *-" in result.output


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


def test_file_access_error():
    # type: () -> None
    """Test handling of file access errors."""
    runner = CliRunner()

    # Test with non-existent file
    result = runner.invoke(cli, ["non_existent_file.txt"])
    assert result.exit_code == 2
    assert "iscc-sum: non_existent_file.txt:" in result.output
    assert "No such file or directory" in result.output or "cannot find the file" in result.output


def test_unexpected_error_during_processing():
    # type: () -> None
    """Test handling of unexpected errors during file processing."""
    from unittest.mock import mock_open, patch

    runner = CliRunner()

    # Create a mock that raises an unexpected exception
    with patch("builtins.open", mock_open()) as mock_file:
        mock_file.return_value.read.side_effect = RuntimeError("Unexpected error")
        result = runner.invoke(cli, ["test.txt"])
        assert result.exit_code == 2
        assert "iscc-sum: test.txt: unexpected error: Unexpected error" in result.output
