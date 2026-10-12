// Copyright 2026 Noriwake contributors. SPDX-License-Identifier: Apache-2.0
#include <iostream>
#include <vector>
#include "flatbuffers/reflection_generated.h"

int main() {
  flatbuffers::FlatBufferBuilder builder;
  const auto fields = builder.CreateVector(std::vector<flatbuffers::Offset<reflection::Field>>{});
  const auto z = reflection::CreateObject(builder, builder.CreateString("zebra"), fields);
  const auto a = reflection::CreateObject(builder, builder.CreateString("antelope"), fields);
  std::vector<flatbuffers::Offset<reflection::Object>> objects{z, a};
  const auto sorted = builder.CreateVectorOfSortedTables(&objects);
  builder.Finish(sorted);
  typedef flatbuffers::Vector<flatbuffers::Offset<reflection::Object>> Objects;
  const auto* result = flatbuffers::GetRoot<Objects>(builder.GetBufferPointer());
  if (result->size() != 2 || result->Get(0)->name()->str() != "antelope" ||
      result->Get(1)->name()->str() != "zebra") return 1;
  std::cout << "Pinned FlatBuffers sorted-table comparator copies and sorts correctly.\n";
  return 0;
}
