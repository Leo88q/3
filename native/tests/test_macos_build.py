# Copyright 2026 Noriwake contributors. SPDX-License-Identifier: Apache-2.0
import json
import re
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools'))
import check_native_cpp as cpp
import build_macos_game as mac


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

    def test_smoke_rejects_broken_behavior_graphs_even_on_exit_zero(self):
        good = 'SMOKE: initialized real game and OpenGL context\nSMOKE PASSED: done'
        self.assertTrue(mac.smoke_succeeded(good, 0))
        self.assertFalse(mac.smoke_succeeded(good + '\nError in graph "hippo": 3 edges, expected 4', 0))
        self.assertFalse(mac.smoke_succeeded(good, -11))
        self.assertFalse(mac.smoke_succeeded('SMOKE PASSED:', 0))

    def test_body_hit_audio_keeps_four_typed_inputs(self):
        for animal in ['bird', 'croc', 'giraffe', 'hippo', 'mandrill']:
            text = (ROOT/f'native/zooshi/src/rawassets/graphs/{animal}.json').read_text()
            graph = json.loads(re.sub(r'//[^\n]*', '', text))
            node = graph['node_list'][5]
            self.assertEqual((node['module'], node['name']), ('audio', 'play_sound'))
            edges = node['input_edge_list']
            self.assertEqual(len(edges), 4)
            self.assertEqual(edges[1]['edge_type'], 'breadboard_module_library_SoundHandle')
            self.assertEqual(edges[1]['edge']['value'], 'hit_char')
            self.assertEqual(edges[2]['edge'], {'node_index': 2, 'edge_index': 1})
            self.assertEqual(edges[3]['edge']['value'], 1.0)
