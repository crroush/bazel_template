use pyo3::prelude::*;

#[pyfunction]
fn greet(name: &str) -> String {
    format!("Hello, {name} from Rust!")
}

#[pymodule]
fn _rust_greeting(module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_function(wrap_pyfunction!(greet, module)?)?;
    Ok(())
}
