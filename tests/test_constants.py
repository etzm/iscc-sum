# -*- coding: utf-8 -*-
import subprocess
import sys


def test_constants_main():
    """Test the main block in constants.py to cover lines 394-399."""
    # Run the module as a script
    result = subprocess.run([sys.executable, "-m", "iscc_sum.constants"], capture_output=True, text=True)

    # Check that it ran successfully
    assert result.returncode == 0

    # Check that it printed the expected output
    assert "MPA:" in result.stdout
    assert "MPB:" in result.stdout
    assert "CDC_GEAR:" in result.stdout
    assert "maxbits" in result.stdout
