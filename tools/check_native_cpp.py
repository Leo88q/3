#!/usr/bin/env python3
# Copyright 2026 Noriwake contributors. SPDX-License-Identifier: Apache-2.0
"""Compile actual game translation units on Linux x86_64. NOT NDK, linkage or APK."""
import argparse
import concurrent.futures
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys

import native
import build_native_assets as assets

DEPENDENCIES = tuple(sorted(set(assets.REQUIRED) | {
    'bulletphysics', 'fplutil', 'freetype', 'harfbuzz', 'libunibreak',
    'mathfu', 'sdl', 'sdl_mixer', 'stb', 'vectorial', 'webp'}))
CACHE = native.ROOT/'.cache/native-cpp-check'
# Host-only Mesa OpenGL declarations. License is retained in the downloaded header.
GL_REPOSITORY = 'notaz/mesa'
GL_BLOB = '5b284802885cd1454ff30d46e6c28fffd04e4f62'


def source_files():
    text = (native.GAME/'jni/libs/src/Android.mk').read_text()
    block = text.split('LOCAL_SRC_FILES :=', 1)[1].split('\n\n', 1)[0]
    files = re.findall(r'\bsrc/[A-Za-z0-9_/]+\.cpp\b', block)
    if not files or len(files) != len(set(files)):
        raise ValueError('Missing or duplicated game source list')
    return files


def gl_header(fetch):
    path = CACHE/'include/GL/gl.h'
    if not path.exists():
        if not fetch:
            raise ValueError('Missing pinned host GL header; run with --fetch')
        data = subprocess.run(['gh', 'api', '-H', 'Accept: application/vnd.github.raw+json',
            f'repos/{GL_REPOSITORY}/git/blobs/{GL_BLOB}'], check=True, capture_output=True).stdout
        if native.blob_hash(data) != GL_BLOB:
            raise ValueError('Host GL header provenance mismatch')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    if path.is_symlink() or native.blob_hash(path.read_bytes()) != GL_BLOB:
        raise ValueError('Modified host GL header')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fetch', action='store_true')
    parser.add_argument('--compiler', default=os.environ.get('CXX', 'g++'))
    parser.add_argument('--jobs', type=int, default=2)
    args = parser.parse_args()
    if args.jobs < 1 or args.jobs > 16:
        parser.error('--jobs must be 1..16')
    if platform.system() != 'Linux' or platform.machine() != 'x86_64':
        raise ValueError('This check targets Linux x86_64 host objects only')
    inputs = assets.verify_inputs(fetch=args.fetch, dependencies=DEPENDENCIES)
    assets.check_output(inputs)
    gl_header(args.fetch)
    generated = CACHE/'generated'
    generated.mkdir(parents=True, exist_ok=True)
    logs = CACHE/'logs'; logs.mkdir(exist_ok=True)
    objects = CACHE/'objects'; objects.mkdir(exist_ok=True)
    # Stale generated headers must not hide missing includes after schema removal.
    for path in generated.glob('*_generated.h'):
        path.unlink()
    roots = assets.schema_directories()
    schemas = sorted(p for root in roots for p in root.glob('*.fbs'))
    if len({p.name for p in schemas}) != len(schemas):
        raise ValueError('Schema basename collision; use separate include directories')
    flatc = native.ROOT/'.cache/native-asset-tools/flatbuffers/flatc'
    for schema in schemas:
        subprocess.run([str(flatc), '--gen-mutable', '-c', '-o', str(generated),
            *[arg for root in roots for arg in ('-I', str(root))], str(schema)], check=True)
    dep = assets.DEPS
    include = [native.GAME/'src', generated, CACHE/'include',
        dep/'fplbase/external/include', dep/'bulletphysics/src', dep/'webp/src',
        dep/'harfbuzz/src', dep/'fplutil/libfplutil/include',
        dep/'breadboard/module_library/include', dep/'corgi/component_library/include']
    include += [dep/name/'include' for name in DEPENDENCIES if (dep/name/'include').is_dir()]
    flags = ['-std=c++11', '-O0', '-g0', '-fPIC', '-msse4.1', '-Wall', '-Wextra',
        '-DFPLBASE_ANDROID_VR=0', '-DFPLBASE_OPENGL', '-DDEBUG=1',
        '-DBREADBOARD_MODULE_LIBRARY_BUILD_MATHFU',
        '-DBREADBOARD_MODULE_LIBRARY_BUILD_CORGI_COMPONENT_LIBRARY',
        '-DBREADBOARD_MODULE_LIBRARY_BUILD_PINDROP', *['-I'+str(path) for path in include]]
    def compile_one(source):
        stem = source.replace('/', '_')
        output = objects/(stem+'.o')
        output.unlink(missing_ok=True)
        command = [args.compiler, *flags, '-c', str(native.GAME/source), '-o', str(output)]
        process = subprocess.run(command, capture_output=True, text=True)
        (logs/(stem+'.log')).write_text(process.stdout+process.stderr)
        return {'source': source, 'exit_code': process.returncode,
                'warnings': process.stderr.count('warning:'),
                'object_sha256': assets.sha(output) if process.returncode == 0 else None}
    files = source_files()
    with concurrent.futures.ThreadPoolExecutor(args.jobs) as pool:
        results = list(pool.map(compile_one, files))
    report = {'scope': 'Linux host game objects ONLY; no engine-library compilation, linking, JNI, NDK or APK',
              'compiler': subprocess.check_output([args.compiler, '--version'], text=True).splitlines()[0],
              'host_gl': {'repository': GL_REPOSITORY, 'git_blob': GL_BLOB, 'license': 'MIT (header)'},
              'flags': flags, 'schemas': len(schemas), 'results': results}
    (CACHE/'summary.json').write_text(json.dumps(report, indent=2)+'\n')
    failed = [r['source'] for r in results if r['exit_code']]
    print(f'Host C++ objects: {len(files)-len(failed)}/{len(files)}; '
          f'{sum(r["warnings"] for r in results)} warnings retained in {logs}')
    if failed:
        raise ValueError('Compilation failed: '+', '.join(failed))
    # Exercise the reflection data that World loads at runtime with the pinned verifier.
    verifier = CACHE/'schema-resource-test'
    subprocess.run([args.compiler, '-std=c++11', '-Wall', '-Wextra', '-Werror',
        '-I'+str(dep/'flatbuffers/include'), str(native.ROOT/'native/tests/schema_resource_test.cpp'),
        '-o', str(verifier)], check=True)
    subprocess.run([str(verifier), str(assets.OUTPUT/'flatbufferschemas/components.bfbs')], check=True)
    print('Host checks passed. No Android binary or runtime claim.')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        print('C++ CHECK FAILED:', exc, file=sys.stderr)
        sys.exit(1)
