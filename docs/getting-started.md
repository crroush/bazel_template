# Start a project from the Bazel template

## 1. Create your repository

On GitHub, open [bazel_template](https://github.com/crroush/bazel_template).
If **Use this template** is available, select it, create the repository in
your account or organization, and clone the new repository.

```bash
git clone https://github.com/YOUR-OWNER/YOUR-PROJECT.git
cd YOUR-PROJECT
```

If the template button is unavailable, create an empty GitHub repository
without a README, then copy the tracked template files into a fresh local
repository. Replace `YOUR-OWNER` and `YOUR-PROJECT` in the commands.

```bash
git clone https://github.com/crroush/bazel_template.git bazel-template-source
mkdir YOUR-PROJECT
git -C bazel-template-source archive HEAD | tar -x -C YOUR-PROJECT
cd YOUR-PROJECT
git init -b main
git add .
git commit -m "Initialize project from Bazel template"
git remote add origin https://github.com/YOUR-OWNER/YOUR-PROJECT.git
git push -u origin main
```

## 2. Verify the template on your machine

Follow the [Linux prerequisites and Bazelisk installation](../README.md#setup).
From the directory containing the root `MODULE.bazel`, run:

```bash
bazel --version
bazel run //examples/cpp:hello
bazel test --lockfile_mode=error --config=strict //...
```

Expect `bazel 7.6.1`, `Hello, world from C++!`, and a passing native test suite.
The first run downloads and extracts toolchains and dependencies. Run
`bazel info workspace` if you need to confirm which workspace Bazel selected.
The S2 example is a separate workspace and has its own
[build instructions](dependencies/README.md#build-the-example).

## 3. Add a package with a binary and test

This example creates a C++ package under `app/` that you can build without
depending on any demo code. Run the following from the project root.

```bash
mkdir -p app

cat > app/greeting.h <<'EOF_CPP'
#ifndef APP_GREETING_H_
#define APP_GREETING_H_

#include <string_view>

constexpr std::string_view Greeting() { return "Hello from my project!"; }

#endif  // APP_GREETING_H_
EOF_CPP

cat > app/main.cc <<'EOF_CPP'
#include <iostream>

#include "app/greeting.h"

int main() {
  std::cout << Greeting() << '\n';
  return 0;
}
EOF_CPP

cat > app/greeting_test.cc <<'EOF_CPP'
#include "app/greeting.h"

int main() {
  return Greeting() == "Hello from my project!" ? 0 : 1;
}
EOF_CPP

cat > app/BUILD.bazel <<'EOF_BAZEL'
load("@rules_cc//cc:defs.bzl", "cc_binary", "cc_library", "cc_test")

cc_library(
    name = "greeting",
    hdrs = ["greeting.h"],
)

cc_binary(
    name = "hello",
    srcs = ["main.cc"],
    deps = [":greeting"],
)

cc_test(
    name = "greeting_test",
    size = "small",
    srcs = ["greeting_test.cc"],
    deps = [":greeting"],
)
EOF_BAZEL

bazel run //app:hello
bazel test //app:greeting_test
```

The binary prints `Hello from my project!`. The test exits successfully
when the library returns the expected greeting. A directory with a `BUILD.bazel` file
defines a Bazel package. In `//app:hello`, `app` is the package and `hello`
is the target. `:greeting` refers to the library in the same package.

Use the matching example BUILD file as a starting point for another language.

| Language | Example | Dependencies |
| --- | --- | --- |
| C++ | [Executable, library, and test](../examples/cpp/BUILD.bazel) | [External C++ dependencies](dependencies/README.md) |
| Python | [Executable, test, and optional C++ binding and wheel](../examples/python/BUILD.bazel) | [PyPI dependencies and lockfiles](../examples/python/README.md#manage-python-dependencies-and-lockfiles) |
| Rust | [Executable and inline tests](../examples/rust/BUILD.bazel) | [Crate Universe](https://bazelbuild.github.io/rules_rust/crate_universe_bzlmod.html) |
| Rust bindings for Python | [PyO3 executable and tests](../examples/pyo3/BUILD.bazel) | [PyO3 bindings and crate locks](../examples/pyo3/README.md) |
| JavaScript | [CommonJS executable, library, and test](../examples/javascript/BUILD.bazel) | [rules_js and npm integration](https://github.com/aspect-build/rules_js) |

## 4. Make the repository your own

- Set your project's name and version in the root `MODULE.bazel` and
  update the README. Keep the MPL 2.0 license and the template's attribution
  notice when redistributing covered files. Leave the toolchain pins in
  place while getting the first build working. Review and commit any changes
  Bazel generates in `MODULE.bazel.lock`.
- In [`.bazelrc`](../.bazelrc), add your source paths to the `strict`
  configuration's `--per_file_copt` pattern and your package labels to the
  coverage `--instrumentation_filter`. For example, use
  `(examples|app)/.*@-Wall,-Wextra,-Werror` for strict warnings and
  `^//(examples|app)[/:]` for coverage while keeping both directories.
  Update the `SOURCES` list in [the coverage checker](../tools/coverage/check.py)
  and its fixtures in [the checker tests](../tools/coverage/check_test.py)
  to match the files your project measures.
- In [the GitHub Actions workflow](../.github/workflows/build.yml), replace
  the explicit sanitizer test and ARM64 executable labels and output paths
  with your project's targets. If you ship a wheel, update the wheel build
  label, filename pattern, and Python smoke test. If you remove the wheel or
  the standalone S2 workspace, remove its CI check. The general `//...`
  build and test steps already discover your new packages.
- Before removing demo packages, update any references to them. The Python
  binding uses `//examples/cpp:greeting`, and `pip.parse` in `MODULE.bazel`
  points to `examples/python:requirements.lock`. If you keep the wheel,
  update its distribution metadata and installed import paths in the
  [Python BUILD file](../examples/python/BUILD.bazel). If you remove
  `examples/s2`, remove its entries from `.bazelignore` and `.gitignore`.
- Run `bazel build //...` and `bazel test --lockfile_mode=error --config=strict //...` after
  customization, then run the coverage, sanitizer, and ARM64 commands you
  kept in your workflow.
