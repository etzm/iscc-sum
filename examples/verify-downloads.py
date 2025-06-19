#!/usr/bin/env python3
# Example: Verify downloaded files using iscc-sum
# This script demonstrates automated download verification

import os
import subprocess
import sys
import tempfile
import urllib.request


def download_file(url, output_path):
    """Download a file from URL."""
    print(f"Downloading: {url}")
    try:
        urllib.request.urlretrieve(url, output_path)
        print(f"Downloaded to: {output_path}")
        return True
    except Exception as e:
        print(f"Download failed: {e}", file=sys.stderr)
        return False


def calculate_checksum(filepath):
    """Calculate ISCC checksum for a file."""
    try:
        result = subprocess.run(["iscc-sum", filepath], capture_output=True, text=True, check=True)
        # Extract just the checksum from output
        checksum = result.stdout.strip().split()[0]
        return checksum
    except subprocess.CalledProcessError as e:
        print(f"Checksum calculation failed: {e.stderr}", file=sys.stderr)
        return None


def verify_checksum(filepath, expected_checksum):
    """Verify file against expected checksum."""
    # Create temporary checksum file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".checksums", delete=False) as f:
        f.write(f"{expected_checksum} *{filepath}\n")
        temp_checksum_file = f.name

    try:
        # Run verification
        result = subprocess.run(["iscc-sum", "-c", temp_checksum_file], capture_output=True, text=True)

        return result.returncode == 0, result.stdout + result.stderr
    finally:
        os.unlink(temp_checksum_file)


def main():
    if len(sys.argv) < 2:
        print("Usage: verify-downloads.py <mode> [args...]")
        print("\nModes:")
        print("  generate <file>           - Generate checksum for a file")
        print("  download <url> <checksum> - Download and verify file")
        print("  verify <file> <checksum>  - Verify existing file")
        print("\nExamples:")
        print("  verify-downloads.py generate document.pdf")
        print("  verify-downloads.py download https://example.com/file.zip ISCC:KAC...")
        print("  verify-downloads.py verify file.zip ISCC:KAC...")
        sys.exit(1)

    mode = sys.argv[1]

    if mode == "generate":
        if len(sys.argv) < 3:
            print("Error: Missing file argument", file=sys.stderr)
            sys.exit(1)

        filepath = sys.argv[2]
        if not os.path.exists(filepath):
            print(f"Error: File not found: {filepath}", file=sys.stderr)
            sys.exit(1)

        checksum = calculate_checksum(filepath)
        if checksum:
            print(f"\nFile: {filepath}")
            print(f"ISCC: {checksum}")
            print("\nShare this checksum with the file for verification")

    elif mode == "download":
        if len(sys.argv) < 4:
            print("Error: Missing URL or checksum argument", file=sys.stderr)
            sys.exit(1)

        url = sys.argv[2]
        expected_checksum = sys.argv[3]

        # Extract filename from URL or use temp name
        filename = os.path.basename(url) or "download.tmp"

        print("\nDownload and Verify Operation")
        print(f"URL: {url}")
        print(f"Expected ISCC: {expected_checksum}")
        print("-" * 50)

        # Download file
        if download_file(url, filename):
            # Calculate actual checksum
            actual_checksum = calculate_checksum(filename)
            if actual_checksum:
                print(f"\nActual ISCC: {actual_checksum}")

                # Verify
                success, output = verify_checksum(filename, expected_checksum)

                if success:
                    print("\n✓ Verification PASSED - File is authentic")
                else:
                    print("\n✗ Verification FAILED - File may be corrupted or modified")
                    print(output)
                    # Optionally remove failed download
                    response = input("\nDelete corrupted file? [y/N] ")
                    if response.lower() == "y":
                        os.unlink(filename)
                        print("File deleted")

    elif mode == "verify":
        if len(sys.argv) < 4:
            print("Error: Missing file or checksum argument", file=sys.stderr)
            sys.exit(1)

        filepath = sys.argv[2]
        expected_checksum = sys.argv[3]

        if not os.path.exists(filepath):
            print(f"Error: File not found: {filepath}", file=sys.stderr)
            sys.exit(1)

        print(f"\nVerifying: {filepath}")
        print(f"Expected ISCC: {expected_checksum}")

        success, output = verify_checksum(filepath, expected_checksum)

        if success:
            print("\n✓ Verification PASSED")
        else:
            print("\n✗ Verification FAILED")
            print(output)

    else:
        print(f"Error: Unknown mode: {mode}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
