#!/usr/bin/env python3
# Copyright 2026 Noriwake contributors. SPDX-License-Identifier: Apache-2.0
"""Build real upstream game assets on Linux x86_64; never an APK build."""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tempfile

import native
import engine_overrides

ROOT = native.ROOT
GAME = native.GAME
DEPS = GAME / 'dependencies'
OUTPUT = GAME / 'built_assets'
MANIFEST = 'noriwake-build-manifest.json'
REQUIRED = ('flatbuffers', 'scene_lab', 'fplbase', 'motive', 'flatui',
            'hyphenation-patterns', 'breadboard', 'corgi', 'pindrop')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_inputs(fetch=False, dependencies=REQUIRED):
    lock = json.loads((ROOT/'native/upstream.lock.json').read_text())
    if fetch:
        native.hydrate(lock)
    native.verify(lock, assets=True)
    pins = {d['path'].split('/')[-1]: d['commit'] for d in lock['dependencies']}
    approved = {(i['dependency'], i['path']): i for i, _ in engine_overrides.entries()}
    for name in dependencies:
        stamp = DEPS/name/'.noriwake-source.json'
        if not stamp.exists():
            if not fetch:
                raise ValueError('Missing dependency '+name+'; use --fetch once.')
            native.fetch_dependency(lock, name)
        if fetch and any(dep == name for dep, _ in approved):
            engine_overrides.apply(only=name)
        doc = json.loads(stamp.read_text())
        if doc['commit'] != pins[name]:
            raise ValueError('Wrong dependency pin: '+name)
        for entry in doc['files']:
            path = native.safe_path(DEPS/name, entry['path'])
            data = native.read_blob(path)
            override = approved.get((name, entry['path']))
            if override:
                if entry['sha'] != override['upstream_blob_sha1'] or hashlib.sha256(data).hexdigest() != override['sha256']:
                    raise ValueError('Missing or modified approved override: '+str(path))
            elif native.blob_hash(data) != entry['sha']:
                raise ValueError('Modified dependency: '+str(path))
    # Track implementation and reviewed source identities; machine paths excluded.
    inputs = ['native/upstream.lock.json', 'native/modifications.json',
              'native/dependency-overrides.json', 'native/dependency-mirrors.json',
              'tools/build_native_assets.py', 'tools/requirements-native-assets.txt']
    return {name: sha(ROOT/name) for name in inputs}


def output_inventory(folder):
    result = {}
    for path in sorted(folder.rglob('*')):
        if path.is_symlink():
            raise ValueError('Generated assets must not be symlinks: '+str(path))
        if path.is_file() and path.name != MANIFEST:
            if not path.stat().st_size:
                raise ValueError('Empty generated asset: '+str(path))
            result[path.relative_to(folder).as_posix()] = sha(path)
    return result


def check_output(inputs):
    if OUTPUT.is_symlink():
        raise ValueError('Asset output cannot be a symlink')
    report = json.loads((OUTPUT/MANIFEST).read_text())
    if report.get('schema') != 1 or report['inputs'] != inputs:
        raise ValueError('Asset inputs changed: rebuild with tools/build_native_assets.py')
    if output_inventory(OUTPUT) != report['outputs']:
        raise ValueError('Assets missing, added or modified: rebuild with tools/build_native_assets.py')
    print('Prepared assets verified:', len(report['outputs']), 'files (not an APK).')


def schema_directories():
    return [GAME/'src/flatbufferschemas'] + [DEPS/path for path in (
        'fplbase/schemas', 'motive/schemas', 'pindrop/schemas', 'flatui/schemas',
        'scene_lab/schemas', 'breadboard/module_library/schemas',
        'corgi/component_library/schemas')]


def run(command):
    subprocess.run([str(x) for x in command], check=True, cwd=ROOT)


def build(args, inputs):
    if platform.system() != 'Linux' or platform.machine() not in ('x86_64', 'AMD64'):
        raise ValueError('This host recipe requires Linux x86_64 for pinned FBX tools; use Linux/WSL2.')
    import PIL
    import PIL.Image
    from PIL import features
    if PIL.__version__ != '11.3.0' or not features.check('webp'):
        raise ValueError('Install tools/requirements-native-assets.txt (Pillow with WebP support).')
    cache = ROOT/'.cache/native-asset-tools'
    cache.mkdir(parents=True, exist_ok=True)
    compiler = cache/'flatbuffers'
    # Debug deliberately avoids old optimized-header diagnostics; all upstream
    # -Werror checks stay enabled. Only reviewed source corrections are applied.
    run([args.cmake, '-S', DEPS/'flatbuffers', '-B', compiler, '-G', 'Ninja',
         '-DCMAKE_MAKE_PROGRAM='+str(Path(args.ninja).resolve()),
         '-DCMAKE_BUILD_TYPE=Debug', '-DFLATBUFFERS_BUILD_TESTS=OFF',
         '-DFLATBUFFERS_BUILD_FLATHASH=OFF'])
    run([args.cmake, '--build', compiler, '--target', 'flatc', '--parallel', '2'])
    flatc = compiler/'flatc'
    spec = importlib.util.spec_from_file_location('zooshi_asset_recipe', GAME/'scripts/build_assets.py')
    recipe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(recipe)
    with tempfile.TemporaryDirectory(prefix='assets-', dir=cache) as tmp:
        stage = Path(tmp)/'complete'
        stage.mkdir()
        # Fresh output and intermediate trees: no stale textures/metadata reuse.
        recipe.ASSETS_PATH = str(stage)
        recipe.INTERMEDIATE_TEXTURE_PATH = str(Path(tmp)/'intermediate')
        recipe.ASSET_ROOTS = [recipe.RAW_ASSETS_PATH, recipe.INTERMEDIATE_TEXTURE_PATH]
        argv = sys.argv
        try:
            sys.argv = [str(GAME/'scripts/build_assets.py'), '--flatc', str(flatc),
                        '--mesh-pipeline', str(DEPS/'fplbase/bin/Linux/mesh_pipeline'),
                        '--anim-pipeline', str(DEPS/'motive/bin/Linux/anim_pipeline'),
                        '--cwebp', '', '--output', str(stage), '--target', 'all']
            if recipe.main() != 0:
                raise ValueError('Original asset conversion failed')
        finally:
            sys.argv = argv
        # Required by World / DefaultEntityFactory, not just the scene editor.
        # The old NDK recipe generated this outside the prepared asset tree.
        run([flatc, '-b', '--schema',
             *[arg for folder in schema_directories() for arg in ('-I', folder)],
             '-o', stage/'flatbufferschemas',
             GAME/'src/flatbufferschemas/components.fbs'])
        reflection = stage/'flatbufferschemas/components.bfbs'
        if reflection.read_bytes()[4:8] != b'BFBS':
            raise ValueError('Missing/invalid entity reflection schema')
        # Same source directories as upstream CMake, plus original static assets.
        for source, target in [(GAME/'assets', stage),
                               (GAME/'src/rawassets/fonts', stage/'fonts'),
                               (DEPS/'flatui/assets/shaders', stage/'shaders'),
                               (DEPS/'fplbase/shaders', stage/'shaders'),
                               (DEPS/'flatui/assets/hyphen-data', stage/'hyphen-data')]:
            shutil.copytree(source, target, dirs_exist_ok=True)
        hyb_tools = DEPS/'flatui/cmake/hyphenation_patterns'
        patterns = re.findall(r'([A-Za-z-]+/hyph-[a-z0-9-]+\.pat\.txt)',
                              (hyb_tools/'CMakeLists.txt').read_text())
        if len(patterns) != 33 or len(set(patterns)) != 33:
            raise ValueError('Pinned hyphenation recipe changed')
        for pattern in patterns:
            source = DEPS/'hyphenation-patterns'/pattern
            target = stage/'hyphen-data'/source.name.replace('.pat.txt', '.hyb')
            run([sys.executable, hyb_tools/'mk_hyb_file.py', source, target])
            notices = stage/'hyphen-data/licenses'/source.parent.name
            notices.mkdir(parents=True, exist_ok=True)
            for notice in source.parent.iterdir():
                if notice.name in ('NOTICE', 'MODULE_LICENSE_NOTICE') or notice.name.endswith('.lic.txt'):
                    if notice.stat().st_size:
                        shutil.copy2(notice, notices/notice.name)
        expected = set()
        builder = recipe.builder
        for fn, ext in [(recipe.fbx_files_to_convert, 'fplmesh'),
                        (recipe.anim_files_to_convert, 'motiveanim'),
                        (recipe.png_files_to_convert, 'webp')]:
            sources = builder.input_files_add_overlays(fn(), recipe.ASSET_ROOTS,
                                                       recipe.OVERLAY_DIRS,
                                                       overlay_globs=['*.png' if ext == 'webp' else '*.fbx'])
            for source in sources:
                expected.add(Path(builder.processed_file_path(source, recipe.ASSET_ROOTS, str(stage), ext)[0]))
        for element in builder.flatbuffers_conversion_data_add_overlays(
                recipe.FLATBUFFERS_CONVERSION_DATA, recipe.ASSET_ROOTS, recipe.OVERLAY_DIRS):
            for source in element.input_files:
                expected.add(Path(builder.processed_file_path(source, recipe.ASSET_ROOTS, str(stage), element.extension)[0]))
        if any(not path.is_file() for path in expected):
            raise ValueError('Missing declared conversion output')
        for path in stage.rglob('*.webp'):
            with PIL.Image.open(path) as image:
                image.load()
                if any(size & (size - 1) for size in image.size):
                    raise ValueError('Non power-of-two texture: '+str(path))
        outputs = output_inventory(stage)
        report = {'schema': 1, 'inputs': inputs, 'outputs': outputs,
                  'counts': dict(sorted(Counter(Path(p).suffix for p in outputs).items())),
                  'tools': {'pillow': PIL.__version__, 'libwebp_encoder': features.version('webp')},
                  'scope': 'Host resource conversion only; not APK, runtime or release approval.'}
        (stage/MANIFEST).write_text(json.dumps(report, indent=2)+'\n')
        # Publish only after every conversion succeeds. Preserve previous output on failure.
        if OUTPUT.is_symlink():
            raise ValueError('Asset output cannot be a symlink')
        previous = Path(tmp)/'previous'
        if OUTPUT.exists():
            OUTPUT.rename(previous)
        try:
            stage.rename(OUTPUT)
        except OSError:
            if previous.exists():
                previous.rename(OUTPUT)
            raise
    check_output(inputs)
    print(json.dumps(report['counts'], indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fetch', action='store_true', help='Fetch missing pinned source/assets and apply approved overrides')
    parser.add_argument('--check', action='store_true', help='Verify prepared output without building or downloading')
    parser.add_argument('--cmake', default=shutil.which('cmake') or 'cmake')
    parser.add_argument('--ninja', default=shutil.which('ninja') or 'ninja')
    args = parser.parse_args()
    if args.fetch and args.check:
        parser.error('--check cannot download/modify dependencies')
    try:
        inputs = verify_inputs(args.fetch)
        if args.check:
            check_output(inputs)
        else:
            build(args, inputs)
    except (OSError, ValueError, KeyError, ImportError, subprocess.CalledProcessError) as exc:
        print('ASSET BUILD FAILED:', exc, file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
