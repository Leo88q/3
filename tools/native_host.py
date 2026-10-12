#!/usr/bin/env python3
# Copyright 2026 Noriwake contributors. SPDX-License-Identifier: Apache-2.0
"""Host selection for real pinned FBX tools; never install/approve Rosetta silently."""
import platform
import struct
import subprocess


def host(system=None, machine=None):
    system = system or platform.system()
    machine = machine or platform.machine()
    if system == 'Linux' and machine in ('x86_64', 'AMD64'):
        return 'Linux', machine
    if system == 'Darwin' and machine in ('arm64', 'x86_64'):
        return 'Darwin', machine
    raise ValueError(f'Unsupported native host: {system}/{machine}; use Linux x86_64 or macOS arm64/x86_64.')


def require_translation(system, machine):
    if system != 'Darwin' or machine != 'arm64':
        return
    # Only legacy FBX converters need x86_64. Python, flatc and C++ stay native ARM64.
    process = subprocess.run(['/usr/bin/arch', '-x86_64', '/usr/bin/true'],
                             capture_output=True, text=True, timeout=30)
    if process.returncode:
        raise ValueError('Pinned macOS FBX tools require Rosetta 2. If you accept Apple licensing, '
                         'install it explicitly with: softwareupdate --install-rosetta . '
                         'This script does not install it or accept the license for you.\n'+process.stderr)


def converters(dependencies, system, machine):
    require_translation(system, machine)
    result = {}
    for kind, dependency, executable in [('mesh', 'fplbase', 'mesh_pipeline'),
                                          ('anim', 'motive', 'anim_pipeline')]:
        path = dependencies/dependency/'bin'/system/executable
        if system == 'Darwin':
            with path.open('rb') as stream:
                header = stream.read(32)
            if len(header) != 32 or struct.unpack_from('<II', header) != (0xfeedfacf, 0x01000007):
                raise ValueError('Expected pinned 64-bit Intel Mach-O converter: '+str(path))
        process = subprocess.run([str(path), '--help'], capture_output=True,
                                 text=True, errors='replace', timeout=30)
        output = process.stdout + process.stderr
        # Original tools return 1 for usage. A crash/missing dylib must not count as success.
        if process.returncode not in (0, 1) or 'Usage: '+executable not in output:
            raise ValueError(f'{executable} cannot run on {system}/{machine} '
                             f'(exit {process.returncode}). No security checks are disabled.\n'+output[-4000:])
        result[kind] = path
    return result


def cpp_flags(system, machine):
    host(system, machine)
    return ['-msse4.1'] if machine in ('x86_64', 'AMD64') else []
