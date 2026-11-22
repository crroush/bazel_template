# NVIDIA CUDA vector addition

From the repository root:

```bash
# Compilation needs no GPU or system CUDA installation.
bazel build --config=cuda //examples/cuda:vector_add //examples/cuda:vector_add_test

# Execution requires an NVIDIA GPU and driver.
bazel run --config=cuda //examples/cuda:vector_add
bazel test --config=cuda --test_output=all //examples/cuda:vector_add_test
```

The kernel adds 1,003 pairs of floats. The program checks every result against
a CPU calculation, including the partially filled final block. CUDA errors,
missing devices, and incorrect results fail the test; there is no CPU fallback.

This example supports Linux x86-64 and compute capability 8.0+ (Ampere or newer).
It emits SM80 machine code and compute_80 PTX for newer GPUs. Install a driver
compatible with CUDA 12.8.1 and PTX JIT (use a current supported NVIDIA driver). Check driver/device visibility with `nvidia-smi`.
Containers need GPU passthrough, for example through NVIDIA Container Toolkit.
Bazel does not install a kernel driver or provide GPU access.

CUDA 12.8.1 redistributables and their manifest are checksum-pinned. Device code
is compiled with the existing pinned Clang toolchain, not a system `nvcc` or
`clang`; the CUDA runtime is linked statically. Downloads come from
`developer.download.nvidia.com` and are subject to NVIDIA's toolkit license.
ARM64/Jetson is not configured by this example.

Clang cannot detect the toolkit version from the split redistributable layout
and emits an `unknown-cuda-version` warning. The CUDA configuration explicitly
pins PTX 8.7 to match the CUDA 12.8 assembler; it does not disable version checks.

All CUDA targets are `manual`, so ordinary root `//...` builds and tests remain
CPU-only. CI builds the explicit CUDA targets without running them. The GPU test
is local and uncached so a cached result cannot stand in for checking the current
GPU. Run it explicitly on a GPU worker; compile actions can still use a remote
cache with matching toolchain and architecture settings.
