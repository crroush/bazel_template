#include <iostream>
#include "examples/cpp/greeting.h"

int main() {
  if (hello::greet("world") != "Hello, world from C++!" ||
      hello::greet("ARM") != "Hello, ARM from C++!") {
    std::cerr << "Unexpected greeting\n";
    return 1;
  }
  return 0;
}
