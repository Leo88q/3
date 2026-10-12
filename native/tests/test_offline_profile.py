# Copyright 2026 Noriwake contributors. SPDX-License-Identifier: Apache-2.0
"""Static boundary checks supplement compiled provider tests, not APK verification."""
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
GAME = ROOT/'native/zooshi'
ANDROID = '{http://schemas.android.com/apk/res/android}'

class OfflineProfileTests(unittest.TestCase):
    def test_no_cloud_headers_or_calls_in_game_sources(self):
        for path in (GAME/'src').rglob('*'):
            if path.suffix not in ('.cpp', '.h'): continue
            with self.subTest(file=str(path.relative_to(GAME))):
                text = path.read_text()
                self.assertNotRegex(text, r'#\s*include\s+[<"]firebase/')
                self.assertNotIn('firebase::', text)
                self.assertNotRegex(text, r'#\s*define\s+USING_GOOGLE_PLAY_GAMES\b')

    def test_no_cloud_or_play_sdk_in_android_build(self):
        gradle=(GAME/'build.gradle').read_text()
        for dependency in ['com.google.android.gms:', 'com.google.firebase:',
                           'com.google.firebase.messaging.cpp:', 'com.google.gms:google-services',
                           "apply plugin: 'com.google.gms.google-services'", 'FIREBASE_SDK']:
            self.assertNotIn(dependency, gradle)
        self.assertNotIn('jcenter()',gradle)
        self.assertNotIn('23.0+',gradle)
        ndk=(GAME/'jni/libs/src/Android.mk').read_text()
        for token in ['libfirebase_', '  libgpg', 'DEPENDENCIES_GPG_DIR',
                      'DEPENDENCIES_FIREBASE_DIR', 'GPG_JNI_OnLoad']:
            self.assertNotIn(token, ndk)
        self.assertNotIn('all-makefiles-under', (GAME/'jni/Android.mk').read_text())
        self.assertNotIn('PREBUILT_STATIC_LIBRARY', (GAME/'jni/libs/gpg/Android.mk').read_text())

    def test_no_cloud_requirement_in_desktop_link_graph(self):
        cmake=(GAME/'CMakeLists.txt').read_text()
        for token in ['firebase_sdk_dir','FIREBASE_SDK','firebase_app','firebase_analytics',
                      'firebase_admob','firebase_invites','firebase_messaging','firebase_config']:
            self.assertNotIn(token, cmake)
        self.assertNotIn('gpg_multiplayer.cpp', cmake)

    def test_source_manifest_is_offline_and_independently_identified(self):
        manifest=ET.parse(GAME/'AndroidManifest.xml').getroot()
        self.assertNotIn('package', manifest.attrib)
        self.assertEqual(manifest.findall('uses-permission'), [])
        app=manifest.find('application')
        self.assertEqual(app.attrib[ANDROID+'allowBackup'],'false')
        self.assertEqual(app.findall('service'), [])
        self.assertEqual(app.findall('receiver'), [])
        self.assertEqual(app.findall('meta-data'), [])
        self.assertEqual(manifest.findall('.//data'), [])
        activities=app.findall('activity')
        self.assertEqual(len(activities),1)
        self.assertEqual(activities[0].attrib[ANDROID+'name'], 'com.google.fpl.zooshi.ZooshiActivity')
        gradle=(GAME/'build.gradle').read_text()
        self.assertIn("applicationId 'com.noriwake.game.nativepreview'", gradle)
        self.assertIn("namespace 'com.noriwake.game.nativepreview'", gradle)
        self.assertIn('versionCode 2', gradle)
        self.assertIn('compileSdk 35', gradle)
        self.assertIn('minSdk 23', gradle)
        self.assertEqual(manifest.findall('uses-sdk'), [])
        # Important: this checks our source manifest, NOT the unbuilt merged APK.

    def test_no_online_invite_entrypoint_and_video_guard(self):
        gui=(GAME/'src/gui.cpp').read_text()
        self.assertNotRegex(gui,r'\bSendInvite\s*\(')
        self.assertNotIn('kConfigMenuSendInvite',gui)
        self.assertIn('kAdMobStatusDisabled',gui)
        menu=(GAME/'src/states/game_menu_state.cpp').read_text()
        start=menu.split('void GameMenuState::StartRewardedVideo() {')[1].split('\n}')[0]
        self.assertIn('if (!world_->admob_helper->rewarded_video_available())',start)
        self.assertIn('return;',start)

    def test_touch_activity_disables_sensor_initialization(self):
        java=(GAME/'src_java/com/google/fpl/zooshi/ZooshiActivity.java').read_text()
        for method in ['SupportsHeadMountedDisplay']:
            self.assertRegex(java, method+r'\(\)\s*\{\s*return false;')
        bridge=(GAME/'src/gpg_manager.cpp').read_text()
        self.assertIn('Java_com_google_fpl_fplbase_FPLActivity_nativeOnActivityResult',bridge)
        self.assertNotIn('GPG_JNI_OnLoad',bridge)

if __name__=='__main__': unittest.main()
