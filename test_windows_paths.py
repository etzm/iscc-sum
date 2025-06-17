#!/usr/bin/env python
# Test script to debug Windows path issue

import os
import tempfile
from pathlib import Path

from iscc_sum.treewalk import treewalk_iscc

# Create a temporary directory structure
with tempfile.TemporaryDirectory() as tmpdir:
    testdir = os.path.join(tmpdir, "testdir")
    os.mkdir(testdir)

    # Create test files
    Path(os.path.join(testdir, "file1.txt")).write_text("content1")
    Path(os.path.join(testdir, "file2.txt")).write_text("content2")

    print(f"Temp dir: {tmpdir}")
    print(f"Test dir: {testdir}")
    print(f"Test dir exists: {os.path.exists(testdir)}")
    print(f"Test dir is_dir: {os.path.isdir(testdir)}")

    # Test treewalk_iscc output
    print("\nTreewalk output:")
    for file_path in treewalk_iscc(testdir):
        print(f"  Raw: {file_path}")
        print(f"  Type: {type(file_path)}")

    # Test relative path calculation
    print("\nRelative path calculation:")
    path_obj = Path(testdir)
    for file_path in treewalk_iscc(path_obj):
        try:
            relative_path = file_path.relative_to(path_obj.resolve())
            result = os.path.join("testdir", str(relative_path))
            print(f"  File: {file_path}")
            print(f"  Relative: {relative_path}")
            print(f"  Result: {result}")
        except Exception as e:
            print(f"  Error: {e}")
