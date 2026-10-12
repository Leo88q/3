# Copyright 2026 Noriwake contributors. SPDX-License-Identifier: Apache-2.0
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools'))
import check_native_cpp as cpp
import native


class CppPreflightTests(unittest.TestCase):
    def test_checks_real_ndk_source_set_without_cloud_or_hmd(self):
        sources = cpp.source_files()
        self.assertEqual(len(sources), 53)
        self.assertIn('src/game.cpp', sources)
        self.assertIn('src/world.cpp', sources)
        self.assertIn('src/states/gameplay_state.cpp', sources)
        self.assertNotIn('src/gpg_multiplayer.cpp', sources)
        self.assertNotIn('src/inputcontrollers/android_cardboard_controller.cpp', sources)
        for source in sources:
            self.assertTrue((native.GAME/source).is_file())

    def test_ndk_uses_prepared_tools_and_verify_only_resources(self):
        make = (native.GAME/'jni/libs/src/Android.mk').read_text()
        self.assertIn('FLATBUFFERS_FLATC_PATH := $(NORIWAKE_ROOT)/.cache/native-asset-tools/flatbuffers', make)
        self.assertIn('prepared flatc missing', make)
        self.assertIn('tools/build_native_assets.py --check', make)
        self.assertNotIn('scripts/build_assets.py', make)
        self.assertNotIn('--copy_tree', make)
        self.assertNotIn('clean_assets', make)
        self.assertNotIn('$(ZOOSHI_DIR)/assets/', make)

    def test_reflection_schema_is_generated_in_staged_output(self):
        script = (ROOT/'tools/build_native_assets.py').read_text()
        self.assertIn("'-b', '--schema'", script)
        self.assertIn("stage/'flatbufferschemas/components.bfbs'", script)
        self.assertIn("reflection.read_bytes()[4:8] != b'BFBS'", script)
        test = (ROOT/'native/tests/schema_resource_test.cpp').read_text()
        self.assertIn('VerifySchemaBuffer(verifier)', test)
        self.assertIn('VerifySchemaBuffer(damaged)', test)
        self.assertIn('VerifySchemaBuffer(truncated)', test)

    def test_modified_or_missing_gl_header_rejected_without_network(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(cpp, 'CACHE', Path(tmp)):
            with self.assertRaisesRegex(ValueError, 'Missing pinned'):
                cpp.gl_header(False)
            path = Path(tmp)/'include/GL/gl.h'; path.parent.mkdir(parents=True)
            path.write_bytes(b'not the reviewed Mesa header')
            with self.assertRaisesRegex(ValueError, 'Modified host GL'):
                cpp.gl_header(False)

    def test_explicit_limits_in_approved_dependency_headers(self):
        manifest = json.loads((ROOT/'native/dependency-overrides.json').read_text())
        for dep, path in [('motive', 'include/motive/common.h'),
                          ('flatui', 'include/flatui/internal/distance_computer.h')]:
            item = next(i for i in manifest['files'] if i['dependency'] == dep and i['path'] == path)
            self.assertEqual(len(item['upstream_blob_sha1']), 40)
            self.assertIn('#include <limits>', (ROOT/'native/overrides'/dep/path).read_text())
            self.assertTrue((ROOT/'native/overrides'/dep/'LICENSE').is_file())
