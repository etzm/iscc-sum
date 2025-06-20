"""
Comprehensive tests for the listdir_upath function with 100% coverage.
"""

import os
import tempfile
from pathlib import Path
from unicodedata import normalize

import pytest
from upath import UPath

from iscc_sum.treewalk import listdir_upath


class TestListdirUpathBasic:
    """Basic functionality tests for listdir_upath."""

    def test_empty_directory(self, tmp_path):
        # type: (Path) -> None
        """Test listing an empty directory."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        result = listdir_upath(str(empty_dir))
        assert result == []
        assert isinstance(result, list)

    def test_single_file(self, tmp_path):
        # type: (Path) -> None
        """Test listing a directory with a single file."""
        test_dir = tmp_path / "single"
        test_dir.mkdir()
        (test_dir / "file.txt").write_text("content")

        result = listdir_upath(str(test_dir))
        assert len(result) == 1
        assert isinstance(result[0], UPath)
        assert result[0].name == "file.txt"
        assert result[0].is_file()

    def test_single_directory(self, tmp_path):
        # type: (Path) -> None
        """Test listing a directory with a subdirectory."""
        test_dir = tmp_path / "dir"
        test_dir.mkdir()
        (test_dir / "subdir").mkdir()

        result = listdir_upath(str(test_dir))
        assert len(result) == 1
        assert isinstance(result[0], UPath)
        assert result[0].name == "subdir"
        assert result[0].is_dir()

    def test_mixed_entries(self, tmp_path):
        # type: (Path) -> None
        """Test listing a directory with mixed files and subdirectories."""
        test_dir = tmp_path / "mixed"
        test_dir.mkdir()
        (test_dir / "file1.txt").write_text("content1")
        (test_dir / "subdir").mkdir()
        (test_dir / "file2.txt").write_text("content2")

        result = listdir_upath(str(test_dir))
        names = [e.name for e in result]
        assert len(result) == 3
        assert "file1.txt" in names
        assert "file2.txt" in names
        assert "subdir" in names


class TestListdirUpathSorting:
    """Tests for sorting behavior."""

    def test_deterministic_sorting(self, tmp_path):
        # type: (Path) -> None
        """Test that entries are sorted deterministically."""
        test_dir = tmp_path / "sort"
        test_dir.mkdir()

        # Create files in non-alphabetical order
        names = ["zebra.txt", "apple.txt", "mango.txt", "Banana.txt", "APPLE.txt"]
        for name in names:
            (test_dir / name).write_text("test")

        # Check which files actually exist (case-insensitive filesystems may merge some)
        actual_files = [f.name for f in test_dir.iterdir() if f.is_file()]

        result = listdir_upath(str(test_dir))
        result_names = [e.name for e in result]

        # Verify the same files are returned
        assert set(result_names) == set(actual_files)

        # Verify they are sorted correctly using our deterministic algorithm
        from unicodedata import normalize

        expected_sorted = sorted(
            actual_files, key=lambda n: (normalize("NFC", n).encode("utf-8"), n.encode("utf-8"))
        )
        assert result_names == expected_sorted

    def test_unicode_sorting(self, tmp_path):
        # type: (Path) -> None
        """Test sorting with Unicode characters."""
        test_dir = tmp_path / "unicode"
        test_dir.mkdir()

        # Create files with various Unicode names
        unicode_names = ["café.txt", "über.txt", "日本.txt", "Москва.txt", "apple.txt"]
        for name in unicode_names:
            (test_dir / name).write_text("test")

        result = listdir_upath(str(test_dir))
        names = [e.name for e in result]

        # Verify all files are present
        assert len(names) == 5
        for expected in unicode_names:
            assert expected in names

        # Verify deterministic ordering based on NFC-normalized UTF-8
        expected_order = sorted(
            unicode_names, key=lambda n: (normalize("NFC", n).encode("utf-8"), n.encode("utf-8"))
        )
        assert names == expected_order

    def test_unicode_normalization_tie_breaking(self, tmp_path):
        # type: (Path) -> None
        """Test tie-breaking for entries with identical NFC-normalized names."""
        test_dir = tmp_path / "nfc"
        test_dir.mkdir()

        # Create two files that normalize to the same NFC form
        # but have different original byte sequences
        (test_dir / "Café.txt").write_text("NFC")  # NFC form
        (test_dir / "Cafe\u0301.txt").write_text("NFD")  # NFD form

        result = listdir_upath(str(test_dir))
        names = [e.name for e in result]

        # Both files should exist
        assert len(names) == 2

        # NFD form should come first due to secondary sort by original bytes
        assert names[0] == "Cafe\u0301.txt"
        assert names[1] == "Café.txt"


class TestListdirUpathSymlinks:
    """Tests for symlink handling."""

    def test_excludes_symlinks(self, tmp_path):
        # type: (Path) -> None
        """Test that symlinks are excluded from results."""
        test_dir = tmp_path / "symlinks"
        test_dir.mkdir()

        # Create real files and directories
        (test_dir / "real.txt").write_text("real")
        (test_dir / "realdir").mkdir()

        # Create symlinks
        (test_dir / "link.txt").symlink_to(test_dir / "real.txt")
        (test_dir / "linkdir").symlink_to(test_dir / "realdir")

        result = listdir_upath(str(test_dir))
        names = [e.name for e in result]

        assert len(result) == 2
        assert "real.txt" in names
        assert "realdir" in names
        assert "link.txt" not in names
        assert "linkdir" not in names


class TestListdirUpathInputTypes:
    """Tests for different input types."""

    def test_path_object_input(self, tmp_path):
        # type: (Path) -> None
        """Test using Path object as input."""
        test_dir = tmp_path / "path_obj"
        test_dir.mkdir()
        (test_dir / "file.txt").write_text("test")

        # Test with Path object
        result = listdir_upath(Path(str(test_dir)))
        assert len(result) == 1
        assert result[0].name == "file.txt"

    def test_string_path_input(self, tmp_path):
        # type: (Path) -> None
        """Test using string path as input."""
        test_dir = tmp_path / "string"
        test_dir.mkdir()
        (test_dir / "file.txt").write_text("test")

        # Test with string path
        result = listdir_upath(str(test_dir))
        assert len(result) == 1
        assert result[0].name == "file.txt"

    def test_upath_object_input(self, tmp_path):
        # type: (Path) -> None
        """Test using UPath object as input."""
        test_dir = tmp_path / "upath"
        test_dir.mkdir()
        (test_dir / "file.txt").write_text("test")

        # Test with UPath object
        upath = UPath(str(test_dir))
        result = listdir_upath(upath)
        assert len(result) == 1
        assert result[0].name == "file.txt"


class TestListdirUpathErrors:
    """Tests for error conditions."""

    def test_nonexistent_directory(self, tmp_path):
        # type: (Path) -> None
        """Test error handling for non-existent directory."""
        nonexistent = tmp_path / "nonexistent"

        with pytest.raises(FileNotFoundError, match="Directory not found"):
            listdir_upath(str(nonexistent))

    def test_file_instead_of_directory(self, tmp_path):
        # type: (Path) -> None
        """Test error handling when path is a file."""
        test_file = tmp_path / "file.txt"
        test_file.write_text("not a directory")

        with pytest.raises(NotADirectoryError, match="Path is not a directory"):
            listdir_upath(str(test_file))

    def test_backend_error_handling(self):
        # type: () -> None
        """Test handling of backend-specific errors during iteration."""

        # Create a mock path that raises an error during iteration
        class ErrorPath:
            def __init__(self):
                pass

            def exists(self):
                return True

            def is_dir(self):
                return True

            def iterdir(self):
                raise RuntimeError("Backend error during iteration")

            def __str__(self):
                return "error://test"

        # Pass the mock directly since we can't easily mock UPath constructor
        with pytest.raises(OSError, match="Error listing directory"):
            # We need to bypass UPath creation, so we'll test the error handling
            # by directly calling the function with our mock
            from iscc_sum import treewalk

            # Save original UPath
            original_upath = treewalk.UPath

            try:
                # Replace UPath temporarily
                class MockUPath:
                    def __new__(cls, path, **kwargs):
                        if isinstance(path, ErrorPath):
                            return path
                        return original_upath(path, **kwargs)

                treewalk.UPath = MockUPath
                listdir_upath(ErrorPath())
            finally:
                # Restore original UPath
                treewalk.UPath = original_upath


class TestListdirUpathMemoryFilesystem:
    """Tests for memory filesystem."""

    def test_empty_directory_memory(self):
        # type: () -> None
        """Test listing an empty directory in memory."""
        mem_path = UPath("memory:///test_empty_mem")
        mem_path.mkdir(parents=True, exist_ok=True)

        result = listdir_upath(mem_path)
        assert result == []

    def test_single_file_memory(self):
        # type: () -> None
        """Test listing a directory with a single file in memory."""
        mem_dir = UPath("memory:///test_single_mem")
        mem_dir.mkdir(parents=True, exist_ok=True)

        # Create a file
        mem_file = mem_dir / "file.txt"
        mem_file.write_text("test content")

        result = listdir_upath(mem_dir)
        assert len(result) == 1
        assert result[0].name == "file.txt"
        assert result[0].is_file()

    def test_mixed_entries_memory(self):
        # type: () -> None
        """Test listing a directory with mixed entries in memory."""
        mem_dir = UPath("memory:///test_mixed_mem")
        mem_dir.mkdir(parents=True, exist_ok=True)

        # Create files and directories
        (mem_dir / "file1.txt").write_text("content1")
        (mem_dir / "subdir").mkdir()
        (mem_dir / "file2.txt").write_text("content2")

        result = listdir_upath(mem_dir)
        names = [e.name for e in result]

        assert len(result) == 3
        assert "file1.txt" in names
        assert "file2.txt" in names
        assert "subdir" in names

    def test_unicode_memory(self):
        # type: () -> None
        """Test Unicode handling in memory filesystem."""
        mem_dir = UPath("memory:///test_unicode_mem")
        mem_dir.mkdir(parents=True, exist_ok=True)

        # Create files with Unicode names
        unicode_names = ["café.txt", "über.txt", "日本.txt"]
        for name in unicode_names:
            (mem_dir / name).write_text("test")

        result = listdir_upath(mem_dir)
        names = [e.name for e in result]

        assert len(names) == 3
        for expected in unicode_names:
            assert expected in names

    def test_backend_without_symlink_support(self):
        # type: () -> None
        """Test handling of backends that don't support symlink detection."""
        # Memory filesystem doesn't support symlinks, so all entries should be included
        mem_dir = UPath("memory:///test_no_symlink_mem")
        mem_dir.mkdir(parents=True, exist_ok=True)

        # Create some files
        (mem_dir / "file1.txt").write_text("content1")
        (mem_dir / "file2.txt").write_text("content2")

        result = listdir_upath(mem_dir)
        assert len(result) == 2

        # Verify that the is_symlink check is handled gracefully
        for entry in result:
            # Memory filesystem entries won't have is_symlink method
            assert not hasattr(entry, "is_symlink") or not entry.is_symlink()


class TestListdirUpathSpecialCases:
    """Test special cases and edge conditions."""

    def test_hidden_files(self, tmp_path):
        # type: (Path) -> None
        """Test handling of hidden files (dot files)."""
        test_dir = tmp_path / "hidden"
        test_dir.mkdir()

        (test_dir / ".hidden").write_text("hidden")
        (test_dir / "visible.txt").write_text("visible")
        (test_dir / ".another_hidden").write_text("hidden2")

        result = listdir_upath(str(test_dir))
        names = [e.name for e in result]

        # All files should be included
        assert len(names) == 3
        assert ".another_hidden" in names
        assert ".hidden" in names
        assert "visible.txt" in names

    def test_special_characters_in_names(self, tmp_path):
        # type: (Path) -> None
        """Test handling of special characters in filenames."""
        test_dir = tmp_path / "special"
        test_dir.mkdir()

        special_names = [
            "file with spaces.txt",
            "file-with-dashes.txt",
            "file_with_underscores.txt",
            "file.multiple.dots.txt",
        ]

        for name in special_names:
            (test_dir / name).write_text("test")

        result = listdir_upath(str(test_dir))
        names = [e.name for e in result]

        assert len(names) == len(special_names)
        for expected in special_names:
            assert expected in names

    def test_many_files(self, tmp_path):
        # type: (Path) -> None
        """Test with many files."""
        test_dir = tmp_path / "many"
        test_dir.mkdir()

        # Create 50 files
        for i in range(50):
            (test_dir / f"file_{i:03d}.txt").write_text(f"content{i}")

        result = listdir_upath(str(test_dir))
        assert len(result) == 50

        # Verify they're sorted correctly
        names = [e.name for e in result]
        assert names == sorted(names)

    def test_nested_upath_usage(self):
        # type: () -> None
        """Test that returned UPath objects work correctly."""
        mem_dir = UPath("memory:///test_nested_usage")
        mem_dir.mkdir(parents=True, exist_ok=True)

        # Create a subdirectory and file
        (mem_dir / "subdir").mkdir()
        (mem_dir / "subdir" / "nested.txt").write_text("nested content")

        # List and navigate
        result = listdir_upath(mem_dir)
        assert len(result) == 1

        # The returned UPath should be usable
        subdir = result[0]
        assert subdir.name == "subdir"
        assert subdir.is_dir()

        # Should be able to list the subdirectory
        nested_result = listdir_upath(subdir)
        assert len(nested_result) == 1
        assert nested_result[0].name == "nested.txt"


class TestListdirUpathConsistency:
    """Tests to ensure listdir_upath matches listdir behavior."""

    def test_sorting_consistency(self, tmp_path):
        # type: (Path) -> None
        """Test that sorting matches the original listdir function."""
        from iscc_sum.treewalk import listdir

        test_dir = tmp_path / "consistency"
        test_dir.mkdir()

        test_names = ["file3.txt", "File1.txt", "file2.txt", "café.txt", "über.txt"]
        for name in test_names:
            (test_dir / name).write_text("test")

        # Compare results from both functions
        listdir_result = listdir(str(test_dir))
        listdir_names = [e.name for e in listdir_result]

        upath_result = listdir_upath(str(test_dir))
        upath_names = [e.name for e in upath_result]

        assert listdir_names == upath_names

    def test_symlink_filtering_consistency(self, tmp_path):
        # type: (Path) -> None
        """Test that symlink filtering matches the original listdir."""
        from iscc_sum.treewalk import listdir

        test_dir = tmp_path / "symlinks_consistency"
        test_dir.mkdir()

        (test_dir / "real.txt").write_text("real")
        (test_dir / "link.txt").symlink_to(test_dir / "real.txt")

        # Compare results
        listdir_result = listdir(str(test_dir))
        listdir_names = [e.name for e in listdir_result]

        upath_result = listdir_upath(str(test_dir))
        upath_names = [e.name for e in upath_result]

        assert listdir_names == upath_names
        assert "link.txt" not in upath_names


class TestListdirUpathBackendSpecific:
    """Tests for specific backend behavior."""

    def test_file_protocol(self, tmp_path):
        # type: (Path) -> None
        """Test using file:// protocol explicitly."""
        test_dir = tmp_path / "file_protocol"
        test_dir.mkdir()
        (test_dir / "test.txt").write_text("test")

        # Test with file:// protocol
        file_url = f"file://{test_dir}"
        result = listdir_upath(file_url)

        assert len(result) == 1
        assert result[0].name == "test.txt"

    def test_symlink_exception_handling(self):
        # type: () -> None
        """Test handling of different symlink-related exceptions."""

        # Create custom entries that raise different exceptions
        class EntryWithNotImplemented:
            def __init__(self, name):
                self.name = name

            def is_symlink(self):
                raise NotImplementedError("Backend doesn't support symlinks")

        class EntryWithAttrError:
            def __init__(self, name):
                self.name = name

            def is_symlink(self):
                raise AttributeError("No symlink support")

        class EntryNormal:
            def __init__(self, name):
                self.name = name

            # No is_symlink method at all

        class TestPath:
            def __init__(self, entries):
                self._entries = entries

            def exists(self):
                return True

            def is_dir(self):
                return True

            def iterdir(self):
                return iter(self._entries)

            def __str__(self):
                return "test://path"

        # Test with various entry types
        entries = [
            EntryWithNotImplemented("file1.txt"),
            EntryWithAttrError("file2.txt"),
            EntryNormal("file3.txt"),
        ]

        from iscc_sum import treewalk

        # Save original UPath
        original_upath = treewalk.UPath

        try:
            # Replace UPath temporarily
            class MockUPath:
                def __new__(cls, path, **kwargs):
                    if isinstance(path, TestPath):
                        return path
                    return original_upath(path, **kwargs)

            treewalk.UPath = MockUPath

            test_path = TestPath(entries)
            result = listdir_upath(test_path)

            # All entries should be included despite symlink detection issues
            assert len(result) == 3

        finally:
            # Restore original UPath
            treewalk.UPath = original_upath
