// Noriwake modification (2026-10-12): Remove discontinued cloud invitations; offline calls finish unsuccessfully and cannot award referrals.
// Copyright 2016 Google Inc. All rights reserved.
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

#ifndef ZOOSHI_INVITES_H_
#define ZOOSHI_INVITES_H_
#include <string>
namespace fpl {
namespace zooshi {
void SendInvite();
// Terminal failure in offline builds; both outputs are always initialized.
bool UpdateSentInviteStatus(bool* did_send, bool* first_sent);
class InvitesListener {
 public:
  void HandlePendingInvite() {}
  void Reset() {}
  bool has_pending_invite() const { return false; }
  bool received_invite() const { return false; }
  const std::string& invitation_id() const { return empty_; }
  const std::string& deep_link() const { return empty_; }
 private:
  const std::string empty_;
};
}  // namespace zooshi
}  // namespace fpl
#endif
