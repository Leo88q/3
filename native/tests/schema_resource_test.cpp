// Copyright 2026 Noriwake contributors. SPDX-License-Identifier: Apache-2.0
#include <fstream>
#include <iostream>
#include <iterator>
#include <string>
#include <vector>
#include "flatbuffers/reflection_generated.h"

int main(int argc, char** argv) {
  if (argc != 2) return 2;
  std::ifstream input(argv[1], std::ios::binary);
  if (!input) return 3;
  std::vector<char> data((std::istreambuf_iterator<char>(input)),
                         std::istreambuf_iterator<char>());
  if (data.size() < 8) return 4;
  const auto* bytes = reinterpret_cast<const uint8_t*>(data.data());
  flatbuffers::Verifier verifier(bytes, data.size());
  if (!reflection::VerifySchemaBuffer(verifier)) return 5;
  const auto* schema = reflection::GetSchema(bytes);
  if (!schema->root_table() || !schema->root_table()->name() ||
      schema->root_table()->name()->str() != "fpl.EntityListDef") return 6;
  if (!schema->file_ident() || schema->file_ident()->str() != "ENTI") return 7;
  // Reject a damaged header and truncation rather than treating any file as success.
  auto corrupt = data;
  corrupt[4] ^= 0x7f;
  flatbuffers::Verifier damaged(reinterpret_cast<const uint8_t*>(corrupt.data()), corrupt.size());
  flatbuffers::Verifier truncated(bytes, 7);
  if (reflection::VerifySchemaBuffer(damaged) || reflection::VerifySchemaBuffer(truncated)) return 8;
  std::cout << "Entity reflection schema verified; corruption/truncation rejected.\n";
  return 0;
}
