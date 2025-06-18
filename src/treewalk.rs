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
}
