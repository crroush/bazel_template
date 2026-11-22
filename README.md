# Bazel polyglot template

C++20, Rust, JavaScript, and Python bindings to C++ (pybind11) and Rust (PyO3).
Targets Linux x86-64 and ARM64.

Pinned tools: Bazel 7.6.1, Clang 23.1.6, CPython 3.12, Rust 1.85.1,
and Node.js 22.14.0.

## Setup

Use Linux with glibc 2.34+ (Ubuntu 22.04+ or RHEL 9+) and at least 20 GB free.
Install `ca-certificates`, `curl`, `file`, `git`, `tar`, `gzip`, `unzip`, and
`xz-utils` (`xz` on RHEL).

Install [Bazelisk](https://github.com/bazelbuild/bazelisk#installation) as `bazel`
on your PATH. It reads `.bazelversion`; Bazel downloads the language toolchains
and dependencies on the first build. Run as your normal user.

## Build and test

From the repository root:

```bash
bazel build --lockfile_mode=error //...
bazel test --lockfile_mode=error --config=strict --nocache_test_results //...
```

This runs all six native test targets, including PyO3. `--config=strict` treats
first-party C/C++ warnings as errors; `--nocache_test_results` forces tests to
execute. Omit it for routine cached runs. `--lockfile_mode=error` rejects stale
module locks.

S2 Geometry has a separate workspace and is **not included** in root `//...`:

```bash
(cd examples/s2 && bazel test //:geometry_test)
```

S2 extracts its own toolchain, so allow additional disk space.

## Run the examples

```bash
bazel run //examples/cpp:hello
bazel run //examples/rust:hello
bazel run //examples/javascript:hello
bazel run //examples/python:hello  # Python calling C++
bazel run //examples/pyo3:hello    # Python calling Rust
```

To exercise the Rust bindings directly:

```bash
bazel test --nocache_test_results --test_output=all //examples/pyo3:hello_test
```

The PyO3 demo prints `Hello, world from Rust!`. Its tests cover greetings,
Unicode, and invalid argument types using Bazel's Python runtime—no local
virtual environment or pip install needed.

## Additional checks

```bash
# C++ memory and undefined-behavior checks
bazel test --config=asan --config=ubsan //examples/cpp:hello_test

# Coverage and the selected-source 80% threshold
bazel coverage //...
python3 tools/coverage/check.py bazel-out/_coverage/_coverage_report.dat
```

The coverage checker covers an explicit list of original example sources;
it does not assert coverage of the PyO3 Rust extension. For HTML output, install
`lcov` and run `genhtml bazel-out/_coverage/_coverage_report.dat -o coverage-html`.

## Release builds and ARM64

Use `--config=debug`, `--config=release`, or `--config=minsize` to select a build
mode. Outputs are under `bazel-bin/`.

```bash
bazel build --config=release //examples/python:wheel
bazel build --config=arm64 --config=release \
  //examples/cpp:hello //examples/rust:hello //examples/python:wheel
file bazel-bin/examples/cpp/hello bazel-bin/examples/rust/hello
```

Cross-compiled executables should report AArch64. Run them on a compatible ARM64
Linux host or emulator; the Python wheel requires CPython 3.12.

## Shared builds and further setup

A remote cache lets developers download matching CI build outputs. Cache misses
still build locally, and toolchain downloads are separate. Follow the
[remote cache guide](docs/remote-cache.md) for server setup, credentials,
read-only developer access, and checking cache hits. Put machine-specific
settings in the ignored `.bazelrc.local`.

- [PyO3 bindings and crate locks](examples/pyo3/README.md)
- [Python/C++ wheels and PyPI dependencies](examples/python/README.md)
- [External C++ dependencies and S2](docs/dependencies/README.md)
- [Hermeticity guarantees and host limitations](docs/hermeticity.md)

Sysroot files are tracked individually in both workspaces; see the
[toolchain patch](tools/patches/README.md). Pinned toolchains do not by themselves
make the host environment fully hermetic.
