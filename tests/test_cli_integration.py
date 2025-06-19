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
        binary_name = "isum.exe"
    else:
        binary_name = "isum"

    # Check release build first
    release_path = root_dir / "target" / "release" / binary_name
    if release_path.exists():
        return str(release_path)

    # Check debug build
    debug_path = root_dir / "target" / "debug" / binary_name
    if debug_path.exists():
        return str(debug_path)

    # If not found, try to build it
    subprocess.run(["cargo", "build", "--release", "--bin", "isum"], check=True)
    if release_path.exists():
        return str(release_path)

    raise FileNotFoundError(f"Could not find {binary_name} binary")


# TODO: Implement actual CLI functionality and uncomment these tests
# def test_rust_binary_basic_execution():
#     # type: () -> None
#     """Test that the Rust binary executes without errors."""
#     binary_path = get_rust_binary_path()
#     result = subprocess.run(
#         [binary_path],
#         capture_output=True,
#         text=True,
#     )
#     assert result.returncode == 0
#     # TODO: Update assertions when CLI is implemented


# def test_rust_binary_help_flag():
#     # type: () -> None
#     """Test that help flag works (when implemented)."""
#     binary_path = get_rust_binary_path()
#     result = subprocess.run(
#         [binary_path, "--help"],
#         capture_output=True,
#         text=True,
#     )
#     # TODO: Update assertions when --help is implemented


# def test_python_cli_entry_point():
#     # type: () -> None
#     """Test Python CLI entry point via -m flag."""
#     result = subprocess.run(
#         [sys.executable, "-m", "iscc_sum"],
#         capture_output=True,
#         text=True,
#     )
#     # TODO: Update assertions when CLI is implemented


# def test_python_cli_with_args():
#     # type: () -> None
#     """Test Python CLI with arguments (when implemented)."""
#     result = subprocess.run(
#         [sys.executable, "-m", "iscc_sum", "--help"],
#         capture_output=True,
#         text=True,
#     )
#     # TODO: Update assertions when argument parsing is implemented


# def test_rust_binary_file_not_found():
#     # type: () -> None
#     """Test Rust binary behavior with non-existent file (when implemented)."""
#     binary_path = get_rust_binary_path()
#     result = subprocess.run(
#         [binary_path, "nonexistent.txt"],
#         capture_output=True,
#         text=True,
#     )
#     # TODO: Update assertions when file processing is implemented


# def test_binary_environment_variables():
#     # type: () -> None
#     """Test that binary respects environment variables (when applicable)."""
#     binary_path = get_rust_binary_path()
#     env = os.environ.copy()
#     env["RUST_LOG"] = "debug"
#
#     result = subprocess.run(
#         [binary_path],
#         capture_output=True,
#         text=True,
#         env=env,
#     )
#     # TODO: Update assertions when environment variable handling is implemented
