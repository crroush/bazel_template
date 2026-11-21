#include <pybind11/pybind11.h>
#include "examples/cpp/greeting.h"

PYBIND11_MODULE(_greeting, module) {
  module.doc() = "C++ greetings exposed to Python";
  module.def("greet", &hello::greet, pybind11::arg("name") = "world");
}
