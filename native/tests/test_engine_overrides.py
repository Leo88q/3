# Copyright 2026 Noriwake contributors. SPDX-License-Identifier: Apache-2.0
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('engine_overrides',ROOT/'tools/engine_overrides.py')
engine=importlib.util.module_from_spec(spec);spec.loader.exec_module(engine)

class EngineOverridesTests(unittest.TestCase):
    def fixture(self,root):
        original=b'original engine'; replacement=b'// reviewed change'
        pin='a'*40
        (root/'zooshi/dependencies/fplbase').mkdir(parents=True)
        (root/'overrides/fplbase').mkdir(parents=True)
        (root/'overrides/fplbase/Activity.java').write_bytes(replacement)
        (root/'zooshi/dependencies/fplbase/Activity.java').write_bytes(original)
        item={'dependency':'fplbase','path':'Activity.java','commit':pin,
              'upstream_blob_sha1':engine.git_blob(original),'sha256':engine.digest(replacement)}
        (root/'dependency-overrides.json').write_text(json.dumps({'schema':1,'files':[item]}))
        (root/'upstream.lock.json').write_text(json.dumps({'dependencies':[{'path':'dependencies/fplbase','commit':pin}]}))
        (root/'zooshi/dependencies/fplbase/.noriwake-source.json').write_text(json.dumps({'commit':pin,'files':[{'path':'Activity.java','sha':engine.git_blob(original)}]}))
        return root/'zooshi/dependencies/fplbase/Activity.java'

    def test_apply_repeat_and_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); target=self.fixture(root)
            with self.assertRaisesRegex(ValueError,'not applied'): engine.apply(root,check=True)
            engine.apply(root);self.assertEqual(target.read_bytes(),b'// reviewed change')
            engine.apply(root);engine.apply(root,check=True)

    def test_selective_apply_and_unknown_selection(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);target=self.fixture(root)
            engine.apply(root, only='fplbase')
            engine.apply(root, check=True, only='fplbase')
            self.assertEqual(target.read_bytes(), b'// reviewed change')
            with self.assertRaisesRegex(ValueError, 'Unknown override dependency'):
                engine.apply(root, only='unknown')

    def test_dirty_target_and_source_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);target=self.fixture(root);target.write_bytes(b'my edit')
            with self.assertRaisesRegex(ValueError,'Refusing'): engine.apply(root)
            self.assertEqual(target.read_bytes(),b'my edit')
            (root/'overrides/fplbase/Activity.java').write_bytes(b'unreviewed')
            with self.assertRaisesRegex(ValueError,'Unreviewed|unreviewed'): engine.apply(root)

    def test_wrong_revision_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);self.fixture(root)
            stamp=root/'zooshi/dependencies/fplbase/.noriwake-source.json'
            doc=json.loads(stamp.read_text());doc['commit']='b'*40;stamp.write_text(json.dumps(doc))
            with self.assertRaisesRegex(ValueError,'commit mismatch'): engine.apply(root)

    def test_escape_and_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'link').symlink_to('/tmp')
            for path in ['../outside','/etc/passwd','link/file','link','a\\b']:
                with self.subTest(path=path), self.assertRaises(ValueError): engine.confined(root,path)

    def test_tracked_override_sources_have_pinned_provenance(self):
        self.assertEqual({item['dependency'] for item,_ in engine.entries(ROOT/'native')},
                         {'fplbase','flatbuffers','scene_lab','flatui','motive'})

    def test_no_vr_sdk_or_removed_ndk_helpers_in_active_overrides(self):
        root=ROOT/'native/overrides/fplbase'
        java=(root/'src_java/com/google/fpl/fplbase/FPLActivity.java').read_text()
        self.assertNotIn('com.google.vr',java)
        self.assertNotIn('import android.nfc',java)
        self.assertNotIn('NfcSensor',java)
        self.assertIn('PendingIntent.FLAG_IMMUTABLE',java)
        self.assertIn('Choreographer.FrameCallback',java)
        self.assertIn('nativeOnGamepadInput',java)
        mk=(root/'jni/Android.mk').read_text()
        self.assertNotIn('-DFPLBASE_ANDROID_VR=1',mk)
        self.assertNotIn('renderer_hmd_gl.cpp',mk)
        self.assertNotIn('ndk_helper',mk)
        self.assertNotIn('android/cpufeatures',mk)
        self.assertIn('-lGLESv3',mk)
        self.assertNotIn('SDL_spinlock.c.arm',(root/'jni/sdl/Android.mk').read_text())

    def test_modern_configuration_has_no_copy_or_binary_wildcard(self):
        game=ROOT/'native/zooshi';gradle=(game/'build.gradle').read_text()
        for text in ['copyCardboard','copyFplbase','fileTree','jcenter','abiFilters \'armeabi-v7a\'']:
            self.assertNotIn(text,gradle)
        for text in ['8.7.3','28.2.13676358',"'arm64-v8a', 'x86_64'",'checkEngineOverrides']:
            self.assertIn(text,gradle)
        app=(game/'jni/Application.mk').read_text()
        self.assertNotIn('gnustl',app);self.assertIn('c++_shared',app)
        self.assertIn('android-23',app)
        self.assertIn('8.11.1-bin.zip',(game/'gradle/wrapper/gradle-wrapper.properties').read_text())

if __name__=='__main__':unittest.main()
