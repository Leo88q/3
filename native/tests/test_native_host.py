# Copyright 2026 Noriwake contributors. SPDX-License-Identifier: Apache-2.0
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools'))
import native_host as host


class NativeHostTests(unittest.TestCase):
    def test_supported_hosts_and_flags(self):
        for system, arch in [('Linux', 'x86_64'), ('Darwin', 'arm64'), ('Darwin', 'x86_64')]:
            self.assertEqual(host.host(system, arch), (system, arch))
        self.assertEqual(host.cpp_flags('Darwin', 'arm64'), [])
        self.assertEqual(host.cpp_flags('Darwin', 'x86_64'), ['-msse4.1'])
        for system, arch in [('Linux', 'aarch64'), ('Windows', 'AMD64'), ('Darwin', 'i386')]:
            with self.assertRaises(ValueError): host.host(system, arch)

    def test_rosetta_is_checked_not_installed(self):
        with mock.patch.object(host.subprocess, 'run') as run:
            host.require_translation('Linux', 'x86_64')
            host.require_translation('Darwin', 'x86_64')
            run.assert_not_called()
            run.return_value = subprocess.CompletedProcess([], 1, '', 'Bad CPU type')
            with self.assertRaisesRegex(ValueError, 'Rosetta 2'):
                host.require_translation('Darwin', 'arm64')
            self.assertEqual(run.call_args.args[0], ['/usr/bin/arch', '-x86_64', '/usr/bin/true'])
            run.return_value = subprocess.CompletedProcess([], 0, '', '')
            host.require_translation('Darwin', 'arm64')

    def fixture(self, folder):
        for dep, exe in [('fplbase', 'mesh_pipeline'), ('motive', 'anim_pipeline')]:
            path = folder/dep/'bin/Darwin'/exe
            path.parent.mkdir(parents=True)
            path.write_bytes(struct.pack('<8I', 0xfeedfacf, 0x01000007, 3, 2, 0, 0, 0, 0))

    def test_real_tool_selection_with_spaces_and_usage_exit_one(self):
        with tempfile.TemporaryDirectory(prefix=' Noriwake ') as tmp:
            root = Path(tmp); self.fixture(root)
            def run(command, **kwargs):
                return subprocess.CompletedProcess(command, 1, 'Usage: '+Path(command[0]).name, '')
            with mock.patch.object(host.subprocess, 'run', side_effect=run):
                tools = host.converters(root, 'Darwin', 'x86_64')
            self.assertEqual(tools['mesh'], root/'fplbase/bin/Darwin/mesh_pipeline')
            self.assertEqual(tools['anim'], root/'motive/bin/Darwin/anim_pipeline')

    def test_loader_failure_is_not_accepted_as_help(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self.fixture(root)
            with mock.patch.object(host.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1, '', 'dyld: missing library')):
                with self.assertRaisesRegex(ValueError, 'cannot run'):
                    host.converters(root, 'Darwin', 'x86_64')
            (root/'fplbase/bin/Darwin/mesh_pipeline').write_bytes(b'not Mach-O')
            with self.assertRaisesRegex(ValueError, 'Mach-O'):
                host.converters(root, 'Darwin', 'x86_64')

    def test_crash_even_with_usage_text_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self.fixture(root)
            with mock.patch.object(host.subprocess, 'run', return_value=subprocess.CompletedProcess([], -9, 'Usage: mesh_pipeline', '')):
                with self.assertRaisesRegex(ValueError, 'exit -9'):
                    host.converters(root, 'Darwin', 'x86_64')
