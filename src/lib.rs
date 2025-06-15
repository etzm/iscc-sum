// Core library implementation for iscc-sum

use pyo3::prelude::*;

pub mod cdc;
pub mod constants;
pub mod data;
pub mod instance;
pub mod minhash;
pub mod sum;

pub fn get_hello_message() -> String {
    "hello iscc-sum".to_string()
}

#[pyfunction]
fn hello_from_bin() -> String {
    get_hello_message()
}

/// A Python module implemented in Rust. The name of this function must match
/// the `lib.name` setting in the `Cargo.toml`, else Python will not be able to
/// import the module.
#[pymodule]
fn _core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(hello_from_bin, m)?)?;
    m.add_class::<data::DataCodeProcessor>()?;
    m.add_class::<instance::InstanceCodeProcessor>()?;
    m.add_class::<sum::IsccSumProcessor>()?;
    m.add_class::<sum::IsccSumResult>()?;
    m.add_function(wrap_pyfunction!(sum::code_iscc_sum, m)?)?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_hello_message() {
        assert_eq!(get_hello_message(), "hello iscc-sum");
    }
}
