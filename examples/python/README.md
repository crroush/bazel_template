# Bazel Template Greeting

`bazel-template-greeting` is a CPython 3.12 package that exposes a C++ greeting
through pybind11. Its Python wrapper uses NumPy to apply the binding to an
array of names while preserving the shape.

```python
from bazel_template_greeting import greet, greet_many

print(greet("wheel"))  # Hello, wheel from C++!
print(greet_many(["Bazel", "NumPy"]).tolist())
```

## Build and install

From the repository root on Linux:

```bash
bazel build --config=release //examples/python:wheel
wheel="$PWD/bazel-bin/examples/python/bazel_template_greeting-0.2.0-cp312-cp312-linux_$(uname -m).whl"

wheel_venv=$(mktemp -d)
python3.12 -m venv "$wheel_venv"
"$wheel_venv/bin/python" -m pip install "$wheel"
"$wheel_venv/bin/python" -I -c 'from bazel_template_greeting import greet_many; print(greet_many(["Bazel", "NumPy"]).tolist())'
```

Bazel uses its own CPython 3.12 toolchain. The install test uses local
CPython 3.12 with `venv` support. On Ubuntu 24.04, install `python3.12-venv`
if `venv` or `ensurepip` is missing.

To cross-compile for Linux ARM64, run the following command.

```bash
bazel build --config=arm64 --config=release //examples/python:wheel
```

Copy the resulting `linux_aarch64` wheel from `bazel-bin/examples/python/`
to an ARM64 Linux host and install it with CPython 3.12.

## Manage Python dependencies and lockfiles

`py_wheel` builds this package and sets its metadata. A `pyproject.toml` is
optional for this workflow. If you use standard packaging tools as well, you
can keep `[project].dependencies` in `pyproject.toml` and pass that file to
`pip-compile`. Keep the wheel metadata in sync with the supported requirements.

| File or target | What it controls |
| --- | --- |
| `requirements.in` | The supported range, `numpy>=2,<3`. The wheel reads it to write `Requires-Dist` metadata. |
| `requirements.lock` | The exact versions and SHA-256 hashes Bazel uses, including NumPy wheels for CPython 3.12 on both Linux architectures. |
| `MODULE.bazel` | `pip.parse` reads the lock and exposes the packages as Bazel targets. |
| `//examples/python:greeting` | `deps = ["@pypi//numpy"]` makes NumPy available to the wrapper and tests. |
| `MODULE.bazel.lock` | Bazel's generated record of Bzlmod resolution and module extension evaluation. |

The greeting wheel includes the Python wrapper and `_greeting.so`. When
someone installs it, `pip` reads the metadata and downloads NumPy separately.
This example imports NumPy from Python. A binding that includes NumPy C
headers also needs those headers as a declared C++ build input.

### Install pip-compile

Install `pip-tools` in a Python 3.12 virtual environment. On Ubuntu, install
`python3.12-venv` first if necessary.

```bash
python3.12 -m venv "$HOME/.venvs/bazel-lock"
"$HOME/.venvs/bazel-lock/bin/python" -m pip install pip-tools
```

Use the full path to `pip-compile` below if the shell reports
`command not found: pip-compile`. This environment is for lock generation.
Bazel runs builds and tests with its own toolchain.

### Add or update a requirement

1. Edit `examples/python/requirements.in`. For example, add
   `pyopenlayersqt>=0.22,<0.23` if the packaged code needs it. That package
   publishes a Python wheel, which Bazel can consume through `pip.parse`.
   If only a separate demo uses it, give the demo its own requirements and
   dependency target. [pyopenlayersqt release files](https://pypi.org/project/pyopenlayersqt/0.22.0/#files)

2. From the repository root, regenerate the Python lock. This pins the
   direct and transitive dependencies and records their allowed hashes.
   Add `--upgrade-package numpy` to refresh that package's pin.

   ```bash
   "$HOME/.venvs/bazel-lock/bin/pip-compile" \
     --generate-hashes --strip-extras --pip-args='--only-binary=:all:' \
     --output-file=examples/python/requirements.lock \
     examples/python/requirements.in
   ```

3. Add the label to the `deps` of the target that imports it. For example,
   use `deps = ["@pypi//numpy", "@pypi//pyopenlayersqt"]` if the library imports
   both. The wheel reads the compatible ranges from `requirements.in`.

4. Build and test the affected target. Rebuild the wheel and repeat the clean
   install test if its requirements changed.

   ```bash
   bazel test //examples/python:hello_test
   bazel build --config=release //examples/python:wheel
   ```

For ARM64, check compatible wheels for all the native dependencies.
`pyopenlayersqt` ships a platform-independent wheel, while its Qt
dependencies need wheels compatible with the target CPU and Linux runtime.
If the dependency graph differs by platform, generate separate locks and
map them with `pip.parse(requirements_by_platform = ...)`.
[rules_python platform lockfiles](https://rules-python.readthedocs.io/en/1.5.0/pypi/download.html#requirements-for-a-specific-os-architecture)

For a library distributed as source, you can build and host a wheel on a
package index. For use inside Bazel, you can also wrap the source with
`py_library`.

### Find a wheel hash

Each SHA-256 identifies one exact archive. The Linux x86-64 and ARM64 NumPy
wheels have different hashes even at the same version. `pip-compile` writes
the hashes for you. To check one manually, open **Download files → View
details** on PyPI or download and hash the wheel.

```bash
wheel_dir=$(mktemp -d)
"$HOME/.venvs/bazel-lock/bin/python" -m pip download --only-binary=:all: \
  --no-deps --dest "$wheel_dir" 'pyopenlayersqt==0.22.0'
"$HOME/.venvs/bazel-lock/bin/python" -m pip hash "$wheel_dir"/*.whl
```

`pip hash` prints a `--hash=sha256:...` entry. Use the lock generation command
to resolve and hash the full dependency graph.
[pip-tools documentation](https://pip-tools.pypa.io/en/stable/)

### Review and commit both lockfiles

- Generate `requirements.lock` before building a new `@pypi//...` target.
  Review and commit it with `requirements.in` and the consuming code and
  BUILD changes.
- Bazel updates `MODULE.bazel.lock` as needed during module resolution.
  Review and commit its changes with the declarations that caused them.
  [Bazel lockfile documentation](https://bazel.build/external/lockfile)

## Check a wheel for distribution

Bazel produces wheels tagged `linux_x86_64` or `linux_aarch64`. For public
distribution, inspect shared-library requirements with `auditwheel show` and
use `auditwheel repair` to produce a validated manylinux wheel where supported.
With `auditwheel`, `patchelf`, and `twine` installed, check the x86-64 wheel
using the `$wheel` path from the install example.

```bash
auditwheel show "$wheel"
repaired_dir=$(mktemp -d)
auditwheel repair --plat manylinux_2_28_x86_64 --wheel-dir "$repaired_dir" "$wheel"
twine check --strict "$repaired_dir"/*.whl
```

Install and test the repaired wheel with the target interpreter. Choose your
distribution name and version in the `py_wheel` target before releasing it.
