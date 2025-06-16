// Main entry point for the iscc-sum CLI tool

use clap::Parser;
use std::fs::File;
use std::io::{self, Read};
use std::path::PathBuf;
use std::process;

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
        // Process files
        for file in &cli.files {
            process_file(file, cli.narrow)?;
        }
    }

    Ok(())
}

/// Process a single file and output its ISCC checksum
fn process_file(path: &PathBuf, narrow: bool) -> io::Result<()> {
    // Check if file exists
    if !path.exists() {
        return Err(io::Error::new(
            io::ErrorKind::NotFound,
            format!("{}: No such file or directory", path.display()),
        ));
    }

    // Check if it's a regular file
    let metadata = path.metadata()?;
    if !metadata.is_file() {
        return Err(io::Error::new(
            io::ErrorKind::InvalidInput,
            format!("{}: Is not a regular file", path.display()),
        ));
    }

    // Open the file
    let mut file = File::open(path)?;

    // Process the file and get the result
    let result = process_reader(&mut file, narrow)?;

    // Output the result in Unix checksum format
    let filename = path.display();
    println!("{} *{}", result.iscc, filename);

    Ok(())
}

/// Process stdin and output its ISCC checksum
fn process_stdin(narrow: bool) -> io::Result<()> {
    let mut stdin = io::stdin();
    let result = process_reader(&mut stdin, narrow)?;

    // Output with '-' as filename for stdin
    println!("{} *-", result.iscc);

    Ok(())
}

/// Process any reader (file or stdin) and return the ISCC result
fn process_reader<R: Read>(reader: &mut R, narrow: bool) -> io::Result<IsccSumResult> {
    let mut processor = IsccSumProcessor::new();
    let mut buffer = vec![0; BUFFER_SIZE];

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
        let mut cursor = Cursor::new(data.to_vec());
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
        let mut cursor = Cursor::new(data.to_vec());
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

        let mut cursor1 = Cursor::new(data.to_vec());
        let result1 = process_reader(&mut cursor1, false).unwrap();

        let mut cursor2 = Cursor::new(data.to_vec());
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

        let mut cursor1 = Cursor::new(data1.to_vec());
        let result1 = process_reader(&mut cursor1, false).unwrap();

        let mut cursor2 = Cursor::new(data2.to_vec());
        let result2 = process_reader(&mut cursor2, false).unwrap();

        // Different data should produce different checksums
        assert_ne!(result1.iscc, result2.iscc);
    }

    #[test]
    fn test_narrow_vs_wide_format() {
        // Test that narrow and wide formats differ for same data
        let data = b"Format comparison test";

        let mut cursor1 = Cursor::new(data.to_vec());
        let narrow_result = process_reader(&mut cursor1, true).unwrap();

        let mut cursor2 = Cursor::new(data.to_vec());
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
        };
        assert!(cli.narrow);

        let cli = Cli {
            files: vec![],
            narrow: false,
        };
        assert!(!cli.narrow);
    }
}
