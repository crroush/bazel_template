# Python calling Rust with PyO3

```bash
bazel test //examples/pyo3:hello_test
bazel run //examples/pyo3:hello
```

`rust_shared_library` compiles a Rust `cdylib`; `copy_file` stages it under the
Python module name `_rust_greeting.so`. A Python library carries that file in
runfiles, and the test imports and calls real Rust code, including Unicode and
Python type-error handling. No pip install or local virtual environment is used.

PyO3 0.23.5 uses `extension-module` and `abi3-py312`. The limited Python ABI targets
CPython 3.12 and later, while this workspace runs tests with its pinned 3.12
interpreter. `PYO3_NO_PYTHON=1` on the PyO3 configuration build script prevents
host interpreter discovery. Linux resolves Python symbols from the importing
interpreter; the extension does not link an ambient libpython. This example is
for the template's Linux GNU platforms, not a portable macOS/Windows wheel.

Crate Universe pins the transitive crates in `Cargo.lock` and records Bazel
rendering metadata in `Cargo.Bazel.lock`. Both are required by this rules version. To intentionally
change dependencies, edit the spec in MODULE.bazel, then run:

```bash
CARGO_BAZEL_REPIN=1 bazel build //examples/pyo3:hello
bazel test //examples/pyo3:hello_test
bazel test --lockfile_mode=error //examples/pyo3:hello_test
```

The ordinary test command refreshes module-extension metadata after the repin
environment variable is removed; the following frozen-lock command checks it.
Review and commit both crate locks and MODULE.bazel.lock changes. Ordinary builds
must not set the repin environment variable. The existing coverage checker lists
specific original sources; it does not assert Rust-extension coverage for this
example. The Python integration tests are the acceptance check here.
