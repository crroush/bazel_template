# Adding external C++ dependencies: S2 Geometry and Abseil

The runnable example in [`examples/s2`](../../examples/s2) pins Google S2
Geometry v0.12.0 and Abseil 20240722.0 for Bazel 7 and Clang 23.1.6. It
has its own `MODULE.bazel` so you can build it independently.

## Build the example

From the template repository root, enter the example workspace and build it.

```bash
cd examples/s2
bazel build //...
bazel test //:geometry_test
bazel run //:geometry_test
```

The executable is `bazel-bin/geometry_test`. It prints the S2 cell token for
a sample coordinate. `bazel build //...` from the template root builds the
main workspace. Run it inside `examples/s2` to build the S2 example.

To cross-compile from the example workspace and inspect the output, run

```bash
bazel build --config=arm64 --config=release //:geometry_test
file bazel-bin/geometry_test
```

`file` should report `ARM aarch64`. Copy the executable to a compatible ARM64
Linux host to run it. Use `bazel mod graph` from the example workspace to
inspect the dependency graph.

Declare the sources, versions, build rules, and transitive dependencies so
Bazel can fetch them and compile against the selected toolchain. The first
fetch needs network access. The archive checksum verifies the downloaded bytes.

## Choose the integration method

| What the dependency supplies | Integration |
| --- | --- |
| A suitable Bazel Central Registry module | `bazel_dep` |
| `MODULE.bazel` and BUILD files, but you need a source release/fork | `bazel_dep` plus `archive_override` or a commit-pinned `git_override` |
| BUILD files but no module | `http_archive` with explicit external dependency declarations |
| No Bazel files | `http_archive` plus a BUILD overlay you maintain, or `rules_foreign_cc` for its CMake/Make build |

The source-archive method works independently of S2's registry availability
and reuses both libraries' upstream Bazel files.

## 1. Inspect the pinned upstream build

For S2 v0.12.0, the Bazel module lives at **`src/MODULE.bazel`**. Its module
name is `s2geometry`, and its public library is `//:s2`. Its module declares
Abseil, BoringSSL, and GoogleTest. S2's Bazel build uses BoringSSL and its CMake
build uses OpenSSL.

Check the exact release's
[module](https://github.com/google/s2geometry/blob/v0.12.0/src/MODULE.bazel),
[BUILD file](https://github.com/google/s2geometry/blob/v0.12.0/src/BUILD.bazel),
and [upstream instructions](https://github.com/google/s2geometry/tree/v0.12.0).
Repository names, source layout, and target labels can change between releases.

## 2. Pin the source archive in MODULE.bazel

The example's [`MODULE.bazel`](../../examples/s2/MODULE.bazel) declares both
dependencies and supplies S2 from its upstream source archive.

```starlark
bazel_dep(name = "s2geometry", version = "0.12.0")
bazel_dep(name = "abseil-cpp", version = "20240722.0")

archive_override(
    module_name = "s2geometry",
    urls = ["https://github.com/google/s2geometry/archive/refs/tags/v0.12.0.tar.gz"],
    strip_prefix = "s2geometry-0.12.0/src",
    integrity = "sha256-wJ7HUcMEOWWg1EHgRqc8RWyZXmBjQ5pyKQ9mHBBU1hE=",
    patches = ["//:s2-bit-width.patch"],
    patch_strip = 1,
)
```

`strip_prefix` makes S2's `src/` directory the external repository root. The
archive contains its module and BUILD files there. A plain root-level prefix
would leave Bazel unable to find the module.

The consuming root module controls the override. Upstream v0.12.0 identifies
its module version as `head`, so the archive and integrity value pin the source.
Bzlmod reads the transitive dependency declarations from that source.

Stripping to `src/` also omits top-level files such as release documentation
and license notices from this build view. Preserve upstream license/NOTICE
files separately when packaging or redistributing the libraries.

The second override fetches Abseil from its upstream release archive.

```starlark
archive_override(
    module_name = "abseil-cpp",
    urls = ["https://github.com/abseil/abseil-cpp/archive/refs/tags/20240722.0.tar.gz"],
    strip_prefix = "abseil-cpp-20240722.0",
    integrity = "sha256-9Q5awxGoE4Laf6dblzEOS5AGR0+VYKxG9UqZZ/B9SuM=",
)
```

These overrides bypass the registry for those two modules. Other dependencies
resolve through the configured registry.

The downloaded archives have the following SHA-256 values.

```text
S2:     c09ec751c3043965a0d441e046a73c456c995e6063439a72290f661c1054d611
Abseil: f50e5ac311a81382da7fa75b97310e4b9006474f9560ac46f54a9967f07d4ae3
```

When upgrading, download the chosen archive from the upstream release, inspect
it, and compute its new digest. See Bazel's [archive_override reference](https://bazel.build/rules/lib/globals/module#archive_override).

Run these commands to compute both common digest formats for a new archive.

```bash
sha256sum library.tar.gz
openssl dgst -sha256 -binary library.tar.gz | openssl base64 -A
```

Use the hexadecimal output for `http_archive(sha256 = ...)`, or prefix the
base64 output with `sha256-` for `archive_override(integrity = ...)`.

## 3. Use a consistent C++ standard

S2's upstream Bazel configuration uses C++20. The example sets the standard
for S2, Abseil, and their consumers in `llvm.toolchain` in `MODULE.bazel`.

```starlark
cxx_standard = {"": "c++20"},
```

Mixing C++ standard library implementations or incompatible build settings can
cause ABI/link errors. Keep exceptions enabled.

The [S2 patch](../../examples/s2/s2-bit-width.patch) converts the bit count to
a signed integer before subtracting it. The libstdc++ headers in the Bullseye
sysroot return an unsigned type from `bit_width`, which S2 v0.12.0 mixes with
a negative sentinel. The bit count is at most 64 and fits in `int`.

## 4. Add a consumer with explicit dependencies

[`BUILD.bazel`](../../examples/s2/BUILD.bazel) declares the test and its
direct dependencies.

```starlark
load("@rules_cc//cc:defs.bzl", "cc_test")

cc_test(
    name = "geometry_test",
    size = "small",
    srcs = ["geometry_test.cc"],
    linkstatic = True,
    deps = [
        "@abseil-cpp//absl/strings",
        "@s2geometry//:s2",
    ],
)
```

The [test source](../../examples/s2/geometry_test.cc) directly includes
Abseil headers, so it declares Abseil in `deps` even though S2 also uses it.
The exported targets propagate their headers, libraries, and transitive
dependencies.

`linkstatic = True` links the C++ dependency libraries into this test, which
also makes copying it to ARM simpler. The executable still uses the system
Linux loader and libc.

## 5. Handle toolchain differences

`--config=arm64` selects the ARM64 target platform and compiler. This Abseil
release also reads the legacy `--cpu` flag when choosing hardware AES compiler
options. The example's `arm64` config sets `--cpu=aarch64` for that reason.
Abseil selects `-march=armv8-a+crypto` for the translation unit that implements
its hardware-accelerated random number generator.

When using this recipe in another workspace, copy the dependency declarations
and overrides into that workspace's `MODULE.bazel`. Export the S2 patch from a
BUILD package and update its label in `patches`. Set C++20 for the dependency
graph and add `--cpu=aarch64` to its ARM config. Add the library labels
to the targets that consume them.

Commit the module changes, generated `MODULE.bazel.lock`, consumer, and any
patches/overlays you add. Inspect `bazel mod graph` during upgrades: ordinary
`bazel_dep` versions participate in module resolution and another dependency
can request a higher version. Root source overrides deliberately fix the
selected module to the supplied source archive.

## What if the library has no Bazel build files?

For a library without Bazel files, supply a BUILD overlay. Replace the archive
URL, digest, and filenames in this **schematic example** with the library's
actual values.

Declare the archive and overlay in `MODULE.bazel`.

```starlark
http_archive = use_repo_rule("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

http_archive(
    name = "vendor_geometry",
    urls = ["https://YOUR_MIRROR/vendor-geometry-1.2.3.tar.gz"],
    sha256 = "REPLACE_WITH_VERIFIED_64_HEX_DIGEST",
    strip_prefix = "vendor-geometry-1.2.3",
    build_file = "//third_party/vendor_geometry:BUILD.vendor.bazel",
)
```

Export the overlay in `third_party/vendor_geometry/BUILD.bazel`.

```starlark
exports_files(["BUILD.vendor.bazel"])
```

Define the external library in `third_party/vendor_geometry/BUILD.vendor.bazel`.

```starlark
load("@rules_cc//cc:defs.bzl", "cc_library")

cc_library(
    name = "geometry",
    srcs = ["src/geometry.cc"],
    hdrs = ["include/vendor/geometry.h"],
    includes = ["include"],
    deps = ["@abseil-cpp//absl/strings"],
    visibility = ["//visibility:public"],
)
```

The overlay's paths refer to the extracted external archive. Consumers use
`deps = ["@vendor_geometry//:geometry"]`. Declare the external dependencies
that the overlay references in the root module. If the
upstream BUILD files use legacy repository names, patch the labels to match
your Bzlmod declarations. See the [http_archive reference](https://bazel.build/rules/lib/repo/http#http_archive).

List production sources deliberately. A blanket `glob(["**/*.cc"])` can pull
in test mains, benchmarks, unsupported platforms, or optional backends. Handle
generated configuration headers, platform-specific sources, assembly, compile
defines, and licenses explicitly. Keep patches in `third_party/` and apply
them with the archive rule's `patches` and `patch_args`.

If porting a large CMake build would be impractical, investigate
[rules_foreign_cc](https://bazel-contrib.github.io/rules_foreign_cc/).
That requires configuring the compiler, build tools, dependency prefixes,
outputs, and cross-compilation behavior. For hermetic CMake builds, disable
undeclared system dependency discovery and build-time downloads. Configure
generators to run on the host platform.

## Practical upgrade checks

1. Verify the release URL, digest, archive layout, module name, and licenses.
2. Review changed upstream dependencies and exported targets.
3. Build native and ARM outputs and run tests on the appropriate architecture.
4. Run strict warnings, native diagnostics, and coverage as applicable.
5. Refresh editor compile commands and commit the updated lockfile.

Keep persistent fixes in the checked-in overlay or patch. Bazel may replace
the generated `bazel-*` and `external/` paths on the next fetch or clean.
