// Copyright 2026 Noriwake contributors.
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy at http://www.apache.org/licenses/LICENSE-2.0
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#ifndef NORIWAKE_SESSION_H_
#define NORIWAKE_SESSION_H_

#include <algorithm>
#include <limits>

namespace noriwake {

// Only advance from GameplayState. Pause/menu/loading time never counts.
// Header-only and engine-independent so the policy can be compiled/tested
// without reviving the legacy Android toolchain first.
class Session {
 public:
  enum Mode { kShortRun = 0, kClassic = 1 };
  enum State { kIdle, kRunning, kFinished };

  Session() : state_(kIdle), mode_(kShortRun), elapsed_ms_(0), settled_(false) {}

  void Start(Mode mode) {
    mode_ = mode;
    state_ = kRunning;
    elapsed_ms_ = 0;
    settled_ = false;
  }

  // Return true only on the frame that reaches the short-run deadline.
  bool Advance(int delta_ms) {
    if (state_ != kRunning || delta_ms <= 0) return false;
    const int limit = mode_ == kShortRun ? 90000 : std::numeric_limits<int>::max();
    elapsed_ms_ += std::min(delta_ms, limit - elapsed_ms_);
    if (mode_ == kShortRun && elapsed_ms_ == limit) {
      state_ = kFinished;
      return true;
    }
    return false;
  }

  void Finish() { if (state_ == kRunning) state_ = kFinished; }

  // GameOverState may be re-entered. Local progression is awarded once.
  // This is NOT a server-verified NFT entitlement.
  bool Settle() {
    if (state_ != kFinished || settled_) return false;
    settled_ = true;
    return true;
  }

  int remaining_seconds() const {
    return mode_ == kShortRun ? (90000 - elapsed_ms_ + 999) / 1000 : -1;
  }
  int elapsed_ms() const { return elapsed_ms_; }
  State state() const { return state_; }
  Mode mode() const { return mode_; }

 private:
  State state_;
  Mode mode_;
  int elapsed_ms_;
  bool settled_;
};

struct LocalProgress {
  int best_deliveries;
  int completed_runs;
  int total_deliveries;

  LocalProgress(int best = 0, int runs = 0, int total = 0)
      : best_deliveries(std::max(0, best)), completed_runs(std::max(0, runs)),
        total_deliveries(std::max(std::max(0, total), best_deliveries)) {}

  bool Record(Session* session, int deliveries) {
    if (!session || deliveries < 0 || !session->Settle()) return false;
    best_deliveries = std::max(best_deliveries, deliveries);
    completed_runs = SaturatingAdd(completed_runs, 1);
    total_deliveries = SaturatingAdd(total_deliveries, deliveries);
    return true;
  }

  // Story checkpoints only; these do NOT imply playable new 3D districts yet.
  int story_chapter() const {
    return total_deliveries >= 100 ? 2 : total_deliveries >= 25 ? 1 : 0;
  }

 private:
  static int SaturatingAdd(int a, int b) {
    return a + std::min(b, std::numeric_limits<int>::max() - a);
  }
};

}  // namespace noriwake
#endif  // NORIWAKE_SESSION_H_
