# Copyright 2026 Noriwake contributors. SPDX-License-Identifier: Apache-2.0
"""Offline reproduction of interrupted GitHub transfers; no network required."""
import http.client
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
import urllib.error
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('download_tools', ROOT / 'tools/native.py')
native = importlib.util.module_from_spec(spec)
spec.loader.exec_module(native)


class Response(io.BytesIO):
    def __init__(self, data=b'complete', length=None):
        super().__init__(data)
        self.headers = {} if length is None else {'Content-Length': str(length)}


class BrokenResponse(Response):
    def read(self, size=-1):
        if self.tell() == 0:
            return super().read(3)
        raise http.client.IncompleteRead(b'partial', 10)


class DownloadTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.path = Path(tmp.name) / 'dependency.tar.gz'
        self.sleep = patch.object(native.time, 'sleep').start()
        self.addCleanup(patch.stopall)
        self.url = 'https://codeload.github.com/example/repo/tar.gz/pinned'

    def assert_no_partial(self):
        self.assertEqual(list(self.path.parent.glob('*.part')), [])

    def test_chunked_interruption_restarts_instead_of_appending(self):
        broken = BrokenResponse(b'bad prefix')
        with patch.object(native.urllib.request, 'urlopen',
                          side_effect=[broken, Response()]) as fetch:
            native.download(self.url, self.path)
        self.assertEqual(fetch.call_count, 2)
        self.assertEqual(self.path.read_bytes(), b'complete')
        self.assertTrue(broken.closed)
        self.sleep.assert_called_once_with(2)
        self.assert_no_partial()

    def test_content_length_truncation_retries(self):
        with patch.object(native.urllib.request, 'urlopen',
                          side_effect=[Response(b'ab', 8), Response(length=8)]):
            native.download(self.url, self.path)
        self.assertEqual(self.path.read_bytes(), b'complete')
        self.assert_no_partial()

    def test_exhausted_retries_preserve_existing_destination(self):
        self.path.write_bytes(b'previous verified download')
        with patch.object(native.urllib.request, 'urlopen',
                          side_effect=[BrokenResponse(b'bad') for _ in range(4)]) as fetch:
            with self.assertRaisesRegex(OSError, 'after 4 attempts'):
                native.download(self.url, self.path)
        self.assertEqual(fetch.call_count, 4)
        self.assertEqual(self.path.read_bytes(), b'previous verified download')
        self.assertEqual([c.args[0] for c in self.sleep.call_args_list], [2, 4, 8])
        self.assert_no_partial()

    def test_exhausted_connection_errors_do_not_create_archive(self):
        with patch.object(native.urllib.request, 'urlopen', side_effect=ConnectionResetError()):
            with self.assertRaises(OSError):
                native.download(self.url, self.path)
        self.assertFalse(self.path.exists())
        self.assert_no_partial()

    def test_timeout_and_url_errors_retry(self):
        with patch.object(native.urllib.request, 'urlopen', side_effect=[
                TimeoutError(), urllib.error.URLError('temporary DNS failure'), Response()]):
            native.download(self.url, self.path)
        self.assertEqual(self.path.read_bytes(), b'complete')

    def test_transient_http_errors_retry(self):
        for code in (408, 429, 500, 502, 503, 504):
            with self.subTest(code=code):
                body = io.BytesIO(b'error')
                error = urllib.error.HTTPError(self.url, code, 'Temporary', {}, body)
                with patch.object(native.urllib.request, 'urlopen',
                                  side_effect=[error, Response()]):
                    native.download(self.url, self.path)
                self.assertTrue(body.closed)
                self.assertEqual(self.path.read_bytes(), b'complete')

    def test_permanent_http_errors_fail_without_retry(self):
        for code in (401, 403, 404):
            with self.subTest(code=code):
                error = urllib.error.HTTPError(self.url, code, 'Permanent', {}, io.BytesIO())
                with patch.object(native.urllib.request, 'urlopen', side_effect=error) as fetch:
                    with self.assertRaises(urllib.error.HTTPError):
                        native.download(self.url, self.path)
                self.assertEqual(fetch.call_count, 1)
        self.sleep.assert_not_called()
        self.assert_no_partial()

    def test_filesystem_failure_does_not_retry(self):
        with patch.object(native.urllib.request, 'urlopen', return_value=Response()) as fetch:
            with patch.object(native.tempfile, 'NamedTemporaryFile', side_effect=PermissionError('read-only')):
                with self.assertRaises(PermissionError):
                    native.download(self.url, self.path)
        self.assertEqual(fetch.call_count, 1)
        self.sleep.assert_not_called()
        self.assert_no_partial()


if __name__ == '__main__':
    unittest.main()
