// Noriwake modification (2026-10-12): Replace legacy ads SDK with an explicitly unavailable offline provider; never grant video rewards.
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

#include "admob.h"
namespace fpl {
namespace zooshi {
void AdMobHelper::Initialize() {}
void AdMobHelper::LoadNewRewardedVideo() {}
void AdMobHelper::ShowRewardedVideo() {}
bool AdMobHelper::CheckShowRewardedVideo() const { return true; }
AdMobStatus AdMobHelper::rewarded_video_status() const { return kAdMobStatusDisabled; }
bool AdMobHelper::rewarded_video_available() const { return false; }
bool AdMobHelper::rewarded_video_watched() const { return false; }
void AdMobHelper::ResetRewardedVideo() {}
RewardedVideoLocation AdMobHelper::GetRewardedVideoLocation() const {
  return kRewardedVideoLocationCount;  // Neither pregame nor score screen.
}
float AdMobHelper::reward_value() const { return 0.0f; }
}  // namespace zooshi
}  // namespace fpl
