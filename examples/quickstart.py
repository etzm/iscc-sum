#!/usr/bin/env python3
"""Quick start example for iscc-sum"""

from iscc_sum import IsccSumProcessor, code_iscc_sum


def main():
    print("=== ISCC Data-Code Hashing Example ===\n")

    # Simple one-shot hashing
    print("1. Simple one-shot hashing:")
    result = code_iscc_sum(b"Hello World")
    print(f"   ISCC: {result['iscc']}")
    print(f"   Hash: {result['hash'].hex()}")

    print("\n2. Incremental hashing for large files or streaming:")
    processor = IsccSumProcessor()
    processor.update(b"Hello ")
    processor.update(b"World")
    result = processor.result()
    print(f"   ISCC: {result['iscc']}")
    print("   (Should match the one-shot result above)")


if __name__ == "__main__":
    main()
