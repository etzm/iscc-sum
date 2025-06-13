"""ISO Reference Implementation of ISCC Instance-Code"""

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

    :param Stream stream: Binary data stream for Instance-Code generation
    :param int bits: Bit-length of resulting Instance-Code (multiple of 64)
    :return: ISCC object with Instance-Code and properties: datahash, filesize
    :rtype: dict
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
        self.hasher = blake3(max_threads=blake3.AUTO)
        self.filesize = 0
        data = data or b""
        self.push(data)

    def push(self, data):
        # type: (Data) -> None
        """
        Push data to the Instance-Hash generator.

        :param Data data: Data to be hashed
        """
        self.filesize += len(data)
        self.hasher.update(data)

    def digest(self):
        # type: () -> bytes
        """
        Return Instance-Hash

        :return: Instance-Hash digest
        :rtype: bytes
        """
        return self.hasher.digest()

    def multihash(self):
        # type: () -> str
        """
        Return blake3 multihash

        :return: Blake3 hash as 256-bit multihash
        :rtype: str
        """
        return (self.mh_prefix + self.digest()).hex()

    def code(self, bits=INSTANCE_BITS):
        # type: (int) -> str
        """
        Encode digest as an ISCC Instance-Code unit.

        :param int bits: Number of bits for the ISCC Instance-Code
        :return: ISCC Instance-Code
        :rtype: str
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

    :param bytes data: Data for base32 encoding
    :return: Base32 encoded str
    """
    return b32encode(data).decode("ascii").rstrip("=")
