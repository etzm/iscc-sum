# Deterministic Directory Tree Sorting Specification

## Purpose

Define a platform-agnostic method for enumerating and sorting files in a directory tree to enable reproducible
hash computation across different operating systems and filesystems.

## Scope

This specification covers the enumeration and ordering of file paths. Hash computation of file contents is
outside this specification's scope.

## Definitions

- **Regular file**: A file that stores data (S_ISREG in POSIX)
- **Directory tree**: A directory and all its subdirectories recursively
- **Relative path**: Path from the root directory to a file, excluding the root itself

## Requirements

### 1. File Enumeration

1.1. **Include** only regular files from the directory tree.

1.2. **Exclude** all other filesystem objects:

- Symbolic links (to files or directories)
- Directories (as entries themselves)
- Named pipes (FIFOs)
- Sockets
- Device files (block and character)
- Any filesystem object that cannot be accessed

1.3. **Traversal** must not follow symbolic links.

### 2. Path Representation

2.1. Paths must be **relative** to the root directory.

2.2. Path components must be separated by **forward slashes** (`/`).

2.3. Paths must be valid **UTF-8** strings.

2.4. Paths must be normalized to **Unicode Normalization Form C** (NFC).

2.5. Paths must **not** have:

- Leading slashes
- Trailing slashes
- Double slashes (`//`)
- Current directory references (`.`)
- Parent directory references (`..`)

### 3. Sorting Order

3.1. Sort paths by their **UTF-8 byte representation** in ascending lexicographic order.

3.2. Comparison must be performed on **raw bytes**, not Unicode code points or locale-specific collation.

3.3. **Case sensitivity**: Sorting is **always case-sensitive**. Upper case ASCII letters (A-Z) have lower byte
values than lower case letters (a-z), therefore sort first.

3.4. **Filesystem case sensitivity** does not affect sorting order:

- On case-sensitive filesystems (Linux ext4): Both "File.txt" and "file.txt" may exist and will be sorted
  separately
- On case-insensitive filesystems (Windows NTFS, macOS default): Only one variant can exist, but it sorts
  according to its actual case

### 4. Error Handling

4.1. Files that cannot be accessed (permission denied, file deleted during enumeration) must be **silently
skipped**.

4.2. Filenames that are not valid UTF-8 must be **silently skipped**.

4.3. The root directory must exist and be accessible, otherwise the operation must **fail immediately**.

## Example

Given directory structure:

```
root/
├── .hidden
├── café.txt
├── Café.txt
├── CAFE.txt
├── sub/
│   ├── File.txt
│   └── file.txt
└── link.txt -> café.txt
```

Result (ordered list):

```
.hidden
CAFE.txt
Café.txt
café.txt
sub/File.txt
sub/file.txt
```

Notes:

- Capital letters sort before lowercase (`CAFE.txt` before `Café.txt` before `café.txt`)
- On case-insensitive filesystems, some of these files cannot coexist
- `link.txt` is excluded (symbolic link)

## Implementation Notes

1. Use filesystem calls that do not follow symbolic links (e.g., `lstat` instead of `stat`).

2. Apply Unicode normalization after path construction but before sorting.

3. Hidden files (starting with `.`) are treated as regular files with no special handling.

4. Empty directories contribute no entries to the sorted list.

5. The byte sequence for "é" in NFC is `0xC3 0xA9`, while in NFD it would be `0x65 0xCC 0x81`. Always use NFC.

6. **Important**: Do not attempt to normalize case or detect case conflicts. Report files exactly as they exist
   on the filesystem.

## Rationale

- **Regular files only**: Special files have platform-specific behaviors that harm reproducibility.
- **No symlink following**: Prevents cycles and ensures consistent results.
- **Forward slashes**: Universal path separator across platforms.
- **UTF-8 + NFC**: Provides consistent encoding across platforms while supporting international filenames.
- **Byte-level sorting**: Ensures identical ordering regardless of locale settings.
- **Case-sensitive sorting**: Provides deterministic results across all platforms, even though case-insensitive
  filesystems may limit which files can coexist.
- **Silent error handling**: Provides deterministic results even with permission issues or race conditions.
