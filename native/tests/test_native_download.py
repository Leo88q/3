# Copyright 2026 Noriwake contributors. SPDX-License-Identifier: Apache-2.0
"""Offline tests for bounded, visible downloads; no public network required."""
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('download_tools', ROOT / 'tools/native.py')
native = importlib.util.module_from_spec(spec)
spec.loader.exec_module(native)


class DownloadTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.path = Path(tmp.name) / 'dependency.tar.gz'
        sleeper = patch.object(native.time, 'sleep')
        self.sleep = sleeper.start()
        self.addCleanup(sleeper.stop)
        finder = patch.object(native.shutil, 'which', return_value='/usr/bin/curl')
        finder.start()
        self.addCleanup(finder.stop)
        self.url = 'https://codeload.github.com/example/repo/tar.gz/pinned'

    def transfer(self, code=0, status='200', data=b'complete'):
        def run(command, **kwargs):
            target = Path(command[command.index('--output') + 1])
            # Every retry must have a different empty staging file, never append.
            self.assertEqual(target.read_bytes(), b'')
            target.write_bytes(data)
            return subprocess.CompletedProcess(command, code, stdout=status)
        return run

    def assert_no_partial(self):
        self.assertEqual(list(self.path.parent.glob('*.part')), [])

    def test_success_is_atomic_and_has_progress_and_hard_limits(self):
        with patch.object(native.subprocess, 'run', side_effect=self.transfer()) as run:
            with patch('sys.stderr') as stderr:
                native.download(self.url, self.path)
        args, kwargs = run.call_args
        command = args[0]
        self.assertEqual(command[1], '--disable')
        for flag, value in [('--max-time', '120'), ('--connect-timeout', '20'),
                            ('--speed-time', '30'), ('--speed-limit', '1024'),
                            ('--proto', '=https'), ('--proto-redir', '=https')]:
            self.assertEqual(command[command.index(flag) + 1], value)
        self.assertNotIn('--silent', command)  # keep curl's byte/speed/time meter
        self.assertIn('--http1.1', command)
        self.assertNotIn('--insecure', command)
        self.assertNotIn('stderr', kwargs)  # curl's progress remains visible
        self.assertEqual(kwargs['timeout'], 130)
        text = ''.join(str(c.args[0]) for c in stderr.write.call_args_list)
        self.assertIn('max 120s', text)
        self.assertIn('Download complete', text)
        self.assertEqual(self.path.read_bytes(), b'complete')
        self.assert_no_partial()

    def test_partial_http_body_restarts_instead_of_appending(self):
        calls = [self.transfer(18, '200', b'partial'), self.transfer()]
        with patch.object(native.subprocess, 'run', side_effect=lambda *a, **kw: calls.pop(0)(*a, **kw)) as run:
            native.download(self.url, self.path)
        self.assertEqual(run.call_count, 2)
        self.assertEqual(self.path.read_bytes(), b'complete')
        self.sleep.assert_called_once_with(2)
        self.assert_no_partial()

    def test_slow_transfer_exhaustion_preserves_old_destination(self):
        self.path.write_bytes(b'verified old file')
        with patch.object(native.subprocess, 'run', side_effect=self.transfer(28, '200', b'slow partial')) as run:
            with self.assertRaisesRegex(OSError, 'after 4 attempt'):
                native.download(self.url, self.path)
        self.assertEqual(run.call_count, 4)
        self.assertEqual(self.path.read_bytes(), b'verified old file')
        self.assertEqual([c.args[0] for c in self.sleep.call_args_list], [2, 4, 8])
        self.assert_no_partial()

    def test_outer_watchdog_exhaustion_leaves_no_archive(self):
        with patch.object(native.subprocess, 'run', side_effect=subprocess.TimeoutExpired('curl', 130)) as run:
            with self.assertRaisesRegex(OSError, 'exceeded 130s'):
                native.download(self.url, self.path)
        self.assertEqual(run.call_count, 4)
        self.assertFalse(self.path.exists())
        self.assert_no_partial()

    def test_transient_http_errors_retry(self):
        for status in ('408', '429', '500', '502', '503', '504'):
            with self.subTest(status=status):
                calls = [self.transfer(22, status), self.transfer()]
                with patch.object(native.subprocess, 'run', side_effect=lambda *a, **kw: calls.pop(0)(*a, **kw)) as run:
                    native.download(self.url, self.path)
                self.assertEqual(run.call_count, 2)
                self.assert_no_partial()

    def test_permanent_http_tls_and_disk_errors_do_not_retry(self):
        for code, status in ((22, '401'), (22, '403'), (22, '404'), (60, '000'), (23, '200'), (0, '206')):
            with self.subTest(code=code, status=status):
                with patch.object(native.subprocess, 'run', side_effect=self.transfer(code, status)) as run:
                    with self.assertRaises(OSError):
                        native.download(self.url, self.path)
                self.assertEqual(run.call_count, 1)
                self.assert_no_partial()
        self.sleep.assert_not_called()

    def test_ctrl_c_cleans_partial_and_preserves_old_destination(self):
        self.path.write_bytes(b'old')
        def interrupted(command, **kwargs):
            Path(command[command.index('--output') + 1]).write_bytes(b'partial')
            raise KeyboardInterrupt()
        with patch.object(native.subprocess, 'run', side_effect=interrupted):
            with self.assertRaises(KeyboardInterrupt):
                native.download(self.url, self.path)
        self.assertEqual(self.path.read_bytes(), b'old')
        self.sleep.assert_not_called()
        self.assert_no_partial()

    def test_filesystem_failure_does_not_start_download(self):
        with patch.object(native.subprocess, 'run') as run:
            with patch.object(native.tempfile, 'NamedTemporaryFile', side_effect=PermissionError('read-only')):
                with self.assertRaises(PermissionError):
                    native.download(self.url, self.path)
        run.assert_not_called()
        self.sleep.assert_not_called()
        self.assert_no_partial()

    def test_empty_response_refused(self):
        with patch.object(native.subprocess, 'run', side_effect=self.transfer(data=b'')):
            with self.assertRaisesRegex(OSError, 'Empty download'):
                native.download(self.url, self.path)
        self.assertFalse(self.path.exists())
        self.assert_no_partial()

    def test_missing_curl_is_actionable(self):
        with patch.object(native.shutil, 'which', return_value=None):
            with self.assertRaisesRegex(OSError, 'curl is required'):
                native.download(self.url, self.path)


if __name__ == '__main__':
    unittest.main()
