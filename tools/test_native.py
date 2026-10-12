#!/usr/bin/env python3
"""Compile real downstream C++ policy/providers, not an Android build or SDK mock."""
# Copyright 2026 Noriwake contributors. SPDX-License-Identifier: Apache-2.0
from pathlib import Path
import os
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT/'native/zooshi/src'
compiler = os.environ.get('CXX', 'g++')
with tempfile.TemporaryDirectory(prefix='noriwake-test-') as tmp:
    suites = {
        'session': [],
        'offline_services': ['admob', 'analytics', 'gpg_manager', 'invites', 'messaging', 'remote_config'],
    }
    for name, units in suites.items():
        exe = str(Path(tmp) / (name+'-tests'))
        subprocess.run([compiler, '-std=c++11', '-Wall', '-Wextra', '-Werror',
                        '-pedantic', '-fsanitize=undefined', '-fno-sanitize-recover=undefined',
                        '-I'+str(SRC), str(ROOT/'native/tests'/(name+'_test.cpp')),
                        *[str(SRC/(unit+'.cpp')) for unit in units], '-o', exe], check=True)
        subprocess.run([exe], check=True)
    # Fail closed if somebody re-enables old GPG macros in build flags.
    result = subprocess.run([compiler, '-x', 'c++', '-std=c++11', '-fsyntax-only',
                             '-DUSING_GOOGLE_PLAY_GAMES', '-I'+str(SRC), '-'],
                            input='#include "noriwake/build_config.h"\n', text=True,
                            capture_output=True)
    if result.returncode == 0 or 'Legacy Google Play Games is not supported' not in result.stderr:
        raise RuntimeError('Legacy SDK re-enable guard failed')
    print('Build-policy guard: old GPG macro correctly rejected.')

    result = subprocess.run([compiler, '-x', 'c++', '-std=c++11', '-fsyntax-only',
                             '-DFPLBASE_ANDROID_VR=1', '-I'+str(SRC), '-'],
                            input='#include "noriwake/build_config.h"\n', text=True,
                            capture_output=True)
    if result.returncode == 0 or 'Noriwake touch build requires' not in result.stderr:
        raise RuntimeError('Inconsistent VR ABI guard failed')
    print('Build-policy guard: incompatible VR=1 correctly rejected.')
