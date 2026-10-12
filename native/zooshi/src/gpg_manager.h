// Noriwake modification (2026-10-12): Keep only the original unavailable GPG API; prohibit accidental re-enabling of legacy online SDK.
// Copyright 2015 Google Inc. All rights reserved.
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

#ifndef GPG_MANAGER_H
#define GPG_MANAGER_H

#include <string>
#include <cstdint>
#include <cstddef>
#include "noriwake/build_config.h"


namespace fpl {

enum RequestState {
  kPending,
  kComplete,
  kFailed
};

struct GPGKeyValuePair {
  std::string id;
  uint64_t value;
};

class GPGManager {
 public:
  GPGManager();

  // Start of initial initialization and auth.
  bool Initialize(bool ui_login);

  // Call once a frame to allow us to track our async work.
  void Update();

  // To be called from UI to sign out (if we were signed in) or sign back in
  // (if we were signed out).
  void ToggleSignIn();

  // Logged in status, can be shown in UI.
  bool LoggedIn();

  struct GPGIds {
    const char *leaderboard, *event;
  };

  // Request this stat to be saved for the logged in
  // player. Does nothing if not logged in.
  void IncrementEvent(const char *event_id, uint64_t score);

  void ShowLeaderboards(const GPGIds *ids, size_t id_len);
  void ShowLeaderboards(const char *id);
  void ShowAchievements();

  // Submit score to specified leaderboard.
  void SubmitScore(std::string leaderboard_id, int64_t score);

  // Retrieve current player's high score.
  // Returns 0 if no player has been signed in.
  int64_t CurrentPlayerHighScore(std::string leaderboard_id);

  // Asynchronously fetches the stats associated with the current player
  // from the server.  (Does nothing if not logged in.)
  // The status of the data can be checked via event_data_state.
  // const char* fields[]
  void FetchEvents();
  void FetchAchievements();

  // Asynchronously fetches the current player's info from the server.
  // (Does nothing if not logged in.)
  void FetchPlayer();

  uint64_t GetEventValue(std::string event_id);
  bool IsAchievementUnlocked(std::string achievement_id);
  void UnlockAchievement(std::string achievement_id);
  void IncrementAchievement(std::string achievement_id);
  void IncrementAchievement(std::string achievement_id, uint32_t steps);
  void RevealAchievement(std::string achievement_id);

 private:
};

}  // fpl

#endif  // GPG_MANAGER_H
