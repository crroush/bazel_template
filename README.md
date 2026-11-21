# Bazel polyglot template

Build and test C++20, Python with pybind11, Rust, and JavaScript on Linux
x86-64 and ARM64. The workspace pins Bazel 7.6.1, Clang 23.1.6, CPython 3.12,
Rust 1.85.1, and Node.js 22.14.0.

## Install Bazel

Use a Linux build host with glibc 2.34 or newer, such as Ubuntu 22.04+
or RHEL 9+. Install the tools for your distribution.

```bash
# Ubuntu
sudo apt update
sudo apt install -y ca-certificates curl file git tar gzip unzip xz-utils

# RHEL
sudo dnf install -y ca-certificates curl file git tar gzip unzip xz
```

Install [Bazelisk](https://github.com/bazelbuild/bazelisk#installation) as
`bazel`. It uses `.bazelversion` to select the pinned Bazel release.

```bash
(
  set -eu
  case "$(uname -m)" in
    x86_64) bazelisk_arch=amd64 ;;
    aarch64|arm64) bazelisk_arch=arm64 ;;
    *) echo "Unsupported host architecture: $(uname -m)" >&2; exit 1 ;;
  esac
  bazelisk_tmp=$(mktemp)
  trap 'rm -f "$bazelisk_tmp"' EXIT
  curl -fL "https://github.com/bazelbuild/bazelisk/releases/latest/download/bazelisk-linux-$bazelisk_arch" \
    -o "$bazelisk_tmp"
  sudo install -m 0755 "$bazelisk_tmp" /usr/local/bin/bazel
)
```

Make sure `/usr/local/bin` is on your `PATH`. Run builds as your normal user.
The first build downloads toolchains and dependencies. Allow at least 20 GB
of free space for the LLVM archive, extracted files, and build outputs. The
separate S2 workspace has its own extracted toolchain directory.

## Build and run

From the repository root:

```bash
bazel --version
bazel build //...
bazel test //...

bazel run //examples/cpp:hello
bazel run //examples/python:hello
bazel run //examples/rust:hello
bazel run //examples/javascript:hello
```

Each command prints a greeting. The Python demo also calls into C++. A label
such as `//examples/cpp:hello` means target `hello` in package `examples/cpp`.
Each package defines its targets in `BUILD.bazel`. `MODULE.bazel` declares the
external modules and toolchains, and `MODULE.bazel.lock` records Bzlmod
resolution. Commit both when updating module dependencies.

Build outputs are available through `bazel-bin/`. Bazel updates this symlink
when you switch build configurations.

## C++20

`examples/cpp/BUILD.bazel` defines the `greeting` library, the `hello`
executable, and `hello_test`. The executable and the Python extension both
link the greeting library. Use `cc_library` for reusable C++ code and declare
the targets it consumes in `deps`.

`toolchains_llvm` uses the official Clang 23.1.6 distribution and LLD. It sets
`-std=c++20` and uses a pinned Debian Bullseye sysroot for the target CPU. The
sysroot provides Linux headers, glibc, and libstdc++. Standard library features
depend on the libstdc++ version in that sysroot.
[LLVM 23.1.6 release](https://github.com/llvm/llvm-project/releases/tag/llvmorg-23.1.6)

```bash
bazel test //examples/cpp:hello_test
bazel aquery 'mnemonic("CppCompile", //examples/cpp:hello)' --noinclude_artifacts
```

For external libraries, start with the [Bazel Central Registry](https://registry.bazel.build/).
The [external C++ dependencies guide](docs/dependencies/README.md) shows how
to pin a source archive, reuse upstream BUILD files, or supply your own overlay.
Its S2 Geometry and Abseil example has a separate Bazel workspace.

```bash
(cd examples/s2 && bazel test //:geometry_test)
```

## Python and C++ bindings

`examples/python/BUILD.bazel` uses `pybind_extension` to build `_greeting.so`
from `bindings.cc` and the C++ greeting library. The `py_library` supplies the
Python wrapper and makes the shared object available as a runtime file.
`py_binary` runs the demo with CPython 3.12. The wrapper uses NumPy to apply
the binding to an array of names.

`pip.parse` reads `requirements.lock` to provide `@pypi//numpy`. The wheel
target packages the wrapper and extension and reads `requirements.in` to
declare what `pip` should install alongside it. The hashed lockfile pins what
Bazel tests. The wheel metadata declares the compatible version range.

```bash
bazel test //examples/python:hello_test
bazel build --config=release //examples/python:wheel
```

The [Python guide](examples/python/README.md) covers installing the wheel,
adding PyPI dependencies, generating hashes with `pip-compile`, and reviewing
both lockfiles.

## Rust

`examples/rust/BUILD.bazel` uses `rust_binary` to compile `main.rs` and
`rust_test` to run its inline tests. `rules_rust` downloads the pinned
compiler and standard library. Rust uses the selected C/C++ toolchain for
linking, including when targeting `aarch64-unknown-linux-gnu`.

```bash
bazel run //examples/rust:hello
bazel test //examples/rust:hello_test
```

For external crates, use Crate Universe to turn a Cargo dependency graph into
Bazel targets. [Crate Universe for Bzlmod](https://bazelbuild.github.io/rules_rust/crate_universe_bzlmod.html)

## JavaScript

`examples/javascript/BUILD.bazel` uses `js_library` for the greeting module,
`js_binary` for the entry point, and `js_test` for its tests. Bazel stages the
CommonJS sources and runtime files, then runs them with the pinned Node.js
toolchain.

```bash
bazel run //examples/javascript:hello
bazel test //examples/javascript:hello_test
```

For npm packages, use `npm_translate_lock` with a pnpm lockfile and add the
generated targets to the rules that use them. [rules_js documentation](https://github.com/aspect-build/rules_js)

## Cross-compile for Linux ARM64

From x86-64 Linux, the ARM64 configuration selects an ARM target sysroot.
Clang runs on the host and produces ARM64 code. Rust selects the matching
standard library.

```bash
bazel build --config=arm64 --config=release \
  //examples/cpp:hello //examples/rust:hello //examples/python:wheel

file bazel-bin/examples/cpp/hello bazel-bin/examples/rust/hello
```

`file` should report AArch64. The ARM executables need a compatible Linux
loader, glibc, and libstdc++. The Debian Bullseye sysroot uses glibc 2.31.
Install the `linux_aarch64` wheel into CPython 3.12 on the ARM machine.

Use `bazel info --config=arm64 --config=release bazel-bin` to locate the
configuration-specific output directory from anywhere in the workspace.
Run ARM Linux tests on an ARM host or with a configured emulator.

## Build configurations and checks

| Configuration | Purpose |
| --- | --- |
| Default | Bazel's fastbuild mode |
| `--config=debug` or `--config=dbg` | Debug build that keeps symbols |
| `--config=release` or `--config=opt` | Optimized build |
| `--config=minsize` | C/C++ build optimized for size |
| `--config=strict` | Treat first-party C/C++ warnings as errors |
| `--config=asan` and `--config=ubsan` | Native C++ memory and undefined behavior checks |

```bash
bazel test --config=strict //...
bazel test --config=asan --config=ubsan //examples/cpp:hello_test
bazel coverage //...
python3 tools/coverage/check.py bazel-out/_coverage/_coverage_report.dat
genhtml bazel-out/_coverage/_coverage_report.dat --output-directory coverage-html
```

The C++ sanitizer and coverage configurations use the pinned Clang toolchain.
Install `lcov` to render the HTML report. The combined LCOV report includes
C++, Python, Rust, and JavaScript. The checker requires at least 80% line coverage across
its selected example sources and fails on missing or empty records.
Open `coverage-html/index.html` to view the report.

CI runs the native tests and diagnostics, uploads LCOV and HTML reports,
and checks the architecture of the cross-compiled executables.

### Local cache

Put optional machine-specific settings in the ignored `.bazelrc.local`.

```text
build --disk_cache=~/.cache/bazel/polyglot-template
build --experimental_disk_cache_gc_max_size=10G
```
