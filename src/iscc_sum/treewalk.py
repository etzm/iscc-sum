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


def treewalk_ignore(path, ignore_file_name, root_path=None, ignore_spec=None):
    # type: (str|Path, str, Path|None, pathspec.PathSpec|None) -> Iterator[Path]
    """
    Walk a directory tree while respecting ignore-files.

    Yields .ignore files first, then other files, then recurses into directories.
    """
    path = Path(path).resolve(strict=True)
    if root_path is None:
        root_path = path

    # Load local ignore rules if present
    local_ignore = path / ignore_file_name
    if local_ignore.exists():
        with open(local_ignore, "r", encoding="utf-8") as f:
            new_spec = pathspec.PathSpec.from_lines(pathspec.patterns.GitWildMatchPattern, f)
            ignore_spec = new_spec if ignore_spec is None else ignore_spec + new_spec

    entries = listdir(path)
    dirs = [d for d in entries if d.is_dir()]
    files = [f for f in entries if f.is_file()]

    def should_ignore(file_path):
        if ignore_spec is None:
            return False
        rel_path = file_path.relative_to(root_path)
        # Check file pattern match or any parent directory match
        return ignore_spec.match_file(rel_path) or ignore_spec.match_file(str(rel_path) + "/")

    # First yield ignore files (except the current one)
    for file_entry in files:
        file_path = Path(file_entry.path)
        if file_entry.name.startswith(".") and file_entry.name.endswith("ignore") and file_path != local_ignore:
            if not should_ignore(file_path):
                yield file_path

    # Then yield non-ignore files
    for file_entry in files:
        file_path = Path(file_entry.path)
        if not (file_entry.name.startswith(".") and file_entry.name.endswith("ignore")):
            if not should_ignore(file_path):
                yield file_path

    # Then recurse into directories
    for dir_entry in dirs:
        dir_path = Path(dir_entry.path)
        if not should_ignore(dir_path):
            yield from treewalk_ignore(dir_path, ignore_file_name, root_path, ignore_spec)


def treewalk_iscc(path):
    # type: (str|Path) -> Iterator[Path]
    """
    Treewalk-Ignore extended with ISCC support.

    - Allways ignores all files ending with `.iscc.json`
    - Uses ignore rules from strandard .isccignore files.
    """
    path = Path(path).resolve(strict=True)

    # Use treewalk_ignore with .isccignore files
    for file_path in treewalk_ignore(path, ".isccignore"):
        # Skip files ending with .iscc.json
        if not file_path.name.endswith(".iscc.json"):
            yield file_path


def listdir(path):
    # type: (str|Path) -> list[DirEntry]
    """List directory entries with cross-platform stable sorting"""
    with os.scandir(path) as it:
        filtered = [e for e in it if not e.is_symlink()]
    return sorted(filtered, key=lambda e: normalize("NFC", e.name).encode("utf-8"))


if __name__ == "__main__":
    for entry in treewalk_iscc("../../"):
        print(entry.as_posix())
