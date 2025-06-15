# Tests for checksum generation functionality

import pytest
from click.testing import CliRunner

from iscc_sum.cli import cli


def test_file_not_found():
    # type: () -> None
    """Test error handling for non-existent file."""
    runner = CliRunner()
    result = runner.invoke(cli, ["nonexistent.txt"])
    assert result.exit_code == 2
    assert "iscc-sum: nonexistent.txt:" in result.output
    assert "No such file or directory" in result.output or "cannot find the file" in result.output


def test_directory_instead_of_file():
    # type: () -> None
    """Test error handling when directory is passed instead of file."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        import os

        os.mkdir("testdir")

        result = runner.invoke(cli, ["testdir"])
        assert result.exit_code == 2
        assert "iscc-sum: testdir:" in result.output


def test_empty_file():
    # type: () -> None
    """Test handling of empty file."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create empty file
        open("empty.txt", "wb").close()

        result = runner.invoke(cli, ["empty.txt"])
        assert result.exit_code == 0
        assert "ISCC:" in result.output
        assert " *empty.txt" in result.output


def test_large_file_simulation():
    # type: () -> None
    """Test handling of large file by simulating multiple chunks."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create a file larger than one chunk (2MB)
        chunk_size = 2097152  # 2MB
        with open("large.txt", "wb") as f:
            # Write 3 chunks worth of data
            data = b"x" * 1024  # 1KB
            for _ in range(3 * chunk_size // 1024):
                f.write(data)

        result = runner.invoke(cli, ["large.txt"])
        assert result.exit_code == 0
        assert "ISCC:" in result.output
        assert " *large.txt" in result.output


def test_binary_file():
    # type: () -> None
    """Test handling of binary file."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create binary file with various byte values
        with open("binary.dat", "wb") as f:
            f.write(bytes(range(256)))

        result = runner.invoke(cli, ["binary.dat"])
        assert result.exit_code == 0
        assert "ISCC:" in result.output
        assert " *binary.dat" in result.output


def test_units_with_narrow():
    # type: () -> None
    """Test units output with narrow format."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("test.txt", "wb") as f:
            f.write(b"Test content\n")

        result = runner.invoke(cli, ["--units", "--narrow", "test.txt"])
        assert result.exit_code == 0
        lines = result.output.strip().split("\n")
        assert len(lines) == 3  # Main ISCC + 2 units

        # First line should have narrow format main ISCC
        main_iscc = lines[0].split()[0]
        assert main_iscc.startswith("ISCC:")
        assert len(main_iscc) < 35  # Narrow format

        # Units are always in wide format
        for i in [1, 2]:
            assert lines[i].startswith("  ISCC:")  # Indented
            unit_iscc = lines[i].strip()
            assert len(unit_iscc) > 50  # Wide format units


def test_tag_with_units():
    # type: () -> None
    """Test BSD-style output with units."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("test.txt", "wb") as f:
            f.write(b"Test content\n")

        result = runner.invoke(cli, ["--tag", "--units", "test.txt"])
        assert result.exit_code == 0
        lines = result.output.strip().split("\n")
        assert "ISCC-SUM (test.txt) = ISCC:" in lines[0]
        assert "  ISCC:" in lines[1]  # Data-Code unit
        assert "  ISCC:" in lines[2]  # Instance-Code unit


def test_zero_with_multiple_files():
    # type: () -> None
    """Test NUL-terminated output with multiple files."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create test files
        for i in range(3):
            with open(f"file{i}.txt", "wb") as f:
                f.write(f"Content {i}\n".encode())

        result = runner.invoke(cli, ["--zero", "file0.txt", "file1.txt", "file2.txt"])
        assert result.exit_code == 0
        # Should have NUL terminators instead of newlines
        assert "\0" in result.output
        # Should have 3 NUL terminators (one per file)
        assert result.output.count("\0") == 3
        # Should not have newlines
        assert "\n" not in result.output


def test_special_characters_in_filename():
    # type: () -> None
    """Test handling of filenames with special characters."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create file with spaces and special chars
        filename = "test file (with spaces).txt"
        with open(filename, "wb") as f:
            f.write(b"Test content\n")

        result = runner.invoke(cli, [filename])
        assert result.exit_code == 0
        assert "ISCC:" in result.output
        assert f" *{filename}" in result.output
