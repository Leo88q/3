#!/usr/bin/env python3
# Copyright 2026 Noriwake contributors. SPDX-License-Identifier: Apache-2.0
"""Decode every prepared texture using the pinned engine WebP library (host only)."""
import ctypes
import json
import shutil
import subprocess
import sys
from pathlib import Path

import native
import build_native_assets as assets


def main():
    assets.check_output(assets.verify_inputs())
    dep = native.GAME/'dependencies/webp'
    lock = json.loads((native.NATIVE/'upstream.lock.json').read_text())
    pin = next(d['commit'] for d in lock['dependencies'] if d['path'] == 'dependencies/webp')
    stamp = json.loads((dep/'.noriwake-source.json').read_text())
    if stamp['commit'] != pin:
        raise ValueError('Wrong WebP source revision')
    for entry in stamp['files']:
        if native.blob_hash(native.read_blob(native.safe_path(dep, entry['path']))) != entry['sha']:
            raise ValueError('Modified WebP source: '+entry['path'])
    cache = native.ROOT/'.cache/webp-runtime-check'
    source = cache/'source'
    # Separate host objects from NDK/dependency builds. Copy only verified originals.
    if source.exists():
        shutil.rmtree(source)
    source.mkdir(parents=True)
    for entry in stamp['files']:
        target = native.safe_path(source, entry['path'])
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(dep/entry['path'], target, follow_symlinks=False)
    subprocess.run(['make', '-C', str(source), '-f', 'makefile.unix',
                    'src/libwebpdecoder.a', 'EXTRA_FLAGS=', 'CFLAGS=-O2 -DNDEBUG -fPIC', '-j2'], check=True)
    library = cache/'decoder.so'
    subprocess.run(['cc', '-shared', '-Wl,--whole-archive', str(source/'src/libwebpdecoder.a'),
                    '-Wl,--no-whole-archive', '-lm', '-o', str(library)], check=True)
    decoder = ctypes.CDLL(str(library))
    decoder.WebPDecodeRGBA.argtypes = [ctypes.c_void_p, ctypes.c_size_t,
                                      ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)]
    decoder.WebPDecodeRGBA.restype = ctypes.c_void_p
    # This pinned WebP API documents malloc/free ownership for WebPDecodeRGBA.
    free = ctypes.CDLL(None).free
    free.argtypes = [ctypes.c_void_p]
    free.restype = None
    files = sorted(assets.OUTPUT.rglob('*.webp'))
    if not files:
        raise ValueError('No prepared textures')
    for path in files:
        data = path.read_bytes()
        width, height = ctypes.c_int(), ctypes.c_int()
        pixels = decoder.WebPDecodeRGBA(data, len(data), ctypes.byref(width), ctypes.byref(height))
        if not pixels:
            raise ValueError('Pinned runtime decoder rejected '+str(path))
        free(pixels)
        if width.value <= 0 or height.value <= 0:
            raise ValueError('Invalid decoded dimensions')
    print(f'Pinned WebP decoder {pin}: decoded all {len(files)} textures. Not an Android/GPU test.')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        print('WEBP CHECK FAILED:', exc, file=sys.stderr)
        sys.exit(1)
