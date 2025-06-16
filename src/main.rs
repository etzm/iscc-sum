// Main entry point for the iscc-sum CLI tool

use clap::Parser;
use globset::{Glob, GlobSet, GlobSetBuilder};
use std::fs::File;
use std::io::{self, BufReader, Read};
use std::path::PathBuf;
use std::process;
use walkdir::WalkDir;

// Import from the library crate
use _core::sum::{IsccSumProcessor, IsccSumResult};

/// Generate ISCC Data-Code and Instance-Code checksums
#[derive(Parser)]
#[command(name = "isum")]
#[command(version = "0.1.0-alpha.1")]
#[command(about = "Generate ISCC Data-Code and Instance-Code checksums", long_about = None)]
struct Cli {
    /// Files to process (reads from stdin if not provided)
    #[arg(value_name = "FILE")]
    files: Vec<PathBuf>,

    /// Generate narrower 128-bit ISCC checksums (default: 256-bit)
    #[arg(short, long)]
    narrow: bool,

    /// Process directories recursively (default when directory argument is provided)
    #[arg(short, long, conflicts_with = "no_recursive")]
    recursive: bool,

    /// Process only files in the specified directory, not subdirectories
    #[arg(long, conflicts_with = "recursive")]
    no_recursive: bool,

    /// Exclude files matching the given glob pattern (can be specified multiple times)
    #[arg(long, value_name = "PATTERN")]
    exclude: Vec<String>,

    /// Maximum directory depth to traverse (default: unlimited)
    #[arg(long, value_name = "N")]
    max_depth: Option<usize>,
}

/// Exit codes following Unix conventions
const EXIT_ERROR: i32 = 1;

/// Buffer size for reading files (2MB)
const BUFFER_SIZE: usize = 2 * 1024 * 1024;

/// Print an error message to stderr and exit with error code
fn error_exit(message: &str) -> ! {
    eprintln!("isum: {}", message);
    process::exit(EXIT_ERROR);
}

/// Build a GlobSet from exclude patterns
fn build_exclude_set(patterns: &[String]) -> io::Result<Option<GlobSet>> {
    let mut builder = GlobSetBuilder::new();

    for pattern in patterns {
        let glob = Glob::new(pattern).map_err(|e| {
            io::Error::other(format!("Invalid exclude pattern '{}': {}", pattern, e))
        })?;
        builder.add(glob);
    }

    let globset = builder
        .build()
        .map_err(|e| io::Error::other(format!("Failed to build exclude patterns: {}", e)))?;

    Ok(Some(globset))
}

fn main() {
    let cli = Cli::parse();

    // Process the result and handle errors
    if let Err(e) = run(cli) {
        error_exit(&e.to_string());
    }
}

fn run(cli: Cli) -> io::Result<()> {
    if cli.files.is_empty() {
        // Process stdin
        process_stdin(cli.narrow)?;
    } else {
        // Build the exclude glob set if patterns were provided
        let exclude_set = if !cli.exclude.is_empty() {
            build_exclude_set(&cli.exclude)?
        } else {
            None
        };

        // Process files
        for file in &cli.files {
            process_file(file, &cli, exclude_set.as_ref())?;
        }
    }

    Ok(())
}

/// Process a single file and output its ISCC checksum
fn process_file(path: &PathBuf, cli: &Cli, exclude_set: Option<&GlobSet>) -> io::Result<()> {
    // Check if file exists
    if !path.exists() {
        return Err(io::Error::new(
            io::ErrorKind::NotFound,
            format!("{}: No such file or directory", path.display()),
        ));
    }

    // Get metadata (follows symlinks by default, which matches Unix tool behavior)
    let metadata = match path.metadata() {
        Ok(m) => m,
        Err(e) => {
            // Handle permission denied and other metadata errors
            if e.kind() == io::ErrorKind::PermissionDenied {
                return Err(io::Error::new(
                    io::ErrorKind::PermissionDenied,
                    format!("{}: Permission denied", path.display()),
                ));
            }
            return Err(e);
        }
    };

    // Handle special file types
    if metadata.is_dir() {
        // Process directory based on flags
        if cli.no_recursive {
            return process_directory_flat(path, cli, exclude_set);
        } else {
            // Recursive is the default behavior for directories
            return process_directory(path, cli, exclude_set);
        }
    }

    #[cfg(unix)]
    {
        use std::os::unix::fs::FileTypeExt;
        let file_type = metadata.file_type();

        if file_type.is_block_device() || file_type.is_char_device() {
            return Err(io::Error::new(
                io::ErrorKind::InvalidInput,
                format!("{}: Is a device file", path.display()),
            ));
        }

        if file_type.is_fifo() {
            return Err(io::Error::new(
                io::ErrorKind::InvalidInput,
                format!("{}: Is a named pipe", path.display()),
            ));
        }

        if file_type.is_socket() {
            return Err(io::Error::new(
                io::ErrorKind::InvalidInput,
                format!("{}: Is a socket", path.display()),
            ));
        }
    }

    // Process as regular file
    process_regular_file(path, cli.narrow)
}

/// Process stdin and output its ISCC checksum
fn process_stdin(narrow: bool) -> io::Result<()> {
    let mut stdin = io::stdin();
    let result = process_reader(&mut stdin, narrow)?;

    // Output with '-' as filename for stdin
    println!("{} *-", result.iscc);

    Ok(())
}

/// Process a directory non-recursively (only direct children)
fn process_directory_flat(
    dir_path: &PathBuf,
    cli: &Cli,
    exclude_set: Option<&GlobSet>,
) -> io::Result<()> {
    let mut entries = Vec::new();

    // Read directory entries
    for entry in std::fs::read_dir(dir_path)? {
        let entry = entry?;
        let path = entry.path();

        // Only process regular files
        if entry.file_type()?.is_file() {
            // Apply exclude patterns if any
            if let Some(globset) = exclude_set {
                let relative_path = path.strip_prefix(dir_path).unwrap_or(&path);
                if globset.is_match(relative_path) {
                    continue;
                }
            }
            entries.push(path);
        }
    }

    // Sort entries for deterministic output
    entries.sort();

    let mut had_errors = false;

    for entry_path in entries {
        // Process each file, but continue on errors
        if let Err(e) = process_regular_file(&entry_path, cli.narrow) {
            eprintln!("isum: {}: {}", entry_path.display(), e);
            had_errors = true;
        }
    }

    // If we had any errors, return an error to indicate partial failure
    if had_errors {
        Err(io::Error::other("Some files could not be processed"))
    } else {
        Ok(())
    }
}

/// Process a directory recursively and output ISCC checksums for all files
fn process_directory(
    dir_path: &PathBuf,
    cli: &Cli,
    exclude_set: Option<&GlobSet>,
) -> io::Result<()> {
    let mut walker = WalkDir::new(dir_path);

    // Apply max_depth if specified
    if let Some(depth) = cli.max_depth {
        walker = walker.max_depth(depth);
    }

    let mut entries: Vec<_> = walker
        .into_iter()
        .filter_map(|e| e.ok())
        .filter(|e| e.file_type().is_file())
        .filter(|e| {
            // Apply exclude patterns if any
            if let Some(globset) = exclude_set {
                let path = e.path();
                // Get relative path from the starting directory
                let relative_path = path.strip_prefix(dir_path).unwrap_or(path);
                !globset.is_match(relative_path)
            } else {
                true
            }
        })
        .map(|e| e.path().to_path_buf())
        .collect();

    // Sort entries for deterministic output
    entries.sort();

    let mut had_errors = false;

    for entry_path in entries {
        // Process each file, but continue on errors
        if let Err(e) = process_regular_file(&entry_path, cli.narrow) {
            eprintln!("isum: {}: {}", entry_path.display(), e);
            had_errors = true;
        }
    }

    // If we had any errors, return an error to indicate partial failure
    if had_errors {
        Err(io::Error::other("Some files could not be processed"))
    } else {
        Ok(())
    }
}

/// Process a regular file (extracted from process_file to avoid recursion)
fn process_regular_file(path: &PathBuf, narrow: bool) -> io::Result<()> {
    // Open the file with buffered reader for better I/O performance
    let file = match File::open(path) {
        Ok(f) => f,
        Err(e) => {
            // Handle permission denied specifically
            if e.kind() == io::ErrorKind::PermissionDenied {
                return Err(io::Error::new(
                    io::ErrorKind::PermissionDenied,
                    format!("{}: Permission denied", path.display()),
                ));
            }
            return Err(e);
        }
    };

    // Use BufReader for better I/O performance
    let mut reader = BufReader::with_capacity(BUFFER_SIZE, file);

    // Process the file and get the result
    let result = process_reader(&mut reader, narrow)?;

    // Output the result in Unix checksum format
    // Handle potentially invalid UTF-8 in filenames by using to_string_lossy
    let filename = path.to_string_lossy();
    println!("{} *{}", result.iscc, filename);

    Ok(())
}

/// Process any reader (file or stdin) and return the ISCC result
fn process_reader<R: Read>(reader: &mut R, narrow: bool) -> io::Result<IsccSumResult> {
    let mut processor = IsccSumProcessor::new();
    // Use vec! to allocate buffer on heap
    let mut buffer = vec![0u8; BUFFER_SIZE];

    loop {
        let bytes_read = reader.read(&mut buffer)?;
        if bytes_read == 0 {
            break;
        }
        processor.update(&buffer[..bytes_read]);
    }

    // Get the result
    // narrow=true means 64-bit (standard), narrow=false means 128-bit (wide)
    // So we need to invert the narrow flag for the wide parameter
    let wide = !narrow;
    let result = processor.result(wide, false); // Don't include units in CLI output

    Ok(result)
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::Cursor;

    #[test]
    fn test_process_reader_empty() {
        // Test with empty data
        let mut cursor = Cursor::new(vec![]);
        let result = process_reader(&mut cursor, false).unwrap();

        // Empty file should produce a valid ISCC
        assert!(result.iscc.starts_with("ISCC:"));
        assert_eq!(result.filesize, 0);
    }

    #[test]
    fn test_process_reader_small_data() {
        // Test with small data
        let data = b"Hello, World!";
        let mut cursor = Cursor::new(data);
        let result = process_reader(&mut cursor, false).unwrap();

        // Should produce a valid ISCC
        assert!(result.iscc.starts_with("ISCC:"));
        assert_eq!(result.filesize, 13);
        // Extended format (wide=true) should be longer than narrow format
        assert!(result.iscc.len() > 40);
    }

    #[test]
    fn test_process_reader_narrow_format() {
        // Test narrow format
        let data = b"Test data for narrow format";
        let mut cursor = Cursor::new(data);
        let result = process_reader(&mut cursor, true).unwrap();

        // Should produce a valid ISCC
        assert!(result.iscc.starts_with("ISCC:"));
        assert_eq!(result.filesize, 27);
        // Narrow format should be shorter (~29 chars after ISCC:)
        assert!(result.iscc.len() < 40);
    }

    #[test]
    fn test_process_reader_large_data() {
        // Test with data larger than buffer size
        let large_data = vec![0x42u8; BUFFER_SIZE * 2 + 1024];
        let mut cursor = Cursor::new(large_data.clone());
        let result = process_reader(&mut cursor, false).unwrap();

        // Should process all data correctly
        assert!(result.iscc.starts_with("ISCC:"));
        assert_eq!(result.filesize, large_data.len() as u64);
    }

    #[test]
    fn test_process_reader_deterministic() {
        // Test that same data produces same checksum
        let data = b"Deterministic test data";

        let mut cursor1 = Cursor::new(data);
        let result1 = process_reader(&mut cursor1, false).unwrap();

        let mut cursor2 = Cursor::new(data);
        let result2 = process_reader(&mut cursor2, false).unwrap();

        // Same data should produce identical checksums
        assert_eq!(result1.iscc, result2.iscc);
        assert_eq!(result1.datahash, result2.datahash);
        assert_eq!(result1.filesize, result2.filesize);
    }

    #[test]
    fn test_process_reader_different_data() {
        // Test that different data produces different checksums
        let data1 = b"First test data";
        let data2 = b"Second test data";

        let mut cursor1 = Cursor::new(data1);
        let result1 = process_reader(&mut cursor1, false).unwrap();

        let mut cursor2 = Cursor::new(data2);
        let result2 = process_reader(&mut cursor2, false).unwrap();

        // Different data should produce different checksums
        assert_ne!(result1.iscc, result2.iscc);
    }

    #[test]
    fn test_narrow_vs_wide_format() {
        // Test that narrow and wide formats differ for same data
        let data = b"Format comparison test";

        let mut cursor1 = Cursor::new(data);
        let narrow_result = process_reader(&mut cursor1, true).unwrap();

        let mut cursor2 = Cursor::new(data);
        let wide_result = process_reader(&mut cursor2, false).unwrap();

        // Formats should produce different ISCCs
        assert_ne!(narrow_result.iscc, wide_result.iscc);
        // But same filesize
        assert_eq!(narrow_result.filesize, wide_result.filesize);
        // Wide format should be longer
        assert!(wide_result.iscc.len() > narrow_result.iscc.len());
    }

    #[test]
    fn test_chunked_reading() {
        // Test that chunked reading produces same result as single read
        let data = vec![0x55u8; BUFFER_SIZE / 2];

        // Process in one go
        let mut cursor1 = Cursor::new(data.clone());
        let result1 = process_reader(&mut cursor1, false).unwrap();

        // Process same data but ensure it's read in chunks
        // by using a custom reader that limits read size
        struct ChunkedReader {
            data: Cursor<Vec<u8>>,
            max_chunk: usize,
        }

        impl Read for ChunkedReader {
            fn read(&mut self, buf: &mut [u8]) -> io::Result<usize> {
                let limit = buf.len().min(self.max_chunk);
                let limited_buf = &mut buf[..limit];
                self.data.read(limited_buf)
            }
        }

        let mut chunked = ChunkedReader {
            data: Cursor::new(data),
            max_chunk: 1024, // Force small chunks
        };
        let result2 = process_reader(&mut chunked, false).unwrap();

        // Results should be identical
        assert_eq!(result1.iscc, result2.iscc);
    }

    #[test]
    fn test_cli_narrow_flag() {
        // Test CLI parsing of narrow flag
        let cli = Cli {
            files: vec![],
            narrow: true,
            recursive: false,
            no_recursive: false,
            exclude: vec![],
            max_depth: None,
        };
        assert!(cli.narrow);

        let cli = Cli {
            files: vec![],
            narrow: false,
            recursive: false,
            no_recursive: false,
            exclude: vec![],
            max_depth: None,
        };
        assert!(!cli.narrow);
    }

    #[test]
    fn test_empty_file_handling() {
        // Test that empty files are handled correctly
        let empty = vec![];
        let mut cursor = Cursor::new(empty);
        let result = process_reader(&mut cursor, false).unwrap();

        // Empty files should produce valid ISCC with 0 filesize
        assert!(result.iscc.starts_with("ISCC:"));
        assert_eq!(result.filesize, 0);
    }

    #[test]
    fn test_io_error_handling() {
        // Test that I/O errors are properly propagated
        struct FailingReader;

        impl Read for FailingReader {
            fn read(&mut self, _buf: &mut [u8]) -> io::Result<usize> {
                Err(io::Error::other("read error"))
            }
        }

        let mut reader = FailingReader;
        let result = process_reader(&mut reader, false);

        assert!(result.is_err());
        match result {
            Err(e) => assert_eq!(e.kind(), io::ErrorKind::Other),
            Ok(_) => panic!("Expected error but got success"),
        }
    }
}

#[cfg(test)]
mod directory_tests {
    use super::*;
    use std::fs;
    use tempfile::TempDir;

    fn create_test_directory() -> TempDir {
        let temp_dir = TempDir::new().expect("Failed to create temp directory");

        // Create some test files
        fs::write(temp_dir.path().join("file1.txt"), b"Hello, World!").unwrap();
        fs::write(temp_dir.path().join("file2.txt"), b"Test data").unwrap();

        // Create a subdirectory with files
        let sub_dir = temp_dir.path().join("subdir");
        fs::create_dir(&sub_dir).unwrap();
        fs::write(sub_dir.join("file3.txt"), b"Nested file").unwrap();

        temp_dir
    }

    #[test]
    fn test_process_directory_basic() {
        let temp_dir = create_test_directory();
        let cli = Cli {
            files: vec![],
            narrow: false,
            recursive: false,
            no_recursive: false,
            exclude: vec![],
            max_depth: None,
        };
        let result = process_directory(&temp_dir.path().to_path_buf(), &cli, None);

        // Should succeed for directory with readable files
        assert!(result.is_ok());
    }

    #[test]
    fn test_process_directory_empty() {
        let temp_dir = TempDir::new().expect("Failed to create temp directory");
        let cli = Cli {
            files: vec![],
            narrow: false,
            recursive: false,
            no_recursive: false,
            exclude: vec![],
            max_depth: None,
        };
        let result = process_directory(&temp_dir.path().to_path_buf(), &cli, None);

        // Empty directory should succeed (no files to process)
        assert!(result.is_ok());
    }

    #[test]
    fn test_process_directory_with_unreadable_file() {
        let temp_dir = create_test_directory();

        // Create a file that we'll make unreadable
        let unreadable_file = temp_dir.path().join("unreadable.txt");
        fs::write(&unreadable_file, b"Can't read me").unwrap();

        #[cfg(unix)]
        {
            use std::os::unix::fs::PermissionsExt;
            let mut perms = fs::metadata(&unreadable_file).unwrap().permissions();
            perms.set_mode(0o000);
            fs::set_permissions(&unreadable_file, perms).unwrap();
        }

        let cli = Cli {
            files: vec![],
            narrow: false,
            recursive: false,
            no_recursive: false,
            exclude: vec![],
            max_depth: None,
        };
        let result = process_directory(&temp_dir.path().to_path_buf(), &cli, None);

        #[cfg(unix)]
        {
            // Should return error indicating some files failed
            assert!(result.is_err());

            // Clean up permissions so tempdir can be removed
            use std::os::unix::fs::PermissionsExt;
            let mut perms = fs::metadata(&unreadable_file).unwrap().permissions();
            perms.set_mode(0o644);
            fs::set_permissions(&unreadable_file, perms).unwrap();
        }

        #[cfg(not(unix))]
        {
            // On non-Unix systems, we can't easily test permission denied
            // So just verify the directory can be processed
            let _ = result;
        }
    }

    #[test]
    fn test_process_regular_file() {
        let temp_dir = TempDir::new().expect("Failed to create temp directory");
        let test_file = temp_dir.path().join("test.txt");
        fs::write(&test_file, b"Test content").unwrap();

        let result = process_regular_file(&test_file, false);
        assert!(result.is_ok());
    }

    #[test]
    fn test_process_regular_file_not_found() {
        let non_existent = PathBuf::from("/definitely/does/not/exist/file.txt");
        let result = process_regular_file(&non_existent, false);

        assert!(result.is_err());
        assert_eq!(result.unwrap_err().kind(), io::ErrorKind::NotFound);
    }
}
