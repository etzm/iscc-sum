#!/usr/bin/env python
"""Benchmark script comparing Data-Code generation performance between reference and Rust implementation."""

import os
import sys
import time

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from iscc_sum._core import DataCodeProcessor
from iscc_sum.code_data_ref import gen_data_code


def generate_random_data(size_mb):
    # type: (int) -> bytes
    """Generate random data of specified size in MB."""
    return os.urandom(size_mb * 1024 * 1024)


def benchmark_reference(data):
    # type: (bytes) -> float
    """Benchmark the reference implementation."""
    from io import BytesIO

    start_time = time.perf_counter()
    _ = gen_data_code(BytesIO(data))
    end_time = time.perf_counter()
    return end_time - start_time


def benchmark_rust(data):
    # type: (bytes) -> float
    """Benchmark the Rust extension implementation."""
    start_time = time.perf_counter()
    processor = DataCodeProcessor()
    processor.update(data)
    _ = processor.result()
    end_time = time.perf_counter()
    return end_time - start_time


def main():
    """Run benchmarks and print results."""
    print("ISCC Data-Code Benchmark")
    print("=" * 50)

    # Test data sizes in MB
    test_sizes = [1, 10, 50, 100]

    for size_mb in test_sizes:
        print(f"\nBenchmarking with {size_mb} MB of random data...")

        # Generate random data
        data = generate_random_data(size_mb)
        data_size_bytes = len(data)

        # Warm up runs
        _ = benchmark_reference(data[: 1024 * 1024])  # 1MB warmup
        _ = benchmark_rust(data[: 1024 * 1024])  # 1MB warmup

        # Benchmark reference implementation
        ref_time = benchmark_reference(data)
        ref_speed = (data_size_bytes / (1024 * 1024)) / ref_time  # MB/s

        # Benchmark Rust implementation
        rust_time = benchmark_rust(data)
        rust_speed = (data_size_bytes / (1024 * 1024)) / rust_time  # MB/s

        # Calculate speedup
        speedup = rust_speed / ref_speed

        # Print results
        print(f"  Reference implementation: {ref_speed:.2f} MB/s")
        print(f"  Rust extension:          {rust_speed:.2f} MB/s")
        print(f"  Speedup factor:          {speedup:.2f}x")


if __name__ == "__main__":
    main()
