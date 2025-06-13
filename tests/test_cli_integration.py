# CLI integration tests for iscc-sum

import os
import subprocess
import sys
from pathlib import Path


def get_rust_binary_path():
    # type: () -> str
    """Get the path to the compiled Rust binary."""
    # Try to find the binary in the target/release directory
    root_dir = Path(__file__).parent.parent
    if sys.platform == "win32":
        binary_name = "iscc-sum.exe"
    else:
        binary_name = "iscc-sum"

    # Check release build first
    release_path = root_dir / "target" / "release" / binary_name
    if release_path.exists():
        return str(release_path)

    # Check debug build
    debug_path = root_dir / "target" / "debug" / binary_name
    if debug_path.exists():
        return str(debug_path)

    # If not found, try to build it
    subprocess.run(["cargo", "build", "--release", "--bin", "iscc-sum"], check=True)
    if release_path.exists():
        return str(release_path)

    raise FileNotFoundError(f"Could not find {binary_name} binary")


def test_rust_binary_basic_execution():
    # type: () -> None
    """Test that the Rust binary executes without errors."""
    binary_path = get_rust_binary_path()
    result = subprocess.run(
        [binary_path],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "hello iscc-sum"
    assert result.stderr == ""


def test_rust_binary_help_flag():
    # type: () -> None
    """Test that help flag works (when implemented)."""
    binary_path = get_rust_binary_path()
    # Currently the binary doesn't support --help, so we just test current behavior
    result = subprocess.run(
        [binary_path, "--help"],
        capture_output=True,
        text=True,
    )
    # For now it just prints the same message
    # TODO: Update when --help is implemented
    assert result.stdout.strip() == "hello iscc-sum"


def test_python_cli_entry_point():
    # type: () -> None
    """Test Python CLI entry point via -m flag."""
    result = subprocess.run(
        [sys.executable, "-m", "iscc_sum"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "hello iscc-sum"
    assert result.stderr == ""


def test_python_cli_with_args():
    # type: () -> None
    """Test Python CLI with arguments (when implemented)."""
    # Currently doesn't accept arguments, just test it doesn't crash
    result = subprocess.run(
        [sys.executable, "-m", "iscc_sum", "--help"],
        capture_output=True,
        text=True,
    )
    # For now it ignores arguments
    # TODO: Update when argument parsing is implemented
    assert result.stdout.strip() == "hello iscc-sum"


def test_rust_binary_file_not_found():
    # type: () -> None
    """Test Rust binary behavior with non-existent file (when implemented)."""
    binary_path = get_rust_binary_path()
    # Currently doesn't accept file arguments, just test current behavior
    result = subprocess.run(
        [binary_path, "nonexistent.txt"],
        capture_output=True,
        text=True,
    )
    # TODO: Update when file processing is implemented
    assert result.stdout.strip() == "hello iscc-sum"


def test_binary_environment_variables():
    # type: () -> None
    """Test that binary respects environment variables (when applicable)."""
    binary_path = get_rust_binary_path()
    env = os.environ.copy()
    env["RUST_LOG"] = "debug"

    result = subprocess.run(
        [binary_path],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0
    # Currently doesn't use logging, but shouldn't crash
    assert result.stdout.strip() == "hello iscc-sum"
