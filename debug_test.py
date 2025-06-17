#!/usr/bin/env python
# Debug script to understand the path issue

import os
import sys
from pathlib import Path

from click.testing import CliRunner

# Add the src directory to Python path
sys.path.insert(0, "src")

from iscc_sum.cli import _expand_paths, cli

runner = CliRunner()
with runner.isolated_filesystem():
    # Create test structure
    os.mkdir("testdir")
    Path("testdir/file1.txt").write_text("content1")
    Path("testdir/file2.txt").write_text("content2")

    print(f"Current dir: {os.getcwd()}")
    print(f"testdir exists: {os.path.exists('testdir')}")
    print(f"testdir absolute: {os.path.abspath('testdir')}")

    # Test _expand_paths directly
    print("\n_expand_paths output:")
    for path in _expand_paths(("testdir",)):
        print(f"  {path}")

    # Test CLI
    print("\nCLI output:")
    result = runner.invoke(cli, ["testdir"])
    print(result.output)
    print(f"Exit code: {result.exit_code}")
