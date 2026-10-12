// Copyright 2026 Noriwake contributors. SPDX-License-Identifier: Apache-2.0
// These tests link the actual providers used by the game, not SDK mocks.
#include "admob.h"
#include "analytics.h"
#include "gpg_manager.h"
#include "invites.h"
#include "messaging.h"
#include "remote_config.h"
#include "noriwake/build_config.h"
#include <cassert>
#include <iostream>
#include <string>

int main() {
  using namespace fpl::zooshi;
  static_assert(!noriwake::kOnlineServicesEnabled, "Offline must not enable services");
  static_assert(!noriwake::kAnalyticsEnabled, "No telemetry in offline profile");
  AdMobHelper ads;
  // Even before Initialize, state is deterministic and cannot look successful.
  assert(ads.rewarded_video_status() == kAdMobStatusDisabled);
  assert(!ads.rewarded_video_available());
  ads.Initialize();
  for (int i = 0; i < 3; ++i) {
    ads.LoadNewRewardedVideo(); ads.ShowRewardedVideo();
    assert(ads.CheckShowRewardedVideo()); // terminal, NOT success
    assert(!ads.rewarded_video_watched());
    assert(ads.reward_value() == 0.0f);
    assert(ads.GetRewardedVideoLocation() == kRewardedVideoLocationCount);
    ads.ResetRewardedVideo();
    assert(!ads.rewarded_video_available());
  }
  bool sent = true, first = true;
  SendInvite();
  assert(UpdateSentInviteStatus(&sent, &first));
  assert(!sent && !first);
  assert(UpdateSentInviteStatus(nullptr, nullptr));
  InvitesListener invitations;
  invitations.HandlePendingInvite(); invitations.Reset();
  assert(!invitations.has_pending_invite() && !invitations.received_invite());
  assert(invitations.invitation_id().empty() && invitations.deep_link().empty());
  MessageListener messages;
  StartReceivingMessages(nullptr);
  assert(!messages.has_pending_message());
  assert(messages.HandlePendingMessage(nullptr).empty());
  StopReceivingMessages();
  assert(std::string(PlayGameLabel()) == "Start delivery");

  fpl::GPGManager games;
  assert(!games.Initialize(false)); assert(!games.Initialize(true));
  games.Update(); games.ToggleSignIn();
  games.SubmitScore("any", 10000);
  games.IncrementEvent("any", 100);
  games.UnlockAchievement("any");
  games.IncrementAchievement("any"); games.IncrementAchievement("any", 10);
  games.RevealAchievement("any");
  games.FetchEvents(); games.FetchAchievements(); games.FetchPlayer();
  games.ShowAchievements(); games.ShowLeaderboards("any");
  games.ShowLeaderboards(nullptr, 0);
  assert(!games.LoggedIn());
  assert(!games.IsAchievementUnlocked("any"));
  assert(games.CurrentPlayerHighScore("any") == 0);
  assert(games.GetEventValue("any") == 0);
  std::cout << "Actual offline service providers: terminal failure, no rewards, no login.\n";
}
