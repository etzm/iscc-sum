"""
Python implementation of code_iscc_sum using Rust-based IsccSumProcessor.

This module provides a Python wrapper around the Rust IsccSumProcessor that handles
file I/O at the Python level, enabling support for various input sources through
fsspec/upath while maintaining high performance for the core processing.
"""

from upath import UPath

from iscc_sum import IsccSumProcessor

# File I/O Configuration
IO_READ_SIZE = 2097152  # 2MB chunks for efficient file reading


def code_iscc_sum(uri, wide=False, add_units=True):
    # type: (str, bool, bool) -> dict
    """
    Generate an ISCC-CODE SUM for a file using Python I/O and Rust processing.

    This function handles file reading at the Python level using upath/fsspec,
    which enables support for various input sources (local files, URLs, S3, etc.),
    while using the high-performance Rust IsccSumProcessor for the actual processing.

    :param uri: Path or fsspec URL to the file to process
    :param wide: If True, generates 128-bit codes (256-bit total); if False, 64-bit codes (128-bit total)
    :param add_units: If True, includes individual Data-Code and Instance-Code units in the result
    :return: Dictionary containing:
        - iscc: The composite ISCC-CODE SUM identifier
        - datahash: Blake3 multihash of the file content
        - filesize: Size of the file in bytes
        - units: List of individual ISCC units [Data-Code, Instance-Code] (if add_units=True)
    """
    processor = IsccSumProcessor()
    path = UPath(uri)

    with path.open("rb") as stream:
        data = stream.read(IO_READ_SIZE)
        while data:
            processor.update(data)
            data = stream.read(IO_READ_SIZE)

    return processor.result(wide=wide, add_units=add_units)
