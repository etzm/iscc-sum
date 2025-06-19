# Tests for path normalization on Windows

import os
import tempfile
from pathlib import Path

from click.testing import CliRunner
from pyfakefs.fake_filesystem_unittest import Patcher

from iscc_sum.cli import cli


class TestPathNormalization:
    """Test path normalization for Windows compatibility."""

    def test_normalize_path_display_function(self):
        # type: () -> None
        """Test the _normalize_path_display function."""
        from iscc_sum.cli import _normalize_path_display

        # Test regular paths with backslashes
        assert _normalize_path_display("C:\\Users\\test\\file.txt") == "C:/Users/test/file.txt"
        assert _normalize_path_display("E:\\data\\file.epub") == "E:/data/file.epub"

        # Test paths that already have forward slashes
        assert _normalize_path_display("/home/user/file.txt") == "/home/user/file.txt"
        assert _normalize_path_display("C:/Users/test/file.txt") == "C:/Users/test/file.txt"

        # Test mixed slashes
        assert _normalize_path_display("C:\\Users\\test/file.txt") == "C:/Users/test/file.txt"

        # Test stdin placeholder
        assert _normalize_path_display("-") == "-"

    def test_windows_glob_pattern_output(self):
        # type: () -> None
        """Test that glob patterns on Windows produce forward slash output."""
        runner = CliRunner()

        with Patcher() as patcher:
            # Create test files with Windows-style paths
            patcher.fs.create_file("E:\\data\\file1.epub", contents=b"test1")
            patcher.fs.create_file("E:\\data\\file2.epub", contents=b"test2")

            # Simulate how Windows glob expansion might work
            # (paths with backslashes passed to CLI)
            result = runner.invoke(cli, ["E:\\data\\file1.epub", "E:\\data\\file2.epub"])

            assert result.exit_code == 0

            # Check that output contains forward slashes
            assert "E:/data/file1.epub" in result.output
            assert "E:/data/file2.epub" in result.output

            # Make sure no backslashes appear in output
            assert "\\" not in result.output

    def test_directory_expansion_output(self):
        # type: () -> None
        """Test that directory expansion produces forward slash output."""
        runner = CliRunner()

        with Patcher() as patcher:
            # Create directory with files
            patcher.fs.create_dir("/tmp/projects")
            patcher.fs.create_file("/tmp/projects/file1.txt", contents=b"content1")
            patcher.fs.create_file("/tmp/projects/file2.txt", contents=b"content2")

            # Simulate Windows path expansion by using paths with backslashes
            # but since we're on Linux, we'll test path normalization directly
            result = runner.invoke(cli, ["/tmp/projects"])

            assert result.exit_code == 0

            # Output should contain forward slashes
            output_lines = result.output.strip().split("\n")
            for line in output_lines:
                if "*" in line:
                    # Extract the path part after the asterisk
                    path_part = line.split("*")[1]
                    # No backslashes should appear
                    assert "\\" not in path_part

    def test_tag_format_with_windows_paths(self):
        # type: () -> None
        """Test BSD-style tag format with Windows paths."""
        runner = CliRunner()

        with Patcher() as patcher:
            patcher.fs.create_file("D:\\documents\\report.pdf", contents=b"PDF content")

            result = runner.invoke(cli, ["--tag", "D:\\documents\\report.pdf"])

            assert result.exit_code == 0

            # Check BSD format with forward slashes
            assert "ISCC-SUM (D:/documents/report.pdf) =" in result.output
            assert "\\" not in result.output

    def test_similar_mode_windows_paths(self):
        # type: () -> None
        """Test similar mode output with Windows paths."""
        runner = CliRunner()

        with Patcher() as patcher:
            # Create similar files
            patcher.fs.create_file("E:\\books\\book1.txt", contents=b"Hello world")
            patcher.fs.create_file("E:\\books\\book2.txt", contents=b"Hello world")

            result = runner.invoke(cli, ["--similar", "E:\\books\\book1.txt", "E:\\books\\book2.txt"])

            assert result.exit_code == 0

            # Check that similar files output uses forward slashes
            assert "E:/books/book1.txt" in result.output
            assert "E:/books/book2.txt" in result.output
            assert "\\" not in result.output

    def test_tree_mode_windows_paths(self):
        # type: () -> None
        """Test tree mode with directory paths."""
        runner = CliRunner()

        with Patcher() as patcher:
            # Create directory tree
            patcher.fs.create_dir("/tmp/workspace/project")
            patcher.fs.create_file("/tmp/workspace/project/main.py", contents=b"print('hello')")
            patcher.fs.create_file("/tmp/workspace/project/test.py", contents=b"import main")

            result = runner.invoke(cli, ["--tree", "/tmp/workspace/project"])

            assert result.exit_code == 0

            # Check tree mode output doesn't contain backslashes
            assert "\\" not in result.output
            # Should have trailing slash for tree mode
            assert "/tmp/workspace/project/" in result.output

    def test_verification_output_format(self):
        # type: () -> None
        """Test that verification mode shows paths correctly."""
        runner = CliRunner()

        with Patcher() as patcher:
            # Create test files first
            patcher.fs.create_file("/tmp/file1.txt", contents=b"test content 1")
            patcher.fs.create_file("/tmp/file2.txt", contents=b"test content 2")

            # Generate checksums first
            gen_result = runner.invoke(cli, ["/tmp/file1.txt", "/tmp/file2.txt"])
            assert gen_result.exit_code == 0

            # Save the checksums to a file
            patcher.fs.create_file("/tmp/checksums.txt", contents=gen_result.output)

            # Now verify the checksums
            result = runner.invoke(cli, ["--check", "/tmp/checksums.txt"])

            assert result.exit_code == 0

            # Verification output should not contain backslashes
            assert "\\" not in result.output
            assert ": OK" in result.output
