from iscc_sum._core import (
    DataCodeProcessor,
    InstanceCodeProcessor,
    IsccSumProcessor,
    hello_from_bin,
)
from iscc_sum.code_iscc_sum import code_iscc_sum

__all__ = [
    "DataCodeProcessor",
    "InstanceCodeProcessor",
    "IsccSumProcessor",
    "code_iscc_sum",
    "hello_from_bin",
]


def main() -> None:
    print(hello_from_bin())
