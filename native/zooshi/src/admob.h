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

#ifndef ZOOSHI_ADMOB_H_
#define ZOOSHI_ADMOB_H_
namespace fpl {
namespace zooshi {
enum AdMobStatus {
  kAdMobStatusInitializing, kAdMobStatusLoading, kAdMobStatusAvailable,
  kAdMobStatusShowing, kAdMobStatusError,
  kAdMobStatusDisabled
};
enum RewardedVideoLocation {
  kRewardedVideoLocationPregame = 0,
  kRewardedVideoLocationScoreScreen,
  kRewardedVideoLocationCount
};
// Compatibility boundary for the existing menu, NOT an ad-service simulator.
// A future provider must replace this implementation and receive consent.
class AdMobHelper {
 public:
  void Initialize();
  void LoadNewRewardedVideo();
  void ShowRewardedVideo();
  // True means the attempt is terminal, not that a video was watched.
  bool CheckShowRewardedVideo() const;
  AdMobStatus rewarded_video_status() const;
  bool rewarded_video_available() const;
  bool rewarded_video_watched() const;
  void ResetRewardedVideo();
  RewardedVideoLocation GetRewardedVideoLocation() const;
  float reward_value() const;
};
}  // namespace zooshi
}  // namespace fpl
#endif
