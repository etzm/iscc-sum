#!/usr/bin/env python3
"""Benchmark script for isum (Rust CLI) performance testing."""

import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path


def create_test_file(size_mb):
    """Create a test file of specified size in MB."""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        # Write random-like data (more realistic than zeros)
        chunk_size = 1024 * 1024  # 1MB
        data = bytearray(os.urandom(chunk_size))
        for _ in range(size_mb):
            f.write(data)
        return f.name


def benchmark_isum(file_path, iterations=5):
    """Benchmark isum on a file."""
    times = []

    # Warm up run
    subprocess.run(["./target/release/isum", file_path], capture_output=True, check=True)

    for i in range(iterations):
        start = time.perf_counter()
        result = subprocess.run(["./target/release/isum", file_path], capture_output=True, check=True)
        end = time.perf_counter()
        times.append(end - start)

    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)

    return {"avg": avg_time, "min": min_time, "max": max_time, "output": result.stdout.decode().strip()}


def benchmark_python_cli(file_path, iterations=5):
    """Benchmark Python iscc-sum CLI for comparison."""
    times = []

    # Warm up run
    subprocess.run([sys.executable, "-m", "iscc_sum.cli", file_path], capture_output=True, check=True)

    for i in range(iterations):
        start = time.perf_counter()
        result = subprocess.run(
            [sys.executable, "-m", "iscc_sum.cli", file_path], capture_output=True, check=True
        )
        end = time.perf_counter()
        times.append(end - start)

    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)

    return {"avg": avg_time, "min": min_time, "max": max_time, "output": result.stdout.decode().strip()}


def measure_memory_usage(file_path):
    """Measure peak memory usage of isum (Linux only)."""
    try:
        result = subprocess.run(
            ["/usr/bin/time", "-v", "./target/release/isum", file_path],
            capture_output=True,
            text=True,
            check=True,
        )
        # Parse peak RSS from time output
        for line in result.stderr.split("\n"):
            if "Maximum resident set size" in line:
                memory_kb = int(line.split()[-1])
                return memory_kb / 1024  # Convert to MB
    except FileNotFoundError:
        return None  # time command not available
    except Exception:
        return None


def main():
    print("ISUM Performance Benchmark")
    print("=" * 50)

    # Check if release binary exists
    if not Path("./target/release/isum").exists():
        print("Error: Release binary not found. Run 'cargo build --release' first.")
        sys.exit(1)

    # Test with different file sizes
    test_sizes = [1, 10, 100, 500]  # MB

    for size_mb in test_sizes:
        print(f"\nTesting with {size_mb}MB file...")
        test_file = create_test_file(size_mb)

        try:
            # Benchmark Rust isum
            print("  Benchmarking isum (Rust)...")
            rust_results = benchmark_isum(test_file)

            # Benchmark Python CLI
            print("  Benchmarking iscc-sum (Python)...")
            python_results = benchmark_python_cli(test_file)

            # Measure memory usage
            memory_mb = measure_memory_usage(test_file)

            # Display results
            print(f"\n  Results for {size_mb}MB file:")
            print("  Rust isum:")
            print(f"    Average time: {rust_results['avg']:.4f}s")
            print(f"    Min time: {rust_results['min']:.4f}s")
            print(f"    Max time: {rust_results['max']:.4f}s")
            if memory_mb:
                print(f"    Peak memory: {memory_mb:.1f}MB")

            print("  Python iscc-sum:")
            print(f"    Average time: {python_results['avg']:.4f}s")
            print(f"    Min time: {python_results['min']:.4f}s")
            print(f"    Max time: {python_results['max']:.4f}s")

            speedup = python_results["avg"] / rust_results["avg"]
            print(f"\n  Speedup: {speedup:.2f}x faster")

            # Verify outputs match
            rust_checksum = rust_results["output"].split()[0]
            python_checksum = python_results["output"].split()[0]
            if rust_checksum == python_checksum:
                print(f"  ✓ Checksums match: {rust_checksum}")
            else:
                print("  ✗ Checksum mismatch!")
                print(f"    Rust:   {rust_checksum}")
                print(f"    Python: {python_checksum}")

        finally:
            os.unlink(test_file)

    # Test startup time with small file
    print("\n" + "=" * 50)
    print("Startup time test (10 iterations with 1KB file)...")
    # Create a small file directly
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"x" * 1024)  # 1KB
        small_file = f.name

    try:
        rust_startup = benchmark_isum(small_file, iterations=10)
        python_startup = benchmark_python_cli(small_file, iterations=10)

        print(f"  Rust isum startup: {rust_startup['avg'] * 1000:.1f}ms average")
        print(f"  Python iscc-sum startup: {python_startup['avg'] * 1000:.1f}ms average")
        print(f"  Startup speedup: {python_startup['avg'] / rust_startup['avg']:.1f}x faster")

    finally:
        os.unlink(small_file)


if __name__ == "__main__":
    main()
