#include <iostream>

#include "absl/strings/str_cat.h"
#include "s2/s2cell_id.h"
#include "s2/s2latlng.h"

int main() {
  const auto position = S2LatLng::FromDegrees(40.0, -105.0);
  const auto cell = S2CellId(position).parent(12);
  if (!cell.is_valid() || cell.level() != 12) {
    std::cerr << "Invalid S2 cell\n";
    return 1;
  }
  std::cout << absl::StrCat("S2 level ", cell.level(), ": ", cell.ToToken())
            << '\n';
  return 0;
}
