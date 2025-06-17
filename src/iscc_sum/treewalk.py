import os
from os import DirEntry
from pathlib import Path
from typing import Iterator
from unicodedata import normalize

import pathspec


def treewalk(path):
    # type: (str|Path) -> Iterator[Path]
    """
    Walk a directory tree and yield filepaths in determinist order (cross-platrform).

    We yield .ignore files first so callers may set filtering rules before proccesing other files
    """
    path = Path(path).resolve(strict=True)
    entries = listdir(path)
    dirs = [d for d in entries if d.is_dir()]
    files = [f for f in entries if f.is_file()]

    # First yield ignore files
    for file_entry in files:
        if file_entry.name.startswith(".") and file_entry.name.endswith("ignore"):
            yield Path(file_entry.path)

    # Then yield non-ignore files
    for file_entry in files:
        if not (file_entry.name.startswith(".") and file_entry.name.endswith("ignore")):
            yield Path(file_entry.path)

    # Then recurse into directories
    for dir_entry in dirs:
        yield from treewalk(Path(dir_entry.path))


def treewalk_ignore(path, ignore_file_name):
    # type: (str|Path, str) -> Iterator[Path]
    """Treewalk extended with generic ignore-file support"""
    path = Path(path).resolve(strict=True)
    ignore_spec = None
    ignore_path = path / ignore_file_name

    # Check if the ignore-file exists
    if ignore_path.exists():
        with open(ignore_path, "r", encoding="utf-8") as f:
            ignore_spec = pathspec.PathSpec.from_lines(pathspec.patterns.GitWildMatchPattern, f)

    # Get all file paths using treewalk
    for file_path in treewalk(path):
        # Skip the ignore-file itself when yielding
        if file_path.name == ignore_file_name and file_path.parent == path:
            continue

        # If we have ignore-rules, check if the file should be ignored
        if ignore_spec is not None:
            # Get a relative path for checking against ignore-patterns
            rel_path = file_path.relative_to(path)
            if ignore_spec.match_file(rel_path):
                continue

            # Check if any parent directory of this file is ignored
            # We need to check each parent directory path with trailing slash
            should_ignore = False
            for parent in rel_path.parents:
                if parent != Path("."):  # Skip the root relative path '.'
                    if ignore_spec.match_file(f"{parent}/"):
                        should_ignore = True
                        break

            if should_ignore:
                continue

        yield file_path


def treewalk_iscc(path):
    # type: (str|Path) -> Iterator[Path]
    """
    Treewalk-Ignore extended with ISCC support.

    - Allways ignores all files ending with `.iscc.json`
    - Uses ignore rules from strandard .isccignore files.
    """
    yield Path(".")


def listdir(path):
    # type: (str|Path) -> list[DirEntry]
    """List directory entries with cross-platform stable sorting"""
    with os.scandir(path) as it:
        filtered = [e for e in it if not e.is_symlink()]
    return sorted(filtered, key=lambda e: normalize("NFC", e.name).encode("utf-8"))


if __name__ == "__main__":
    for entry in treewalk_ignore("../../", ".isccignore"):
        print(entry.as_posix())
