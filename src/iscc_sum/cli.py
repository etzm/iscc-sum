# Command-line interface for iscc-sum tool

import sys
from importlib.metadata import PackageNotFoundError, version

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
def cli(check, tag, zero, quiet, status, warn, strict, narrow, units, similar, threshold, files):
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


def _handle_verification(files, quiet, status, warn, strict):
    # type: (tuple, bool, bool, bool, bool) -> None
    """Handle checksum verification mode."""
    click.echo("iscc-sum: verification mode not yet implemented", err=True)
    sys.exit(EXIT_ERROR)


def _handle_similarity(files, threshold, narrow, tag, zero):
    # type: (tuple, int, bool, bool, bool) -> None
    """Handle similarity matching mode."""
    click.echo("iscc-sum: similarity mode not yet implemented", err=True)
    sys.exit(EXIT_ERROR)


if __name__ == "__main__":
    cli()
