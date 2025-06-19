#!/bin/bash
# Generate flamegraph for isum performance analysis

set -e

# Check if flamegraph is installed
if ! command -v cargo-flamegraph &> /dev/null; then
    echo "Installing cargo-flamegraph..."
    cargo install flamegraph
fi

# Create a large test file
echo "Creating 100MB test file..."
dd if=/dev/urandom of=/tmp/test_large.bin bs=1M count=100 2>/dev/null

# Generate flamegraph
echo "Generating flamegraph..."
cargo flamegraph --bin isum -- /tmp/test_large.bin

# Cleanup
rm /tmp/test_large.bin

echo "Flamegraph generated: flamegraph.svg"