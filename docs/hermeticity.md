# Hermeticity boundary and template review

This is a Linux Bazel template with pinned language toolchains, not a complete
hermetic operating-system image. Distinguish reproducible action inputs from
network availability, runtime compatibility, and supply-chain provenance.

| Area | Current behavior and implication |
| --- | --- |
| Bazel | `.bazelversion` pins 7.6.1; install a verified Bazel/Bazelisk binary. The README's latest Bazelisk URL is not itself a pinned bootstrap artifact. |
| C++ | LLVM archive and Debian sysroots have checksums. Host glibc must still run LLVM; produced binaries dynamically use the target's libc/libstdc++. |
| Sysroot tracking | A local patch to toolchains_llvm 1.13.0 declares individual sysroot files, so Bazel tracks file content in action inputs instead of an opaque directory. Both workspaces apply the patch. Systemd service definitions are excluded because they are not build inputs and contain a filename Bazel cannot represent as a label. |
| Python | rules_python resolves a downloaded 3.12 runtime through the module lock; NumPy wheels are versioned and hashed. This is not system Python. |
| Rust | rules_rust pins 1.85.1. PyO3's transitive crate graph has a separate checked-in lock. ABI3 plus PYO3_NO_PYTHON avoids ambient Python discovery. |
| CUDA | Optional Linux x86-64 example uses Clang and checksum-pinned CUDA 12.8.1 redistributables. GPU execution requires an external NVIDIA driver and compute capability 8.0+ device; neither is supplied by Bazel. GPU tests run locally without cached results. |
| JavaScript | rules_nodejs pins Node 22.14.0. Future npm dependencies need a committed lock and declared Bazel targets. |
| Actions | Strict action environment reduces accidental environment inputs; sandboxing is useful but not proof of total isolation. Tool scripts can still depend on host shell/utilities and the kernel. |
| Network | Build and test sandboxes disable network by default. Repository fetching still requires network or warmed caches; explicit action requirements and unsandboxed strategies can override isolation. |
| CI | Ubuntu runner labels and action major tags are mutable. Pin action SHAs and a development/execution image digest in a production derivative and maintain an update policy. |
| Separate S2 workspace | Own module lock, Bazel rc and toolchain extraction. Root `//...` excludes it, and root local cache settings do not apply automatically. |
| Coverage | The checker asserts coverage only for its explicit original source list. Passing it does not establish coverage of every added example. |

For a production derivative, pin a Linux image with the required host tools,
use the same execution platform in CI and development, run ordinary CI with
`--lockfile_mode=error`, and update dependencies in an explicit reviewed job.
Keep repository rules checksum-verifying. Never use host `/usr` headers or an
ambient Python interpreter as a shortcut around missing pinned dependencies.

Validate sandboxed native tests, then compare action-cache reuse in independent
output bases. Add offline checks only after warming every required platform's
repository downloads. Consider remote execution if developers should not need
local toolchains or host compatibility. See [remote cache setup](remote-cache.md).

In this managed host, Bazel selected `processwrapper-sandbox`, which does not
provide Linux namespace/network isolation. The network flag is a default for
capable sandbox implementations, not an enforced security boundary here. Use
a host supporting `linux-sandbox` or an isolated remote executor when that
is required.
