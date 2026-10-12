// Copyright 2026 Noriwake contributors. SPDX-License-Identifier: Apache-2.0
// Desktop entrypoint: real SDL/FPL game, not a web view.
#define SDL_MAIN_HANDLED
#include <SDL.h>
#include <atomic>
#include <cstring>
#include <iostream>
#include "game.h"
extern "C" int FPL_main(int argc, char** argv);

namespace {
std::atomic<int> quit_posted(0);
Uint32 QuitSmokeTest(Uint32, void*) {
  SDL_Event event{};
  event.type = SDL_QUIT;
  quit_posted.store(SDL_PushEvent(&event));
  return 0;  // one-shot timer
}

int SmokeTest(const char* executable) {
  fpl::zooshi::Game::SetOverlayName("");
  fpl::zooshi::Game game;
  if (!game.Initialize(executable)) {
    std::cerr << "SMOKE FAILED: real Game::Initialize returned false\n";
    return 2;
  }
  if (!SDL_GL_GetCurrentContext() || !SDL_GL_GetCurrentWindow()) {
    std::cerr << "SMOKE FAILED: no real SDL window/OpenGL context\n";
    return 3;
  }
  if (SDL_InitSubSystem(SDL_INIT_TIMER) != 0) return 4;
  const SDL_TimerID timer = SDL_AddTimer(5000, QuitSmokeTest, nullptr);
  if (!timer) return 5;
  std::cout << "SMOKE: initialized real game and OpenGL context; entering update/render loop\n" << std::flush;
  game.Run();
  SDL_RemoveTimer(timer);
  if (quit_posted.load() != 1) return 6;
  std::cout << "SMOKE PASSED: game loop exited after scheduled SDL_QUIT; not full gameplay QA\n" << std::flush;
  return 0;
}
}  // namespace

int main(int argc, char** argv) {
  SDL_SetMainReady();
  if (argc == 2 && std::strcmp(argv[1], "--smoke-test") == 0) return SmokeTest(argv[0]);
  return FPL_main(argc, argv);
}
