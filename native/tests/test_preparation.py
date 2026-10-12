# Copyright 2026 Noriwake contributors. SPDX-License-Identifier: Apache-2.0
"""Offline tests for pinned-source preparation and license/provenance invariants."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('native_tools', ROOT/'tools/native.py')
native = importlib.util.module_from_spec(spec)
spec.loader.exec_module(native)


class PreparationTests(unittest.TestCase):
    def test_git_blob_identity(self):
        self.assertEqual(native.blob_hash(b''), 'e69de29bb2d1d6434b8b29ae775ad8c2e48c5391')

    def test_traversal_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            for name in ['/etc/passwd','../outside','a/../../outside','a\\..\\outside']:
                with self.subTest(name=name), self.assertRaises(ValueError):
                    native.safe_path(Path(tmp), name)

    def test_escaping_parent_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)/'root'; root.mkdir()
            (root/'link').symlink_to(Path(tmp), target_is_directory=True)
            with self.assertRaises(ValueError): native.safe_path(root,'link/outside')

    def test_all_upstream_source_changes_are_recorded(self):
        lock=json.loads((ROOT/'native/upstream.lock.json').read_text())
        native.verify(lock)
        mods=json.loads((ROOT/'native/modifications.json').read_text())
        for name in mods:
            if name.endswith(('.cpp','.h','.json','.xml')):
                self.assertIn('Noriwake modification', (ROOT/'native/zooshi'/name).read_text())

    def test_license_and_upstream_cloud_config_policy(self):
        lock=json.loads((ROOT/'native/upstream.lock.json').read_text())
        files={f['path']:f for f in lock['files']}
        game=ROOT/'native/zooshi'
        self.assertEqual(native.blob_hash((game/'LICENSE').read_bytes()),files['LICENSE']['git_blob_sha1'])
        self.assertEqual(files['google-services.json']['storage'],'excluded-config')
        self.assertFalse((game/'google-services.json').exists())
        self.assertIn('This application may use or contain portions', (game/'assets/licenses.txt').read_text())
        self.assertIn('Apache License', (game/'assets/licenses.txt').read_text())

    def test_missing_offline_archive_fails_without_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            lock={'files':[{'path':'asset.png','storage':'external','git_blob_sha1':'unused'}]}
            with patch.object(native,'GAME',root/'game'), patch.object(native,'CACHE',root/'cache'), patch.object(native,'download') as download:
                with self.assertRaisesRegex(ValueError,'No cached archive'): native.hydrate(lock,True)
                download.assert_not_called()

    def test_asset_edits_are_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); (root/'asset.png').write_bytes(b'modified artwork')
            lock={'files':[{'path':'asset.png','storage':'external','git_blob_sha1':native.blob_hash(b'original')}]}
            with patch.object(native,'GAME',root), self.assertRaisesRegex(ValueError,'refusing overwrite'):
                native.hydrate(lock)
            self.assertEqual((root/'asset.png').read_bytes(),b'modified artwork')

    def test_no_moving_dependency_revisions(self):
        lock=json.loads((ROOT/'native/upstream.lock.json').read_text())
        self.assertEqual(len(lock['dependencies']),25)
        for d in lock['dependencies']:
            self.assertRegex(d['commit'],r'^[0-9a-f]{40}$')

if __name__=='__main__': unittest.main()
