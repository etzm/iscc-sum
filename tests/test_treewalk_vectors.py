"""
Test treewalk implementation against test vectors from the specification.

This module dynamically parses test vectors from docs/treewalk-spec.md and
validates the treewalk implementation against them using YAML for structured data.
"""

import re
import sys
from pathlib import Path
from unicodedata import normalize

import pytest
import yaml
from pyfakefs.fake_filesystem_unittest import Patcher

from iscc_sum.treewalk import listdir, treewalk, treewalk_ignore, treewalk_iscc


def is_case_insensitive_filesystem():
    # type: () -> bool
    """
    Detect if the filesystem is case-insensitive.

    This is typically true for:
    - Windows (NTFS by default, though can be case-sensitive)
    - macOS (HFS+ and APFS by default, though can be case-sensitive)
    """
    import os

    # For pyfakefs, we simulate based on platform
    # macOS and Windows are typically case-insensitive
    if sys.platform == "darwin" or os.name == "nt":
        return True
    return False


def parse_test_vectors_from_spec():
    # type: () -> list[dict]
    """Parse test vectors from the treewalk specification markdown file."""
    spec_path = Path(__file__).parent.parent / "docs" / "treewalk-spec.md"
    with open(spec_path, "r", encoding="utf-8") as f:
        content = f.read()

    test_vectors = []
    lines = content.splitlines()
    i = 0

    while i < len(lines):
        line = lines[i]

        # Look for test case headers
        if line.startswith("#### Test Case"):
            match = re.match(r"#### Test Case (\d+): (.+)", line)
            if match:
                test_num = match.group(1)
                test_name = match.group(2)
                test_case = {
                    "number": test_num,
                    "name": test_name,
                    "structure": [],
                    "expected": [],
                    "test_type": None,
                }

                # Look for Structure and Expected sections
                j = i + 1
                while j < len(lines) and not lines[j].startswith("####"):
                    if lines[j].strip() == "**Structure:**":
                        # Find the yaml block
                        yaml_start = j + 1
                        while yaml_start < len(lines) and lines[yaml_start].strip() != "```yaml":
                            yaml_start += 1
                        if yaml_start < len(lines):
                            yaml_end = yaml_start + 1
                            yaml_lines = []
                            while yaml_end < len(lines) and lines[yaml_end].strip() != "```":
                                yaml_lines.append(lines[yaml_end])
                                yaml_end += 1
                            if yaml_lines:
                                structure_data = yaml.safe_load("\n".join(yaml_lines))
                                test_case["structure"] = structure_data if structure_data else []

                    elif lines[j].startswith("**Expected"):
                        # Extract test type from the line
                        if "Base Treewalk" in lines[j]:
                            test_case["test_type"] = "base"
                        elif "Treewalk-Ignore" in lines[j]:
                            test_case["test_type"] = "ignore"
                        elif "Treewalk-ISCC" in lines[j]:
                            test_case["test_type"] = "iscc"

                        # Find the yaml block
                        yaml_start = j + 1
                        while yaml_start < len(lines) and lines[yaml_start].strip() != "```yaml":
                            yaml_start += 1
                        if yaml_start < len(lines):
                            yaml_end = yaml_start + 1
                            yaml_lines = []
                            while yaml_end < len(lines) and lines[yaml_end].strip() != "```":
                                yaml_lines.append(lines[yaml_end])
                                yaml_end += 1
                            if yaml_lines:
                                expected_data = yaml.safe_load("\n".join(yaml_lines))
                                test_case["expected"] = expected_data if expected_data else []

                    j += 1

                test_vectors.append(test_case)

        i += 1

    return test_vectors


def create_test_filesystem(structure, fs):
    # type: (list[dict], object) -> Path
    """Create a test filesystem structure using pyfakefs."""
    # Create test directory in temp location
    # Use OS-appropriate temp directory
    import os
    import tempfile

    if os.name == "nt":  # Windows
        temp_base = Path("C:/tmp")
    else:
        temp_base = Path("/tmp")

    test_root = temp_base / "treewalk_test"
    test_dir = test_root / "test_dir"
    fs.create_dir(str(test_root))
    fs.create_dir(str(test_dir))

    for item in structure:
        if isinstance(item, dict):
            item_path = test_dir / item["path"]

            # Check if it's a directory
            if item.get("type") == "dir":
                fs.create_dir(str(item_path))
            else:
                # Ensure parent directory exists
                fs.makedirs(str(item_path.parent), exist_ok=True)

                # Create file with content if specified
                content = item.get("content", "")

                # Handle special encodings for unicode tests
                if "encoding" in item:
                    if item["encoding"] == "NFD":
                        # Normalize the filename to NFD
                        from unicodedata import normalize

                        nfd_name = normalize("NFD", item_path.name)
                        item_path = item_path.parent / nfd_name

                # Check if file already exists (for duplicate NFC-normalized names)
                # On Windows, file names are case-insensitive, so Café.txt and café.txt
                # would be the same file
                try:
                    fs.create_file(str(item_path), contents=content)
                except (OSError, FileExistsError):
                    # File already exists (case-insensitive match on Windows)
                    pass

    return test_dir


class TestTreewalkVectors:
    """Test treewalk implementation against specification test vectors."""

    def test_parse_vectors(self):
        """Verify we can parse test vectors from the specification."""
        vectors = parse_test_vectors_from_spec()
        assert len(vectors) >= 4, "Should have at least 4 test cases from spec"

        # Check first test case structure
        test1 = vectors[0]
        assert test1["number"] == "1"
        assert "Unicode" in test1["name"]
        assert len(test1["structure"]) > 0
        assert len(test1["expected"]) > 0

    @pytest.mark.parametrize("test_vector", parse_test_vectors_from_spec())
    def test_vector(self, test_vector):
        """Run a single test vector from the specification."""
        with Patcher() as patcher:
            # Create the test filesystem
            test_dir = create_test_filesystem(test_vector["structure"], patcher.fs)

            # Run the appropriate treewalk variant
            if test_vector["test_type"] == "base":
                # For base treewalk, we use listdir to test ordering
                if "Unicode" in test_vector["name"]:
                    # Test unicode normalization at listdir level
                    entries = listdir(test_dir)
                    actual_paths = [f"test_dir/{e.name}" for e in entries if e.is_file()]
                else:
                    # Test full treewalk
                    actual_paths = []
                    for path in treewalk(test_dir):
                        # Make both paths absolute and resolved to handle Windows drive letters
                        abs_path = Path(path).resolve()
                        abs_parent = test_dir.parent.resolve()
                        rel_path = abs_path.relative_to(abs_parent)
                        actual_paths.append(str(rel_path).replace("\\", "/"))

            elif test_vector["test_type"] == "ignore":
                # Test treewalk_ignore with .gitignore
                actual_paths = []
                for path in treewalk_ignore(test_dir, ".gitignore"):
                    # Make both paths absolute and resolved to handle Windows drive letters
                    abs_path = Path(path).resolve()
                    abs_parent = test_dir.parent.resolve()
                    rel_path = abs_path.relative_to(abs_parent)
                    actual_paths.append(str(rel_path).replace("\\", "/"))

            elif test_vector["test_type"] == "iscc":
                # Test treewalk_iscc
                actual_paths = []
                for path in treewalk_iscc(test_dir):
                    # Make both paths absolute and resolved to handle Windows drive letters
                    abs_path = Path(path).resolve()
                    abs_parent = test_dir.parent.resolve()
                    rel_path = abs_path.relative_to(abs_parent)
                    actual_paths.append(str(rel_path).replace("\\", "/"))

            else:
                pytest.fail(f"Unknown test type: {test_vector['test_type']}")

            # Compare with expected
            # Handle case-insensitive filesystems for Unicode test
            if is_case_insensitive_filesystem() and "Unicode" in test_vector["name"]:
                # Case-insensitive filesystems (Windows, macOS) treat "Café.txt" and "café.txt"
                # as the same file. We need to adjust expectations
                if len(actual_paths) < len(test_vector["expected"]):
                    # Filter out the lowercase version from expected
                    expected_filtered = [
                        p
                        for p in test_vector["expected"]
                        if not (p == "test_dir/café.txt" and "test_dir/Café.txt" in test_vector["expected"])
                    ]
                    assert actual_paths == expected_filtered, (
                        f"Test Case {test_vector['number']}: {test_vector['name']} (Case-insensitive FS)\n"
                        f"Expected (adjusted): {expected_filtered}\n"
                        f"Actual: {actual_paths}"
                    )
                else:
                    assert actual_paths == test_vector["expected"], (
                        f"Test Case {test_vector['number']}: {test_vector['name']}\n"
                        f"Expected: {test_vector['expected']}\n"
                        f"Actual: {actual_paths}"
                    )
            else:
                assert actual_paths == test_vector["expected"], (
                    f"Test Case {test_vector['number']}: {test_vector['name']}\n"
                    f"Expected: {test_vector['expected']}\n"
                    f"Actual: {actual_paths}"
                )

    def test_unicode_normalization_detailed(self):
        """Test unicode normalization with both NFC and NFD forms."""
        with Patcher() as patcher:
            import os

            if os.name == "nt":  # Windows
                test_dir = Path("C:/tmp/unicode_test")
            else:
                test_dir = Path("/tmp/unicode_test")
            patcher.fs.create_dir(str(test_dir))

            # Create files with NFC and NFD representations
            nfc_name = "Café.txt"  # NFC form
            nfd_name = normalize("NFD", nfc_name)  # NFD form

            # On case-insensitive filesystems, file names are case-insensitive
            patcher.fs.create_file(str(test_dir / nfc_name))
            try:
                patcher.fs.create_file(str(test_dir / nfd_name))
            except (OSError, FileExistsError):
                pass  # Expected on case-insensitive filesystems
            try:
                patcher.fs.create_file(str(test_dir / "café.txt"))  # lowercase
            except (OSError, FileExistsError):
                pass  # Expected on case-insensitive filesystems

            entries = listdir(test_dir)
            names = [e.name for e in entries]

            # Check based on filesystem case sensitivity
            if is_case_insensitive_filesystem():
                # On case-insensitive systems (Windows, macOS), "Café.txt" and "café.txt" are the same file
                assert len(names) >= 1
            else:
                # All three files should be present on Linux
                assert len(names) == 3
                # They should be ordered by NFC-normalized UTF-8 encoding
                # Capital C comes before lowercase c
                assert names[0] in [nfc_name, nfd_name]  # Both normalize to same form
                assert names[1] in [nfc_name, nfd_name]  # Both normalize to same form
                assert names[2] == "café.txt"

    def test_ignore_file_priority(self):
        """Test that ignore files are always yielded first."""
        with Patcher() as patcher:
            import os

            if os.name == "nt":  # Windows
                test_dir = Path("C:/tmp/ignore_priority_test")
            else:
                test_dir = Path("/tmp/ignore_priority_test")
            patcher.fs.create_dir(str(test_dir))

            # Create files in non-alphabetical order
            patcher.fs.create_file(str(test_dir / "zzz.txt"))
            patcher.fs.create_file(str(test_dir / "aaa.txt"))
            patcher.fs.create_file(str(test_dir / ".gitignore"))
            patcher.fs.create_file(str(test_dir / ".npmignore"))

            paths = list(treewalk(test_dir))
            names = [p.name for p in paths]

            # Ignore files should come first, in sorted order
            assert names[0] == ".gitignore"
            assert names[1] == ".npmignore"
            assert names[2] == "aaa.txt"
            assert names[3] == "zzz.txt"

    # def test_symlink_exclusion(self):
    #     """Test that symlinks are properly excluded."""
    #     with Patcher() as patcher:
    #         # pyfakefs doesn't support symlinks well, so we'll skip this test
    #         pytest.skip("pyfakefs doesn't properly support symlink testing")

    def test_cascading_ignore_patterns(self):
        """Test that ignore patterns cascade correctly from parent to child directories."""
        with Patcher() as patcher:
            import os

            if os.name == "nt":  # Windows
                test_dir = Path("C:/tmp/cascade_test")
            else:
                test_dir = Path("/tmp/cascade_test")
            patcher.fs.create_dir(str(test_dir))
            patcher.fs.create_dir(str(test_dir / "sub"))

            # Create ignore files with patterns
            patcher.fs.create_file(str(test_dir / ".gitignore"), contents="*.log\n")
            patcher.fs.create_file(str(test_dir / "sub" / ".gitignore"), contents="!important.log\n")

            # Create test files
            patcher.fs.create_file(str(test_dir / "app.py"))
            patcher.fs.create_file(str(test_dir / "debug.log"))
            patcher.fs.create_file(str(test_dir / "sub" / "error.log"))
            patcher.fs.create_file(str(test_dir / "sub" / "important.log"))
            patcher.fs.create_file(str(test_dir / "sub" / "data.txt"))

            paths = list(treewalk_ignore(test_dir, ".gitignore"))
            names = [p.name for p in paths]

            # Check that patterns were applied correctly
            assert "app.py" in names
            assert "debug.log" not in names  # Ignored by root .gitignore
            assert "error.log" not in names  # Ignored by inherited pattern
            assert "important.log" in names  # Re-included by sub/.gitignore
            assert "data.txt" in names

    def test_iscc_metadata_filtering(self):
        """Test ISCC-specific filtering of metadata files."""
        with Patcher() as patcher:
            import os

            if os.name == "nt":  # Windows
                test_dir = Path("C:/tmp/iscc_test")
            else:
                test_dir = Path("/tmp/iscc_test")
            patcher.fs.create_dir(str(test_dir))

            # Create ISCC ignore file
            patcher.fs.create_file(str(test_dir / ".isccignore"), contents="temp/\n*.bak\n")

            # Create test files
            patcher.fs.create_file(str(test_dir / "data.txt"))
            patcher.fs.create_file(str(test_dir / "data.txt.iscc.json"))  # Should be filtered
            patcher.fs.create_file(str(test_dir / "backup.bak"))  # Should be filtered by .isccignore
            patcher.fs.create_dir(str(test_dir / "temp"))
            patcher.fs.create_file(str(test_dir / "temp" / "cache.dat"))  # Should be filtered

            paths = list(treewalk_iscc(test_dir))
            names = [p.name for p in paths]

            # Only non-ISCC files should be present
            assert names == [".isccignore", "data.txt"]

    def test_nested_directories(self):
        """Test traversal of nested directory structures."""
        with Patcher() as patcher:
            import os

            if os.name == "nt":  # Windows
                test_dir = Path("C:/tmp/nested_test")
            else:
                test_dir = Path("/tmp/nested_test")
            patcher.fs.create_dir(str(test_dir))
            patcher.fs.create_dir(str(test_dir / "a"))
            patcher.fs.create_dir(str(test_dir / "b"))
            patcher.fs.create_dir(str(test_dir / "a" / "nested"))

            # Create files in various locations
            patcher.fs.create_file(str(test_dir / "root.txt"))
            patcher.fs.create_file(str(test_dir / "a" / "file_a.txt"))
            patcher.fs.create_file(str(test_dir / "b" / "file_b.txt"))
            patcher.fs.create_file(str(test_dir / "a" / "nested" / "deep.txt"))

            paths = list(treewalk(test_dir))
            rel_paths = []
            for p in paths:
                # Make both paths absolute and resolved to handle Windows drive letters
                abs_path = Path(p).resolve()
                abs_test_dir = test_dir.resolve()
                rel_path = abs_path.relative_to(abs_test_dir)
                rel_paths.append(str(rel_path).replace("\\", "/"))

            # Verify correct order: files first, then subdirs recursively
            expected = ["root.txt", "a/file_a.txt", "a/nested/deep.txt", "b/file_b.txt"]
            assert rel_paths == expected
