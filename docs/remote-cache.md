# Sharing build results with a team

A Bazel remote **action cache** lets trusted CI build a commit once and lets
other machines download matching outputs. It is not a prebuilt checkout:
Bazel still fetches repositories/toolchains, analyzes targets, and computes
input digests. Cache misses build locally. Remote **execution** is a separate
service that also runs those missing actions in the cloud.

## Provision a cache

Use a service implementing Bazel's HTTP cache protocol or Remote Execution
API (for example BuildBuddy, BuildBarn, or bazel-remote). Follow that service's
TLS, authentication, storage quota, retention, and backup instructions. Obtain
an HTTPS or `grpcs://` endpoint and a project namespace. A normal object-store
URL is not automatically a Bazel cache endpoint. No endpoint is provisioned by
this template.

Give protected CI read/write credentials and developers read-only credentials.
Enforce these permissions on the server: `--remote_upload_local_results=false`
is a client preference, not authorization. Untrusted pull requests must not get
writer credentials. Cache contents include build outputs, test logs and source
fragments; scope access to the project. Do not compile credentials into outputs.

## Developer configuration

Add this to the existing ignored `.bazelrc.local` (replace the example endpoint):

```text
build:team --remote_cache=grpcs://cache.example.com
build:team --remote_instance_name=my-team/my-project
build:team --remote_upload_local_results=false
build:team --remote_download_outputs=all
build:team --remote_timeout=60
```

The instance name is optional and must be supported/configured by your provider.
Use its credential helper or a private user rc file for authentication; do not
commit tokens or place them in command history. For a provider using bearer
headers, its private rc entry has the form
`build:team --remote_header=Authorization=Bearer TOKEN`. Protect that file and
avoid sharing `--announce_rc` output or logs containing authentication headers.
Use TLS verification; do not disable it to fix certificate errors.

```bash
bazel build --config=team //...
bazel test --config=team //...
bazel run --config=team //examples/pyo3:hello
```

`all` downloads outputs for subsequent local use. `toplevel` can reduce transfer
volume for large projects; Bazel still downloads inputs needed for local actions.
The cache does not automatically find builds from arbitrary branches: reuse is
by action input digest, so identical actions across commits can hit.

## Populate from trusted CI

Provide the same endpoint, namespace and authentication via a private rc on the
runner. Explicitly enable uploads only in the trusted job:

```bash
bazel build --config=team --remote_upload_local_results=true //...
bazel test --config=team --remote_upload_local_results=true //...
```

Populate each configuration your developers use. The existing CI strict,
coverage, sanitizer and ARM builds have different keys from ordinary fastbuild.
For example, add a default `bazel test` alongside strict tests if developers
expect default test-result hits. Matching source alone is insufficient: Bazel
version, toolchain, target/execution platform, flags, declared environment, and
inputs must also match. Standardize a Linux development image (pinned by digest)
for best reuse. macOS and Linux, or x86-64 and ARM hosts, need not share keys even
when targeting the same architecture. Keep timestamps, absolute workspace paths,
host discovery, and stamping out of build actions.

## Prove reuse

After CI has populated the cache, run the same target and configuration with a
fresh local output base. Use a temporary directory outside the checkout:

```bash
cache_probe=$(mktemp -d)
bazel --output_base="$cache_probe" build --config=team //examples/pyo3:hello
bazel --output_base="$cache_probe" shutdown
```

Inspect Bazel's action summary for `remote cache hit` and the service's request
metrics. A second build in the same output base proves only local reuse. Use no
local disk cache for this probe, and check authentication/namespace/configuration
if remote hits are absent. Remove the probe directory after shutdown when done.
A clean build may still download large compilers before any action-cache hits.

## Repository downloads and offline use

An action cache does not replace Bzlmod, crates.io, PyPI, LLVM, Node, Python or
sysroot download servers. Preserve a Bazel repository cache in developer images
and CI, or maintain verified artifact mirrors/distdirs. Artifact hashes must
remain checked. `bazel fetch //...` warms the current configuration's dependencies;
other platforms/configurations may need additional fetches. Test an offline
workflow explicitly; pinned dependencies alone do not imply offline readiness.

For a workflow where laptops never install compilers or run cache misses, adopt
a managed Linux development environment or configure a compatible remote
executor and its pinned execution image. This template does not configure remote
execution automatically.
