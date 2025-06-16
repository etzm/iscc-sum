// Main entry point for the iscc-sum CLI tool

use clap::Parser;
use std::io;
use std::path::PathBuf;
use std::process;

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
            // Basic validation - check if file exists
            if !file.exists() {
                return Err(io::Error::new(
                    io::ErrorKind::NotFound,
                    format!("{}: No such file or directory", file.display()),
                ));
            }

            // TODO: Implement actual file processing
            eprintln!("Processing file: {:?} (narrow: {})", file, cli.narrow);
        }
    }

    Ok(())
}

fn process_stdin(narrow: bool) -> io::Result<()> {
    // TODO: Implement stdin processing
    eprintln!("Reading from stdin (narrow: {})...", narrow);
    Ok(())
}
