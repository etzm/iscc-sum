#!/usr/bin/env python
# Dogfooding script for iscc-sum - generates and verifies ISCC hashes for the repository

import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import click

from iscc_sum import IsccSumProcessor
from iscc_sum.treewalk import treewalk_iscc

# Buffer size for reading files
IO_READ_SIZE = 1024 * 64  # 64KB chunks


def _hamming_distance(bits_a, bits_b):
    """Calculate hamming distance between two byte sequences.

    Args:
        bits_a: First byte sequence
        bits_b: Second byte sequence

    Returns:
        Number of differing bits
    """
    if len(bits_a) != len(bits_b):
        raise ValueError("Byte sequences must have equal length")

    distance = 0
    for a, b in zip(bits_a, bits_b):
        # XOR the bytes and count the number of 1 bits
        xor_result = a ^ b
        # Count bits set to 1 (Brian Kernighan's algorithm)
        while xor_result:
            distance += 1
            xor_result &= xor_result - 1

    return distance


def _extract_data_code_bits(units):
    """Extract Data-Code bits from units array.

    Args:
        units: List of ISCC units (Data-Code should be first)

    Returns:
        The raw Data-Code bits as bytes
    """
    import base64

    if not units or len(units) == 0:
        raise ValueError("No units found")

    # Data-Code is the first unit in the array
    data_code = units[0]

    # Remove ISCC: prefix and decode from base32
    iscc_clean = data_code.replace("ISCC:", "")

    # Pad to make length multiple of 8 for base32 decoding
    padding = (8 - len(iscc_clean) % 8) % 8
    iscc_padded = iscc_clean + "=" * padding

    # Decode from base32 (RFC4648)
    decoded = base64.b32decode(iscc_padded)

    # Skip the 2-byte header to get the actual Data-Code bits
    return decoded[2:]  # All bytes after the header


def find_repository_root() -> Path:
    """Find the repository root by looking for .git directory."""
    current = Path.cwd()
    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent
    # If no .git found, use current directory
    return Path.cwd()


def generate_iscc(root_path: Path) -> Dict[str, Any]:
    """Generate ISCC hash for all files in the repository.

    Args:
        root_path: Root directory to scan

    Returns:
        Dictionary with ISCC results and metadata
    """
    processor = IsccSumProcessor()
    file_count = 0

    # Process all files in the repository
    for file_path in treewalk_iscc(root_path):
        try:
            # Process file content
            with open(file_path, "rb") as f:
                while True:
                    chunk = f.read(IO_READ_SIZE)
                    if not chunk:
                        break
                    processor.update(chunk)

            file_count += 1

        except (IOError, OSError) as e:
            click.echo(f"Warning: Could not read {file_path}: {e}", err=True)
            continue

    # Get ISCC result with units - use wide mode
    result = processor.result(wide=True, add_units=True)

    # Convert result to dict - don't include file_count and repository
    result_dict = {
        "iscc": result["iscc"],
        "datahash": result["datahash"],
        "datasize": result["filesize"],  # Use datasize for clarity when processing trees
        "units": result["units"],
    }

    return result_dict


@click.group()
def cli():
    """Dogfooding tool for iscc-sum - generate and verify repository ISCC hashes."""
    pass


@cli.command()
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output path for .iscc.json file (default: <repo_root>/.iscc.json)",
)
def generate(output: Optional[Path]):
    """Generate ISCC hash for the repository and save to .iscc.json."""
    # Find repository root
    repo_root = find_repository_root()
    click.echo(f"Repository root: {repo_root}")

    # Determine output path
    if output is None:
        output = repo_root / ".iscc.json"

    # Generate ISCC
    click.echo("Generating ISCC hash for repository...")
    result = generate_iscc(repo_root)

    # Save to file with Linux line endings
    with open(output, "w", newline="\n") as f:
        json.dump(result, f, indent=2)

    click.echo(f"\nGenerated ISCC: {result['iscc']}")
    click.echo(f"Total size: {result['datasize']:,} bytes")
    click.echo(f"Data hash: {result['datahash']}")
    click.echo(f"Saved to: {output}")


@cli.command()
@click.option(
    "--file",
    "-f",
    type=click.Path(exists=True, path_type=Path),
    help="Path to .iscc.json file (default: <repo_root>/.iscc.json)",
)
def verify(file: Optional[Path]):
    """Verify repository against stored ISCC hash."""
    # Find repository root
    repo_root = find_repository_root()

    # Determine file path
    if file is None:
        file = repo_root / ".iscc.json"

    # Check if file exists
    if not file.exists():
        click.echo(f"Error: {file} not found. Run 'generate' first.", err=True)
        sys.exit(1)

    # Load stored data
    try:
        with open(file, "r") as f:
            stored_data = json.load(f)
    except json.JSONDecodeError as e:
        click.echo(f"Error: Invalid JSON in {file}: {e}", err=True)
        sys.exit(1)

    # Generate current ISCC
    click.echo("Calculating current repository ISCC...")
    current_data = generate_iscc(repo_root)

    # Compare results
    stored_iscc = stored_data.get("iscc", "")
    current_iscc = current_data["iscc"]

    click.echo(f"\nStored ISCC:  {stored_iscc}")
    click.echo(f"Current ISCC: {current_iscc}")

    if stored_iscc == current_iscc:
        click.echo("\n✓ Repository matches stored ISCC")
        sys.exit(0)
    else:
        click.echo("\n✗ Repository has changed", err=True)

        # Calculate hamming distance for data-code units
        try:
            # Extract data-code bits from units arrays
            stored_units = stored_data.get("units", [])
            current_units = current_data.get("units", [])

            stored_bits = _extract_data_code_bits(stored_units)
            current_bits = _extract_data_code_bits(current_units)

            distance = _hamming_distance(stored_bits, current_bits)
            click.echo(f"\nData-Code hamming distance: {distance}")
        except Exception as e:
            # If we can't calculate hamming distance, just skip it
            click.echo(f"\nCould not calculate hamming distance: {e}", err=True)

        sys.exit(1)


if __name__ == "__main__":
    # If no arguments provided, default to generate
    if len(sys.argv) == 1:
        sys.argv.append("generate")

    cli()
