#include <iostream>
#include "examples/cpp/greeting.h"

int main() {
  std::cout << hello::greet("world") << '\n';
  return 0;
}
