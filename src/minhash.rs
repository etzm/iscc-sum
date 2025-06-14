//! MinHash implementation for ISCC Data-Code.
//!
//! This module provides the MinHash algorithm used to create compact signatures
//! from sets of features. It's designed for high-performance similarity detection
//! and deduplication.

use crate::constants::{MPA, MPB};
use rayon::prelude::*;

const MAXI64: u64 = 0xFFFF_FFFF_FFFF_FFFF;
const MPRIME: u64 = (1 << 61) - 1;
const MAXH: u64 = (1 << 32) - 1;

/// For each (a, b) pair in MPA and MPB, compute the minimum over all features.
fn minhash(features: &Vec<u32>) -> Vec<u64> {
    MPA.iter()
        .zip(MPB.iter())
        .map(|(&a, &b)| {
            features
                .par_iter()
                .map(|&f| (((a.wrapping_mul(f as u64).wrapping_add(b)) & MAXI64) % MPRIME) & MAXH)
                .min()
                .unwrap_or(MAXH)
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
    let total_bytes = total_bits.div_ceil(8);
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
pub fn minhash_256(features: &Vec<u32>) -> Vec<u8> {
    let mhash = minhash(features);
    minhash_compress(&mhash, 4)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_minhash_empty() {
        let features = Vec::new();
        let result = minhash_256(&features);
        assert_eq!(result.len(), 32); // 256 bits = 32 bytes
    }

    #[test]
    fn test_minhash_single_feature() {
        let features = vec![12345u32];
        let result = minhash_256(&features);
        assert_eq!(result.len(), 32);
    }

    #[test]
    fn test_minhash_deterministic() {
        let features = vec![1, 2, 3, 4, 5];
        let result1 = minhash_256(&features);
        let result2 = minhash_256(&features);
        assert_eq!(result1, result2);
    }

    #[test]
    fn test_minhash_compress() {
        let mhash = vec![0b1010u64, 0b1100u64];
        let compressed = minhash_compress(&mhash, 4);
        assert_eq!(compressed.len(), 1); // 2 * 4 bits = 8 bits = 1 byte
    }

    #[test]
    fn test_minhash_compress_larger() {
        let mhash = vec![0xFFu64; 64]; // 64 values
        let compressed = minhash_compress(&mhash, 4);
        assert_eq!(compressed.len(), 32); // 64 * 4 bits = 256 bits = 32 bytes
    }
}
