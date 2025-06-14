//! Data-Code processor implementation for ISCC.
//!
//! This module provides the DataCodeProcessor which implements incremental
//! hashing of data streams using Content-Defined Chunking (CDC) and MinHash
//! for creating compact, similarity-preserving signatures.

use pyo3::prelude::*;
use pyo3::types::{PyBytes, PyDict};
use xxhash_rust::xxh32::xxh32;

use crate::cdc::{cdc_chunks, DATA_AVG_CHUNK_SIZE};
use crate::minhash::minhash_256;

/// DataHasher collects xxhash32 digests of CDC chunks.
struct DataHasher {
    chunk_features: Vec<u32>,
    tail: Vec<u8>,
    finalized: bool,
}

impl DataHasher {
    fn new() -> Self {
        let mut hasher = DataHasher {
            chunk_features: Vec::new(),
            tail: Vec::new(),
            finalized: false,
        };
        // Match Python reference implementation which calls push(b"") in __init__
        hasher.push(b"");
        hasher
    }

    fn push(&mut self, data: &[u8]) {
        // Prepend any tail carried over from previous push.
        let combined: Vec<u8> = if !self.tail.is_empty() {
            [self.tail.as_slice(), data].concat()
        } else {
            data.to_vec()
        };
        let (chunks, new_tail) = cdc_chunks(&combined, false, DATA_AVG_CHUNK_SIZE);
        for chunk in chunks {
            self.chunk_features.push(xxh32(chunk, 0));
        }
        self.tail = new_tail.to_vec();
    }

    fn finalize(&mut self) {
        if !self.finalized {
            // Always process tail if it exists (even if empty)
            // This matches the Python reference which uses 'if self.tail is not None'
            self.chunk_features.push(xxh32(&self.tail, 0));
            self.tail.clear();
            self.finalized = true;
        }
    }

    /// Finalize and return the 256-bit (32-byte) digest.
    fn digest(&mut self) -> Vec<u8> {
        self.finalize();
        minhash_256(&self.chunk_features)
    }
}

/// A Python-exposed data processor that implements an incremental Data-Code digest.
#[pyclass]
pub struct DataCodeProcessor {
    hasher: DataHasher,
}

#[pymethods]
impl DataCodeProcessor {
    #[new]
    fn new() -> Self {
        DataCodeProcessor {
            hasher: DataHasher::new(),
        }
    }

    /// Incrementally push a chunk of data.
    ///
    /// This method accepts a bytes object from Python.
    fn update(&mut self, data: &[u8]) {
        self.hasher.push(data);
    }

    /// Finalize the processing and return a dictionary with the 256-bit digest.
    ///
    /// The returned dict is of the format: {"digest": <256-bit-bytes-digest>}.
    fn result<'py>(&mut self, py: Python<'py>) -> PyResult<Bound<'py, PyDict>> {
        let digest = self.hasher.digest();
        let dict = PyDict::new(py);
        dict.set_item("digest", PyBytes::new(py, &digest))?;
        Ok(dict)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_data_hasher_new() {
        let hasher = DataHasher::new();
        assert_eq!(hasher.chunk_features.len(), 0);
        assert_eq!(hasher.tail.len(), 0);
        assert!(!hasher.finalized);
    }

    #[test]
    fn test_data_hasher_push_small() {
        let mut hasher = DataHasher::new();
        hasher.push(b"Hello, World!");
        // Small data should go to tail
        assert_eq!(hasher.chunk_features.len(), 0);
        assert_eq!(hasher.tail, b"Hello, World!");
    }

    #[test]
    fn test_data_hasher_finalize() {
        let mut hasher = DataHasher::new();
        hasher.push(b"Hello, World!");
        hasher.finalize();
        // After finalize, tail should be processed
        assert_eq!(hasher.chunk_features.len(), 1);
        assert_eq!(hasher.tail.len(), 0);
    }

    #[test]
    fn test_data_hasher_digest() {
        let mut hasher = DataHasher::new();
        hasher.push(b"Test data for hashing");
        let digest = hasher.digest();
        assert_eq!(digest.len(), 32); // 256 bits = 32 bytes
    }

    #[test]
    fn test_data_hasher_incremental() {
        let mut hasher1 = DataHasher::new();
        hasher1.push(b"Hello, ");
        hasher1.push(b"World!");
        let digest1 = hasher1.digest();

        let mut hasher2 = DataHasher::new();
        hasher2.push(b"Hello, World!");
        let digest2 = hasher2.digest();

        assert_eq!(digest1, digest2);
    }

    #[test]
    fn test_data_hasher_large_data() {
        let mut hasher = DataHasher::new();
        // Create varied data to ensure chunk boundaries
        let mut large_data = Vec::with_capacity(10000);
        for i in 0..10000 {
            large_data.push((i % 256) as u8);
        }
        hasher.push(&large_data);
        // Should have some chunks (but might be in tail)
        let features_before = hasher.chunk_features.len();
        let digest = hasher.digest();
        assert_eq!(digest.len(), 32);
        // After digest, should have processed at least one chunk
        assert!(!hasher.chunk_features.is_empty() || features_before > 0);
    }
}
