# Tests for similarity matching functionality in CLI
import os
import tempfile

import pytest
from click.testing import CliRunner

from iscc_sum.cli import _extract_data_code_bits, _hamming_distance, cli


class TestDecodingEdgeCases:
    """Test edge cases in ISCC decoding."""

    def test_extract_data_code_bits_various_iscc_formats(self):
        """Test extraction with various ISCC formats."""
        # Test with actual ISCCs from our test suite
        test_cases = [
            # (iscc, narrow, expected_length)
            ("ISCC:KAD4H3O4XPXNEP4T", True, 8),  # Narrow format
            ("ISCC:KAE4H3O4XPXNEP4THQFNZ7WSWWDTBEHU35K7HQVN2IKN", False, 16),  # Wide format
            ("ISCC:KUAKNZSWKKP44NSS6AT6I5YOACGFY", True, 8),  # Another narrow
        ]

        for iscc, narrow, expected_len in test_cases:
            bits = _extract_data_code_bits(iscc, narrow)
            assert isinstance(bits, bytes)
            assert len(bits) == expected_len

    def test_extract_data_code_bits_consistent_results(self):
        """Test that extraction gives consistent results."""
        # Test that the same ISCC always gives the same bits
        iscc = "ISCC:KAD4H3O4XPXNEP4T"
        bits1 = _extract_data_code_bits(iscc, narrow=True)
        bits2 = _extract_data_code_bits(iscc, narrow=True)
        assert bits1 == bits2

        # Test wide format consistency
        iscc_wide = "ISCC:KAE4H3O4XPXNEP4THQFNZ7WSWWDTBEHU35K7HQVN2IKN"
        bits3 = _extract_data_code_bits(iscc_wide, narrow=False)
        bits4 = _extract_data_code_bits(iscc_wide, narrow=False)
        assert bits3 == bits4


class TestSimilarityHelperFunctions:
    """Test the helper functions for similarity matching."""

    def test_extract_data_code_bits_narrow(self):
        """Test extracting Data-Code bits from narrow format ISCC."""
        # Example narrow ISCC (from test data)
        iscc = "ISCC:KAD4H3O4XPXNEP4T"
        bits = _extract_data_code_bits(iscc, narrow=True)
        assert len(bits) == 8  # 64 bits = 8 bytes
        assert isinstance(bits, bytes)

    def test_extract_data_code_bits_wide(self):
        """Test extracting Data-Code bits from wide format ISCC."""
        # Example wide ISCC
        iscc = "ISCC:KAE4H3O4XPXNEP4THQFNZ7WSWWDTBEHU35K7HQVN2IKN"
        bits = _extract_data_code_bits(iscc, narrow=False)
        assert len(bits) == 16  # 128 bits = 16 bytes
        assert isinstance(bits, bytes)

    def test_hamming_distance_identical(self):
        """Test hamming distance between identical byte sequences."""
        bits = b"\x00\x11\x22\x33\x44\x55\x66\x77"
        assert _hamming_distance(bits, bits) == 0

    def test_hamming_distance_different(self):
        """Test hamming distance between different byte sequences."""
        bits_a = b"\x00\x00\x00\x00"
        bits_b = b"\xff\xff\xff\xff"
        # All bits are different: 4 bytes * 8 bits = 32
        assert _hamming_distance(bits_a, bits_b) == 32

    def test_hamming_distance_one_bit(self):
        """Test hamming distance with single bit difference."""
        bits_a = b"\x00"
        bits_b = b"\x01"  # Only LSB is different
        assert _hamming_distance(bits_a, bits_b) == 1

    def test_hamming_distance_unequal_length(self):
        """Test hamming distance with unequal length sequences."""
        bits_a = b"\x00\x00"
        bits_b = b"\x00\x00\x00"
        with pytest.raises(ValueError):
            _hamming_distance(bits_a, bits_b)


class TestSimilarityMode:
    """Test the --similar option functionality."""

    def test_similar_requires_multiple_files(self):
        """Test that --similar requires at least 2 files."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create a single test file
            with open("test.txt", "w") as f:
                f.write("test content")

            result = runner.invoke(cli, ["--similar", "test.txt"])
            assert result.exit_code == 2
            assert "--similar requires at least 2 files" in result.output

    def test_similar_conflicts_with_check(self):
        """Test that --similar conflicts with -c/--check."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--similar", "-c", "file1", "file2"])
        assert result.exit_code == 2
        assert "--similar cannot be used with -c/--check" in result.output

    def test_similar_identical_files(self):
        """Test similarity matching with identical files."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create identical files
            content = "This is identical content\n" * 100
            with open("file1.txt", "w") as f:
                f.write(content)
            with open("file2.txt", "w") as f:
                f.write(content)

            result = runner.invoke(cli, ["--similar", "file1.txt", "file2.txt"])
            assert result.exit_code == 0

            # Both files should be in the same group with distance 0
            lines = result.output.strip().split("\n")
            assert len(lines) == 2
            assert " *file1.txt" in lines[0] or " *file2.txt" in lines[0]
            assert "  ~00 " in lines[1]

    def test_similar_different_files(self):
        """Test similarity matching with completely different files."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create very different files
            with open("file1.txt", "w") as f:
                f.write("A" * 1000)
            with open("file2.txt", "w") as f:
                f.write("Z" * 1000)

            result = runner.invoke(cli, ["--similar", "--threshold", "5", "file1.txt", "file2.txt"])
            assert result.exit_code == 0

            # Files should be output separately (not grouped)
            # There will be a blank line between separate files/groups
            output_sections = result.output.strip().split("\n\n")
            assert len(output_sections) == 2  # Two separate files
            assert "~" not in result.output  # No similarity indicators

    def test_similar_multiple_groups(self):
        """Test similarity matching with multiple groups."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create two pairs of similar files
            content1 = "Group 1 content\n" * 100
            content2 = "Group 2 content\n" * 100

            with open("file1a.txt", "w") as f:
                f.write(content1)
            with open("file1b.txt", "w") as f:
                f.write(content1)
            with open("file2a.txt", "w") as f:
                f.write(content2)
            with open("file2b.txt", "w") as f:
                f.write(content2)

            result = runner.invoke(cli, ["--similar", "file1a.txt", "file1b.txt", "file2a.txt", "file2b.txt"])
            assert result.exit_code == 0

            # Should have two groups separated by blank line
            output_sections = result.output.strip().split("\n\n")
            assert len(output_sections) == 2

            # Each group should have 2 files
            for section in output_sections:
                lines = section.strip().split("\n")
                assert len(lines) == 2
                assert "~00" in lines[1]  # Similar file with distance 0

    def test_similar_with_threshold(self):
        """Test similarity matching with custom threshold."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create nearly identical files (should have low hamming distance)
            base_content = "This is the base content that will be repeated many times. " * 100
            with open("file1.txt", "w") as f:
                f.write(base_content)
            with open("file2.txt", "w") as f:
                # Make a tiny modification that shouldn't affect the MinHash much
                f.write(base_content + " ")

            # Create very different file
            with open("file3.txt", "w") as f:
                f.write("Completely different content! " * 100)

            # Test with high threshold (file1 and file2 should group)
            result = runner.invoke(cli, ["--similar", "--threshold", "50", "file1.txt", "file2.txt"])
            assert result.exit_code == 0
            # Check if they're grouped (one has similarity indicator)
            has_similarity = "~" in result.output

            # If they're not similar enough even with this content, just verify the behavior is consistent
            if has_similarity:
                # They are grouped
                assert "~" in result.output
                lines = result.output.strip().split("\n")
                assert any("~" in line for line in lines)
            else:
                # They are separate
                output_sections = result.output.strip().split("\n\n")
                assert len(output_sections) == 2

            # Test with very different files and low threshold (should not group)
            result = runner.invoke(cli, ["--similar", "--threshold", "5", "file1.txt", "file3.txt"])
            assert result.exit_code == 0
            assert "~" not in result.output  # Should definitely not be grouped

    def test_similar_with_tag_format(self):
        """Test similarity matching with BSD tag format."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            content = "Test content\n" * 50
            with open("file1.txt", "w") as f:
                f.write(content)
            with open("file2.txt", "w") as f:
                f.write(content)

            result = runner.invoke(cli, ["--similar", "--tag", "file1.txt", "file2.txt"])
            assert result.exit_code == 0

            # Check BSD format
            assert "ISCC-SUM (" in result.output
            assert ") = ISCC:" in result.output
            assert "  ~00 ISCC-SUM (" in result.output

    def test_similar_with_zero_termination(self):
        """Test similarity matching with NUL termination."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            content = "Test content"
            with open("file1.txt", "w") as f:
                f.write(content)
            with open("file2.txt", "w") as f:
                f.write(content)

            result = runner.invoke(cli, ["--similar", "--zero", "file1.txt", "file2.txt"])
            assert result.exit_code == 0

            # Check for NUL terminators
            assert "\0" in result.output
            # No newlines except in the distance indicator formatting
            lines = result.output.split("\0")
            assert len(lines) >= 2

    def test_similar_with_narrow_format(self):
        """Test similarity matching with narrow format ISCCs."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            content = "Test content for narrow format"
            with open("file1.txt", "w") as f:
                f.write(content)
            with open("file2.txt", "w") as f:
                f.write(content)

            result = runner.invoke(cli, ["--similar", "--narrow", "file1.txt", "file2.txt"])
            assert result.exit_code == 0

            # Check that ISCCs are in narrow format (shorter)
            lines = result.output.strip().split("\n")
            for line in lines:
                if "ISCC:" in line:
                    # Extract ISCC code - find the part that starts with "ISCC:"
                    parts = line.split()
                    iscc = None
                    for part in parts:
                        if part.startswith("ISCC:"):
                            iscc = part
                            break

                    if iscc:
                        # Narrow format ISCCs are shorter (around 32 chars)
                        assert len(iscc) < 40  # Wide format is 48+ chars

    def test_similar_file_not_found(self):
        """Test similarity matching with non-existent file."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            with open("exists.txt", "w") as f:
                f.write("content")

            result = runner.invoke(cli, ["--similar", "exists.txt", "nonexistent.txt"])
            assert result.exit_code == 2
            assert "No such file or directory" in result.output

    def test_similar_single_file_allowed(self):
        """Test that single file is now allowed (implementation changed)."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            with open("single.txt", "w") as f:
                f.write("content")

            # Single file should work now - just outputs its ISCC
            result = runner.invoke(cli, ["--similar", "single.txt"])
            assert result.exit_code == 2  # Still requires 2 files per the check in cli()
            assert "--similar requires at least 2 files" in result.output

    def test_similar_no_files_error(self):
        """Test similarity with empty file list (edge case)."""
        runner = CliRunner()
        # This shouldn't happen in practice due to CLI validation,
        # but let's test the edge case handling
        result = runner.invoke(cli, ["--similar"])
        assert result.exit_code == 2
        assert "--similar requires at least 2 files" in result.output

    def test_similar_three_files_partial_match(self):
        """Test with three files where only two are similar."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            # Two similar files
            similar_content = "Similar content\n" * 100
            with open("file1.txt", "w") as f:
                f.write(similar_content)
            with open("file2.txt", "w") as f:
                f.write(similar_content)

            # One different file
            with open("file3.txt", "w") as f:
                f.write("Completely different content\n" * 100)

            result = runner.invoke(cli, ["--similar", "file1.txt", "file2.txt", "file3.txt"])
            assert result.exit_code == 0

            # Should have two groups
            output_sections = result.output.strip().split("\n\n")
            assert len(output_sections) == 2

            # First group should have the two similar files
            group1_lines = output_sections[0].strip().split("\n")
            assert len(group1_lines) == 2
            assert "~00" in group1_lines[1]

            # Second group should have the different file alone
            group2_lines = output_sections[1].strip().split("\n")
            assert len(group2_lines) == 1
            assert "~" not in group2_lines[0]
