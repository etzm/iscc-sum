# Test for UTF-8 BOM handling in verification
"""Test UTF-8 BOM handling in checksum verification."""

from click.testing import CliRunner

from iscc_sum.cli import cli


def test_verification_utf8_bom():
    # type: () -> None
    """Test verification with UTF-8 BOM in checksum file."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create a checksum file with UTF-8 BOM
        with open("checksums.txt", "wb") as f:
            # Write UTF-8 BOM followed by checksum content
            f.write(b"\xef\xbb\xbf")  # UTF-8 BOM
            f.write(b"ISCC:K4AFR3TDMMLKANIODTGGCF7AS4ZCBZLDGG4ASLMEJB2AIB6CWWWOB3I *test.txt\n")

        # Create the test file
        with open("test.txt", "wb") as f:
            f.write(b"Test content for BOM handling")

        # Run verification
        result = runner.invoke(cli, ["-c", "checksums.txt"])

        # Should succeed and handle BOM correctly
        assert result.exit_code == 0
        assert "test.txt: OK" in result.output
