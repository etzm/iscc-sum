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


def test_tree_mode_verification_basic():
    # type: () -> None
    """Test tree mode verification with correct checksum."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create test directory
        os.makedirs("test_dir")
        Path("test_dir/file1.txt").write_text("Content 1")
        Path("test_dir/file2.txt").write_text("Content 2")

        # Generate tree checksum
        result = runner.invoke(cli, ["--tree", "test_dir"])
        assert result.exit_code == 0

        # Save checksum to file
        Path("checksums.txt").write_text(result.output)

        # Verify the checksum
        result = runner.invoke(cli, ["--check", "checksums.txt"])
        assert result.exit_code == 0
        assert "test_dir/: OK" in result.output


def test_tree_mode_verification_bsd_format():
    # type: () -> None
    """Test tree mode verification with BSD format."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create test directory
        os.makedirs("test_dir")
        Path("test_dir/file.txt").write_text("Test content")

        # Generate BSD format checksum
        result = runner.invoke(cli, ["--tree", "--tag", "test_dir"])
        assert result.exit_code == 0

        # Save checksum
        Path("checksums.txt").write_text(result.output)

        # Verify
        result = runner.invoke(cli, ["--check", "checksums.txt"])
        assert result.exit_code == 0
        assert "test_dir/: OK" in result.output


def test_tree_mode_verification_failed():
    # type: () -> None
    """Test tree mode verification with changed content."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create test directory
        os.makedirs("test_dir")
        Path("test_dir/file.txt").write_text("Original content")

        # Generate checksum
        result = runner.invoke(cli, ["--tree", "test_dir"])
        assert result.exit_code == 0
        Path("checksums.txt").write_text(result.output)

        # Modify file
        Path("test_dir/file.txt").write_text("Changed content")

        # Verify - should fail
        result = runner.invoke(cli, ["--check", "checksums.txt"])
        assert result.exit_code == 1
        assert "test_dir/: FAILED" in result.output


def test_tree_mode_verification_missing_directory():
    # type: () -> None
    """Test tree mode verification with missing directory."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create fake checksum file for non-existent directory
        Path("checksums.txt").write_text(
            "ISCC:KAEFOO3Z7A7QZPXVYDBGBBLBRDQFH6J2GJNXLSM4G5V6VZ5D3Y4Q *missing_dir/\n"
        )

        # Verify - should report missing
        result = runner.invoke(cli, ["--check", "checksums.txt"])
        assert result.exit_code == 1
        assert "missing_dir: No such file or directory" in result.output


def test_tree_mode_verification_not_directory():
    # type: () -> None
    """Test tree mode verification when path is not a directory."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create a file
        Path("file.txt").write_text("content")

        # Create checksum file pointing to file with trailing slash
        Path("checksums.txt").write_text(
            "ISCC:KAEFOO3Z7A7QZPXVYDBGBBLBRDQFH6J2GJNXLSM4G5V6VZ5D3Y4Q *file.txt/\n"
        )

        # Verify - should report not a directory
        result = runner.invoke(cli, ["--check", "checksums.txt"])
        assert result.exit_code == 1
        assert "file.txt: Not a directory" in result.output


def test_tree_mode_verification_mixed():
    # type: () -> None
    """Test verification with mixed tree and file checksums."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create test structure
        os.makedirs("test_dir")
        Path("test_dir/file1.txt").write_text("Content 1")
        Path("standalone.txt").write_text("Standalone content")

        # Generate checksums for both
        result1 = runner.invoke(cli, ["--tree", "test_dir"])
        assert result1.exit_code == 0

        result2 = runner.invoke(cli, ["standalone.txt"])
        assert result2.exit_code == 0

        # Save both checksums
        Path("checksums.txt").write_text(result1.output + result2.output)

        # Verify both
        result = runner.invoke(cli, ["--check", "checksums.txt"])
        assert result.exit_code == 0
        assert "test_dir/: OK" in result.output
        assert "standalone.txt: OK" in result.output


def test_tree_mode_verification_quiet():
    # type: () -> None
    """Test tree mode verification with quiet option."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create test directory
        os.makedirs("test_dir")
        Path("test_dir/file.txt").write_text("content")

        # Generate and save checksum
        result = runner.invoke(cli, ["--tree", "test_dir"])
        Path("checksums.txt").write_text(result.output)

        # Verify with quiet option
        result = runner.invoke(cli, ["--check", "--quiet", "checksums.txt"])
        assert result.exit_code == 0
        assert result.output == ""  # No output in quiet mode for success


def test_tree_mode_verification_io_error():
    # type: () -> None
    """Test tree mode verification with IO errors."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create test directory
        os.makedirs("test_dir")
        Path("test_dir/file1.txt").write_text("content 1")
        Path("test_dir/file2.txt").write_text("content 2")

        # Make one file unreadable before generating checksum
        if os.name != "nt":
            os.chmod("test_dir/file2.txt", 0o000)

            # Generate checksum for the directory (will skip unreadable file)
            result = runner.invoke(cli, ["--tree", "test_dir"])
            assert result.exit_code == 0

            # Save checksum
            Path("checksums.txt").write_text(result.output)

            # Verify - should succeed since both generation and verification skip the same file
            result = runner.invoke(cli, ["--check", "checksums.txt"])

            # Restore permissions
            os.chmod("test_dir/file2.txt", 0o644)

            # The verification should succeed since tree mode skips unreadable files consistently
            assert result.exit_code == 0
            assert "test_dir/: OK" in result.output


def test_tree_mode_verification_unexpected_error():
    # type: () -> None
    """Test tree mode verification with unexpected errors."""
    import unittest.mock

    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create test directory
        os.makedirs("test_dir")
        Path("test_dir/file.txt").write_text("content")

        # Generate checksum
        result = runner.invoke(cli, ["--tree", "test_dir"])
        assert result.exit_code == 0

        # Save checksum
        Path("checksums.txt").write_text(result.output)

        # Mock treewalk to raise an exception
        with unittest.mock.patch("iscc_sum.treewalk.treewalk_iscc") as mock_treewalk:
            mock_treewalk.side_effect = Exception("Simulated error")

            # Verify - should report error
            result = runner.invoke(cli, ["--check", "checksums.txt"])
            assert result.exit_code == 1
            assert "Simulated error" in result.output


def test_walk_mode_basic():
    # type: () -> None
    """Test basic walk mode functionality."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create test directory structure
        os.makedirs("test_dir/sub1/sub2")
        Path("test_dir/file1.txt").write_text("Content 1")
        Path("test_dir/sub1/file2.txt").write_text("Content 2")
        Path("test_dir/sub1/sub2/file3.txt").write_text("Content 3")

        # Run walk mode
        result = runner.invoke(cli, ["--walk", "test_dir"])
        assert result.exit_code == 0

        # Check output contains file paths
        lines = result.output.strip().split("\n")
        assert "file1.txt" in lines
        assert "sub1/file2.txt" in lines
        assert "sub1/sub2/file3.txt" in lines

        # Files should be in deterministic order
        assert lines.index("file1.txt") < lines.index("sub1/file2.txt")
        assert lines.index("sub1/file2.txt") < lines.index("sub1/sub2/file3.txt")


def test_walk_mode_with_isccignore():
    # type: () -> None
    """Test walk mode respects .isccignore files."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create directory with .isccignore
        os.makedirs("test_dir")
        Path("test_dir/.isccignore").write_text("*.log\n")
        Path("test_dir/keep.txt").write_text("Keep this")
        Path("test_dir/ignore.log").write_text("Ignore this")

        # Run walk mode
        result = runner.invoke(cli, ["--walk", "test_dir"])
        assert result.exit_code == 0

        # Should include .isccignore and keep.txt, but not ignore.log
        lines = result.output.strip().split("\n")
        assert ".isccignore" in lines
        assert "keep.txt" in lines
        assert "ignore.log" not in lines


def test_walk_mode_empty_directory():
    # type: () -> None
    """Test walk mode with empty directory."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create empty directory
        os.makedirs("empty_dir")

        # Run walk mode
        result = runner.invoke(cli, ["--walk", "empty_dir"])
        assert result.exit_code == 2
        assert "no files found" in result.output


def test_walk_mode_validation_errors():
    # type: () -> None
    """Test walk mode validation errors."""
    runner = CliRunner()

    # Test with no arguments
    result = runner.invoke(cli, ["--walk"])
    assert result.exit_code == 2
    assert "requires exactly one directory argument" in result.output

    # Test with multiple arguments
    result = runner.invoke(cli, ["--walk", "dir1", "dir2"])
    assert result.exit_code == 2
    assert "requires exactly one directory argument" in result.output

    with runner.isolated_filesystem():
        # Test with file instead of directory
        Path("file.txt").write_text("content")
        result = runner.invoke(cli, ["--walk", "file.txt"])
        assert result.exit_code == 2
        assert "requires a directory, not a file" in result.output


def test_walk_mode_conflicts():
    # type: () -> None
    """Test walk mode conflicts with other options."""
    runner = CliRunner()

    # Walk with tree
    result = runner.invoke(cli, ["--walk", "--tree", "dir"])
    assert result.exit_code == 2
    assert "--walk cannot be used with --tree" in result.output

    # Walk with check
    result = runner.invoke(cli, ["--walk", "--check", "dir"])
    assert result.exit_code == 2
    assert "--walk cannot be used with -c/--check" in result.output

    # Walk with similar
    result = runner.invoke(cli, ["--walk", "--similar", "dir"])
    assert result.exit_code == 2
    assert "--walk cannot be used with --similar" in result.output


def test_walk_mode_zero_terminator():
    # type: () -> None
    """Test walk mode with zero terminator."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create test directory
        os.makedirs("test_dir")
        Path("test_dir/file1.txt").write_text("content 1")
        Path("test_dir/file2.txt").write_text("content 2")

        # Run with zero terminator
        result = runner.invoke(cli, ["--walk", "-z", "test_dir"])
        assert result.exit_code == 0

        # Output should have null bytes between filenames
        assert "\0" in result.output
        assert result.output.endswith("\0")

        # Split on null bytes and check files
        files = result.output.rstrip("\0").split("\0")
        assert "file1.txt" in files
        assert "file2.txt" in files


def test_walk_vs_tree_consistency():
    # type: () -> None
    """Test that walk mode lists exactly the same files that tree mode processes."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create complex directory structure
        os.makedirs("test_dir/sub1/sub2")
        os.makedirs("test_dir/sub3")
        Path("test_dir/.isccignore").write_text("*.tmp\n")
        Path("test_dir/file1.txt").write_text("Content 1")
        Path("test_dir/file2.tmp").write_text("Ignored temp file")
        Path("test_dir/sub1/file3.txt").write_text("Content 3")
        Path("test_dir/sub1/sub2/file4.txt").write_text("Content 4")
        Path("test_dir/sub3/file5.txt").write_text("Content 5")

        # Get files from walk mode
        walk_result = runner.invoke(cli, ["--walk", "test_dir"])
        assert walk_result.exit_code == 0
        walk_files = set(walk_result.output.strip().split("\n"))

        # Get tree checksum (which processes the same files)
        tree_result = runner.invoke(cli, ["--tree", "test_dir"])
        assert tree_result.exit_code == 0

        # Verify walk mode shows expected files
        expected_files = {".isccignore", "file1.txt", "sub1/file3.txt", "sub1/sub2/file4.txt", "sub3/file5.txt"}
        assert walk_files == expected_files

        # file2.tmp should be ignored
        assert "file2.tmp" not in walk_files


def test_walk_mode_deterministic():
    # type: () -> None
    """Test walk mode produces deterministic output."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create test directory with multiple files
        os.makedirs("test_dir/sub")
        Path("test_dir/zebra.txt").write_text("Z")
        Path("test_dir/alpha.txt").write_text("A")
        Path("test_dir/sub/beta.txt").write_text("B")

        # Run multiple times
        outputs = []
        for _ in range(3):
            result = runner.invoke(cli, ["--walk", "test_dir"])
            assert result.exit_code == 0
            outputs.append(result.output)

        # All outputs should be identical
        assert len(set(outputs)) == 1

        # Check ordering is consistent with treewalk expectations
        files = outputs[0].strip().split("\n")
        # Files before subdirectories, alphabetical within each level
        assert files.index("alpha.txt") < files.index("zebra.txt")
        assert files.index("zebra.txt") < files.index("sub/beta.txt")


def test_walk_mode_io_error_handling():
    # type: () -> None
    """Test walk mode handles IO errors gracefully."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create test directory
        os.makedirs("test_dir")
        Path("test_dir/file1.txt").write_text("Content 1")
        Path("test_dir/file2.txt").write_text("Content 2")

        # Walk mode doesn't actually read files, so IO permissions don't affect it
        # But let's test that it still lists files even if they would be unreadable
        if os.name != "nt":  # Skip on Windows
            os.chmod("test_dir/file2.txt", 0o000)

            # Run walk mode - should list all files regardless of permissions
            result = runner.invoke(cli, ["--walk", "test_dir"])

            # Restore permissions for cleanup
            os.chmod("test_dir/file2.txt", 0o644)

            # Should list both files
            assert result.exit_code == 0
            files = result.output.strip().split("\n")
            assert "file1.txt" in files
            assert "file2.txt" in files


def test_walk_mode_gitignore_negation_star_vs_star_slash():
    # type: () -> None
    """Test gitignore negation patterns with '*' vs '*/'."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create directory structure
        os.makedirs("test_dir/subdir")
        Path("test_dir/root.txt").write_text("root content")
        Path("test_dir/subdir/sub.txt").write_text("sub content")

        # Test with '*/' pattern (ignores directories, allows files)
        Path("test_dir/.isccignore").write_text("*/\n!subdir/**\n")
        result = runner.invoke(cli, ["--walk", "test_dir"])
        assert result.exit_code == 0
        files = set(result.output.strip().split("\n"))
        assert ".isccignore" in files  # .isccignore is not ignored by */
        assert "root.txt" in files  # root.txt is not ignored by */
        assert "subdir/sub.txt" in files  # Included by !subdir/**

        # Test with '*' pattern (ignores everything, but negation allows subdir/**)
        Path("test_dir/.isccignore").write_text("*\n!subdir/**\n")
        result = runner.invoke(cli, ["--walk", "test_dir"])
        assert result.exit_code == 0
        files = set(result.output.strip().split("\n"))
        # The '*' pattern ignores everything at root level
        assert ".isccignore" not in files  # Ignored by *
        assert "root.txt" not in files  # Ignored by *
        assert "subdir/sub.txt" in files  # Included by !subdir/**
