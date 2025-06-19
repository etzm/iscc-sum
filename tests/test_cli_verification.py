# Tests for checksum verification functionality

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from iscc_sum.cli import cli


def test_verification_no_files():
    # type: () -> None
    """Test verification mode with no checksum files specified."""
    runner = CliRunner()
    result = runner.invoke(cli, ["-c"])
    assert result.exit_code == 2
    assert "no checksum file specified" in result.output


def test_verification_file_not_found():
    # type: () -> None
    """Test verification with non-existent checksum file."""
    runner = CliRunner()
    result = runner.invoke(cli, ["-c", "nonexistent_checksums.txt"])
    assert result.exit_code == 2
    assert "nonexistent_checksums.txt" in result.output


def test_verification_success():
    # type: () -> None
    """Test successful verification of checksums."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create test files
        with open("file1.txt", "wb") as f:
            f.write(b"Content of file 1")
        with open("file2.txt", "wb") as f:
            f.write(b"Content of file 2")

        # Generate checksums
        result = runner.invoke(cli, ["file1.txt", "file2.txt"])
        assert result.exit_code == 0

        # Save checksums to file
        with open("checksums.txt", "w") as f:
            f.write(result.output)

        # Verify checksums
        result = runner.invoke(cli, ["-c", "checksums.txt"])
        assert result.exit_code == 0
        assert "file1.txt: OK" in result.output
        assert "file2.txt: OK" in result.output


def test_verification_failure():
    # type: () -> None
    """Test verification failure when content changed."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create original file
        with open("file.txt", "wb") as f:
            f.write(b"Original content")

        # Generate checksum
        result = runner.invoke(cli, ["file.txt"])
        assert result.exit_code == 0

        # Save checksum
        with open("checksums.txt", "w") as f:
            f.write(result.output)

        # Modify file
        with open("file.txt", "wb") as f:
            f.write(b"Modified content")

        # Verify should fail
        result = runner.invoke(cli, ["-c", "checksums.txt"])
        assert result.exit_code == 1
        assert "file.txt: FAILED" in result.output
        assert "WARNING: 1 computed checksum(s) did NOT match" in result.output


def test_verification_missing_file():
    # type: () -> None
    """Test verification with missing target file."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create checksum file with non-existent file
        with open("checksums.txt", "w") as f:
            f.write("ISCC:KACYPXW445FTYNJ3CYSXHAFJMA2HUWULUNRFE3BLHRSCXYH2M5AEGQY *missing.txt\n")

        # Verify should report missing file
        result = runner.invoke(cli, ["-c", "checksums.txt"])
        assert result.exit_code == 1
        assert "missing.txt: No such file or directory" in result.output


def test_verification_quiet_mode():
    # type: () -> None
    """Test quiet mode suppresses OK messages."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create test file
        with open("file.txt", "wb") as f:
            f.write(b"Test content")

        # Generate checksum
        result = runner.invoke(cli, ["file.txt"])
        with open("checksums.txt", "w") as f:
            f.write(result.output)

        # Verify with quiet mode
        result = runner.invoke(cli, ["-c", "--quiet", "checksums.txt"])
        assert result.exit_code == 0
        assert "OK" not in result.output

        # Also test with -q
        result = runner.invoke(cli, ["-c", "-q", "checksums.txt"])
        assert result.exit_code == 0
        assert "OK" not in result.output


def test_verification_status_mode():
    # type: () -> None
    """Test status mode suppresses all output."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create test file
        with open("file.txt", "wb") as f:
            f.write(b"Test content")

        # Generate checksum
        result = runner.invoke(cli, ["file.txt"])
        with open("checksums.txt", "w") as f:
            f.write(result.output)

        # Verify with status mode (success)
        result = runner.invoke(cli, ["-c", "--status", "checksums.txt"])
        assert result.exit_code == 0
        assert result.output == ""

        # Modify file
        with open("file.txt", "wb") as f:
            f.write(b"Modified content")

        # Verify with status mode (failure)
        result = runner.invoke(cli, ["-c", "--status", "checksums.txt"])
        assert result.exit_code == 1
        assert result.output == ""


def test_verification_bsd_format():
    # type: () -> None
    """Test verification with BSD-style checksum format."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create test file
        with open("file.txt", "wb") as f:
            f.write(b"Test content")

        # Generate BSD-style checksum
        result = runner.invoke(cli, ["--tag", "file.txt"])
        assert result.exit_code == 0

        # Save checksum
        with open("checksums.txt", "w") as f:
            f.write(result.output)

        # Verify BSD format
        result = runner.invoke(cli, ["-c", "checksums.txt"])
        assert result.exit_code == 0
        assert "file.txt: OK" in result.output


def test_verification_mixed_formats():
    # type: () -> None
    """Test verification with mixed checksum formats."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create test files
        with open("file1.txt", "wb") as f:
            f.write(b"Content 1")
        with open("file2.txt", "wb") as f:
            f.write(b"Content 2")

        # Generate default format for file1
        result1 = runner.invoke(cli, ["file1.txt"])

        # Generate BSD format for file2
        result2 = runner.invoke(cli, ["--tag", "file2.txt"])

        # Mix formats in checksum file
        with open("checksums.txt", "w") as f:
            f.write(result1.output)
            f.write(result2.output)

        # Verify mixed formats
        result = runner.invoke(cli, ["-c", "checksums.txt"])
        assert result.exit_code == 0
        assert "file1.txt: OK" in result.output
        assert "file2.txt: OK" in result.output


def test_verification_warn_invalid_format():
    # type: () -> None
    """Test warning about improperly formatted lines."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create checksum file with invalid line
        with open("checksums.txt", "w") as f:
            f.write("Invalid checksum line\n")
            f.write("ISCC:KACYPXW445FTYNJ3CYSXHAFJMA2HUWULUNRFE3BLHRSCXYH2M5AEGQY *file.txt\n")

        # Create the file
        with open("file.txt", "wb") as f:
            f.write(b"Test")

        # Verify with warnings
        result = runner.invoke(cli, ["-c", "--warn", "checksums.txt"])
        # Exit code depends on whether file.txt matches the checksum
        assert "improperly formatted ISCC checksum line" in result.output
        assert "checksums.txt: 1:" in result.output


def test_verification_strict_mode():
    # type: () -> None
    """Test strict mode exits on format errors."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create checksum file with invalid line
        with open("checksums.txt", "w") as f:
            f.write("Invalid checksum line\n")

        # Verify with strict mode
        result = runner.invoke(cli, ["-c", "--strict", "checksums.txt"])
        assert result.exit_code == 2


def test_verification_empty_lines():
    # type: () -> None
    """Test that empty lines are ignored."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create test file
        with open("file.txt", "wb") as f:
            f.write(b"Test content")

        # Generate checksum
        result = runner.invoke(cli, ["file.txt"])

        # Create checksum file with empty lines
        with open("checksums.txt", "w") as f:
            f.write("\n")  # Empty line at start
            f.write(result.output)
            f.write("\n\n")  # Empty lines at end

        # Verify should work
        result = runner.invoke(cli, ["-c", "checksums.txt"])
        assert result.exit_code == 0
        assert "file.txt: OK" in result.output


def test_verification_narrow_format():
    # type: () -> None
    """Test verification with narrow format checksums."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create test file
        with open("file.txt", "wb") as f:
            f.write(b"Test content")

        # Generate narrow checksum
        result = runner.invoke(cli, ["--narrow", "file.txt"])
        assert result.exit_code == 0

        # Save checksum
        with open("checksums.txt", "w") as f:
            f.write(result.output)

        # Verify narrow format
        result = runner.invoke(cli, ["-c", "checksums.txt"])
        assert result.exit_code == 0
        assert "file.txt: OK" in result.output


def test_verification_multiple_checksum_files():
    # type: () -> None
    """Test verification with multiple checksum files."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create test files
        with open("file1.txt", "wb") as f:
            f.write(b"Content 1")
        with open("file2.txt", "wb") as f:
            f.write(b"Content 2")

        # Generate checksums
        result1 = runner.invoke(cli, ["file1.txt"])
        result2 = runner.invoke(cli, ["file2.txt"])

        # Save to separate checksum files
        with open("checksums1.txt", "w") as f:
            f.write(result1.output)
        with open("checksums2.txt", "w") as f:
            f.write(result2.output)

        # Verify multiple checksum files
        result = runner.invoke(cli, ["-c", "checksums1.txt", "checksums2.txt"])
        assert result.exit_code == 0
        assert "file1.txt: OK" in result.output
        assert "file2.txt: OK" in result.output


def test_verification_strict_with_format_errors_only():
    # type: () -> None
    """Test strict mode exits with code 2 when there are format errors but no failed files."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create a valid file
        with open("valid.txt", "wb") as f:
            f.write(b"Valid content")

        # Generate checksum for it
        result = runner.invoke(cli, ["valid.txt"])
        valid_checksum = result.output

        # Create checksum file with valid entry followed by invalid ones
        with open("checksums.txt", "w") as f:
            f.write(valid_checksum)  # Valid line that will pass
            f.write("Invalid line 1\n")  # Invalid line
            f.write("Another invalid line\n")  # Another invalid line

        # Verify without strict mode first - should only fail with exit code 0 and show warning
        result = runner.invoke(cli, ["-c", "checksums.txt"])
        assert result.exit_code == 0  # No failed checksums, just format errors
        assert "WARNING: 2 line(s) improperly formatted" in result.output

        # Now verify with strict mode - should exit with code 2
        result = runner.invoke(cli, ["-c", "--strict", "checksums.txt"])
        assert result.exit_code == 2


def test_verification_file_io_error():
    # type: () -> None
    """Test handling of I/O errors during verification."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create checksum file with a valid checksum
        # First generate a real checksum for "Test"
        with open("temp.txt", "wb") as f:
            f.write(b"Test")

        gen_result = runner.invoke(cli, ["temp.txt"])
        expected_checksum = gen_result.output.split()[0]

        with open("checksums.txt", "w") as f:
            f.write(f"{expected_checksum} *file.txt\n")

        # Use os.chmod to make file unreadable on Unix systems
        import os
        import platform

        # Create file
        with open("file.txt", "wb") as f:
            f.write(b"Test")

        if platform.system() != "Windows":
            # On Unix, remove read permissions
            os.chmod("file.txt", 0o000)

            result = runner.invoke(cli, ["-c", "checksums.txt"])

            # Restore permissions so cleanup works
            os.chmod("file.txt", 0o644)

            assert result.exit_code == 1
            assert "Permission denied" in result.output or "file.txt:" in result.output
        else:
            # On Windows, we'll just skip this test
            # or use a different approach
            import pytest

            pytest.skip("Permission test not implemented for Windows")


def test_verification_io_error_during_read():
    # type: () -> None
    """Test handling of I/O errors during file reading in verification."""
    from unittest.mock import mock_open

    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create a valid checksum file
        with open("checksums.txt", "w") as f:
            f.write("ISCC:KACYPXW445FTYNJ3CYSXHAFJMA2HUWULUNRFE3BLHRSCXYH2M5AEGQY *file.txt\n")

        # Create the file
        with open("file.txt", "wb") as f:
            f.write(b"Test content")

        # Mock the file reading to raise IOError
        original_open = open

        def mock_open_wrapper(filename, *args, **kwargs):
            # Allow opening checksums.txt normally
            if "checksums.txt" in str(filename):
                return original_open(filename, *args, **kwargs)
            # For file.txt, first allow the exists check, then fail on actual read
            if "file.txt" in str(filename) and "rb" in str(args):
                # Create a mock file object that raises IOError on read
                mock_file = mock_open()()
                mock_file.read.side_effect = IOError("Read error during verification")
                return mock_file
            return original_open(filename, *args, **kwargs)

        with patch("builtins.open", side_effect=mock_open_wrapper):
            result = runner.invoke(cli, ["-c", "checksums.txt"])
            assert result.exit_code == 1
            assert "Read error during verification" in result.output
            assert "file.txt:" in result.output
