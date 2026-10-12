// Copyright 2026 Noriwake contributors. SPDX-License-Identifier: Apache-2.0
// See native/zooshi/LICENSE.
#ifndef NORIWAKE_BUILD_CONFIG_H_
#define NORIWAKE_BUILD_CONFIG_H_
// Offline is a deliberate build profile, not a successful connection simulator.
// Reintroducing online features requires a new, reviewed implementation.
#ifdef USING_GOOGLE_PLAY_GAMES
#error "Legacy Google Play Games is not supported in Noriwake's offline build."
#endif
#if defined(FPLBASE_ANDROID_VR) && FPLBASE_ANDROID_VR
#error "Noriwake touch build requires FPLBASE_ANDROID_VR=0 consistently in game and engine."
#endif
namespace noriwake {
constexpr bool kOnlineServicesEnabled = false;
}
#endif
