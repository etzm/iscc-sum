#!/usr/bin/env python3
"""Profile isum execution with perf (Linux only)."""

import os
import subprocess
import sys
import tempfile
from pathlib import Path


def create_test_files():
    """Create test files of various sizes."""
    files = {}
    sizes = {
        "tiny": 1024,  # 1KB
        "small": 1024 * 1024,  # 1MB
        "medium": 10 * 1024 * 1024,  # 10MB
        "large": 100 * 1024 * 1024,  # 100MB
    }

    for name, size in sizes.items():
        with tempfile.NamedTemporaryFile(delete=False) as f:
            # Write random data
            f.write(os.urandom(size))
            files[name] = f.name

    return files


def profile_with_perf(binary_path, file_path):
    """Profile binary with perf stat."""
    cmd = ["perf", "stat", "-d", binary_path, file_path]

    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stderr  # perf outputs to stderr


def main():
    if not Path("./target/release/isum").exists():
        print("Error: Release binary not found. Run 'cargo build --release' first.")
        sys.exit(1)

    # Check if perf is available
    try:
        subprocess.run(["perf", "--version"], capture_output=True, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("Error: perf not available. Install with: sudo apt-get install linux-tools-common")
        sys.exit(1)

    print("ISUM Performance Profile")
    print("=" * 50)

    test_files = create_test_files()

    try:
        for size_name, file_path in test_files.items():
            print(f"\nProfiling {size_name} file...")
            output = profile_with_perf("./target/release/isum", file_path)

            # Extract key metrics
            lines = output.split("\n")
            for line in lines:
                if (
                    "task-clock" in line
                    or "cycles" in line
                    or "instructions" in line
                    or "branches" in line
                    or "cache" in line
                    or "seconds time elapsed" in line
                ):
                    print(f"  {line.strip()}")

    finally:
        # Cleanup
        for file_path in test_files.values():
            os.unlink(file_path)


if __name__ == "__main__":
    main()
