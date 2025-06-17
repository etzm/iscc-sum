# Command-line interface for iscc-sum tool

import sys
from importlib.metadata import PackageNotFoundError, version
from typing import Iterator

import click

# Constants
IO_READ_SIZE = 2097152  # 2MB chunk size

# Exit codes
EXIT_SUCCESS = 0
EXIT_VERIFICATION_FAILURE = 1
EXIT_ERROR = 2


def get_version():
    # type: () -> str
    """Get the version of iscc-sum package."""
    try:
        return version("iscc-sum")
    except PackageNotFoundError:
        return "0.1.0-alpha.1"  # Fallback version


@click.command(
    context_settings={"help_option_names": ["-h", "--help"]},
    epilog="Exit status: 0 if OK, 1 if checksum verification fails, 2 if trouble.",
)
@click.version_option(version=get_version(), prog_name="iscc-sum")
@click.option(
    "-c",
    "--check",
    is_flag=True,
    help="Read checksums from FILEs and verify them",
)
@click.option(
    "--tag",
    is_flag=True,
    help="Create a BSD-style checksum output",
)
@click.option(
    "-z",
    "--zero",
    is_flag=True,
    help="End each output line with NUL, not newline",
)
@click.option(
    "-q",
    "--quiet",
    is_flag=True,
    help="Don't print OK for successfully verified files",
)
@click.option(
    "--status",
    is_flag=True,
    help="Don't output anything, status code shows success",
)
@click.option(
    "-w",
    "--warn",
    is_flag=True,
    help="Warn about improperly formatted checksum lines",
)
@click.option(
    "--strict",
    is_flag=True,
    help="Exit non-zero for improperly formatted checksum lines",
)
@click.option(
    "--narrow",
    is_flag=True,
    help="Generate narrow format (2×64-bit ISO 24138:2024 conformant) (default: 2×128-bit extended format)",
)
@click.option(
    "--units",
    is_flag=True,
    help="Include individual Data-Code and Instance-Code units in output (verification mode: ignored)",
)
@click.option(
    "--similar",
    is_flag=True,
    help="Group files by similarity based on Data-Code hamming distance",
)
@click.option(
    "--threshold",
    type=click.IntRange(min=0),
    default=12,
    show_default=True,
    help="Maximum hamming distance for similarity matching",
)
@click.argument("files", nargs=-1, type=click.Path())
def cli(
    check,
    tag,
    zero,
    quiet,
    status,
    warn,
    strict,
    narrow,
    units,
    similar,
    threshold,
    files,
):
    # type: (bool, bool, bool, bool, bool, bool, bool, bool, bool, bool, int, tuple) -> None
    """Compute ISCC (International Standard Content Code) checksums for files.

    Each checksum consists of a 2-byte self-describing header followed by a
    composite of Data-Code and Instance-Code (BLAKE3) components. All files
    are processed as binary data.

    Unlike traditional checksum tools that only verify exact matches, iscc-sum
    enables similarity detection between files through the Data-Code component.
    Files with similar content will have similar Data-Codes, allowing similarity
    matching based on hamming distance.

    \b
    Examples:
      # Generate checksums
      iscc-sum document.pdf
      iscc-sum *.txt

      # Verify checksums
      iscc-sum -c checksums.txt

      # Find similar files
      iscc-sum --similar *.jpg
    """
    # Validate conflicting options
    if similar and check:
        click.echo("iscc-sum: --similar cannot be used with -c/--check", err=True)
        sys.exit(EXIT_ERROR)

    if similar and len(files) < 2:
        click.echo("iscc-sum: --similar requires at least 2 files to compare", err=True)
        sys.exit(EXIT_ERROR)

    try:
        if check:
            # Verification mode
            _handle_verification(files, quiet, status, warn, strict)
        elif similar:
            # Similarity matching mode
            _handle_similarity(files, threshold, narrow, tag, zero)
        else:
            # Normal checksum generation mode
            _handle_checksum_generation(files, narrow, units, tag, zero)
    except Exception as e:
        click.echo(f"iscc-sum: {e}", err=True)
        sys.exit(EXIT_ERROR)

    sys.exit(EXIT_SUCCESS)


def _expand_paths(paths):
    # type: (tuple) -> Iterator[str]
    """Expand file and directory paths to individual file paths.

    For file paths, yield as-is. For directory paths, use treewalk_iscc
    to get all files in deterministic order.

    Args:
        paths: Tuple of file/directory paths

    Yields:
        Individual file paths
    """
    import os
    from pathlib import Path

    from iscc_sum.treewalk import treewalk_iscc

    for path in paths:
        path_obj = Path(path)

        # Check if path exists
        if not path_obj.exists():
            raise IOError(f"No such file or directory: '{path}'")

        if path_obj.is_file():
            # Yield file path as-is
            yield str(path_obj)
        elif path_obj.is_dir():
            # Use treewalk_iscc for deterministic directory traversal
            for file_path in treewalk_iscc(path_obj):
                yield str(file_path)
        else:
            # Not a regular file or directory (e.g., device, pipe)
            raise IOError(f"Not a regular file or directory: '{path}'")


def _handle_checksum_generation(files, narrow, units, tag, zero):
    # type: (tuple, bool, bool, bool, bool) -> None
    """Handle normal checksum generation mode."""
    import os

    from iscc_sum import IsccSumProcessor

    if not files:
        # Read from stdin
        files = ("-",)

    for filepath in files:
        try:
            processor = IsccSumProcessor()

            # Handle stdin
            if filepath == "-":
                # Use binary buffer for stdin
                stdin = sys.stdin.buffer

                while True:
                    chunk = stdin.read(IO_READ_SIZE)
                    if not chunk:
                        break
                    processor.update(chunk)

                display_name = "-"
            else:
                # Handle regular file
                with open(filepath, "rb") as f:
                    while True:
                        chunk = f.read(IO_READ_SIZE)
                        if not chunk:
                            break
                        processor.update(chunk)

                display_name = filepath

            # Get result
            result = processor.result(wide=not narrow, add_units=units)

            # Format output
            terminator = "\0" if zero else "\n"

            if tag:
                # BSD-style output
                output = "ISCC-SUM ({}) = {}".format(display_name, result.iscc)
            else:
                # Default output format
                output = "{} *{}".format(result.iscc, display_name)

            click.echo(output, nl=False)
            click.echo(terminator, nl=False)

            # Display units if requested
            if units and result.units:
                for unit in result.units:
                    unit_output = "  {}".format(unit)
                    click.echo(unit_output, nl=False)
                    click.echo(terminator, nl=False)

        except IOError as e:
            error_msg = "iscc-sum: {}: {}".format(filepath, str(e))
            click.echo(error_msg, err=True)
            sys.exit(EXIT_ERROR)
        except Exception as e:
            error_msg = "iscc-sum: {}: unexpected error: {}".format(filepath, str(e))
            click.echo(error_msg, err=True)
            sys.exit(EXIT_ERROR)


def _parse_checksum_line(line):
    # type: (str) -> tuple | None
    """Parse a checksum line in either default or BSD format.

    Returns (iscc_code, filename) tuple or None if invalid format.
    """
    import re

    # BSD format: ISCC-SUM (filename) = ISCC:xxx
    bsd_match = re.match(r"^ISCC-SUM \((.+)\) = (ISCC:[A-Z0-9]+)$", line)
    if bsd_match:
        return bsd_match.group(2), bsd_match.group(1)

    # Default format: ISCC:xxx *filename
    default_match = re.match(r"^(ISCC:[A-Z0-9]+) \*(.+)$", line)
    if default_match:
        return default_match.group(1), default_match.group(2)

    return None


def _handle_verification(files, quiet, status, warn, strict):
    # type: (tuple, bool, bool, bool, bool) -> None
    """Handle checksum verification mode."""
    import os

    from iscc_sum import IsccSumProcessor

    if not files:
        click.echo("iscc-sum: no checksum file specified", err=True)
        sys.exit(EXIT_ERROR)

    total_files = 0
    failed_files = 0
    missing_files = 0
    format_errors = 0

    for checksum_file in files:
        try:
            with open(checksum_file, "r", encoding="utf-8") as f:
                line_number = 0
                for line in f:
                    line_number += 1
                    line = line.rstrip("\n\r")

                    if not line:
                        continue

                    # Parse the checksum line
                    parsed = _parse_checksum_line(line)
                    if parsed is None:
                        format_errors += 1
                        if warn:
                            click.echo(
                                f"iscc-sum: {checksum_file}: {line_number}: "
                                f"improperly formatted ISCC checksum line",
                                err=True,
                            )
                        if strict:
                            sys.exit(EXIT_ERROR)
                        continue

                    expected_iscc, filename = parsed
                    total_files += 1

                    # Check if file exists
                    if not os.path.exists(filename):
                        missing_files += 1
                        if not status:
                            click.echo(f"iscc-sum: {filename}: No such file or directory")
                        failed_files += 1
                        continue

                    # Calculate actual checksum
                    try:
                        processor = IsccSumProcessor()
                        with open(filename, "rb") as target_file:
                            while True:
                                chunk = target_file.read(IO_READ_SIZE)
                                if not chunk:
                                    break
                                processor.update(chunk)

                        # Determine if expected is narrow or wide format
                        is_narrow = len(expected_iscc) < 35
                        result = processor.result(wide=not is_narrow, add_units=False)
                        actual_iscc = result.iscc

                        # Compare checksums
                        if actual_iscc == expected_iscc:
                            if not quiet and not status:
                                click.echo(f"{filename}: OK")
                        else:
                            failed_files += 1
                            if not status:
                                click.echo(f"{filename}: FAILED")

                    except IOError as e:
                        failed_files += 1
                        if not status:
                            click.echo(f"iscc-sum: {filename}: {e}")

        except IOError as e:
            click.echo(f"iscc-sum: {checksum_file}: {e}", err=True)
            sys.exit(EXIT_ERROR)

    # Display summary if there were any issues
    if not status and (failed_files > 0 or format_errors > 0):
        if format_errors > 0:
            click.echo(f"iscc-sum: WARNING: {format_errors} line(s) improperly formatted", err=True)
        if failed_files > 0:
            click.echo(f"iscc-sum: WARNING: {failed_files} computed checksum(s) did NOT match", err=True)

    # Exit with appropriate code
    if failed_files > 0:
        sys.exit(EXIT_VERIFICATION_FAILURE)


def _extract_data_code_bits(iscc_string, narrow):
    # type: (str, bool) -> bytes
    """Extract Data-Code bits from an ISCC string.

    Args:
        iscc_string: The ISCC string (e.g., "ISCC:KAD4...")
        narrow: Whether this is a narrow format ISCC

    Returns:
        The raw Data-Code bits as bytes
    """
    import base64

    # Remove ISCC: prefix and decode from base32
    iscc_clean = iscc_string.replace("ISCC:", "")

    # Pad to make length multiple of 8 for base32 decoding
    padding = (8 - len(iscc_clean) % 8) % 8
    iscc_padded = iscc_clean + "=" * padding

    # Decode from base32 (RFC4648)
    # ISCC codes should always decode properly with correct padding
    decoded = base64.b32decode(iscc_padded)

    # Skip the 2-byte header
    # Data-Code is the first component after header
    if narrow:
        # Narrow format: 64-bit Data-Code (8 bytes)
        return decoded[2:10]  # bytes 2-9
    else:
        # Extended format: 128-bit Data-Code (16 bytes)
        return decoded[2:18]  # bytes 2-17


def _hamming_distance(bits_a, bits_b):
    # type: (bytes, bytes) -> int
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


def _handle_similarity(files, threshold, narrow, tag, zero):
    # type: (tuple, int, bool, bool, bool) -> None
    """Handle similarity matching mode."""
    from iscc_sum import IsccSumProcessor

    # Process all files and compute their ISCCs
    file_data = []  # List of (filepath, iscc, data_code_bits)

    for filepath in files:
        try:
            # Process file to get ISCC
            processor = IsccSumProcessor()
            with open(filepath, "rb") as f:
                while True:
                    chunk = f.read(IO_READ_SIZE)
                    if not chunk:
                        break
                    processor.update(chunk)

            result = processor.result(wide=not narrow, add_units=False)

            # Extract Data-Code bits from ISCC for comparison
            data_code_bits = _extract_data_code_bits(result.iscc, narrow)
            file_data.append((filepath, result.iscc, data_code_bits))

        except IOError as e:
            click.echo(f"iscc-sum: {filepath}: {e}", err=True)
            sys.exit(EXIT_ERROR)

    # The CLI already validates that we have at least 2 files,
    # so we don't need to handle empty or single file cases

    # Find similar files for each reference file
    processed = set()  # Track which files have been output
    group_count = 0

    for i, (ref_path, ref_iscc, ref_bits) in enumerate(file_data):
        if ref_path in processed:
            continue

        # Find all files similar to this reference file
        similar_files = []

        for j, (comp_path, comp_iscc, comp_bits) in enumerate(file_data):
            if i == j:  # Skip self-comparison
                continue

            # Calculate hamming distance
            distance = _hamming_distance(ref_bits, comp_bits)

            if distance <= threshold:
                similar_files.append((comp_path, comp_iscc, distance))
                processed.add(comp_path)

        # If this file has similar files, output the group
        if similar_files:
            # Add blank line between groups (except before first group)
            if group_count > 0:
                if not zero:
                    click.echo()

            group_count += 1

            # Output reference file
            _output_checksum(ref_iscc, ref_path, tag, zero)
            processed.add(ref_path)

            # Sort similar files by hamming distance (ascending)
            similar_files.sort(key=lambda x: x[2])

            # Output similar files with distance indicator
            for sim_path, sim_iscc, distance in similar_files:
                if tag:
                    output = f"  ~{distance:02d} ISCC-SUM ({sim_path}) = {sim_iscc}"
                else:
                    output = f"  ~{distance:02d} {sim_iscc} *{sim_path}"

                click.echo(output, nl=not zero)
                if zero:
                    click.echo("\0", nl=False)

        # If this file has no similar files but hasn't been processed, output it alone
        elif ref_path not in processed:
            # Add blank line between groups (except before first group)
            if group_count > 0:
                if not zero:
                    click.echo()

            group_count += 1

            _output_checksum(ref_iscc, ref_path, tag, zero)
            processed.add(ref_path)


def _output_checksum(iscc, filepath, tag, zero):
    # type: (str, str, bool, bool) -> None
    """Output a checksum in the specified format."""
    if tag:
        output = f"ISCC-SUM ({filepath}) = {iscc}"
    else:
        output = f"{iscc} *{filepath}"

    click.echo(output, nl=not zero)
    if zero:
        click.echo("\0", nl=False)


if __name__ == "__main__":
    cli()
