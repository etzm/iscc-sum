# Test for __main__.py module coverage

import subprocess
import sys


def test_main_module_execution():
    # type: () -> None
    """Test that __main__.py module executes correctly."""
    result = subprocess.run(
        [sys.executable, "-m", "iscc_sum", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Usage:" in result.stdout or "usage:" in result.stdout
    assert "iscc-sum" in result.stdout.lower()
