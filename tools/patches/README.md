# LLVM sysroot file tracking

`sysroot-files.patch` changes the pinned toolchains_llvm 1.13.0 sysroot
filegroup from a source directory to individual files. This removes Bazel's
unsound-directory warning and allows headers and libraries to participate in
normal action dependency checking. Downloads, checksums, extraction, and
sysroot paths remain controlled by the upstream rule.

Exclude `lib/systemd/**`: these runtime service definitions are not compiler or
linker inputs, and one contains a literal backslash, which Bazel labels forbid.

The separate S2 workspace carries an identical copy at
`examples/s2/sysroot-files.patch`, because it must work as an independent Bazel
workspace. Keep both copies identical when updating the toolchain.

Individual files cost more analysis and sandbox setup than one directory, but
provide correct dependency tracking. Validate native tests and inspect action
inputs when upgrading the toolchain; do not suppress directory warnings.
