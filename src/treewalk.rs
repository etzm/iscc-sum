// Rust implementation of the treewalk algorithm for deterministic file tree traversal

use globset::{Glob, GlobSet, GlobSetBuilder};
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

/// Represents a single gitignore pattern with metadata
#[derive(Debug, Clone)]
struct PatternEntry {
    /// The original pattern string (with ! prefix if applicable)
    #[allow(dead_code)]
    original: String,
    /// The pattern string without ! prefix
    pattern: String,
    /// True if this is a whitelist pattern (starts with !)
    is_whitelist: bool,
    /// Line number in the ignore file (for precedence)
    line_number: usize,
}

/// Wrapper around GlobSet for handling gitignore-style patterns
#[derive(Debug, Clone, Default)]
pub struct IgnoreSpec {
    /// All patterns in order of appearance
    entries: Vec<PatternEntry>,
}

impl IgnoreSpec {
    /// Create a new empty IgnoreSpec
    pub fn new() -> Self {
        Self::default()
    }

    /// Parse gitignore-style patterns from lines
    pub fn from_lines<I, S>(lines: I) -> Result<Self, TreewalkError>
    where
        I: IntoIterator<Item = S>,
        S: AsRef<str>,
    {
        let mut entries = Vec::new();
        let mut line_number = 0;

        for line in lines {
            let line = line.as_ref().trim();

            // Skip empty lines and comments
            if line.is_empty() || line.starts_with('#') {
                continue;
            }

            // Check for negation pattern
            let (pattern, is_whitelist) = if let Some(stripped) = line.strip_prefix('!') {
                // Remove the ! prefix
                (stripped, true)
            } else {
                (line, false)
            };

            entries.push(PatternEntry {
                original: line.to_string(),
                pattern: pattern.to_string(),
                is_whitelist,
                line_number,
            });

            line_number += 1;
        }

        Ok(IgnoreSpec { entries })
    }

    /// Combine two IgnoreSpec instances
    pub fn combine(&self, other: &IgnoreSpec) -> IgnoreSpec {
        let mut entries = self.entries.clone();

        // When combining, we need to adjust line numbers to maintain precedence
        let offset = self.entries.len();
        for mut entry in other.entries.clone() {
            entry.line_number += offset;
            entries.push(entry);
        }

        IgnoreSpec { entries }
    }

    /// Build separate GlobSets for ignore and whitelist patterns
    #[allow(dead_code)]
    fn build_globsets(&self) -> Result<(GlobSet, GlobSet), TreewalkError> {
        let mut ignore_builder = GlobSetBuilder::new();
        let mut whitelist_builder = GlobSetBuilder::new();

        for entry in &self.entries {
            // Convert gitignore pattern to glob pattern
            let glob_pattern = if entry.pattern.ends_with('/') {
                // Directory pattern - match the directory and everything under it
                format!("{}**", entry.pattern)
            } else if let Some(stripped) = entry.pattern.strip_prefix('/') {
                // Anchored pattern - match from root
                stripped.to_string()
            } else if entry.pattern.contains('/') && !entry.pattern.starts_with("**/") {
                // Pattern with slash but not starting with **/ - make it relative
                format!("**/{}", entry.pattern)
            } else {
                // Simple pattern - match anywhere
                format!("**/{}", entry.pattern)
            };

            let glob = Glob::new(&glob_pattern).map_err(|e| {
                TreewalkError::InvalidPath(format!("Invalid pattern '{}': {}", entry.pattern, e))
            })?;

            if entry.is_whitelist {
                whitelist_builder.add(glob);
            } else {
                ignore_builder.add(glob);
            }
        }

        let ignore_set = ignore_builder.build().map_err(|e| {
            TreewalkError::InvalidPath(format!("Failed to build ignore set: {}", e))
        })?;
        let whitelist_set = whitelist_builder.build().map_err(|e| {
            TreewalkError::InvalidPath(format!("Failed to build whitelist set: {}", e))
        })?;

        Ok((ignore_set, whitelist_set))
    }

    /// Check if a path matches any ignore pattern
    pub fn matches<P: AsRef<Path>>(&self, path: P) -> Result<bool, TreewalkError> {
        self.matches_with_precedence(path.as_ref(), false)
    }

    /// Check if a path matches as a directory (with trailing slash)
    pub fn matches_dir<P: AsRef<Path>>(&self, path: P) -> Result<bool, TreewalkError> {
        self.matches_with_precedence(path.as_ref(), true)
    }

    /// Internal method that properly handles precedence
    fn matches_with_precedence(&self, path: &Path, is_dir: bool) -> Result<bool, TreewalkError> {
        let path_str = path.to_string_lossy();

        // For directories, also check with trailing slash
        let dir_path = if is_dir {
            Some(format!("{}/", path_str))
        } else {
            None
        };

        // Find all matching patterns and respect their order (last match wins)
        let mut should_ignore = false;

        for entry in &self.entries {
            let glob_pattern = if entry.pattern.ends_with('/') {
                format!("{}**", entry.pattern)
            } else if let Some(stripped) = entry.pattern.strip_prefix('/') {
                stripped.to_string()
            } else {
                // Both cases: pattern with slash or simple pattern - match anywhere
                format!("**/{}", entry.pattern)
            };

            // Try to match the pattern
            if let Ok(glob) = Glob::new(&glob_pattern) {
                let matches = glob.compile_matcher().is_match(path)
                    || (is_dir
                        && dir_path
                            .as_ref()
                            .is_some_and(|dp| glob.compile_matcher().is_match(dp.as_str())));

                if matches {
                    // Last matching pattern determines the outcome
                    should_ignore = !entry.is_whitelist;
                }
            }
        }

        Ok(should_ignore)
    }

    /// Check if a directory has any whitelisted content (for traversal decisions)
    pub fn has_whitelisted_content(&self, dir_path: &Path) -> Result<bool, TreewalkError> {
        let dir_str = dir_path.to_string_lossy();

        for entry in &self.entries {
            if !entry.is_whitelist {
                continue;
            }

            // Check if this whitelist pattern could match something under this directory
            if entry.pattern.starts_with(&format!("{}/", dir_str))
                || entry.pattern.starts_with(&format!("{}", dir_str))
            {
                return Ok(true);
            }

            // Check if pattern could match files under this directory
            // For example, !build/dist/ should allow traversal into build/
            let parts: Vec<&str> = entry.pattern.split('/').collect();
            let dir_parts: Vec<&str> = dir_str.split('/').collect();

            if parts.len() > dir_parts.len() {
                let mut matches = true;
                for (i, dir_part) in dir_parts.iter().enumerate() {
                    if parts[i] != *dir_part {
                        matches = false;
                        break;
                    }
                }
                if matches {
                    return Ok(true);
                }
            }
        }

        Ok(false)
    }
}

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

/// Walk a directory tree while respecting ignore file patterns.
///
/// Yields paths in deterministic order while filtering based on accumulated
/// ignore patterns from the root down to each subdirectory.
///
/// # Arguments
///
/// * `path` - Directory to walk
/// * `ignore_file_name` - Name of the ignore-file to look for (e.g., ".gitignore")
/// * `root_path` - Root directory for relative path calculations (defaults to the path argument)
/// * `ignore_spec` - Existing IgnoreSpec with ignored patterns to extend
///
/// # Returns
///
/// Iterator of absolute file paths for non-ignored files
pub fn treewalk_ignore<P: AsRef<Path>>(
    path: P,
    ignore_file_name: &str,
    root_path: Option<&Path>,
    ignore_spec: Option<&IgnoreSpec>,
) -> Result<Vec<std::path::PathBuf>, TreewalkError> {
    let path = path.as_ref();
    let root_path = root_path.unwrap_or(path);

    // Verify the path exists and is a directory
    if !path.exists() {
        return Err(TreewalkError::IoError(io::Error::new(
            io::ErrorKind::NotFound,
            format!("Path does not exist: {}", path.display()),
        )));
    }

    if !path.is_dir() {
        return Err(TreewalkError::IoError(io::Error::new(
            io::ErrorKind::InvalidInput,
            format!("Path is not a directory: {}", path.display()),
        )));
    }

    let mut result = Vec::new();
    let base_spec = ignore_spec.cloned().unwrap_or_else(IgnoreSpec::new);
    treewalk_ignore_recursive(path, ignore_file_name, root_path, &base_spec, &mut result)?;
    Ok(result)
}

/// Helper function for recursive tree traversal with ignore patterns
fn treewalk_ignore_recursive(
    dir: &Path,
    ignore_file_name: &str,
    root_path: &Path,
    ignore_spec: &IgnoreSpec,
    result: &mut Vec<std::path::PathBuf>,
) -> Result<(), TreewalkError> {
    // Check for ignore file in current directory and update spec
    let mut current_spec = ignore_spec.clone();
    let ignore_file_path = dir.join(ignore_file_name);

    if ignore_file_path.exists() && ignore_file_path.is_file() {
        let contents = fs::read_to_string(&ignore_file_path).map_err(TreewalkError::IoError)?;
        let lines: Vec<&str> = contents.lines().collect();
        let new_spec = IgnoreSpec::from_lines(lines)?;
        current_spec = current_spec.combine(&new_spec);
    }

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
            // Check if this is an ignore file
            if entry.name.starts_with('.') && entry.name.ends_with("ignore") {
                ignore_files.push(entry);
            } else {
                regular_files.push(entry);
            }
        }
    }

    // Helper to check if a path should be ignored
    let should_ignore = |path: &Path| -> Result<bool, TreewalkError> {
        let rel_path = path.strip_prefix(root_path).map_err(|_| {
            TreewalkError::InvalidPath(format!(
                "Failed to compute relative path for: {}",
                path.display()
            ))
        })?;
        current_spec.matches(rel_path)
    };

    // Yield ignore files first (they are not filtered)
    for entry in &ignore_files {
        if !should_ignore(&entry.path)? {
            result.push(entry.path.clone());
        }
    }

    // Yield regular files second
    for entry in &regular_files {
        if !should_ignore(&entry.path)? {
            result.push(entry.path.clone());
        }
    }

    // Recursively process directories (check if directory itself is ignored)
    for entry in &directories {
        let rel_path = entry.path.strip_prefix(root_path).map_err(|_| {
            TreewalkError::InvalidPath(format!(
                "Failed to compute relative path for: {}",
                entry.path.display()
            ))
        })?;

        // Check if directory should be excluded
        // Also check if it has whitelisted content that should be traversed
        let is_ignored = current_spec.matches_dir(rel_path)?;
        let has_whitelisted = current_spec.has_whitelisted_content(rel_path)?;

        if !is_ignored || has_whitelisted {
            treewalk_ignore_recursive(
                &entry.path,
                ignore_file_name,
                root_path,
                &current_spec,
                result,
            )?;
        }
    }

    Ok(())
}

/// Walk a directory tree with ISCC-specific ignore rules.
///
/// Automatically filters out:
/// - Files ending with '.iscc.json' (ISCC metadata files)
/// - Paths matching patterns in '.isccignore' files
///
/// Uses the same deterministic ordering as treewalk_ignore.
///
/// # Arguments
///
/// * `path` - Directory path to walk
///
/// # Returns
///
/// Iterator of absolute file paths for non-ignored, non-ISCC metadata files
pub fn treewalk_iscc<P: AsRef<Path>>(path: P) -> Result<Vec<std::path::PathBuf>, TreewalkError> {
    let path = path.as_ref();

    // Use treewalk_ignore with .isccignore files
    let all_paths = treewalk_ignore(path, ".isccignore", None, None)?;

    // Filter out files ending with .iscc.json
    let filtered_paths: Vec<std::path::PathBuf> = all_paths
        .into_iter()
        .filter(|p| {
            p.file_name()
                .and_then(|name| name.to_str())
                .map(|name| !name.ends_with(".iscc.json"))
                .unwrap_or(true)
        })
        .collect();

    Ok(filtered_paths)
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

    #[test]
    fn test_ignore_spec_from_lines() {
        // Test parsing basic patterns
        let lines = vec![
            "*.tmp",
            "# comment",
            "",
            "build/",
            "/src/*.log",
            "!important.log",
        ];
        let spec = IgnoreSpec::from_lines(lines).unwrap();

        assert_eq!(spec.entries.len(), 4);
        assert_eq!(spec.entries[0].pattern, "*.tmp");
        assert!(!spec.entries[0].is_whitelist);
        assert_eq!(spec.entries[1].pattern, "build/");
        assert!(!spec.entries[1].is_whitelist);
        assert_eq!(spec.entries[2].pattern, "/src/*.log");
        assert!(!spec.entries[2].is_whitelist);
        assert_eq!(spec.entries[3].pattern, "important.log");
        assert!(spec.entries[3].is_whitelist);
    }

    #[test]
    fn test_ignore_spec_combine() {
        let spec1 = IgnoreSpec::from_lines(vec!["*.tmp", "*.log"]).unwrap();
        let spec2 = IgnoreSpec::from_lines(vec!["build/", "dist/", "!build/important/"]).unwrap();

        let combined = spec1.combine(&spec2);
        assert_eq!(combined.entries.len(), 5);
        assert_eq!(combined.entries[0].pattern, "*.tmp");
        assert_eq!(combined.entries[1].pattern, "*.log");
        assert_eq!(combined.entries[2].pattern, "build/");
        assert_eq!(combined.entries[3].pattern, "dist/");
        assert_eq!(combined.entries[4].pattern, "build/important/");
        assert!(combined.entries[4].is_whitelist);

        // Check line numbers are adjusted correctly
        assert_eq!(combined.entries[0].line_number, 0);
        assert_eq!(combined.entries[1].line_number, 1);
        assert_eq!(combined.entries[2].line_number, 2);
        assert_eq!(combined.entries[3].line_number, 3);
        assert_eq!(combined.entries[4].line_number, 4);
    }

    #[test]
    fn test_ignore_spec_matches() {
        let spec = IgnoreSpec::from_lines(vec!["*.tmp", "*.log", "test_*.py"]).unwrap();

        assert!(spec.matches("file.tmp").unwrap());
        assert!(spec.matches("debug.log").unwrap());
        assert!(spec.matches("test_foo.py").unwrap());
        assert!(!spec.matches("file.txt").unwrap());
        assert!(!spec.matches("script.py").unwrap());
    }

    #[test]
    fn test_ignore_spec_negation_patterns() {
        // Test basic negation
        let spec = IgnoreSpec::from_lines(vec!["*.log", "!important.log"]).unwrap();

        assert!(spec.matches("debug.log").unwrap());
        assert!(spec.matches("error.log").unwrap());
        assert!(!spec.matches("important.log").unwrap()); // Should NOT be ignored due to !
        assert!(!spec.matches("file.txt").unwrap());

        // Test directory negation
        let spec2 = IgnoreSpec::from_lines(vec!["build/", "!build/dist/"]).unwrap();

        assert!(spec2.matches_dir("build").unwrap());
        assert!(spec2.matches("build/temp.txt").unwrap());
        assert!(!spec2.matches_dir("build/dist").unwrap()); // Should NOT be ignored
        assert!(!spec2.matches("build/dist/app.js").unwrap());
    }

    #[test]
    fn test_treewalk_ignore_basic() {
        use std::fs::{self, File};
        use tempfile::TempDir;

        let temp_dir = TempDir::new().unwrap();
        let root = temp_dir.path();

        // Create .gitignore
        fs::write(root.join(".gitignore"), "*.tmp\n*.log\n").unwrap();

        // Create files
        File::create(root.join("keep.txt")).unwrap();
        File::create(root.join("temp.tmp")).unwrap();
        File::create(root.join("debug.log")).unwrap();

        let paths = treewalk_ignore(root, ".gitignore", None, None).unwrap();

        // Convert to filenames for easier checking
        let filenames: Vec<String> = paths
            .iter()
            .map(|p| p.file_name().unwrap().to_string_lossy().to_string())
            .collect();

        // Should include .gitignore and keep.txt, but not *.tmp or *.log files
        assert_eq!(filenames.len(), 2);
        assert!(filenames.contains(&".gitignore".to_string()));
        assert!(filenames.contains(&"keep.txt".to_string()));
        assert!(!filenames.contains(&"temp.tmp".to_string()));
        assert!(!filenames.contains(&"debug.log".to_string()));
    }

    #[test]
    fn test_treewalk_ignore_directory_exclusion() {
        use std::fs::{self, File};
        use tempfile::TempDir;

        let temp_dir = TempDir::new().unwrap();
        let root = temp_dir.path();

        // Create .gitignore with directory pattern
        fs::write(root.join(".gitignore"), "build/\nnode_modules/\n").unwrap();

        // Create directory structure
        fs::create_dir(root.join("src")).unwrap();
        File::create(root.join("src/main.rs")).unwrap();

        fs::create_dir(root.join("build")).unwrap();
        File::create(root.join("build/output.exe")).unwrap();

        fs::create_dir(root.join("node_modules")).unwrap();
        File::create(root.join("node_modules/package.json")).unwrap();

        let paths = treewalk_ignore(root, ".gitignore", None, None).unwrap();

        // Convert to relative paths
        let relative_paths: Vec<String> = paths
            .iter()
            .map(|p| {
                p.strip_prefix(root)
                    .unwrap()
                    .to_string_lossy()
                    .replace('\\', "/")
            })
            .collect();

        // Should not include anything from build/ or node_modules/
        assert!(relative_paths.contains(&".gitignore".to_string()));
        assert!(relative_paths.contains(&"src/main.rs".to_string()));
        assert!(!relative_paths.iter().any(|p| p.starts_with("build/")));
        assert!(!relative_paths
            .iter()
            .any(|p| p.starts_with("node_modules/")));
    }

    #[test]
    fn test_treewalk_ignore_cascading() {
        use std::fs::{self, File};
        use tempfile::TempDir;

        let temp_dir = TempDir::new().unwrap();
        let root = temp_dir.path();

        // Root .gitignore
        fs::write(root.join(".gitignore"), "*.tmp\n").unwrap();

        // Create subdirectory with its own .gitignore
        fs::create_dir(root.join("src")).unwrap();
        fs::write(root.join("src/.gitignore"), "*.log\n").unwrap();

        // Create files
        File::create(root.join("root.txt")).unwrap();
        File::create(root.join("root.tmp")).unwrap();
        File::create(root.join("src/main.rs")).unwrap();
        File::create(root.join("src/debug.log")).unwrap();
        File::create(root.join("src/temp.tmp")).unwrap();

        let paths = treewalk_ignore(root, ".gitignore", None, None).unwrap();

        // Convert to relative paths
        let relative_paths: Vec<String> = paths
            .iter()
            .map(|p| {
                p.strip_prefix(root)
                    .unwrap()
                    .to_string_lossy()
                    .replace('\\', "/")
            })
            .collect();

        // Root level: *.tmp ignored
        assert!(relative_paths.contains(&".gitignore".to_string()));
        assert!(relative_paths.contains(&"root.txt".to_string()));
        assert!(!relative_paths.contains(&"root.tmp".to_string()));

        // Src level: both *.tmp (inherited) and *.log (local) ignored
        assert!(relative_paths.contains(&"src/.gitignore".to_string()));
        assert!(relative_paths.contains(&"src/main.rs".to_string()));
        assert!(!relative_paths.contains(&"src/debug.log".to_string()));
        assert!(!relative_paths.contains(&"src/temp.tmp".to_string()));
    }

    #[test]
    fn test_treewalk_ignore_empty_gitignore() {
        use std::fs::{self, File};
        use tempfile::TempDir;

        let temp_dir = TempDir::new().unwrap();
        let root = temp_dir.path();

        // Create empty .gitignore
        fs::write(root.join(".gitignore"), "").unwrap();

        // Create files
        File::create(root.join("file1.txt")).unwrap();
        File::create(root.join("file2.log")).unwrap();

        let paths = treewalk_ignore(root, ".gitignore", None, None).unwrap();

        // All files should be included
        assert_eq!(paths.len(), 3); // .gitignore, file1.txt, file2.log
    }

    #[test]
    fn test_treewalk_ignore_with_negation() {
        use std::fs::{self, File};
        use tempfile::TempDir;

        let temp_dir = TempDir::new().unwrap();
        let root = temp_dir.path();

        // Create .gitignore with negation patterns
        fs::write(
            root.join(".gitignore"),
            "*.log\n!important.log\nbuild/\n!build/dist/\n",
        )
        .unwrap();

        // Create files
        File::create(root.join("debug.log")).unwrap();
        File::create(root.join("error.log")).unwrap();
        File::create(root.join("important.log")).unwrap();
        File::create(root.join("file.txt")).unwrap();

        // Create directories
        fs::create_dir(root.join("build")).unwrap();
        File::create(root.join("build/temp.txt")).unwrap();
        fs::create_dir(root.join("build/dist")).unwrap();
        File::create(root.join("build/dist/app.js")).unwrap();

        let paths = treewalk_ignore(root, ".gitignore", None, None).unwrap();

        // Convert to relative paths
        let relative_paths: Vec<String> = paths
            .iter()
            .map(|p| {
                p.strip_prefix(root)
                    .unwrap()
                    .to_string_lossy()
                    .replace('\\', "/")
            })
            .collect();

        // Should include important.log (negated) and build/dist/app.js (negated directory)
        assert!(relative_paths.contains(&".gitignore".to_string()));
        assert!(relative_paths.contains(&"important.log".to_string())); // Negated
        assert!(relative_paths.contains(&"file.txt".to_string()));
        assert!(relative_paths.contains(&"build/dist/app.js".to_string())); // In negated directory

        // Should NOT include regular log files or non-negated build files
        assert!(!relative_paths.contains(&"debug.log".to_string()));
        assert!(!relative_paths.contains(&"error.log".to_string()));
        assert!(!relative_paths.contains(&"build/temp.txt".to_string()));
    }

    #[test]
    fn test_treewalk_ignore_nonexistent_path() {
        let result = treewalk_ignore("/this/path/should/not/exist", ".gitignore", None, None);
        assert!(result.is_err());
        match result.unwrap_err() {
            TreewalkError::IoError(e) => {
                assert_eq!(e.kind(), io::ErrorKind::NotFound);
            }
            _ => panic!("Expected IoError with NotFound"),
        }
    }

    #[test]
    fn test_treewalk_ignore_file_not_directory() {
        use std::fs::File;
        use tempfile::TempDir;

        let temp_dir = TempDir::new().unwrap();
        let file_path = temp_dir.path().join("file.txt");
        File::create(&file_path).unwrap();

        let result = treewalk_ignore(&file_path, ".gitignore", None, None);
        assert!(result.is_err());
        match result.unwrap_err() {
            TreewalkError::IoError(e) => {
                assert_eq!(e.kind(), io::ErrorKind::InvalidInput);
            }
            _ => panic!("Expected IoError with InvalidInput"),
        }
    }

    #[test]
    fn test_treewalk_ignore_with_initial_spec() {
        use std::fs::{self, File};
        use tempfile::TempDir;

        let temp_dir = TempDir::new().unwrap();
        let root = temp_dir.path();

        // Create initial spec with *.bak pattern
        let initial_spec = IgnoreSpec::from_lines(vec!["*.bak"]).unwrap();

        // Create .gitignore with additional patterns
        fs::write(root.join(".gitignore"), "*.tmp\n").unwrap();

        // Create files
        File::create(root.join("keep.txt")).unwrap();
        File::create(root.join("temp.tmp")).unwrap();
        File::create(root.join("backup.bak")).unwrap();

        let paths = treewalk_ignore(root, ".gitignore", None, Some(&initial_spec)).unwrap();

        // Convert to filenames
        let filenames: Vec<String> = paths
            .iter()
            .map(|p| p.file_name().unwrap().to_string_lossy().to_string())
            .collect();

        // Should exclude both *.tmp (from .gitignore) and *.bak (from initial spec)
        assert_eq!(filenames.len(), 2);
        assert!(filenames.contains(&".gitignore".to_string()));
        assert!(filenames.contains(&"keep.txt".to_string()));
        assert!(!filenames.contains(&"temp.tmp".to_string()));
        assert!(!filenames.contains(&"backup.bak".to_string()));
    }

    #[test]
    fn test_ignore_spec_matches_directory() {
        let spec = IgnoreSpec::from_lines(vec!["build/", "dist/"]).unwrap();

        // Directory patterns should match directories
        assert!(spec.matches_dir("build").unwrap());
        assert!(spec.matches_dir("dist").unwrap());

        // But not files with the same name
        assert!(!spec.matches("build").unwrap());
        assert!(!spec.matches("dist").unwrap());
    }

    #[test]
    fn test_treewalk_ignore_multiple_ignore_types() {
        use std::fs::{self, File};
        use tempfile::TempDir;

        let temp_dir = TempDir::new().unwrap();
        let root = temp_dir.path();

        // Create both .gitignore and .customignore
        fs::write(root.join(".gitignore"), "*.tmp\n").unwrap();
        fs::write(root.join(".customignore"), "*.log\n").unwrap();

        // Create files
        File::create(root.join("keep.txt")).unwrap();
        File::create(root.join("temp.tmp")).unwrap();
        File::create(root.join("debug.log")).unwrap();

        // Use .gitignore
        let paths = treewalk_ignore(root, ".gitignore", None, None).unwrap();
        let filenames: Vec<String> = paths
            .iter()
            .map(|p| p.file_name().unwrap().to_string_lossy().to_string())
            .collect();

        // .gitignore rules apply, .customignore is treated as regular file
        assert!(filenames.contains(&".gitignore".to_string()));
        assert!(filenames.contains(&".customignore".to_string()));
        assert!(filenames.contains(&"keep.txt".to_string()));
        assert!(filenames.contains(&"debug.log".to_string())); // Not ignored by .gitignore
        assert!(!filenames.contains(&"temp.tmp".to_string())); // Ignored by .gitignore

        // Use .customignore
        let paths = treewalk_ignore(root, ".customignore", None, None).unwrap();
        let filenames: Vec<String> = paths
            .iter()
            .map(|p| p.file_name().unwrap().to_string_lossy().to_string())
            .collect();

        // .customignore rules apply, .gitignore is treated as regular file
        assert!(filenames.contains(&".gitignore".to_string()));
        assert!(filenames.contains(&".customignore".to_string()));
        assert!(filenames.contains(&"keep.txt".to_string()));
        assert!(filenames.contains(&"temp.tmp".to_string())); // Not ignored by .customignore
        assert!(!filenames.contains(&"debug.log".to_string())); // Ignored by .customignore
    }

    #[test]
    fn test_treewalk_iscc_filters_metadata() {
        use std::fs::File;
        use tempfile::TempDir;

        let temp_dir = TempDir::new().unwrap();
        let root = temp_dir.path();

        // Create files including .iscc.json files
        File::create(root.join("document.txt")).unwrap();
        File::create(root.join("document.iscc.json")).unwrap();
        File::create(root.join("image.png")).unwrap();
        File::create(root.join("image.iscc.json")).unwrap();
        File::create(root.join("data.iscc.json")).unwrap();

        let paths = treewalk_iscc(root).unwrap();

        // Convert to filenames
        let filenames: Vec<String> = paths
            .iter()
            .map(|p| p.file_name().unwrap().to_string_lossy().to_string())
            .collect();

        // Should include regular files but not .iscc.json files
        assert_eq!(filenames.len(), 2);
        assert!(filenames.contains(&"document.txt".to_string()));
        assert!(filenames.contains(&"image.png".to_string()));
        assert!(!filenames.contains(&"document.iscc.json".to_string()));
        assert!(!filenames.contains(&"image.iscc.json".to_string()));
        assert!(!filenames.contains(&"data.iscc.json".to_string()));
    }

    #[test]
    fn test_treewalk_iscc_respects_isccignore() {
        use std::fs::{self, File};
        use tempfile::TempDir;

        let temp_dir = TempDir::new().unwrap();
        let root = temp_dir.path();

        // Create .isccignore with patterns
        fs::write(root.join(".isccignore"), "*.tmp\nbuild/\n").unwrap();

        // Create files and directories
        File::create(root.join("keep.txt")).unwrap();
        File::create(root.join("temp.tmp")).unwrap();
        File::create(root.join("data.iscc.json")).unwrap();

        fs::create_dir(root.join("build")).unwrap();
        File::create(root.join("build/output.exe")).unwrap();
        File::create(root.join("build/manifest.iscc.json")).unwrap();

        fs::create_dir(root.join("src")).unwrap();
        File::create(root.join("src/main.rs")).unwrap();
        File::create(root.join("src/main.iscc.json")).unwrap();

        let paths = treewalk_iscc(root).unwrap();

        // Convert to relative paths
        let relative_paths: Vec<String> = paths
            .iter()
            .map(|p| {
                p.strip_prefix(root)
                    .unwrap()
                    .to_string_lossy()
                    .replace('\\', "/")
            })
            .collect();

        // Check that both .isccignore patterns and .iscc.json filtering work
        assert!(relative_paths.contains(&".isccignore".to_string())); // ignore files are included
        assert!(relative_paths.contains(&"keep.txt".to_string()));
        assert!(relative_paths.contains(&"src/main.rs".to_string()));

        // Should NOT include:
        assert!(!relative_paths.contains(&"temp.tmp".to_string())); // ignored by pattern
        assert!(!relative_paths.iter().any(|p| p.starts_with("build/"))); // ignored directory
        assert!(!relative_paths.contains(&"data.iscc.json".to_string())); // .iscc.json file
        assert!(!relative_paths.contains(&"src/main.iscc.json".to_string())); // .iscc.json file
    }

    #[test]
    fn test_treewalk_iscc_cascading_ignore() {
        use std::fs::{self, File};
        use tempfile::TempDir;

        let temp_dir = TempDir::new().unwrap();
        let root = temp_dir.path();

        // Root .isccignore
        fs::write(root.join(".isccignore"), "*.log\n").unwrap();

        // Create subdirectory with its own .isccignore
        fs::create_dir(root.join("subdir")).unwrap();
        fs::write(root.join("subdir/.isccignore"), "*.tmp\n").unwrap();

        // Create files
        File::create(root.join("root.txt")).unwrap();
        File::create(root.join("root.log")).unwrap();
        File::create(root.join("root.iscc.json")).unwrap();

        File::create(root.join("subdir/file.txt")).unwrap();
        File::create(root.join("subdir/debug.log")).unwrap();
        File::create(root.join("subdir/temp.tmp")).unwrap();
        File::create(root.join("subdir/file.iscc.json")).unwrap();

        let paths = treewalk_iscc(root).unwrap();

        // Convert to relative paths
        let relative_paths: Vec<String> = paths
            .iter()
            .map(|p| {
                p.strip_prefix(root)
                    .unwrap()
                    .to_string_lossy()
                    .replace('\\', "/")
            })
            .collect();

        // Check cascading ignore rules + .iscc.json filtering
        assert!(relative_paths.contains(&".isccignore".to_string()));
        assert!(relative_paths.contains(&"root.txt".to_string()));
        assert!(relative_paths.contains(&"subdir/.isccignore".to_string()));
        assert!(relative_paths.contains(&"subdir/file.txt".to_string()));

        // Should NOT include:
        assert!(!relative_paths.contains(&"root.log".to_string())); // ignored by root .isccignore
        assert!(!relative_paths.contains(&"root.iscc.json".to_string())); // .iscc.json file
        assert!(!relative_paths.contains(&"subdir/debug.log".to_string())); // ignored by inherited pattern
        assert!(!relative_paths.contains(&"subdir/temp.tmp".to_string())); // ignored by local .isccignore
        assert!(!relative_paths.contains(&"subdir/file.iscc.json".to_string()));
        // .iscc.json file
    }

    #[test]
    fn test_treewalk_iscc_empty_directory() {
        use tempfile::TempDir;

        let temp_dir = TempDir::new().unwrap();
        let paths = treewalk_iscc(temp_dir.path()).unwrap();

        assert_eq!(paths.len(), 0);
    }

    #[test]
    fn test_treewalk_iscc_nonexistent_path() {
        let result = treewalk_iscc("/this/path/should/not/exist");
        assert!(result.is_err());
        match result.unwrap_err() {
            TreewalkError::IoError(e) => {
                assert_eq!(e.kind(), io::ErrorKind::NotFound);
            }
            _ => panic!("Expected IoError with NotFound"),
        }
    }

    #[test]
    fn test_negation_precedence_and_cascading() {
        use std::fs::{self, File};
        use tempfile::TempDir;

        let temp_dir = TempDir::new().unwrap();
        let root = temp_dir.path();

        // Root .gitignore
        fs::write(root.join(".gitignore"), "*.log\n!important.log\n").unwrap();

        // Create subdirectory with its own .gitignore
        fs::create_dir(root.join("src")).unwrap();
        fs::write(root.join("src/.gitignore"), "!debug.log\n").unwrap();

        // Create files
        File::create(root.join("debug.log")).unwrap();
        File::create(root.join("error.log")).unwrap();
        File::create(root.join("important.log")).unwrap();

        fs::create_dir(root.join("src/logs")).unwrap();
        File::create(root.join("src/debug.log")).unwrap();
        File::create(root.join("src/error.log")).unwrap();
        File::create(root.join("src/logs/trace.log")).unwrap();

        let paths = treewalk_ignore(root, ".gitignore", None, None).unwrap();

        // Convert to relative paths
        let relative_paths: Vec<String> = paths
            .iter()
            .map(|p| {
                p.strip_prefix(root)
                    .unwrap()
                    .to_string_lossy()
                    .replace('\\', "/")
            })
            .collect();

        // Root level: important.log is whitelisted
        assert!(relative_paths.contains(&"important.log".to_string()));
        assert!(!relative_paths.contains(&"debug.log".to_string()));
        assert!(!relative_paths.contains(&"error.log".to_string()));

        // src level: debug.log is whitelisted (overrides parent)
        assert!(relative_paths.contains(&"src/debug.log".to_string()));
        assert!(!relative_paths.contains(&"src/error.log".to_string()));
        assert!(!relative_paths.contains(&"src/logs/trace.log".to_string()));
    }
}
