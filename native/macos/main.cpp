// Copyright 2026 Noriwake contributors. SPDX-License-Identifier: Apache-2.0
// Desktop entrypoint: real SDL/FPL game, not a web view.
#define SDL_MAIN_HANDLED
#include <SDL.h>
extern "C" int FPL_main(int argc, char** argv);
int main(int argc, char** argv) {
  SDL_SetMainReady();
  return FPL_main(argc, argv);
}
