#!/usr/bin/env python3
# Example: Monitor file integrity using iscc-sum
# This script tracks changes to important files and alerts on modifications

import json
import os
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

# Configuration
STATE_DIR = Path.home() / ".iscc-integrity"
LOG_FILE = STATE_DIR / "integrity.log"


def log_message(message):
    """Log message with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    print(log_entry)

    # Ensure log directory exists
    STATE_DIR.mkdir(exist_ok=True)

    # Append to log file
    with open(LOG_FILE, "a") as f:
        f.write(log_entry + "\n")


def get_state_file(directory):
    """Get state file path for directory."""
    # Create a safe filename from directory path
    safe_name = str(Path(directory).resolve()).replace(os.sep, "_").replace(":", "")
    return STATE_DIR / f"state_{safe_name}.json"


def find_files(directory):
    """Find all readable files in directory."""
    path = Path(directory)
    files = []

    for item in path.rglob("*"):
        if item.is_file():
            try:
                # Check if file is readable
                with open(item, "rb") as f:
                    f.read(1)
                files.append(str(item))
            except (OSError, IOError):
                # Skip unreadable files
                pass

    return sorted(files)


def generate_checksums(files):
    """Generate checksums for files."""
    if not files:
        return {}

    try:
        result = subprocess.run(["iscc-sum"] + files, capture_output=True, text=True, check=True)

        # Parse output into dictionary
        checksums = {}
        for line in result.stdout.strip().split("\n"):
            if line:
                parts = line.split(maxsplit=1)
                if len(parts) == 2:
                    checksum = parts[0]
                    filename = parts[1].lstrip("*")
                    checksums[filename] = checksum

        return checksums

    except subprocess.CalledProcessError as e:
        log_message(f"Error generating checksums: {e.stderr}")
        return {}


def load_state(state_file):
    """Load previous state from file."""
    if state_file.exists():
        with open(state_file, "r") as f:
            return json.load(f)
    return {}


def save_state(state_file, checksums):
    """Save current state to file."""
    STATE_DIR.mkdir(exist_ok=True)
    with open(state_file, "w") as f:
        json.dump(checksums, f, indent=2)


def compare_states(old_state, new_state):
    """Compare old and new states, return changes."""
    old_files = set(old_state.keys())
    new_files = set(new_state.keys())

    added = new_files - old_files
    removed = old_files - new_files
    common = old_files & new_files

    modified = []
    for file in common:
        if old_state[file] != new_state[file]:
            modified.append(file)

    return {"added": sorted(added), "removed": sorted(removed), "modified": sorted(modified)}


def monitor_directory(directory):
    """Monitor directory for changes."""
    directory = Path(directory).resolve()
    state_file = get_state_file(directory)

    # Find current files
    log_message(f"Checking integrity of {directory}")
    files = find_files(directory)

    # Generate current checksums
    current_state = generate_checksums(files)

    # Load previous state
    previous_state = load_state(state_file)

    if not previous_state:
        # Initial run
        log_message(f"Initializing integrity monitoring for {directory}")
        save_state(state_file, current_state)
        log_message(f"Initial state created with {len(current_state)} files")
        return

    # Compare states
    changes = compare_states(previous_state, current_state)

    # Report changes
    has_changes = any(changes[k] for k in ["added", "removed", "modified"])

    if has_changes:
        log_message("INTEGRITY CHANGES DETECTED!")

        if changes["added"]:
            print("\nAdded files:")
            for file in changes["added"]:
                print(f"  + {file}")

        if changes["modified"]:
            print("\nModified files:")
            for file in changes["modified"]:
                print(f"  ! {file}")

        if changes["removed"]:
            print("\nRemoved files:")
            for file in changes["removed"]:
                print(f"  - {file}")

        # Ask to update state
        response = input("\nUpdate integrity state? [y/N] ")
        if response.lower() == "y":
            save_state(state_file, current_state)
            log_message("Integrity state updated")
        else:
            log_message("Integrity state NOT updated - changes remain unacknowledged")

        sys.exit(1)
    else:
        log_message("No changes detected - all files intact")
        sys.exit(0)


def main():
    if len(sys.argv) < 2:
        print("Usage: integrity-monitor.py <directory>")
        print("\nMonitors file integrity in specified directory")
        print("State files stored in: ~/.iscc-integrity/")
        sys.exit(1)

    directory = sys.argv[1]

    # Check if directory exists
    if not Path(directory).is_dir():
        print(f"Error: Directory not found: {directory}", file=sys.stderr)
        sys.exit(1)

    monitor_directory(directory)


if __name__ == "__main__":
    main()
