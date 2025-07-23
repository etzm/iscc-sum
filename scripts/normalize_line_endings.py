#!/usr/bin/env python
"""Check and report line ending normalization status."""

import subprocess
import sys
from pathlib import Path


def check_line_endings():
    """Check if any files need line ending normalization."""
    try:
        # Configure git to ensure consistent behavior
        subprocess.run(
            ["git", "config", "core.autocrlf", "false"],
            capture_output=True
        )
        
        # Check current status
        print("Checking line endings...")
        
        # Add --renormalize flag to check which files would be normalized
        result = subprocess.run(
            ["git", "add", "--dry-run", "--renormalize", "."],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        
        if result.returncode != 0:
            print(f"Error checking files: {result.stdout}")
            return False
        
        # Check if any files would be normalized
        status_result = subprocess.run(
            ["git", "diff", "--name-only", "--cached"],
            capture_output=True,
            text=True
        )
        
        # Reset any staged changes from dry-run
        subprocess.run(["git", "reset"], capture_output=True)
        
        # Actually check which files have wrong line endings
        # by running renormalize and then checking status
        subprocess.run(
            ["git", "add", "--renormalize", "."],
            capture_output=True,
            text=True
        )
        
        status_result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True
        )
        
        files_with_wrong_endings = []
        if status_result.stdout.strip():
            for line in status_result.stdout.splitlines():
                if line.startswith("M ") or line.startswith("A "):
                    files_with_wrong_endings.append(line[3:].strip())
        
        # Reset the changes
        subprocess.run(["git", "reset", "--hard"], capture_output=True)
        
        if files_with_wrong_endings:
            print(f"\n⚠️  WARNING: {len(files_with_wrong_endings)} files have incorrect line endings:")
            for file in files_with_wrong_endings[:10]:
                print(f"  - {file}")
            if len(files_with_wrong_endings) > 10:
                print(f"  ... and {len(files_with_wrong_endings) - 10} more files")
            
            print("\nTo fix line endings, run:")
            print("  git add --renormalize .")
            print("  git commit -m 'fix: normalize line endings to LF'")
            print("\nThis will ensure consistent ISCC hashes across all platforms.")
            return False
        else:
            print("✓ All files have correct line endings (LF)")
            return True
        
    except subprocess.CalledProcessError as e:
        print(f"Git command failed: {e}")
        return False
    except FileNotFoundError:
        print("Error: git not found. Please ensure git is installed and in PATH")
        return False


def main():
    """Main entry point."""
    # Find repository root
    current = Path.cwd()
    while current != current.parent:
        if (current / ".git").exists():
            break
        current = current.parent
    else:
        print("Error: Not in a git repository")
        sys.exit(1)
    
    if not check_line_endings():
        sys.exit(1)


if __name__ == "__main__":
    main()