// Rust implementation of the treewalk algorithm for deterministic file tree traversal

use std::io;

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
}
