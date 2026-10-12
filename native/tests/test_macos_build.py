# Copyright 2026 Noriwake contributors. SPDX-License-Identifier: Apache-2.0
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools'))
import check_native_cpp as cpp


class MacDesktopBuildTests(unittest.TestCase):
    def test_real_desktop_source_set(self):
        doc = json.loads((ROOT/'native/macos/sources.json').read_text())
        self.assertEqual(doc['schema'], 1)
        self.assertEqual(set(doc['sources']['game']), set(cpp.source_files()) | {'src/inputcontrollers/mouse_controller.cpp'})
        for group, paths in doc['sources'].items():
            self.assertEqual(len(paths), len(set(paths)), group)
            for path in paths:
                self.assertFalse(Path(path).is_absolute())
                self.assertNotIn('..', Path(path).parts)
                self.assertNotIn('renderer_hmd', path)
                self.assertNotIn('gpg_multiplayer', path)
                self.assertNotIn('synchronous_loader/', path.replace('asynchronous_loader/', ''))
        self.assertNotIn('src/main.cpp', doc['sources']['fplbase'])
        self.assertIn('src/asynchronous_loader/file_loader.cpp', doc['sources']['pindrop'])

    def test_native_entrypoint_not_webview(self):
        main = (ROOT/'native/macos/main.cpp').read_text()
        self.assertIn('SDL_SetMainReady()', main)
        self.assertIn('return FPL_main(argc, argv)', main)
        self.assertNotIn('localhost', main)
        cmake = (ROOT/'native/macos/CMakeLists.txt').read_text()
        self.assertIn('add_executable(noriwake', cmake)
        self.assertIn('FPLBASE_ANDROID_VR=0', cmake)
        self.assertIn('PkgConfig::MACLIBS', cmake)
        self.assertNotIn('npm', cmake)
        self.assertNotIn('file(GLOB', cmake)

    def test_report_does_not_claim_runtime_or_portable_app(self):
        tool = (ROOT/'tools/build_macos_game.py').read_text()
        self.assertIn("'runtime_tested': False", tool)
        self.assertIn("['otool', '-L'", tool)
        self.assertIn("['lipo', '-archs'", tool)
        self.assertIn('refusing overwrite', tool)
        self.assertIn("if args.run:", tool)
        self.assertIn('SDL2/SDL2_mixer 2.x, not SDL3', tool)

    def test_workers_stop_before_stack_context_is_destroyed(self):
        code = (ROOT/'native/zooshi/src/game.cpp').read_text()
        header = (ROOT/'native/zooshi/src/game.h').read_text()
        self.assertIn('std::atomic<bool> game_exiting_', header)
        self.assertIn('SDL_WaitThread(update_thread, nullptr)', code)
        self.assertIn('SDL_WaitThread(vsync_simulator_thread, nullptr)', code)
        self.assertIn('std::atomic<bool> stop_vsync(false)', code)
        self.assertIn('input_.app_event_callbacks().clear()', code)
        self.assertNotIn('input_.AddAppEventCallback(nullptr)', code)
        self.assertIn('if (rt_data->game_exiting->load()) break', code)
