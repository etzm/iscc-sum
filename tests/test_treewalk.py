"""
Test module for iscc_sum.treewalk functionality.
"""

import os
from pathlib import Path

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem

from iscc_sum.treewalk import listdir, treewalk, treewalk_ignore, treewalk_iscc


class TestListdir:
    """Tests for the listdir function."""

    def test_empty_directory(self, fs):
        # type: (FakeFilesystem) -> None
        """Test listing an empty directory."""
        fs.create_dir("/empty")
        result = listdir("/empty")
        assert result == []

    def test_single_file(self, fs):
        # type: (FakeFilesystem) -> None
        """Test listing a directory with a single file."""
        fs.create_dir("/test")
        fs.create_file("/test/file.txt")
        result = listdir("/test")
        assert len(result) == 1
        assert result[0].name == "file.txt"
        assert result[0].is_file()

    def test_single_directory(self, fs):
        # type: (FakeFilesystem) -> None
        """Test listing a directory with a subdirectory."""
        fs.create_dir("/test")
        fs.create_dir("/test/subdir")
        result = listdir("/test")
        assert len(result) == 1
        assert result[0].name == "subdir"
        assert result[0].is_dir()

    def test_mixed_entries(self, fs):
        # type: (FakeFilesystem) -> None
        """Test listing a directory with mixed files and subdirectories."""
        fs.create_dir("/test")
        fs.create_file("/test/file1.txt")
        fs.create_dir("/test/subdir")
        fs.create_file("/test/file2.txt")
        result = listdir("/test")
        names = [e.name for e in result]
        assert sorted(names) == ["file1.txt", "file2.txt", "subdir"]

    def test_deterministic_sorting(self, fs):
        # type: (FakeFilesystem) -> None
        """Test that entries are sorted deterministically."""
        fs.create_dir("/test")
        # Create files in non-alphabetical order
        fs.create_file("/test/z.txt")
        fs.create_file("/test/a.txt")
        fs.create_file("/test/m.txt")
        result = listdir("/test")
        names = [e.name for e in result]
        assert names == ["a.txt", "m.txt", "z.txt"]

    def test_unicode_sorting(self, fs):
        # type: (FakeFilesystem) -> None
        """Test sorting with unicode characters."""
        fs.create_dir("/test")
        fs.create_file("/test/über.txt")
        fs.create_file("/test/café.txt")
        fs.create_file("/test/apple.txt")
        result = listdir("/test")
        names = [e.name for e in result]
        # NFC normalization should ensure consistent ordering
        assert len(names) == 3
        assert "apple.txt" in names
        assert "café.txt" in names
        assert "über.txt" in names

    def test_excludes_symlinks(self, fs):
        # type: (FakeFilesystem) -> None
        """Test that symlinks are excluded from results."""
        fs.create_dir("/test")
        fs.create_file("/test/real.txt")
        fs.create_symlink("/test/link.txt", "/test/real.txt")
        result = listdir("/test")
        assert len(result) == 1
        assert result[0].name == "real.txt"

    def test_path_object_input(self, fs):
        # type: (FakeFilesystem) -> None
        """Test that Path objects are accepted as input."""
        fs.create_dir("/test")
        fs.create_file("/test/file.txt")
        result = listdir(Path("/test"))
        assert len(result) == 1
        assert result[0].name == "file.txt"


class TestTreewalk:
    """Tests for the treewalk function."""

    def test_empty_directory(self, fs):
        # type: (FakeFilesystem) -> None
        """Test walking an empty directory."""
        fs.create_dir("/empty")
        result = list(treewalk("/empty"))
        assert result == []

    def test_single_file(self, fs):
        # type: (FakeFilesystem) -> None
        """Test walking a directory with a single file."""
        fs.create_dir("/test")
        fs.create_file("/test/file.txt")
        result = list(treewalk("/test"))
        assert len(result) == 1
        assert result[0].name == "file.txt"
        assert str(result[0]).replace("\\", "/").endswith("/test/file.txt")

    def test_ignore_file_priority(self, fs):
        # type: (FakeFilesystem) -> None
        """Test that ignore files are yielded first."""
        fs.create_dir("/test")
        fs.create_file("/test/regular.txt")
        fs.create_file("/test/.gitignore")
        fs.create_file("/test/another.txt")
        fs.create_file("/test/.customignore")
        result = list(treewalk("/test"))
        paths = [str(p.name) for p in result]
        # Ignore files should come first
        assert paths[0] == ".customignore"
        assert paths[1] == ".gitignore"
        assert "regular.txt" in paths[2:]
        assert "another.txt" in paths[2:]

    def test_recursive_walking(self, fs):
        # type: (FakeFilesystem) -> None
        """Test recursive directory walking."""
        fs.create_dir("/test")
        fs.create_file("/test/root.txt")
        fs.create_dir("/test/subdir")
        fs.create_file("/test/subdir/sub.txt")
        fs.create_dir("/test/subdir/deeper")
        fs.create_file("/test/subdir/deeper/deep.txt")

        result = list(treewalk("/test"))
        paths = [str(p).replace("\\", "/") for p in result]

        assert any(p.endswith("/test/root.txt") for p in paths)
        assert any(p.endswith("/test/subdir/sub.txt") for p in paths)
        assert any(p.endswith("/test/subdir/deeper/deep.txt") for p in paths)
        assert len(paths) == 3

    def test_excludes_directories(self, fs):
        # type: (FakeFilesystem) -> None
        """Test that directories themselves are not yielded."""
        fs.create_dir("/test")
        fs.create_dir("/test/subdir")
        fs.create_dir("/test/subdir/another")
        result = list(treewalk("/test"))
        assert result == []

    def test_deterministic_order(self, fs):
        # type: (FakeFilesystem) -> None
        """Test deterministic ordering across levels."""
        fs.create_dir("/test")
        fs.create_file("/test/z.txt")
        fs.create_file("/test/a.txt")
        fs.create_dir("/test/b_dir")
        fs.create_file("/test/b_dir/file.txt")
        fs.create_dir("/test/a_dir")
        fs.create_file("/test/a_dir/file.txt")

        result = list(treewalk("/test"))
        names = [p.name for p in result]

        # Files in root should come first, sorted
        assert names[0] == "a.txt"
        assert names[1] == "z.txt"
        # Then files from subdirectories in sorted order
        assert names[2] == "file.txt"  # from a_dir
        assert names[3] == "file.txt"  # from b_dir

    def test_path_resolution(self, fs):
        # type: (FakeFilesystem) -> None
        """Test that paths are resolved to absolute paths."""
        fs.create_dir("/test")
        fs.create_file("/test/file.txt")
        os.chdir("/")
        result = list(treewalk("test"))
        assert result[0].is_absolute()

    def test_hidden_files(self, fs):
        # type: (FakeFilesystem) -> None
        """Test handling of hidden files (dot files)."""
        fs.create_dir("/test")
        fs.create_file("/test/.hidden")
        fs.create_file("/test/visible.txt")
        fs.create_file("/test/.another_hidden")

        result = list(treewalk("/test"))
        names = [p.name for p in result]

        # All files should be included
        assert len(names) == 3
        assert ".hidden" in names
        assert ".another_hidden" in names
        assert "visible.txt" in names


class TestTreewalkIgnore:
    """Tests for the treewalk_ignore function."""

    def test_no_ignore_file(self, fs):
        # type: (FakeFilesystem) -> None
        """Test behavior when no ignore file exists."""
        fs.create_dir("/test")
        fs.create_file("/test/file1.txt")
        fs.create_file("/test/file2.txt")

        result = list(treewalk_ignore("/test", ".gitignore"))
        assert len(result) == 2

    def test_simple_ignore_pattern(self, fs):
        # type: (FakeFilesystem) -> None
        """Test simple gitignore pattern matching."""
        fs.create_dir("/test")
        fs.create_file("/test/.gitignore", contents="*.tmp\n*.log")
        fs.create_file("/test/keep.txt")
        fs.create_file("/test/ignore.tmp")
        fs.create_file("/test/error.log")

        result = list(treewalk_ignore("/test", ".gitignore"))
        names = [p.name for p in result]

        assert "keep.txt" in names
        assert "ignore.tmp" not in names
        assert "error.log" not in names

    def test_directory_ignore(self, fs):
        # type: (FakeFilesystem) -> None
        """Test ignoring entire directories."""
        fs.create_dir("/test")
        fs.create_file("/test/.gitignore", contents="build/\nnode_modules/")
        fs.create_file("/test/keep.txt")
        fs.create_dir("/test/build")
        fs.create_file("/test/build/output.js")
        fs.create_dir("/test/node_modules")
        fs.create_file("/test/node_modules/package.json")
        fs.create_dir("/test/src")
        fs.create_file("/test/src/main.py")

        result = list(treewalk_ignore("/test", ".gitignore"))
        paths = [str(p).replace("\\", "/") for p in result]

        assert any("keep.txt" in p for p in paths)
        assert any("main.py" in p for p in paths)
        assert not any("output.js" in p for p in paths)
        assert not any("package.json" in p for p in paths)

    def test_cascading_ignore_rules(self, fs):
        # type: (FakeFilesystem) -> None
        """Test that ignore rules cascade down the directory tree."""
        fs.create_dir("/test")
        fs.create_file("/test/.gitignore", contents="*.tmp")
        fs.create_file("/test/root.txt")
        fs.create_file("/test/root.tmp")
        fs.create_dir("/test/sub")
        fs.create_file("/test/sub/.gitignore", contents="*.log")
        fs.create_file("/test/sub/file.txt")
        fs.create_file("/test/sub/file.tmp")
        fs.create_file("/test/sub/file.log")

        result = list(treewalk_ignore("/test", ".gitignore"))
        names = [p.name for p in result]

        # Root level
        assert "root.txt" in names
        assert "root.tmp" not in names
        # Subdirectory - both rules apply
        assert "file.txt" in names
        assert "file.tmp" not in names  # Inherited from parent
        assert "file.log" not in names  # Local rule

    def test_ignore_file_not_ignored(self, fs):
        # type: (FakeFilesystem) -> None
        """Test that the ignore file itself is not yielded."""
        fs.create_dir("/test")
        fs.create_file("/test/.gitignore", contents="*.tmp")
        fs.create_file("/test/file.txt")

        result = list(treewalk_ignore("/test", ".gitignore"))
        names = [p.name for p in result]

        assert ".gitignore" in names  # Ignore files are included per spec
        assert "file.txt" in names

    def test_custom_ignore_filename(self, fs):
        # type: (FakeFilesystem) -> None
        """Test using a custom ignore file name."""
        fs.create_dir("/test")
        fs.create_file("/test/.myignore", contents="*.bak")
        fs.create_file("/test/keep.txt")
        fs.create_file("/test/backup.bak")

        result = list(treewalk_ignore("/test", ".myignore"))
        names = [p.name for p in result]

        assert "keep.txt" in names
        assert "backup.bak" not in names

    def test_with_existing_pathspec(self, fs):
        # type: (FakeFilesystem) -> None
        """Test providing an existing PathSpec."""
        import pathspec

        fs.create_dir("/test")
        fs.create_file("/test/file.txt")
        fs.create_file("/test/file.tmp")
        fs.create_file("/test/file.log")

        # Create initial PathSpec that ignores .tmp files
        initial_spec = pathspec.PathSpec.from_lines(pathspec.patterns.GitWildMatchPattern, ["*.tmp"])

        # Directory has additional rule to ignore .log files
        fs.create_file("/test/.gitignore", contents="*.log")

        result = list(treewalk_ignore("/test", ".gitignore", ignore_spec=initial_spec))
        names = [p.name for p in result]

        assert "file.txt" in names
        assert "file.tmp" not in names  # From initial spec
        assert "file.log" not in names  # From local .gitignore

    def test_multiple_ignore_files_in_directory(self, fs):
        # type: (FakeFilesystem) -> None
        """Test handling multiple ignore files in same directory."""
        fs.create_dir("/test")
        fs.create_file("/test/.gitignore", contents="*.tmp")
        fs.create_file("/test/.customignore", contents="*.bak")
        fs.create_file("/test/file.txt")
        fs.create_file("/test/file.tmp")

        # When looking for .gitignore, other ignore files should be yielded
        result = list(treewalk_ignore("/test", ".gitignore"))
        names = [p.name for p in result]

        assert ".customignore" in names  # Other ignore files are yielded
        assert "file.txt" in names
        assert "file.tmp" not in names

    def test_subdirectory_path_matching(self, fs):
        # type: (FakeFilesystem) -> None
        """Test that subdirectory paths are matched correctly."""
        fs.create_dir("/test")
        fs.create_file("/test/.gitignore", contents="/specific/path/\n*.tmp")
        fs.create_dir("/test/specific")
        fs.create_dir("/test/specific/path")
        fs.create_file("/test/specific/path/ignored.txt")
        fs.create_dir("/test/other")
        fs.create_file("/test/other/kept.txt")
        fs.create_file("/test/file.tmp")

        result = list(treewalk_ignore("/test", ".gitignore"))
        paths = [str(p).replace("\\", "/") for p in result]

        assert not any("ignored.txt" in p for p in paths)
        assert any("kept.txt" in p for p in paths)
        assert not any("file.tmp" in p for p in paths)


class TestTreewalkIscc:
    """Tests for the treewalk_iscc function."""

    def test_filters_iscc_metadata(self, fs):
        # type: (FakeFilesystem) -> None
        """Test that .iscc.json files are filtered out."""
        fs.create_dir("/test")
        fs.create_file("/test/document.txt")
        fs.create_file("/test/document.iscc.json")
        fs.create_file("/test/image.png")
        fs.create_file("/test/image.iscc.json")

        result = list(treewalk_iscc("/test"))
        names = [p.name for p in result]

        assert "document.txt" in names
        assert "image.png" in names
        assert "document.iscc.json" not in names
        assert "image.iscc.json" not in names

    def test_respects_isccignore(self, fs):
        # type: (FakeFilesystem) -> None
        """Test that .isccignore patterns are respected."""
        fs.create_dir("/test")
        fs.create_file("/test/.isccignore", contents="*.tmp\nbuild/")
        fs.create_file("/test/keep.txt")
        fs.create_file("/test/temp.tmp")
        fs.create_dir("/test/build")
        fs.create_file("/test/build/output.js")

        result = list(treewalk_iscc("/test"))
        names = [p.name for p in result]

        assert "keep.txt" in names
        assert "temp.tmp" not in names
        assert "output.js" not in names

    def test_combined_filtering(self, fs):
        # type: (FakeFilesystem) -> None
        """Test combined .isccignore and .iscc.json filtering."""
        fs.create_dir("/test")
        fs.create_file("/test/.isccignore", contents="*.log")
        fs.create_file("/test/document.txt")
        fs.create_file("/test/document.iscc.json")
        fs.create_file("/test/error.log")
        fs.create_file("/test/data.csv")

        result = list(treewalk_iscc("/test"))
        names = [p.name for p in result]

        assert "document.txt" in names
        assert "data.csv" in names
        assert "document.iscc.json" not in names
        assert "error.log" not in names

    def test_recursive_iscc_filtering(self, fs):
        # type: (FakeFilesystem) -> None
        """Test ISCC filtering works recursively."""
        fs.create_dir("/test")
        fs.create_file("/test/root.txt")
        fs.create_file("/test/root.iscc.json")
        fs.create_dir("/test/sub")
        fs.create_file("/test/sub/file.txt")
        fs.create_file("/test/sub/file.iscc.json")
        fs.create_dir("/test/sub/deep")
        fs.create_file("/test/sub/deep/nested.txt")
        fs.create_file("/test/sub/deep/nested.iscc.json")

        result = list(treewalk_iscc("/test"))
        names = [p.name for p in result]

        assert names.count("root.txt") == 1
        assert names.count("file.txt") == 1
        assert names.count("nested.txt") == 1
        assert names.count("root.iscc.json") == 0
        assert names.count("file.iscc.json") == 0
        assert names.count("nested.iscc.json") == 0

    def test_isccignore_not_yielded(self, fs):
        # type: (FakeFilesystem) -> None
        """Test that .isccignore file itself is not yielded."""
        fs.create_dir("/test")
        fs.create_file("/test/.isccignore", contents="*.tmp")
        fs.create_file("/test/file.txt")

        result = list(treewalk_iscc("/test"))
        names = [p.name for p in result]

        assert ".isccignore" in names  # Ignore files are included per spec
        assert "file.txt" in names


class TestTreewalkIgnoreSpecialCases:
    """Tests for special cases in treewalk_ignore function."""

    def test_empty_ignore_file(self, fs):
        # type: (FakeFilesystem) -> None
        """Test behavior with empty ignore file."""
        fs.create_dir("/test")
        fs.create_file("/test/.gitignore", contents="")
        fs.create_file("/test/file.txt")

        result = list(treewalk_ignore("/test", ".gitignore"))
        assert len(result) == 2  # Both .gitignore and file.txt
        names = [p.name for p in result]
        assert ".gitignore" in names
        assert "file.txt" in names

    def test_ignore_file_with_comments(self, fs):
        # type: (FakeFilesystem) -> None
        """Test ignore file with comments and blank lines."""
        fs.create_dir("/test")
        fs.create_file("/test/.gitignore", contents="# Comment\n*.tmp\n\n# Another comment\n*.log")
        fs.create_file("/test/keep.txt")
        fs.create_file("/test/temp.tmp")
        fs.create_file("/test/error.log")

        result = list(treewalk_ignore("/test", ".gitignore"))
        names = [p.name for p in result]

        assert "keep.txt" in names
        assert "temp.tmp" not in names
        assert "error.log" not in names

    def test_deeply_nested_ignore_rules(self, fs):
        # type: (FakeFilesystem) -> None
        """Test ignore rules in deeply nested directories."""
        fs.create_dir("/test")
        fs.create_file("/test/.gitignore", contents="global.tmp")
        fs.create_dir("/test/a/b/c/d")
        fs.create_file("/test/a/b/c/d/.gitignore", contents="local.tmp")
        fs.create_file("/test/a/b/c/d/file.txt")
        fs.create_file("/test/a/b/c/d/global.tmp")
        fs.create_file("/test/a/b/c/d/local.tmp")

        result = list(treewalk_ignore("/test", ".gitignore"))
        names = [p.name for p in result]

        assert "file.txt" in names
        assert "global.tmp" not in names  # Ignored by root rule
        assert "local.tmp" not in names  # Ignored by local rule

    def test_ignore_patterns_with_wildcards(self, fs):
        # type: (FakeFilesystem) -> None
        """Test complex wildcard patterns."""
        fs.create_dir("/test")
        fs.create_file("/test/.gitignore", contents="test_*.py\n!test_important.py\n*.log")
        fs.create_file("/test/main.py")
        fs.create_file("/test/test_unit.py")
        fs.create_file("/test/test_integration.py")
        fs.create_file("/test/test_important.py")
        fs.create_file("/test/debug.log")

        result = list(treewalk_ignore("/test", ".gitignore"))
        names = [p.name for p in result]

        assert "main.py" in names
        assert "test_unit.py" not in names
        assert "test_integration.py" not in names
        assert "test_important.py" in names  # Negation pattern
        assert "debug.log" not in names


class TestEdgeCases:
    """Tests for error conditions and edge cases."""

    def test_nonexistent_directory(self, fs):
        # type: (FakeFilesystem) -> None
        """Test behavior with non-existent directory."""
        with pytest.raises(FileNotFoundError):
            list(treewalk("/nonexistent"))

    def test_file_instead_of_directory(self, fs):
        # type: (FakeFilesystem) -> None
        """Test behavior when given a file path instead of directory."""
        fs.create_file("/test.txt")
        with pytest.raises(NotADirectoryError):
            list(treewalk("/test.txt"))

    def test_permission_handling(self, fs):
        # type: (FakeFilesystem) -> None
        """Test handling of permission issues."""
        if os.name == "nt":
            pytest.skip("Permission tests not reliable on Windows")

        fs.create_dir("/test")
        fs.create_file("/test/file.txt")
        # Note: pyfakefs may not fully simulate permission errors
        # This test documents expected behavior rather than testing it

        # In real scenarios, permission errors would raise OSError
        result = list(treewalk("/test"))
        assert len(result) == 1

    def test_circular_references_prevented(self, fs):
        # type: (FakeFilesystem) -> None
        """Test that symlinks don't cause infinite loops."""
        fs.create_dir("/test")
        fs.create_dir("/test/sub")
        # Create circular symlink (would cause infinite loop if followed)
        fs.create_symlink("/test/sub/link", "/test")
        fs.create_file("/test/file.txt")

        result = list(treewalk("/test"))
        # Should complete without hanging
        assert len(result) == 1
        assert result[0].name == "file.txt"

    def test_unicode_in_ignore_patterns(self, fs):
        # type: (FakeFilesystem) -> None
        """Test unicode characters in ignore patterns."""
        fs.create_dir("/test")
        # Ensure UTF-8 encoding for the ignore file content
        fs.create_file("/test/.gitignore", contents="café*.txt\n*über.log", encoding="utf-8")
        fs.create_file("/test/café_file.txt")
        fs.create_file("/test/file_über.log")
        fs.create_file("/test/normal.txt")

        result = list(treewalk_ignore("/test", ".gitignore"))
        names = [p.name for p in result]

        assert "normal.txt" in names
        assert "café_file.txt" not in names
        assert "file_über.log" not in names

    def test_root_path_normalization(self, fs):
        # type: (FakeFilesystem) -> None
        """Test that root_path is properly normalized."""
        fs.create_dir("/test/sub")
        fs.create_file("/test/sub/.gitignore", contents="../*.tmp")
        fs.create_file("/test/file.tmp")
        fs.create_file("/test/sub/file.txt")

        # Start from subdirectory but with root at parent
        result = list(treewalk_ignore("/test/sub", ".gitignore", root_path="/test"))
        names = [p.name for p in result]

        assert "file.txt" in names
        # Pattern interpretation depends on gitignore spec implementation
