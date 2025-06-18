// Rust implementation of the treewalk algorithm for deterministic file tree traversal

use std::cmp::Ordering;
use std::fs;
use std::io;
use std::path::Path;
use unicode_normalization::UnicodeNormalization;

/// Represents a directory entry with type information
#[derive(Debug, Clone)]
pub struct DirEntry {
    pub name: String,
    pub path: std::path::PathBuf,
    pub is_dir: bool,
    pub is_file: bool,
}

/// Error types for treewalk operations
#[derive(Debug)]
pub enum TreewalkError {
    IoError(io::Error),
    InvalidPath(String),
}

impl From<io::Error> for TreewalkError {
    fn from(err: io::Error) -> Self {
        TreewalkError::IoError(err)
    }
}

impl std::fmt::Display for TreewalkError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            TreewalkError::IoError(err) => write!(f, "IO error: {}", err),
            TreewalkError::InvalidPath(path) => write!(f, "Invalid path: {}", path),
        }
    }
}

impl std::error::Error for TreewalkError {}

/// List directory entries with deterministic cross-platform sorting.
///
/// Returns directory entries sorted by NFC-normalized UTF-8 encoded names,
/// ensuring consistent ordering across different filesystems and locales.
/// Symlinks are excluded for security and consistency.
///
/// # Arguments
///
/// * `path` - Directory path to list
///
/// # Returns
///
/// Sorted vector of DirEntry objects (excluding symlinks)
pub fn listdir<P: AsRef<Path>>(path: P) -> Result<Vec<DirEntry>, TreewalkError> {
    let path = path.as_ref();
    let mut entries = Vec::new();

    // Read directory entries
    for entry in fs::read_dir(path)? {
        let entry = entry?;
        let metadata = entry.metadata()?;

        // Skip symlinks
        if metadata.is_symlink() {
            continue;
        }

        let name = entry
            .file_name()
            .into_string()
            .map_err(|_| TreewalkError::InvalidPath("Invalid UTF-8 in filename".to_string()))?;

        entries.push(DirEntry {
            name,
            path: entry.path(),
            is_dir: metadata.is_dir(),
            is_file: metadata.is_file(),
        });
    }

    // Sort entries by normalized name with original name as tie-breaker
    entries.sort_by(|a, b| {
        let a_normalized = a.name.nfc().collect::<String>();
        let b_normalized = b.name.nfc().collect::<String>();

        match a_normalized.as_bytes().cmp(b_normalized.as_bytes()) {
            Ordering::Equal => a.name.as_bytes().cmp(b.name.as_bytes()),
            other => other,
        }
    });

    Ok(entries)
}

/// Recursively walk a directory tree with deterministic ordering.
///
/// This function traverses the directory tree starting from the given path,
/// yielding file paths in a specific order:
/// 1. Ignore files (.*ignore pattern) from each directory level
/// 2. Regular files from each directory level
/// 3. Subdirectories are processed recursively
///
/// The ordering ensures that ignore files can be processed first for efficient
/// filtering in downstream processors.
///
/// # Arguments
///
/// * `path` - Root directory path to start traversal
///
/// # Returns
///
/// Iterator of absolute file paths (directories are traversed but not yielded)
pub fn treewalk<P: AsRef<Path>>(path: P) -> Result<Vec<std::path::PathBuf>, TreewalkError> {
    let root = path.as_ref();

    // Verify the path exists and is a directory
    if !root.exists() {
        return Err(TreewalkError::IoError(io::Error::new(
            io::ErrorKind::NotFound,
            format!("Path does not exist: {}", root.display()),
        )));
    }

    if !root.is_dir() {
        return Err(TreewalkError::IoError(io::Error::new(
            io::ErrorKind::InvalidInput,
            format!("Path is not a directory: {}", root.display()),
        )));
    }

    let mut result = Vec::new();
    treewalk_recursive(root, &mut result)?;
    Ok(result)
}

/// Helper function for recursive tree traversal
fn treewalk_recursive(
    dir: &Path,
    result: &mut Vec<std::path::PathBuf>,
) -> Result<(), TreewalkError> {
    // Get sorted entries from the directory
    let entries = listdir(dir)?;

    // Separate entries into files and directories
    let mut ignore_files = Vec::new();
    let mut regular_files = Vec::new();
    let mut directories = Vec::new();

    for entry in entries {
        if entry.is_dir {
            directories.push(entry);
        } else if entry.is_file {
            // Check if this is an ignore file (starts with '.' and ends with 'ignore')
            if entry.name.starts_with('.') && entry.name.ends_with("ignore") {
                ignore_files.push(entry);
            } else {
                regular_files.push(entry);
            }
        }
    }

    // Yield ignore files first
    for entry in &ignore_files {
        result.push(entry.path.clone());
    }

    // Yield regular files second
    for entry in &regular_files {
        result.push(entry.path.clone());
    }

    // Recursively process directories
    for entry in &directories {
        treewalk_recursive(&entry.path, result)?;
    }

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_error_conversion() {
        let io_err = io::Error::new(io::ErrorKind::NotFound, "test error");
        let treewalk_err: TreewalkError = io_err.into();
        match treewalk_err {
            TreewalkError::IoError(_) => (),
            _ => panic!("Expected IoError variant"),
        }
    }

    #[test]
    fn test_listdir_basic_sorting() {
        use std::fs::{self, File};
        use tempfile::TempDir;

        let temp_dir = TempDir::new().unwrap();
        let dir_path = temp_dir.path();

        // Create files in non-alphabetical order
        File::create(dir_path.join("zebra.txt")).unwrap();
        File::create(dir_path.join("apple.txt")).unwrap();
        File::create(dir_path.join("banana.txt")).unwrap();
        fs::create_dir(dir_path.join("directory")).unwrap();

        let entries = listdir(dir_path).unwrap();

        // Verify sorted order
        assert_eq!(entries.len(), 4);
        assert_eq!(entries[0].name, "apple.txt");
        assert_eq!(entries[1].name, "banana.txt");
        assert_eq!(entries[2].name, "directory");
        assert_eq!(entries[3].name, "zebra.txt");

        // Verify type detection
        assert!(entries[0].is_file);
        assert!(!entries[0].is_dir);
        assert!(entries[2].is_dir);
        assert!(!entries[2].is_file);
    }

    #[test]
    fn test_listdir_unicode_normalization() {
        use std::fs::File;
        use tempfile::TempDir;

        let temp_dir = TempDir::new().unwrap();
        let dir_path = temp_dir.path();

        // Create files with different Unicode representations
        // café (NFC: é as single codepoint U+00E9)
        File::create(dir_path.join("café")).unwrap();
        // café (NFD: e + combining acute accent U+0065 U+0301)
        File::create(dir_path.join("cafe\u{0301}")).unwrap();
        // Different file to ensure sorting works
        File::create(dir_path.join("cafd")).unwrap();

        let entries = listdir(dir_path).unwrap();

        // Should have all 3 files
        assert_eq!(entries.len(), 3);

        // Verify correct ordering - normalized forms should sort together
        assert_eq!(entries[0].name, "cafd");
        // The two café variants should be adjacent, original bytes determine order
        assert!(entries[1].name == "café" || entries[1].name == "cafe\u{0301}");
        assert!(entries[2].name == "café" || entries[2].name == "cafe\u{0301}");
    }

    #[test]
    fn test_listdir_duplicate_normalized_names() {
        use std::fs::File;
        use tempfile::TempDir;

        let temp_dir = TempDir::new().unwrap();
        let dir_path = temp_dir.path();

        // Create files that normalize to the same string
        // These will have the same normalized form but different original bytes
        File::create(dir_path.join("Å")).unwrap(); // U+00C5 (Latin Capital Letter A with Ring Above)
        File::create(dir_path.join("A\u{030A}")).unwrap(); // U+0041 U+030A (A + Combining Ring Above)
        File::create(dir_path.join("B")).unwrap(); // Regular B for comparison

        let entries = listdir(dir_path).unwrap();

        assert_eq!(entries.len(), 3);

        // All entries should be present
        let names: Vec<&str> = entries.iter().map(|e| e.name.as_str()).collect();
        assert!(names.contains(&"Å"));
        assert!(names.contains(&"A\u{030A}"));
        assert!(names.contains(&"B"));

        // The two forms of Å should be adjacent in the sorted list
        let a_ring_positions: Vec<usize> = entries
            .iter()
            .enumerate()
            .filter(|(_, e)| e.name == "Å" || e.name == "A\u{030A}")
            .map(|(i, _)| i)
            .collect();
        assert_eq!(a_ring_positions.len(), 2);
        assert_eq!(a_ring_positions[1] - a_ring_positions[0], 1); // They are adjacent
    }

    #[test]
    fn test_listdir_symlink_filtering() {
        use std::fs::{self, File};
        use tempfile::TempDir;

        let temp_dir = TempDir::new().unwrap();
        let dir_path = temp_dir.path();

        // Create a regular file and a directory
        let file_path = dir_path.join("regular.txt");
        File::create(&file_path).unwrap();
        let subdir_path = dir_path.join("subdir");
        fs::create_dir(&subdir_path).unwrap();

        // Create symlinks (Unix-specific, will be skipped on Windows)
        #[cfg(unix)]
        {
            use std::os::unix::fs::symlink;
            symlink(&file_path, dir_path.join("symlink_to_file")).unwrap();
            symlink(&subdir_path, dir_path.join("symlink_to_dir")).unwrap();
        }

        let entries = listdir(dir_path).unwrap();

        // Should only have the regular file and directory, no symlinks
        #[cfg(unix)]
        assert_eq!(entries.len(), 2);
        #[cfg(not(unix))]
        assert_eq!(entries.len(), 2); // No symlinks created on non-Unix

        let names: Vec<&str> = entries.iter().map(|e| e.name.as_str()).collect();
        assert!(names.contains(&"regular.txt"));
        assert!(names.contains(&"subdir"));
        assert!(!names.contains(&"symlink_to_file"));
        assert!(!names.contains(&"symlink_to_dir"));
    }

    #[test]
    fn test_listdir_empty_directory() {
        use tempfile::TempDir;

        let temp_dir = TempDir::new().unwrap();
        let entries = listdir(temp_dir.path()).unwrap();

        assert_eq!(entries.len(), 0);
    }

    #[test]
    fn test_listdir_nonexistent_path() {
        let result = listdir("/this/path/should/not/exist/anywhere");
        assert!(result.is_err());
        match result.unwrap_err() {
            TreewalkError::IoError(_) => (),
            _ => panic!("Expected IoError for nonexistent path"),
        }
    }

    #[test]
    fn test_listdir_file_not_directory() {
        use std::fs::File;
        use tempfile::TempDir;

        let temp_dir = TempDir::new().unwrap();
        let file_path = temp_dir.path().join("file.txt");
        File::create(&file_path).unwrap();

        let result = listdir(&file_path);
        assert!(result.is_err());
        match result.unwrap_err() {
            TreewalkError::IoError(_) => (),
            _ => panic!("Expected IoError when path is a file"),
        }
    }

    #[test]
    #[cfg(unix)]
    fn test_listdir_permission_denied() {
        use std::fs::{self, File};
        use std::os::unix::fs::PermissionsExt;
        use tempfile::TempDir;

        let temp_dir = TempDir::new().unwrap();
        let restricted_dir = temp_dir.path().join("restricted");
        fs::create_dir(&restricted_dir).unwrap();

        // Create a file inside before restricting permissions
        File::create(restricted_dir.join("file.txt")).unwrap();

        // Remove read permissions
        let mut perms = fs::metadata(&restricted_dir).unwrap().permissions();
        perms.set_mode(0o000);
        fs::set_permissions(&restricted_dir, perms).unwrap();

        let result = listdir(&restricted_dir);
        assert!(result.is_err());

        // Restore permissions for cleanup
        let mut perms = fs::metadata(&restricted_dir).unwrap().permissions();
        perms.set_mode(0o755);
        fs::set_permissions(&restricted_dir, perms).unwrap();
    }

    #[test]
    fn test_treewalk_basic() {
        use std::fs::{self, File};
        use tempfile::TempDir;

        let temp_dir = TempDir::new().unwrap();
        let root = temp_dir.path();

        // Create a simple directory structure
        File::create(root.join("file1.txt")).unwrap();
        File::create(root.join("file2.txt")).unwrap();
        fs::create_dir(root.join("subdir")).unwrap();
        File::create(root.join("subdir").join("file3.txt")).unwrap();

        let paths = treewalk(root).unwrap();

        // Should have 3 files total
        assert_eq!(paths.len(), 3);

        // Convert to relative paths for easier verification
        let relative_paths: Vec<String> = paths
            .iter()
            .map(|p| {
                p.strip_prefix(root)
                    .unwrap()
                    .to_string_lossy()
                    .replace('\\', "/")
            })
            .collect();

        assert!(relative_paths.contains(&"file1.txt".to_string()));
        assert!(relative_paths.contains(&"file2.txt".to_string()));
        assert!(relative_paths.contains(&"subdir/file3.txt".to_string()));
    }

    #[test]
    fn test_treewalk_ignore_file_priority() {
        use std::fs::File;
        use tempfile::TempDir;

        let temp_dir = TempDir::new().unwrap();
        let root = temp_dir.path();

        // Create files with .gitignore being yielded first
        File::create(root.join("zebra.txt")).unwrap();
        File::create(root.join(".gitignore")).unwrap();
        File::create(root.join("apple.txt")).unwrap();
        File::create(root.join(".customignore")).unwrap();

        let paths = treewalk(root).unwrap();

        assert_eq!(paths.len(), 4);

        // Convert to filenames only for verification
        let filenames: Vec<String> = paths
            .iter()
            .map(|p| p.file_name().unwrap().to_string_lossy().to_string())
            .collect();

        // Ignore files should come first
        assert_eq!(filenames[0], ".customignore");
        assert_eq!(filenames[1], ".gitignore");
        // Then regular files in sorted order
        assert_eq!(filenames[2], "apple.txt");
        assert_eq!(filenames[3], "zebra.txt");
    }

    #[test]
    fn test_treewalk_recursive_ordering() {
        use std::fs::{self, File};
        use tempfile::TempDir;

        let temp_dir = TempDir::new().unwrap();
        let root = temp_dir.path();

        // Create a more complex structure
        File::create(root.join("root.txt")).unwrap();
        File::create(root.join(".rootignore")).unwrap();

        fs::create_dir(root.join("a_dir")).unwrap();
        File::create(root.join("a_dir").join("a_file.txt")).unwrap();
        File::create(root.join("a_dir").join(".ignore")).unwrap();

        fs::create_dir(root.join("b_dir")).unwrap();
        File::create(root.join("b_dir").join("b_file.txt")).unwrap();

        let paths = treewalk(root).unwrap();

        // Convert to relative paths for verification
        let relative_paths: Vec<String> = paths
            .iter()
            .map(|p| {
                p.strip_prefix(root)
                    .unwrap()
                    .to_string_lossy()
                    .replace('\\', "/")
            })
            .collect();

        // Expected order:
        // 1. Root level ignore files
        assert_eq!(relative_paths[0], ".rootignore");
        // 2. Root level regular files
        assert_eq!(relative_paths[1], "root.txt");
        // 3. Subdirectory contents (a_dir first alphabetically)
        assert_eq!(relative_paths[2], "a_dir/.ignore");
        assert_eq!(relative_paths[3], "a_dir/a_file.txt");
        assert_eq!(relative_paths[4], "b_dir/b_file.txt");
    }

    #[test]
    fn test_treewalk_empty_directory() {
        use tempfile::TempDir;

        let temp_dir = TempDir::new().unwrap();
        let paths = treewalk(temp_dir.path()).unwrap();

        assert_eq!(paths.len(), 0);
    }

    #[test]
    fn test_treewalk_empty_subdirectories() {
        use std::fs;
        use tempfile::TempDir;

        let temp_dir = TempDir::new().unwrap();
        let root = temp_dir.path();

        // Create empty subdirectories
        fs::create_dir(root.join("empty1")).unwrap();
        fs::create_dir(root.join("empty2")).unwrap();
        fs::create_dir(root.join("empty1").join("nested_empty")).unwrap();

        let paths = treewalk(root).unwrap();

        // Should yield no files
        assert_eq!(paths.len(), 0);
    }

    #[test]
    fn test_treewalk_deeply_nested() {
        use std::fs::{self, File};
        use tempfile::TempDir;

        let temp_dir = TempDir::new().unwrap();
        let mut current = temp_dir.path().to_path_buf();

        // Create a deeply nested structure
        for i in 0..5 {
            current = current.join(format!("level{}", i));
            fs::create_dir(&current).unwrap();
            File::create(current.join(format!("file{}.txt", i))).unwrap();
        }

        let paths = treewalk(temp_dir.path()).unwrap();

        // Should have 5 files, one at each level
        assert_eq!(paths.len(), 5);

        // Verify all files are found
        for (i, path) in paths.iter().enumerate() {
            let filename = path.file_name().unwrap().to_string_lossy();
            assert_eq!(filename, format!("file{}.txt", i));
        }
    }

    #[test]
    fn test_treewalk_nonexistent_path() {
        let result = treewalk("/this/path/should/not/exist");
        assert!(result.is_err());
        match result.unwrap_err() {
            TreewalkError::IoError(e) => {
                assert_eq!(e.kind(), io::ErrorKind::NotFound);
            }
            _ => panic!("Expected IoError with NotFound"),
        }
    }

    #[test]
    fn test_treewalk_file_not_directory() {
        use std::fs::File;
        use tempfile::TempDir;

        let temp_dir = TempDir::new().unwrap();
        let file_path = temp_dir.path().join("file.txt");
        File::create(&file_path).unwrap();

        let result = treewalk(&file_path);
        assert!(result.is_err());
        match result.unwrap_err() {
            TreewalkError::IoError(e) => {
                assert_eq!(e.kind(), io::ErrorKind::InvalidInput);
            }
            _ => panic!("Expected IoError with InvalidInput"),
        }
    }

    #[test]
    #[cfg(unix)]
    fn test_treewalk_permission_denied() {
        use std::fs::{self, File};
        use std::os::unix::fs::PermissionsExt;
        use tempfile::TempDir;

        let temp_dir = TempDir::new().unwrap();
        let root = temp_dir.path();

        // Create a directory with a file, then remove permissions
        let restricted = root.join("restricted");
        fs::create_dir(&restricted).unwrap();
        File::create(restricted.join("file.txt")).unwrap();

        // Remove read permissions
        let mut perms = fs::metadata(&restricted).unwrap().permissions();
        perms.set_mode(0o000);
        fs::set_permissions(&restricted, perms).unwrap();

        // treewalk should fail when it tries to read the restricted directory
        let result = treewalk(root);
        assert!(result.is_err());

        // Restore permissions for cleanup
        let mut perms = fs::metadata(&restricted).unwrap().permissions();
        perms.set_mode(0o755);
        fs::set_permissions(&restricted, perms).unwrap();
    }

    #[test]
    fn test_treewalk_unicode_files() {
        use std::fs::File;
        use tempfile::TempDir;

        let temp_dir = TempDir::new().unwrap();
        let root = temp_dir.path();

        // Create files with Unicode names
        File::create(root.join("café.txt")).unwrap();
        File::create(root.join("日本語.txt")).unwrap();
        File::create(root.join("emoji🎉.txt")).unwrap();

        let paths = treewalk(root).unwrap();

        assert_eq!(paths.len(), 3);

        // Verify all files are found
        let filenames: Vec<String> = paths
            .iter()
            .map(|p| p.file_name().unwrap().to_string_lossy().to_string())
            .collect();

        assert!(filenames.contains(&"café.txt".to_string()));
        assert!(filenames.contains(&"日本語.txt".to_string()));
        assert!(filenames.contains(&"emoji🎉.txt".to_string()));
    }
}
