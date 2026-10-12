// Noriwake modification (2026-10-12): Remove remote push/bonus injection and SDK callbacks; no tokens, subscriptions or rewards in offline mode.
// Copyright 2017 Google Inc. All rights reserved.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#ifndef ZOOSHI_MESSAGING_H_
#define ZOOSHI_MESSAGING_H_
#include <string>
namespace fpl {
namespace zooshi {
struct World;
class MessageListener {
 public:
  std::string HandlePendingMessage(World* world);
  bool has_pending_message() const { return false; }
};
void StartReceivingMessages(World* world);
void StopReceivingMessages();
}  // namespace zooshi
}  // namespace fpl
#endif
