#!/usr/bin/env python3
# Example: Finding duplicate or similar files using iscc-sum
# This script demonstrates the similarity matching feature

import os
import subprocess
import sys
from collections import defaultdict


def find_similar_files(directory, threshold=12, extensions=None):
    """Find similar files in a directory using iscc-sum.

    Args:
        directory: Path to search
        threshold: Hamming distance threshold (lower = more similar)
        extensions: List of file extensions to check (e.g., ['.jpg', '.png'])
    """
    # Build file pattern
    if extensions:
        patterns = [os.path.join(directory, f"*{ext}") for ext in extensions]
    else:
        patterns = [os.path.join(directory, "*")]

    # Run iscc-sum with similarity matching
    cmd = ["iscc-sum", "--similar", "--threshold", str(threshold)] + patterns

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr}", file=sys.stderr)
        return None


def parse_similarity_output(output):
    """Parse iscc-sum similarity output into groups."""
    groups = []
    current_group = None

    for line in output.strip().split("\n"):
        if line and not line.startswith(" "):
            # New reference file
            if current_group:
                groups.append(current_group)
            current_group = {"reference": line.strip(), "similar": []}
        elif line.strip().startswith("~"):
            # Similar file with distance
            parts = line.strip().split(maxsplit=1)
            if len(parts) == 2:
                distance = int(parts[0][1:])  # Remove '~' prefix
                filename = parts[1]
                current_group["similar"].append({"file": filename, "distance": distance})

    if current_group:
        groups.append(current_group)

    return groups


def main():
    if len(sys.argv) < 2:
        print("Usage: duplicate-finder.py <directory> [threshold] [extensions...]")
        print("Example: duplicate-finder.py ./photos 8 .jpg .png")
        sys.exit(1)

    directory = sys.argv[1]
    threshold = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    extensions = sys.argv[3:] if len(sys.argv) > 3 else None

    print(f"Searching for similar files in: {directory}")
    print(f"Similarity threshold: {threshold} bits")
    if extensions:
        print(f"File types: {', '.join(extensions)}")
    print("-" * 50)

    # Find similar files
    output = find_similar_files(directory, threshold, extensions)
    if not output:
        print("No similar files found or error occurred.")
        return

    # Parse and display results
    groups = parse_similarity_output(output)

    if not groups:
        print("No similar files found.")
        return

    print(f"\nFound {len(groups)} groups of similar files:\n")

    for i, group in enumerate(groups, 1):
        print(f"Group {i}:")
        print(f"  Reference: {group['reference']}")

        if group["similar"]:
            print("  Similar files:")
            for item in group["similar"]:
                print(f"    - {item['file']} (distance: {item['distance']} bits)")
        else:
            print("  No similar files within threshold")
        print()

    # Summary statistics
    total_similar = sum(len(g["similar"]) for g in groups)
    if total_similar > 0:
        print(f"\nSummary: Found {total_similar} similar file pairs")

        # Find exact duplicates (distance = 0)
        exact_duplicates = sum(1 for g in groups for s in g["similar"] if s["distance"] == 0)
        if exact_duplicates > 0:
            print(f"  - {exact_duplicates} exact duplicates (distance = 0)")


if __name__ == "__main__":
    main()
