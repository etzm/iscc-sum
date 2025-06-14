// ISCC-SUM implementation combining Data-Code and Instance-Code in a single pass

use crate::data::DataHasher;
use crate::instance::InstanceHasher;
use base32;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use std::fs::File;
use std::io::Read;
use std::path::Path;

/// ISCC-SUM processor for generating combined Data-Code and Instance-Code
#[pyclass]
pub struct IsccSumProcessor {
    data_hasher: DataHasher,
    instance_hasher: InstanceHasher,
}

#[pymethods]
impl IsccSumProcessor {
    /// Create a new ISCC-SUM processor
    #[new]
    fn new() -> Self {
        Self {
            data_hasher: DataHasher::new(),
            instance_hasher: InstanceHasher::new(),
        }
    }

    /// Update the processor with new data
    fn update(&mut self, data: &[u8]) {
        self.data_hasher.push(data);
        self.instance_hasher.push(data);
    }

    /// Get the final ISCC-SUM result
    fn result<'py>(
        &mut self,
        py: Python<'py>,
        wide: bool,
        add_units: bool,
    ) -> PyResult<Bound<'py, PyDict>> {
        // Get digests
        let data_digest = self.data_hasher.digest();
        let instance_digest = self.instance_hasher.digest();

        // Use appropriate length based on wide parameter
        let data_code = if wide {
            &data_digest[..16] // 128 bits for wide
        } else {
            &data_digest[..8] // 64 bits for standard
        };
        let instance_code = if wide {
            &instance_digest[..16] // 128 bits for wide
        } else {
            &instance_digest[..8] // 64 bits for standard
        };

        // Construct header
        let main_type: u8 = 0b0101; // ISCC composite code
        let sub_type: u8 = if wide { 0b0111 } else { 0b0101 }; // SUM or SUM wide
        let version: u8 = 0b0000; // V0
        let length: u8 = 0b0000; // no optional units in header

        let header_byte1: u8 = (main_type << 4) | sub_type;
        let header_byte2: u8 = (version << 4) | length;

        // Combine header and body
        let mut iscc_bytes = vec![header_byte1, header_byte2];
        iscc_bytes.extend_from_slice(data_code);
        iscc_bytes.extend_from_slice(instance_code);

        // Base32 encode without padding
        let iscc_code = base32::encode(base32::Alphabet::Rfc4648 { padding: false }, &iscc_bytes);
        let iscc = format!("ISCC:{}", iscc_code);

        // Create result dictionary
        let result_dict = PyDict::new(py);
        result_dict.set_item("iscc", iscc)?;
        result_dict.set_item("datahash", self.instance_hasher.multihash())?;
        result_dict.set_item("filesize", self.instance_hasher.filesize())?;

        // Add units if requested
        if add_units {
            let units = PyList::empty(py);

            // Create full 256-bit Data-Code ISCC
            let data_header_byte1: u8 = 0b0011 << 4; // Data maintype (0011) + subtype (0000)
            let data_header_byte2: u8 = 0b0111; // Version (0000) + length for 256 bits (0111)
            let mut data_iscc_bytes = vec![data_header_byte1, data_header_byte2];
            data_iscc_bytes.extend_from_slice(&data_digest); // Full 256-bit digest
            let data_iscc_code = base32::encode(
                base32::Alphabet::Rfc4648 { padding: false },
                &data_iscc_bytes,
            );
            let data_iscc = format!("ISCC:{}", data_iscc_code);

            // Create full 256-bit Instance-Code ISCC
            let instance_header_byte1: u8 = 0b0100 << 4; // Instance type + subtype
            let instance_header_byte2: u8 = 0b0111; // Version + length for 256 bits
            let mut instance_iscc_bytes = vec![instance_header_byte1, instance_header_byte2];
            instance_iscc_bytes.extend_from_slice(&instance_digest); // Full 256-bit digest
            let instance_iscc_code = base32::encode(
                base32::Alphabet::Rfc4648 { padding: false },
                &instance_iscc_bytes,
            );
            let instance_iscc = format!("ISCC:{}", instance_iscc_code);

            units.append(data_iscc)?;
            units.append(instance_iscc)?;
            result_dict.set_item("units", units)?;
        }

        Ok(result_dict)
    }
}

/// Generate ISCC-SUM from a file path (Python-exposed function)
#[pyfunction]
#[pyo3(signature = (filepath, wide=false, add_units=true))]
pub fn code_iscc_sum<'py>(
    py: Python<'py>,
    filepath: &str,
    wide: bool,
    add_units: bool,
) -> PyResult<Bound<'py, PyDict>> {
    let path = Path::new(filepath);
    let mut file = File::open(path)
        .map_err(|e| pyo3::exceptions::PyIOError::new_err(format!("Failed to open file: {}", e)))?;

    let mut processor = IsccSumProcessor::new();
    let mut buffer = vec![0; 2 * 1024 * 1024]; // 2MB buffer

    loop {
        let bytes_read = file.read(&mut buffer).map_err(|e| {
            pyo3::exceptions::PyIOError::new_err(format!("Failed to read file: {}", e))
        })?;
        if bytes_read == 0 {
            break;
        }
        processor.update(&buffer[..bytes_read]);
    }

    processor.result(py, wide, add_units)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_iscc_sum_processor() {
        let processor = IsccSumProcessor::new();
        // Just test that we can create a processor
        // Actual functionality testing will be done via Python tests
        assert!(std::ptr::eq(
            &processor.data_hasher as *const _,
            &processor.data_hasher as *const _
        ));
    }
}
