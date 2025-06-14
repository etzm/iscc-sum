"""
ISO Reference Implementation of ISCC-CODE SubType SUM (Composite ISCC including only Data- and Instance-Code).

This module implements the ISCC-CODE SUM algorithm as specified in ISO 24138:2024. It generates
a composite ISCC that combines Data-Code (bitstream similarity) and Instance-Code (cryptographic) hashes
in a single identifier.

The ISCC-CODE SUM provides:
- Bitstream similarity detection via Data-Code (using CDC and MinHash)
- Cryptographic integrity verification via Instance-Code (using Blake3)
- Single-pass processing for efficient file handling
- Canonical representation in Base32 encoding

This reference implementation serves as a blueprint for the high-performance Rust implementation
and ensures compliance with the ISO standard. It is not used in production code.
"""

from base64 import b32encode

from upath import UPath

from iscc_sum.code_data_ref import DataHasher
from iscc_sum.code_instance_ref import InstanceHasher

# ISCC Header Components (binary strings)
ISCC_MAINTYPE = "0101"  # Main type: ISCC (composite code)
ISCC_SUBTYPE = "0101"  # Sub type: SUM (composite ISCC including only Data- and Instance-Code)
ISCC_SUBTYPE_W = "0111"  # Sub type: SUM with wide format (128-bit Data- and Instance-Code)
ISCC_VERSION = "0000"  # Version: V0 (initial version)
ISCC_LENGTH = "0000"  # Length: none (no optional units before Data and Instance units)

# File I/O Configuration
IO_READ_SIZE = 2097152  # 2MB chunks for efficient file reading


def code_iscc_sum(file, wide=False, add_units=True):
    # type: (str, bool, bool) -> dict
    """
    Generate an ISCC-CODE SUM for a file using single-pass processing.

    This function reads a file once and simultaneously generates both Data-Code (content-based)
    and Instance-Code (cryptographic) components, then combines them into a composite ISCC-CODE SUM.

    :param file: Path or fsspec URL to the file to process
    :param wide: If True, generates 128-bit codes (256-bit total); if False, 64-bit codes (128-bit total)
    :param add_units: If True, includes individual Data-Code and Instance-Code units in the result
    :return: Dictionary containing:
        - iscc: The composite ISCC-CODE SUM identifier
        - datahash: Blake3 multihash of the file content
        - filesize: Size of the file in bytes
        - units: List of individual ISCC units [Data-Code, Instance-Code] (if add_units=True)
    """
    dh = DataHasher()
    ih = InstanceHasher()
    path = UPath(file)

    with path.open("rb") as stream:
        data = stream.read(IO_READ_SIZE)
        while data:
            dh.push(data)
            ih.push(data)
            data = stream.read(IO_READ_SIZE)

    # Build ISCC Header
    subtype = ISCC_SUBTYPE_W if wide else ISCC_SUBTYPE
    header_int = int(ISCC_MAINTYPE + subtype + ISCC_VERSION + ISCC_LENGTH, 2)
    header = header_int.to_bytes(2, byteorder="big")

    # Build ISCC Body
    data_code_unit = dh.digest()
    instance_code_unit = ih.digest()
    unit_bytes = 128 // 8 if wide else 64 // 8
    body = data_code_unit[:unit_bytes] + instance_code_unit[:unit_bytes]

    # Construct ISCC-CODE SUM
    iscc_code = f"ISCC:{encode_base32(header + body)}"

    result = dict(
        iscc=iscc_code,
        datahash=ih.multihash(),
        filesize=ih.filesize,
    )

    if add_units:
        result["units"] = [f"ISCC:{dh.code(bits=256)}", f"ISCC:{ih.code(bits=256)}"]

    return result


def encode_base32(data):
    # type: (bytes) -> str
    """
    Encode binary data as Base32 without padding.

    Uses standard RFC4648 Base32 encoding and removes any trailing padding characters.
    This encoding is used for ISCC codes to ensure they are URL-safe and human-readable.

    :param data: Binary data to encode
    :return: Base32 encoded string without padding
    """
    return b32encode(data).decode("ascii").rstrip("=")
