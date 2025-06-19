#!/usr/bin/env python3
# Example: Using iscc-sum for backup verification
# This script demonstrates how to create and verify checksums for backup archives

import os
import subprocess
import sys
from pathlib import Path

CHECKSUM_FILE = ".iscc-checksums"


def usage():
    print("Usage: backup-verification.py [create|verify] <directory>")
    print("  create - Generate checksums for all files in directory")
    print("  verify - Verify checksums against stored checksum file")
    sys.exit(1)


def find_files(directory):
    """Find all files in directory tree, excluding checksum file."""
    path = Path(directory)
    files = []
    for item in path.rglob("*"):
        if item.is_file() and item.name != CHECKSUM_FILE:
            files.append(str(item))
    return sorted(files)


def create_checksums(directory):
    """Create checksums for all files in directory."""
    print(f"Creating checksums for {directory}...")

    # Find all files
    files = find_files(directory)
    if not files:
        print("No files found in directory")
        return

    # Change to directory for consistent relative paths
    original_cwd = os.getcwd()
    os.chdir(directory)

    try:
        # Make file paths relative to current directory
        rel_files = [os.path.relpath(f, directory) for f in files]

        # Generate checksums
        result = subprocess.run(["iscc-sum"] + rel_files, capture_output=True, text=True, check=True)

        # Write to checksum file (now in current directory)
        Path(CHECKSUM_FILE).write_text(result.stdout)

        # Count files processed
        file_count = len(files)
        print(f"Created checksums for {file_count} files")
        print(f"Checksums saved to: {Path.cwd() / CHECKSUM_FILE}")

    except subprocess.CalledProcessError as e:
        print(f"Error generating checksums: {e.stderr}", file=sys.stderr)
        sys.exit(1)
    finally:
        os.chdir(original_cwd)


def verify_checksums(directory):
    """Verify checksums for directory."""
    print(f"Verifying checksums for {directory}...")

    checksum_path = Path(directory) / CHECKSUM_FILE

    # Check if checksum file exists
    if not checksum_path.exists():
        print(f"Error: No checksum file found at {checksum_path}")
        print(f"Run 'backup-verification.py create {directory}' first")
        sys.exit(1)

    # Change to directory for relative path verification
    original_cwd = os.getcwd()
    os.chdir(directory)

    try:
        # Verify checksums
        result = subprocess.run(["iscc-sum", "-c", CHECKSUM_FILE], capture_output=True, text=True)

        print(result.stdout, end="")

        if result.returncode == 0:
            print("\nAll files verified successfully!")
        else:
            print("\nVerification failed! Some files have changed or are missing.")
            sys.exit(1)

    except subprocess.CalledProcessError as e:
        print(f"Error verifying checksums: {e.stderr}", file=sys.stderr)
        sys.exit(1)
    finally:
        os.chdir(original_cwd)


def main():
    if len(sys.argv) != 3:
        usage()

    action = sys.argv[1]
    directory = sys.argv[2]

    # Check if directory exists
    if not Path(directory).is_dir():
        print(f"Error: Directory not found: {directory}", file=sys.stderr)
        sys.exit(1)

    if action == "create":
        create_checksums(directory)
    elif action == "verify":
        verify_checksums(directory)
    else:
        usage()


if __name__ == "__main__":
    main()
