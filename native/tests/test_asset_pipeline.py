# Copyright 2026 Noriwake contributors. SPDX-License-Identifier: Apache-2.0
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import tarfile
import subprocess
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools'))
import native
import build_native_assets as assets
spec = importlib.util.spec_from_file_location('reviewed_asset_builder',
    ROOT/'native/overrides/scene_lab/scripts/scene_lab_asset_builder.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class AssetPipelineTests(unittest.TestCase):
    def test_mirrors_preserve_original_pins(self):
        lock = json.loads((ROOT/'native/upstream.lock.json').read_text())
        names = json.loads((ROOT/'native/dependency-mirrors.json').read_text())['mirrors']
        for dep in lock['dependencies']:
            if dep['path'].split('/')[-1] not in names:
                continue
            url, repo = native.dependency_repository(dep)
            self.assertEqual(url, 'https://github.com/'+repo)
            with self.assertRaisesRegex(ValueError, 'immutable upstream pin'):
                native.dependency_repository(dict(dep, commit='0'*40))

    def test_archive_omitted_blob_still_verified(self):
        for corrupt in (False, True):
            with self.subTest(corrupt=corrupt), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp); game = root/'game'; game.mkdir()
                (root/'dependency-mirrors.json').write_text('{"schema":1,"mirrors":{}}')
                pin = 'a'*40; data = b'export-ignored original file'
                archive = root/('fixture-'+pin+'.tar.gz')
                with tarfile.open(archive, 'w:gz') as tar:
                    info = tarfile.TarInfo('fixture-'+pin)
                    info.type = tarfile.DIRTYPE; tar.addfile(info)
                tree = {'tree': [{'type':'blob', 'path':'.gitattributes', 'mode':'100644',
                                  'sha':native.blob_hash(data)}]}
                def fake_run(command, **kwargs):
                    if '/git/trees/' in command[-1]:
                        return subprocess.CompletedProcess(command, 0, json.dumps(tree))
                    self.assertIn('/git/blobs/'+native.blob_hash(data), command[-1])
                    return subprocess.CompletedProcess(command, 0, b'wrong' if corrupt else data)
                dep = {'path':'dependencies/fixture','url':'https://github.com/example/fixture','commit':pin}
                with mock.patch.multiple(native, NATIVE=root, GAME=game, CACHE=root), mock.patch.object(native.subprocess, 'run', side_effect=fake_run):
                    if corrupt:
                        with self.assertRaisesRegex(ValueError, 'blob mismatch'):
                            native.fetch_dependency({'dependencies':[dep]}, 'fixture')
                        self.assertFalse((game/'dependencies/fixture').exists())
                    else:
                        native.fetch_dependency({'dependencies':[dep]}, 'fixture')
                        self.assertEqual((game/'dependencies/fixture/.gitattributes').read_bytes(), data)

    def test_copy_and_incremental_checks_without_distutils(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); source = root/'source'; source.mkdir()
            (source/'a').write_text('original')
            target = root/'target'
            builder.copy_tree(source, target)
            self.assertEqual((target/'a').read_text(), 'original')
            self.assertFalse(builder.newer(source/'a', target/'a'))
            self.assertTrue(builder.newer_group([source/'a'], target/'missing'))
            self.assertEqual(builder.copy_tree(source, source), [])
            with self.assertRaises(ValueError): builder.copy_tree(source, source/'nested')
            with self.assertRaises(FileNotFoundError): builder.newer(source/'missing', target/'a')

    def test_overlay_discovery_is_sorted_and_confined_to_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); raw = root/'raw'; raw.mkdir()
            overlay = raw/'overlays/holiday'; overlay.mkdir(parents=True)
            for name in ['z.png', 'a.png']:
                (raw/name).write_bytes(b'fixture')
                (overlay/name).write_bytes(b'fixture')
            paths = builder.input_files_add_overlays([str(raw/'z.png'), str(raw/'a.png')],
                [str(raw)], ['overlays/holiday'], overlay_globs=['*.png'])
            self.assertEqual(paths, sorted(paths))
            self.assertEqual(len(paths), 4)

    @unittest.skipUnless(builder.PIL_AVAILABLE, 'Install host Pillow requirement')
    def test_real_pillow_resize_and_webp_preserve_alpha(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); source = root/'fixture.png'
            # Tiny codec test fixture only; not game art.
            Image.new('RGBA', (5, 7), (80, 100, 180, 91)).save(source)
            image = builder.Image.read_attributes(str(source), 1024)
            image.convert_resize_image(str(root/'resized.png'), (8, 8))
            with Image.open(root/'resized.png') as output:
                self.assertEqual(output.size, (8, 8))
                self.assertEqual(output.getpixel((0, 0))[3], 91)
            builder.convert_png_image_to_webp('', str(source), str(root/'result.webp'), 80, None, 1024)
            with Image.open(root/'result.webp') as output:
                output.load()
                self.assertEqual(output.size, (8, 8))
                self.assertEqual(output.getpixel((0, 0))[3], 91)

    def test_manifest_rejects_missing_changed_extra_and_symlink_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp); (folder/'model.fplmesh').write_bytes(b'fixture')
            report = {'schema': 1, 'inputs': {'recipe': 'identity'},
                      'outputs': assets.output_inventory(folder)}
            (folder/assets.MANIFEST).write_text(json.dumps(report))
            with mock.patch.object(assets, 'OUTPUT', folder):
                assets.check_output(report['inputs'])
                with self.assertRaisesRegex(ValueError, 'inputs changed'):
                    assets.check_output({'recipe': 'changed'})
                (folder/'extra').write_text('unexpected')
                with self.assertRaises(ValueError): assets.check_output(report['inputs'])
                (folder/'extra').unlink()
                (folder/'model.fplmesh').write_bytes(b'changed')
                with self.assertRaises(ValueError): assets.check_output(report['inputs'])
                (folder/'model.fplmesh').unlink()
                with self.assertRaises(ValueError): assets.check_output(report['inputs'])
                (folder/'link').symlink_to(ROOT/'README.md')
                with self.assertRaisesRegex(ValueError, 'symlinks'):
                    assets.output_inventory(folder)

    def test_gradle_fails_closed_without_prepared_resources(self):
        gradle = (ROOT/'native/zooshi/build.gradle').read_text()
        self.assertIn("assets.srcDirs = ['built_assets']", gradle)
        self.assertIn("'tools/build_native_assets.py', '--check'", gradle)
        self.assertIn('dependsOn checkAssets', gradle)
        self.assertNotIn('import distutils', (ROOT/'native/overrides/scene_lab/scripts/scene_lab_asset_builder.py').read_text())
