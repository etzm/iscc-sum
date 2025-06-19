//! Content-Defined Chunking (CDC) implementation for ISCC Data-Code.
//!
//! This module implements the CDC algorithm used to split data into variable-sized chunks
//! based on content patterns. The chunking is deterministic and content-aware, making it
//! ideal for deduplication and similarity detection.

use crate::constants::CDC_GEAR;

/// Default average chunk size for Data-Code
pub const DATA_AVG_CHUNK_SIZE: usize = 1024;

/// Calculate CDC parameters based on the desired average chunk size.
///
/// Returns: (min_size, max_size, center_size, mask_s, mask_l)
#[inline]
fn cdc_params(avg_size: usize) -> (usize, usize, usize, u32, u32) {
    let min_size = avg_size / 4;
    let max_size = avg_size * 8;
    let offset = min_size + min_size.div_ceil(2);
    let center_size = avg_size - offset;
    let bits = (avg_size as f64).log2().round() as u32;
    let mask = |b: u32| (1 << b) - 1;
    let mask_s = mask(bits + 1);
    let mask_l = mask(bits - 1);
    (min_size, max_size, center_size, mask_s, mask_l)
}

/// Find the offset for the next chunk boundary in the buffer.
///
/// This function uses a rolling hash with the GEAR table to find content-defined
/// chunk boundaries. It's optimized for performance with minimal branching.
#[inline(always)]
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

/// Split data into content-defined chunks.
///
/// Given a data slice, return a vector of complete chunks and the remaining tail chunk.
/// The tail chunk is held back as it may be incomplete and could be extended with
/// additional data in streaming scenarios.
///
/// # Arguments
/// * `data` - The input data to be chunked
/// * `utf32` - If true, ensures chunk boundaries align to 4-byte boundaries for UTF-32
/// * `avg_chunk_size` - The target average size for chunks
///
/// # Returns
/// A tuple of (complete_chunks, tail_chunk)
pub fn cdc_chunks(data: &[u8], utf32: bool, avg_chunk_size: usize) -> (Vec<&[u8]>, &[u8]) {
    let (mi, ma, cs, mask_s, mask_l) = cdc_params(avg_chunk_size);
    let mut chunks = Vec::new();
    let mut buffer = data;
    while !buffer.is_empty() {
        let mut cut = cdc_offset(buffer, mi, ma, cs, mask_s, mask_l);
        if utf32 {
            cut -= cut % 4;
        }
        if cut == 0 {
            break;
        }
        chunks.push(&buffer[..cut]);
        buffer = &buffer[cut..];
    }
    // The last chunk is held back as tail (it may be incomplete)
    let tail = if !chunks.is_empty() {
        chunks.pop().unwrap()
    } else {
        buffer
    };
    (chunks, tail)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_cdc_params() {
        let (min, max, center, mask_s, mask_l) = cdc_params(1024);
        assert_eq!(min, 256);
        assert_eq!(max, 8192);
        assert_eq!(center, 640);
        assert_eq!(mask_s, 2047);
        assert_eq!(mask_l, 511);
    }

    #[test]
    fn test_cdc_chunks_empty() {
        let data = b"";
        let (chunks, tail) = cdc_chunks(data, false, 1024);
        assert_eq!(chunks.len(), 0);
        assert_eq!(tail.len(), 0);
    }

    #[test]
    fn test_cdc_chunks_small() {
        let data = b"Hello, World!";
        let (chunks, tail) = cdc_chunks(data, false, 1024);
        assert_eq!(chunks.len(), 0);
        assert_eq!(tail, data);
    }

    #[test]
    fn test_cdc_chunks_deterministic() {
        let data = vec![0u8; 10000];
        let (chunks1, tail1) = cdc_chunks(&data, false, 1024);
        let (chunks2, tail2) = cdc_chunks(&data, false, 1024);

        assert_eq!(chunks1.len(), chunks2.len());
        assert_eq!(tail1, tail2);

        for (c1, c2) in chunks1.iter().zip(chunks2.iter()) {
            assert_eq!(c1.len(), c2.len());
        }
    }

    #[test]
    fn test_utf32_alignment() {
        // Create data that would normally chunk at a non-4-byte boundary
        let mut data = vec![0u8; 1000];
        // Set pattern to force a chunk boundary
        for (i, item) in data.iter_mut().enumerate() {
            *item = (i % 256) as u8;
        }

        let (chunks, _) = cdc_chunks(&data, true, 64);

        // Verify all chunks are 4-byte aligned
        for chunk in &chunks {
            assert_eq!(
                chunk.len() % 4,
                0,
                "Chunk size {} is not 4-byte aligned",
                chunk.len()
            );
        }
    }
}
