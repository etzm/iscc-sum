from iscc_sum._core import (
    DataCodeProcessor,
    InstanceCodeProcessor,
    IsccSumProcessor,
    code_iscc_sum,
    hello_from_bin,
)

__all__ = [
    "DataCodeProcessor",
    "InstanceCodeProcessor",
    "IsccSumProcessor",
    "code_iscc_sum",
    "hello_from_bin",
]


def main() -> None:
    print(hello_from_bin())
