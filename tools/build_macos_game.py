#!/usr/bin/env python3
# Copyright 2026 Noriwake contributors. SPDX-License-Identifier: Apache-2.0
"""Build/link the native macOS desktop game. No web/Capacitor fallback."""
import argparse
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys

import native
import build_native_assets as assets
import check_native_cpp as cpp

CACHE = native.ROOT/'.cache/macos-game'
MODULES = ('sdl2', 'SDL2_mixer', 'freetype2', 'harfbuzz', 'libunibreak', 'gumbo', 'libwebp')


def source_manifest():
    doc = json.loads((native.ROOT/'native/macos/sources.json').read_text())
    if doc.get('schema') != 1:
        raise ValueError('Unknown macOS source manifest')
    for group, files in doc['sources'].items():
        base = native.GAME if group == 'game' else assets.DEPS/group
        if len(files) != len(set(files)):
            raise ValueError('Duplicate source in '+group)
        if group != 'game':
            originals = {f['path'] for f in json.loads((base/'.noriwake-source.json').read_text())['files']}
            if not set(files) <= originals:
                raise ValueError('Source not present in pinned dependency: '+group)
        for relative in files:
            if not native.safe_path(base, relative).is_file():
                raise ValueError('Missing source '+relative)
    if set(doc['sources']['game']) != set(cpp.source_files()) | {'src/inputcontrollers/mouse_controller.cpp'}:
        raise ValueError('Desktop game source list drifted from reviewed Android list')
    return doc


def run(command):
    subprocess.run([str(x) for x in command], cwd=native.ROOT, check=True)


def smoke_succeeded(log, exit_code):
    return (exit_code == 0 and 'SMOKE PASSED:' in log
            and 'SMOKE: initialized real game and OpenGL context' in log
            and 'Error in graph' not in log)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fetch', action='store_true', help='Prepare missing pinned C++ dependency sources')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--run', action='store_true', help='Launch the actual game after successful build')
    mode.add_argument('--smoke-test', action='store_true', help='Initialize OpenGL/game, run briefly, quit; not gameplay QA')
    parser.add_argument('--jobs', type=int, default=2)
    args = parser.parse_args()
    if platform.system() != 'Darwin' or platform.machine() not in ('arm64', 'x86_64'):
        raise ValueError('This executable profile requires macOS arm64/x86_64')
    if not 1 <= args.jobs <= 16:
        raise ValueError('--jobs must be 1..16')
    report_path = CACHE/'build-report.json'
    report_path.unlink(missing_ok=True)
    inputs = assets.verify_inputs(fetch=args.fetch, dependencies=cpp.DEPENDENCIES)
    assets.check_output(inputs)
    manifest = source_manifest()
    for tool in ('cmake', 'ninja', 'pkg-config'):
        if not shutil.which(tool):
            raise ValueError('Missing build tool: '+tool)
    libraries = {}
    for module in MODULES:
        libraries[module] = subprocess.check_output(['pkg-config', '--modversion', module], text=True).strip()
    if not all(libraries[m].startswith('2.') for m in ('sdl2', 'SDL2_mixer')):
        raise ValueError('The Mac profile requires SDL2/SDL2_mixer 2.x, not SDL3')
    generated = CACHE/'generated'
    generated.mkdir(parents=True, exist_ok=True)
    for old in generated.glob('*_generated.h'):
        old.unlink()
    roots = assets.schema_directories()
    schemas = sorted(p for root in roots for p in root.glob('*.fbs'))
    if len({p.name for p in schemas}) != len(schemas):
        raise ValueError('Generated schema basename collision')
    flatc = native.ROOT/'.cache/native-asset-tools/flatbuffers/flatc'
    for schema in schemas:
        run([flatc, '--gen-mutable', '-c', '-o', generated,
             *[arg for folder in roots for arg in ('-I', folder)], schema])
    # Upstream FlatUI's implementation uses a namespaced generated-header path.
    (generated/'flatui').mkdir(exist_ok=True)
    shutil.copy2(generated/'flatui_generated.h', generated/'flatui/flatui_generated.h')
    run(['cmake', '-S', native.ROOT/'native/macos', '-B', CACHE, '-G', 'Ninja',
         '-DCMAKE_BUILD_TYPE=Debug', '-DCMAKE_OSX_ARCHITECTURES='+platform.machine(),
         '-DCMAKE_MAKE_PROGRAM='+shutil.which('ninja')])
    process = subprocess.run(['cmake', '--build', str(CACHE), '--parallel', str(args.jobs)],
                             text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (CACHE/'compile.log').write_text(process.stdout)
    print(process.stdout, end='')
    if process.returncode:
        errors = [line for line in process.stdout.splitlines() if 'error:' in line or 'Undefined symbols' in line or 'ld:' in line]
        raise ValueError('Native compilation/link failed:\n'+'\n'.join(errors[:16]))
    executable = CACHE/'bin/noriwake'
    if not executable.is_file():
        raise ValueError('Linker did not produce the game executable')
    # Original game searches upwards from argv[0] for an assets directory.
    link = CACHE/'assets'
    if link.is_symlink():
        if link.resolve() != assets.OUTPUT.resolve():
            raise ValueError('Unexpected assets symlink; refusing overwrite')
    elif link.exists():
        raise ValueError('Unexpected assets folder in build cache; refusing overwrite')
    else:
        link.symlink_to(assets.OUTPUT, target_is_directory=True)
    dylibs = subprocess.check_output(['otool', '-L', str(executable)], text=True)
    architecture = subprocess.check_output(['lipo', '-archs', str(executable)], text=True).strip()
    if architecture != platform.machine():
        raise ValueError('Executable architecture does not match the host')
    report = {'scope': 'Native desktop development executable; not signed/not redistributable .app',
              'architecture': architecture, 'executable_sha256': assets.sha(executable),
              'macos': platform.mac_ver()[0], 'system_libraries': libraries,
              'translation_units': sum(len(v) for v in manifest['sources'].values())+1,
              'dynamic_libraries': dylibs, 'inputs': inputs,
              'runtime_tested': False}
    report_path.write_text(json.dumps(report, indent=2)+'\n')
    print('NATIVE GAME LINKED:', executable)
    print('Architecture:', architecture, 'System libraries:', libraries)
    print('Runtime is NOT validated by linking. This is a local development build, not a portable .app.')
    if args.smoke_test:
        try:
            smoke = subprocess.run([str(executable), '--smoke-test'], cwd=CACHE,
                                   capture_output=True, text=True, timeout=60)
            log = smoke.stdout + smoke.stderr
            report['smoke_exit_code'] = smoke.returncode
        except subprocess.TimeoutExpired as exc:
            log = 'SMOKE TIMEOUT: game did not initialize/quit within 60 seconds\n'
            log += (exc.stdout or b'').decode(errors='replace') if isinstance(exc.stdout, bytes) else (exc.stdout or '')
            log += (exc.stderr or b'').decode(errors='replace') if isinstance(exc.stderr, bytes) else (exc.stderr or '')
            report['smoke_exit_code'] = 'timeout'
        (CACHE/'smoke.log').write_text(log)
        report['runtime_tested'] = smoke_succeeded(log, report['smoke_exit_code'])
        report['runtime_scope'] = 'Game initialization, real window/OpenGL context and timed loop exit ONLY'
        report_path.write_text(json.dumps(report, indent=2)+'\n')
        print(log, flush=True)
        print('SMOKE SUMMARY:', json.dumps({'exit': report['smoke_exit_code'],
            'passed': report['runtime_tested'], 'scope': report['runtime_scope']}), flush=True)
        if not report['runtime_tested']:
            raise ValueError('Game startup smoke test failed; see .cache/macos-game/smoke.log')
    if args.run:
        run([executable])


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        print('MAC GAME BUILD FAILED:', exc, file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(130)
