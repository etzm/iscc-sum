//! Instance-Code processor implementation for ISCC.
//!
//! This module provides the InstanceCodeProcessor which implements incremental
//! hashing of data streams using BLAKE3 for creating cryptographic file hashes.

use pyo3::prelude::*;
use pyo3::types::{PyBytes, PyDict};

/// InstanceHasher collects data and computes BLAKE3 hash.
struct InstanceHasher {
    hasher: blake3::Hasher,
    filesize: u64,
}

impl InstanceHasher {
    fn new() -> Self {
        let mut hasher = InstanceHasher {
            hasher: blake3::Hasher::new(),
            filesize: 0,
        };
        // Match Python reference implementation which calls push(b"") in __init__
        hasher.push(b"");
        hasher
    }

    fn push(&mut self, data: &[u8]) {
        self.filesize += data.len() as u64;
        self.hasher.update(data);
    }

    /// Return blake3 hash digest.
    fn digest(&self) -> Vec<u8> {
        self.hasher.finalize().as_bytes().to_vec()
    }

    /// Return blake3 digest as multihash.
    fn multihash(&self) -> String {
        let mh_prefix = vec![0x1e, 0x20]; // BLAKE3 multihash prefix
        let digest = self.digest();
        let mut result = mh_prefix;
        result.extend_from_slice(&digest);
        hex::encode(result)
    }
}

/// A Python-exposed instance processor that implements an incremental Instance-Code digest.
#[pyclass]
pub struct InstanceCodeProcessor {
    hasher: InstanceHasher,
}

#[pymethods]
impl InstanceCodeProcessor {
    #[new]
    fn new() -> Self {
        InstanceCodeProcessor {
            hasher: InstanceHasher::new(),
        }
    }

    /// Incrementally push a chunk of data.
    ///
    /// This method accepts a bytes object from Python.
    fn update(&mut self, data: &[u8]) {
        self.hasher.push(data);
    }

    /// Finalize the processing and return a dictionary with the results.
    ///
    /// The returned dict contains:
    /// - "digest": 32-byte blake3 hash digest
    /// - "multihash": Hex-encoded multihash with blake3 prefix (0x1e20)
    /// - "filesize": Total size of processed data in bytes
    fn result<'py>(&mut self, py: Python<'py>) -> PyResult<Bound<'py, PyDict>> {
        let digest = self.hasher.digest();
        let multihash = self.hasher.multihash();
        let filesize = self.hasher.filesize;

        let dict = PyDict::new(py);
        dict.set_item("digest", PyBytes::new(py, &digest))?;
        dict.set_item("multihash", multihash)?;
        dict.set_item("filesize", filesize)?;
        Ok(dict)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_instance_hasher_new() {
        let hasher = InstanceHasher::new();
        assert_eq!(hasher.filesize, 0);
    }

    #[test]
    fn test_instance_hasher_push() {
        let mut hasher = InstanceHasher::new();
        hasher.push(b"Hello, World!");
        assert_eq!(hasher.filesize, 13);
    }

    #[test]
    fn test_instance_hasher_digest() {
        let mut hasher = InstanceHasher::new();
        hasher.push(b"Test data for hashing");
        let digest = hasher.digest();
        assert_eq!(digest.len(), 32); // BLAKE3 outputs 32 bytes
    }

    #[test]
    fn test_instance_hasher_incremental() {
        let mut hasher1 = InstanceHasher::new();
        hasher1.push(b"Hello, ");
        hasher1.push(b"World!");
        let digest1 = hasher1.digest();

        let mut hasher2 = InstanceHasher::new();
        hasher2.push(b"Hello, World!");
        let digest2 = hasher2.digest();

        assert_eq!(digest1, digest2);
    }

    #[test]
    fn test_instance_hasher_multihash() {
        let mut hasher = InstanceHasher::new();
        hasher.push(b"test");
        let multihash = hasher.multihash();
        // Should start with "1e20" (BLAKE3 multihash prefix)
        assert!(multihash.starts_with("1e20"));
        // Total length should be 2 (prefix) + 32 (hash) bytes * 2 (hex encoding) = 68 chars
        assert_eq!(multihash.len(), 68);
    }

    #[test]
    fn test_instance_hasher_large_data() {
        let mut hasher = InstanceHasher::new();
        let large_data = vec![0u8; 10_000_000]; // 10 MB
        hasher.push(&large_data);
        assert_eq!(hasher.filesize, 10_000_000);
        let digest = hasher.digest();
        assert_eq!(digest.len(), 32);
    }

    #[test]
    fn test_instance_hasher_empty_data() {
        let hasher = InstanceHasher::new();
        let digest = hasher.digest();
        assert_eq!(digest.len(), 32);
        // Empty input should still produce a valid hash
    }
}
