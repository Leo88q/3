# Copyright 2026 Noriwake contributors. SPDX-License-Identifier: Apache-2.0
# Standalone tests of actual downstream code; this is NOT the game/APK target.
cmake_minimum_required(VERSION 3.16)
project(noriwake_policy_tests LANGUAGES CXX)
include(CTest)
set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
option(NORIWAKE_TEST_UBSAN "Check undefined behavior in host tests" ON)
set(GAME_SRC "${CMAKE_CURRENT_LIST_DIR}/../zooshi/src")
add_executable(session_test session_test.cpp)
add_executable(offline_services_test offline_services_test.cpp
  "${GAME_SRC}/admob.cpp"
  "${GAME_SRC}/analytics.cpp"
  "${GAME_SRC}/gpg_manager.cpp"
  "${GAME_SRC}/invites.cpp"
  "${GAME_SRC}/messaging.cpp"
  "${GAME_SRC}/remote_config.cpp")
foreach(target session_test offline_services_test)
  target_include_directories(${target} PRIVATE "${GAME_SRC}")
  if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    target_compile_options(${target} PRIVATE -Wall -Wextra -Werror -pedantic -UNDEBUG)
    if(NORIWAKE_TEST_UBSAN)
      target_compile_options(${target} PRIVATE -fsanitize=undefined -fno-sanitize-recover=undefined)
      target_link_options(${target} PRIVATE -fsanitize=undefined -fno-sanitize-recover=undefined)
    endif()
  elseif(MSVC)
    target_compile_options(${target} PRIVATE /UNDEBUG)
  endif()
  add_test(NAME ${target} COMMAND ${target})
endforeach()
