"""
ISO Reference Implementation of ISCC Instance-Code

This module serves only as reference for correctness and performance of the actual Instance-Code
implementation. The library does not use this code.
"""

import mmap
from base64 import b32encode
from io import BufferedReader, BytesIO
from typing import BinaryIO, Optional, Union

from blake3 import blake3

__all__ = [
    "gen_instance_code",
]

INSTANCE_BITS = 64
INSTANCE_IO_READ_SIZE = 2097152
INSTANCE_MAINTYPE = "0100"  # Instance-Code
INSTANCE_SUBTYPE = "0000"  # None
INSTANCE_VERSION = "0000"  # V0

BIT_LEN_MAP = {
    32: "0000",
    64: "0001",
    96: "0010",
    128: "0011",
    160: "0100",
    192: "0101",
    224: "0110",
    256: "0111",
}

Data = Union[bytes, bytearray, memoryview]
Stream = Union["BinaryIO", "mmap.mmap", "BytesIO", "BufferedReader"]


def gen_instance_code(stream, bits=INSTANCE_BITS):
    # type: (Stream, int) -> dict
    """
    Create an ISCC Instance-Code with algorithm v0.

    :param stream: Binary data stream (file-like object, mmap, BytesIO, or BufferedReader).
    :param bits: Bit-length of Instance-Code (32, 64, 96, 128, 160, 192, 224, or 256).
    :return: Dictionary with 'iscc', 'datahash' (blake3 multihash), and 'filesize' keys.
    """
    hasher = InstanceHasher()
    data = stream.read(INSTANCE_IO_READ_SIZE)
    while data:
        hasher.push(data)
        data = stream.read(INSTANCE_IO_READ_SIZE)

    instance_code = hasher.code(bits=bits)
    iscc = "ISCC:" + instance_code
    instance_code_obj = dict(
        iscc=iscc,
        datahash=hasher.multihash(),
        filesize=hasher.filesize,
    )

    return instance_code_obj


class InstanceHasher:
    """Incremental Instance-Hash generator."""

    #: Multihash prefix
    mh_prefix: bytes = b"\x1e\x20"

    def __init__(self, data=None):
        # type: (Optional[Data]) -> None
        """
        Create an InstanceHasher for incremental Instance-Code generation.

        :param data: Initial data to hash (bytes, bytearray, or memoryview).
        """
        self.hasher = blake3(max_threads=blake3.AUTO)
        self.filesize = 0
        data = data or b""
        self.push(data)

    def push(self, data):
        # type: (Data) -> None
        """
        Push data to the Instance-Hash generator.

        Updates the hash state and tracks total file size.

        :param data: Data chunk to process (bytes, bytearray, or memoryview).
        """
        self.filesize += len(data)
        self.hasher.update(data)

    def digest(self):
        # type: () -> bytes
        """
        Return blake3 hash digest.

        :return: 32-byte blake3 hash digest.
        """
        return self.hasher.digest()

    def multihash(self):
        # type: () -> str
        """
        Return blake3 digest as multihash.

        :return: Hex-encoded multihash with blake3 prefix (0x1e20).
        """
        return (self.mh_prefix + self.digest()).hex()

    def code(self, bits=INSTANCE_BITS):
        # type: (int) -> str
        """
        Encode digest as an ISCC Instance-Code unit.

        :param bits: Number of bits for the Instance-Code (32, 64, 96, 128, 160, 192, 224, or 256).
        :return: Base32-encoded ISCC Instance-Code string with header.
        """
        length = BIT_LEN_MAP[bits]
        header = int(INSTANCE_MAINTYPE + INSTANCE_SUBTYPE + INSTANCE_VERSION + length, 2).to_bytes(
            2, byteorder="big"
        )
        instance_code = encode_base32(header + self.digest()[: bits // 8])

        return instance_code


def encode_base32(data):
    # type: (bytes) -> str
    """
    Standard RFC4648 base32 encoding without padding.

    :param data: Binary data to encode.
    :return: Base32-encoded string without padding characters.
    """
    return b32encode(data).decode("ascii").rstrip("=")
