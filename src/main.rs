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
