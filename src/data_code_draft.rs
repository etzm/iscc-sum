//! This is an experimental performance optimized RUST implementation of the ISCC Data-Code
//! It is not used in production code. It serves as a template/reference for the actual implementation.
//! Don´t change or remove this code.
use pyo3::prelude::*;
use pyo3::types::{PyBytes, PyDict};
use rayon::prelude::*;
use xxhash_rust::xxh32::xxh32;


// ----- Constants and CDC support (from your original implementation) -----
mod constants;

use constants::{MPA, MPB, CDC_GEAR};

const DATA_AVG_CHUNK_SIZE: usize = 1024;
const MAXI64: u64 = 0xFFFF_FFFF_FFFF_FFFF;
const MPRIME: u64 = (1 << 61) - 1;
const MAXH: u64 = (1 << 32) - 1;

// CDC chunking functions
fn cdc_params(avg_size: usize) -> (usize, usize, usize, u32, u32) {
    let ceil_div = |x, y| (x + y - 1) / y;
    let min_size = avg_size / 4;
    let max_size = avg_size * 8;
    let offset = min_size + ceil_div(min_size, 2);
    let center_size = avg_size - offset;
    let bits = (avg_size as f64).log2().round() as u32;
    let mask = |b: u32| (1 << b) - 1;
    let mask_s = mask(bits + 1);
    let mask_l = mask(bits - 1);
    (min_size, max_size, center_size, mask_s, mask_l)
}

fn cdc_offset(buffer: &[u8], mi: usize, ma: usize, cs: usize, mask_s: u32, mask_l: u32) -> usize {
    let size = buffer.len();
    let mut pattern: u32 = 0;
    let mut i = std::cmp::min(mi, size);
    let barrier = std::cmp::min(cs, size);
    while i < barrier {
        pattern = (pattern >> 1).wrapping_add(CDC_GEAR[buffer[i] as usize]);
        if pattern & mask_s == 0 {
            return i + 1;
        }
        i += 1;
    }
    let barrier = std::cmp::min(ma, size);
    while i < barrier {
        pattern = (pattern >> 1).wrapping_add(CDC_GEAR[buffer[i] as usize]);
        if pattern & mask_l == 0 {
            return i + 1;
        }
        i += 1;
    }
    i
}

/// Given a data slice, return a vector of complete chunks and the remaining tail chunk.
fn cdc_chunks(data: &[u8], utf32: bool, avg_chunk_size: usize) -> (Vec<&[u8]>, &[u8]) {
    let (mi, ma, cs, mask_s, mask_l) = cdc_params(avg_chunk_size);
    let mut chunks = Vec::new();
    let mut buffer = data;
    while !buffer.is_empty() {
        let mut cut = cdc_offset(buffer, mi, ma, cs, mask_s, mask_l);
        if utf32 {
            cut -= cut % 4;
        }
        if cut == 0 { break; }
        chunks.push(&buffer[..cut]);
        buffer = &buffer[cut..];
    }
    // The last chunk is held back as tail (it may be incomplete)
    let tail = if !chunks.is_empty() { chunks.pop().unwrap() } else { buffer };
    (chunks, tail)
}

// ----- Core DataHasher and Minhash functions -----

/// DataHasher collects xxhash32 digests of CDC chunks.
struct DataHasher {
    chunk_features: Vec<u32>,
    tail: Vec<u8>,
}

impl DataHasher {
    fn new() -> Self {
        DataHasher {
            chunk_features: Vec::new(),
            tail: Vec::new(),
        }
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
        if !self.tail.is_empty() {
            self.chunk_features.push(xxh32(&self.tail, 0));
            self.tail.clear();
        }
    }

    /// Finalize and return the 256-bit (32-byte) digest.
    fn digest(&mut self) -> Vec<u8> {
        self.finalize();
        minhash_256(&self.chunk_features)
    }
}

/// For each (a, b) pair in MPA and MPB, compute the minimum over all features.
fn minhash(features: &Vec<u32>) -> Vec<u64> {
    MPA.iter().zip(MPB.iter())
        .map(|(&a, &b)| {
            features.par_iter()
                .map(|&f| (((a.wrapping_mul(f as u64).wrapping_add(b)) & MAXI64) % MPRIME) & MAXH)
                .min().unwrap_or(MAXH)
        })
        .collect()
}

/// Compress the minhash vector by concatenating lsb least–significant bits from each integer.
fn minhash_compress(mhash: &[u64], lsb: u32) -> Vec<u8> {
    let total_bits = mhash.len() * lsb as usize;
    let mut bits = vec![0u8; total_bits];
    let mut bit_index = 0;
    for bitpos in 0..lsb {
        for &h in mhash {
            bits[bit_index] = ((h >> bitpos) & 1) as u8;
            bit_index += 1;
        }
    }
    let total_bytes = (total_bits + 7) / 8;
    let mut out = vec![0u8; total_bytes];
    for (i, bit) in bits.iter().enumerate() {
        if *bit != 0 {
            let byte_index = i / 8;
            let bit_in_byte = 7 - (i % 8);
            out[byte_index] |= 1 << bit_in_byte;
        }
    }
    out
}

/// Create a 256–bit digest from the chunk features.
fn minhash_256(features: &Vec<u32>) -> Vec<u8> {
    let mhash = minhash(features);
    minhash_compress(&mhash, 4)
}

// ----- PyO3 Bindings -----

/// A Python-exposed data processor that implements an incremental Data-Code digest.
#[pyclass]
struct DataCodeProcessor {
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
    fn result<'py>(&mut self, py: Python<'py>) -> PyResult<&'py PyDict> {
        let digest = self.hasher.digest();
        let dict = PyDict::new(py);
        dict.set_item("digest", PyBytes::new(py, &digest))?;
        Ok(dict)
    }
}

/// Define the Python module.
#[pymodule]
fn iscc_sum_rs(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<DataCodeProcessor>()?;
    Ok(())
}
