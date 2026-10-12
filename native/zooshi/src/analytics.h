// Noriwake modification (2026-10-12): Remove analytics SDK and event API; gameplay makes no telemetry calls in the offline build.
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

#ifndef ZOOSHI_ANALYTICS_H_
#define ZOOSHI_ANALYTICS_H_
// Deliberately no collection, transport, identifiers or event API.
// Historical header retained to document removal of upstream telemetry.
namespace noriwake {
constexpr bool kAnalyticsEnabled = false;
}
#endif
