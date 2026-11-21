#include "examples/cpp/greeting.h"

namespace hello {
std::string greet(const std::string& name) {
  return "Hello, " + name + " from C++!";
}
}  // namespace hello
