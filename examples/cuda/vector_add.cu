#include <cuda_runtime.h>

#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <vector>

static void check(cudaError_t result, const char* operation) {
  if (result != cudaSuccess) {
    std::fprintf(stderr, "%s: %s\n", operation, cudaGetErrorString(result));
    std::exit(EXIT_FAILURE);
  }
}

__global__ void add(const float* a, const float* b, float* output, int count) {
  const int i = blockIdx.x * blockDim.x + threadIdx.x;
  if (i < count) output[i] = a[i] + b[i];
}

int main() {
  int devices = 0;
  check(cudaGetDeviceCount(&devices), "Find NVIDIA GPU (requires a working driver)");
  if (devices == 0) {
    std::fprintf(stderr, "No NVIDIA GPU available.\n");
    return EXIT_FAILURE;
  }
  cudaDeviceProp properties{};
  check(cudaGetDeviceProperties(&properties, 0), "Read GPU properties");
  if (properties.major < 8) {
    std::fprintf(stderr, "Default build requires compute capability 8.0 or newer.\n");
    return EXIT_FAILURE;
  }
  // Non-multiple of the block size exercises the kernel's bounds check.
  constexpr int count = 1003;
  const size_t bytes = count * sizeof(float);
  std::vector<float> a(count), b(count), output(count);
  for (int i = 0; i < count; ++i) {
    a[i] = static_cast<float>(i) * 0.5f;
    b[i] = static_cast<float>(count - i) * 0.25f;
  }
  float *device_a = nullptr, *device_b = nullptr, *device_output = nullptr;
  check(cudaMalloc(&device_a, bytes), "Allocate a");
  check(cudaMalloc(&device_b, bytes), "Allocate b");
  check(cudaMalloc(&device_output, bytes), "Allocate output");
  check(cudaMemcpy(device_a, a.data(), bytes, cudaMemcpyHostToDevice), "Copy a");
  check(cudaMemcpy(device_b, b.data(), bytes, cudaMemcpyHostToDevice), "Copy b");
  add<<<(count + 255) / 256, 256>>>(device_a, device_b, device_output, count);
  check(cudaGetLastError(), "Launch vector-add kernel");
  check(cudaDeviceSynchronize(), "Execute vector-add kernel");
  check(cudaMemcpy(output.data(), device_output, bytes, cudaMemcpyDeviceToHost), "Copy output");
  bool valid = true;
  for (int i = 0; i < count; ++i) {
    if (!std::isfinite(output[i]) || std::fabs(output[i] - (a[i] + b[i])) > 1e-5f) {
      std::fprintf(stderr, "Mismatch at %d: got %g, expected %g\n", i, output[i], a[i] + b[i]);
      valid = false;
      break;
    }
  }
  check(cudaFree(device_a), "Free a");
  check(cudaFree(device_b), "Free b");
  check(cudaFree(device_output), "Free output");
  if (!valid) return EXIT_FAILURE;
  std::printf("Verified %d vector sums on %s\n", count, properties.name);
  return EXIT_SUCCESS;
}
