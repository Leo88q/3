# Noriwake modification (2026-10-12): Replace removed GNU STL/32-bit ABIs with libc++ and 64-bit API 23+ migration targets.
# Copyright 2014 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Migration target; full native dependency graph still requires validation.
APP_STL := c++_shared
APP_ABI := arm64-v8a x86_64
APP_CPPFLAGS += -std=c++11 -Wno-unused-function -DFPLBASE_ANDROID_VR=0
APP_PLATFORM := android-23
APP_SUPPORT_FLEXIBLE_PAGE_SIZES := true
APP_MODULES := main
