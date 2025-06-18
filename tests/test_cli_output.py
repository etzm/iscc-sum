# Test the -o/--output option
"""Tests for the -o/--output CLI option."""

import os
from pathlib import Path

import pytest
from click.testing import CliRunner
from pyfakefs.fake_filesystem import FakeFilesystem

from iscc_sum.cli import cli


class TestOutputOption:
    """Test cases for the -o/--output option."""

    def test_output_option_basic(self, fs: FakeFilesystem) -> None:
        """Test basic output to file."""
        fs.create_file("/test.txt", contents="test content")
        runner = CliRunner()

        result = runner.invoke(cli, ["-o", "/output.iscc", "/test.txt"])
        assert result.exit_code == 0

        # Check output file was created
        assert os.path.exists("/output.iscc")
        with open("/output.iscc", "r") as f:
            content = f.read()
            assert content.startswith("ISCC:")
            assert " */test.txt\n" in content

    def test_output_option_multiple_files(self, fs: FakeFilesystem) -> None:
        """Test output with multiple input files."""
        fs.create_file("/file1.txt", contents="content 1")
        fs.create_file("/file2.txt", contents="content 2")
        runner = CliRunner()

        result = runner.invoke(cli, ["-o", "/checksums.iscc", "/file1.txt", "/file2.txt"])
        assert result.exit_code == 0

        with open("/checksums.iscc", "r") as f:
            lines = f.readlines()
            assert len(lines) == 2
            assert " */file1.txt\n" in lines[0]
            assert " */file2.txt\n" in lines[1]

    def test_output_option_with_tag(self, fs: FakeFilesystem) -> None:
        """Test output option with BSD-style format."""
        fs.create_file("/test.txt", contents="test")
        runner = CliRunner()

        result = runner.invoke(cli, ["--tag", "-o", "/bsd.iscc", "/test.txt"])
        assert result.exit_code == 0

        with open("/bsd.iscc", "r") as f:
            content = f.read()
            assert "ISCC-SUM (/test.txt) = ISCC:" in content

    def test_output_option_with_tree(self, fs: FakeFilesystem) -> None:
        """Test output option with tree mode."""
        fs.create_dir("/mydir")
        fs.create_file("/mydir/file1.txt", contents="content 1")
        fs.create_file("/mydir/file2.txt", contents="content 2")
        runner = CliRunner()

        result = runner.invoke(cli, ["--tree", "-o", "/tree.iscc", "/mydir"])
        assert result.exit_code == 0

        with open("/tree.iscc", "r") as f:
            content = f.read()
            assert " */mydir/\n" in content

    def test_output_option_with_similar(self, fs: FakeFilesystem) -> None:
        """Test output option with similar mode."""
        fs.create_file("/file1.txt", contents="test content")
        fs.create_file("/file2.txt", contents="test content modified")
        fs.create_file("/file3.txt", contents="completely different")
        runner = CliRunner()

        result = runner.invoke(
            cli, ["--similar", "-o", "/similar.iscc", "/file1.txt", "/file2.txt", "/file3.txt"]
        )
        assert result.exit_code == 0

        assert os.path.exists("/similar.iscc")
        with open("/similar.iscc", "r") as f:
            content = f.read()
            assert "ISCC:" in content

    def test_output_option_encoding(self, fs: FakeFilesystem) -> None:
        """Test that output files are UTF-8 with LF line endings."""
        fs.create_file("/test.txt", contents="test")
        runner = CliRunner()

        result = runner.invoke(cli, ["-o", "/output.iscc", "/test.txt"])
        assert result.exit_code == 0

        # Read as binary to check encoding
        with open("/output.iscc", "rb") as f:
            raw_content = f.read()
            # No BOM
            assert not raw_content.startswith(b"\xef\xbb\xbf")
            # LF line endings
            assert b"\r\n" not in raw_content
            assert b"\n" in raw_content
            # Valid UTF-8
            raw_content.decode("utf-8")

    def test_output_option_overwrites(self, fs: FakeFilesystem) -> None:
        """Test that output option overwrites existing files."""
        fs.create_file("/test.txt", contents="test")
        fs.create_file("/output.iscc", contents="old content")
        runner = CliRunner()

        result = runner.invoke(cli, ["-o", "/output.iscc", "/test.txt"])
        assert result.exit_code == 0

        with open("/output.iscc", "r") as f:
            content = f.read()
            assert "old content" not in content
            assert "ISCC:" in content

    def test_output_option_invalid_path(self, fs: FakeFilesystem) -> None:
        """Test output option with invalid path."""
        fs.create_file("/test.txt", contents="test")
        runner = CliRunner()

        result = runner.invoke(cli, ["-o", "/nonexistent/output.iscc", "/test.txt"])
        assert result.exit_code == 2
        assert "No such file or directory" in result.output

    def test_output_option_with_check_conflicts(self, fs: FakeFilesystem) -> None:
        """Test that -o conflicts with --check."""
        fs.create_file(
            "/checksums.iscc", contents="ISCC:K4AAHQPCQN7Z7V54WGKWVMTIGYJAVTOQ4QRJHXQNXQFCBHRW2W5A *test.txt\n"
        )
        runner = CliRunner()

        result = runner.invoke(cli, ["-o", "/output.iscc", "--check", "/checksums.iscc"])
        assert result.exit_code == 2
        assert "-o/--output cannot be used with -c/--check" in result.output

    def test_output_option_with_zero(self, fs: FakeFilesystem) -> None:
        """Test output option with zero termination."""
        fs.create_file("/file1.txt", contents="test1")
        fs.create_file("/file2.txt", contents="test2")
        runner = CliRunner()

        result = runner.invoke(cli, ["-o", "/zero.iscc", "-z", "/file1.txt", "/file2.txt"])
        assert result.exit_code == 0

        with open("/zero.iscc", "rb") as f:
            content = f.read()
            # Should have null terminators instead of newlines
            assert b"\0" in content
            assert content.count(b"\0") == 2
            # Should not have newlines
            assert b"\n" not in content

    def test_output_option_permissions(self, fs: FakeFilesystem) -> None:
        """Test output option handles permission errors gracefully."""
        if os.name == "nt":
            pytest.skip("Permission test not applicable on Windows")

        fs.create_file("/test.txt", contents="test")
        fs.create_dir("/readonly")
        os.chmod("/readonly", 0o444)  # Read-only directory
        runner = CliRunner()

        result = runner.invoke(cli, ["-o", "/readonly/output.iscc", "/test.txt"])
        assert result.exit_code == 2
        assert "iscc-sum: /readonly/output.iscc:" in result.output
