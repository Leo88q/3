// Noriwake modification (2026-10-12): Compile original unavailable GPG behavior without engine/SDK dependency; retain only neutral Activity-result JNI callback.
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


#include "gpg_manager.h"


namespace fpl {

GPGManager::GPGManager() {
}


bool GPGManager::Initialize(bool ui_login) {
  (void)ui_login;
  return false;
}

// Called every frame from the game, to see if there's anything to be done
// with the async progress from gpg
void GPGManager::Update() {
}

bool GPGManager::LoggedIn() {
  return false;
}

void GPGManager::ToggleSignIn() {
  return;
}

void GPGManager::IncrementEvent(const char *event_id, uint64_t score) {
  (void)event_id;
  (void)score;
}

// This is still somewhat game-specific.  (Because it assumes that your
// leaderboards are tied to events.)  TODO: clean this up further later.
void GPGManager::ShowLeaderboards(const GPGIds *ids, size_t id_len) {
  (void)ids;
  (void)id_len;
}

void GPGManager::ShowLeaderboards(const char *id) {
  (void)id;
}

// Submit score to specified leaderboard.
void GPGManager::SubmitScore(std::string leaderboard_id, int64_t score) {
  (void)leaderboard_id;
  (void)score;
}

// Submit score to specified leaderboard.
int64_t GPGManager::CurrentPlayerHighScore(std::string leaderboard_id) {
  (void)leaderboard_id;
  return 0;
}

// Unlocks a given achievement.
void GPGManager::UnlockAchievement(std::string achievement_id) {
  if (LoggedIn()) {
    (void)achievement_id;
  }
}

// Increments an incremental achievement.
void GPGManager::IncrementAchievement(std::string achievement_id) {
  if (LoggedIn()) {
    (void)achievement_id;
  }
}

// Increments an incremental achievement by an amount.
void GPGManager::IncrementAchievement(std::string achievement_id,
                                      uint32_t steps) {
  (void)achievement_id;
  (void)steps;
}

// Reveals a given achievement.
void GPGManager::RevealAchievement(std::string achievement_id) {
  (void)achievement_id;
}

// Updates local player stats with values from the server:
void GPGManager::FetchEvents() {
}

bool GPGManager::IsAchievementUnlocked(std::string achievement_id) {
  (void)achievement_id;
  return false;
}

uint64_t GPGManager::GetEventValue(std::string event_id) {
  (void)event_id;
  return 0;
}

// Updates local player achievements with values from the server:
void GPGManager::FetchAchievements() {
}

void GPGManager::ShowAchievements() {
}

void GPGManager::FetchPlayer() {
}

}  // fpl

// FPLActivity still invokes this callback for generic Activity results.
// Keep the ABI bridge so Android cannot throw UnsatisfiedLinkError. No sign-in
// result is handled or reported as successful here. MWA will use a new bridge.
#ifdef __ANDROID__
#include <jni.h>
extern "C" JNIEXPORT void JNICALL
Java_com_google_fpl_fplbase_FPLActivity_nativeOnActivityResult(
    JNIEnv*, jobject, jobject, jint, jint, jobject) {}
#endif
