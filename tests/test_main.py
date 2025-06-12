# Tests for main functionality

import subprocess
import sys

from iscc_sum import hello_from_bin, main


def test_hello_from_bin():
    # type: () -> None
    """Test that hello_from_bin returns expected message."""
    result = hello_from_bin()
    assert result == "hello iscc-sum"
    assert "iscc-sum" in result


def test_main_function(capsys):
    # type: (pytest.CaptureFixture[str]) -> None
    """Test that main function prints expected output."""
    main()
    captured = capsys.readouterr()
    assert captured.out.strip() == "hello iscc-sum"


def test_cli_command():
    # type: () -> None
    """Test CLI command execution."""
    result = subprocess.run(
        [sys.executable, "-m", "iscc_sum"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == "hello iscc-sum"
    assert result.returncode == 0
