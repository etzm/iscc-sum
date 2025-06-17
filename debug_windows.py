#!/usr/bin/env python
# Debug script specifically for Windows path handling

import os
from pathlib import Path

# Test Path behavior
print("Testing Path behavior:")
path_str = "testdir"
path_obj = Path(path_str)
print(f"Input: {path_str}")
print(f"Path object: {path_obj}")
print(f"Is absolute: {path_obj.is_absolute()}")
print(f"Resolved: {path_obj.resolve()}")
print(f"String: {str(path_obj)}")

# Test with directory
os.makedirs("testdir", exist_ok=True)
Path("testdir/file.txt").write_text("test")

print("\nWith existing directory:")
path_obj2 = Path("testdir")
print(f"Path object: {path_obj2}")
print(f"Is absolute: {path_obj2.is_absolute()}")
print(f"Exists: {path_obj2.exists()}")
print(f"Is dir: {path_obj2.is_dir()}")

# Test os.path.join behavior
print("\nos.path.join behavior:")
result = os.path.join("testdir", "file.txt")
print(f"os.path.join('testdir', 'file.txt') = {result}")
print(f"os.sep = '{os.sep}'")
