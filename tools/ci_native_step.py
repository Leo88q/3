#!/usr/bin/env python3
# Copyright 2026 Noriwake contributors. SPDX-License-Identifier: Apache-2.0
"""Run a Python check and expose failure details through GitHub check annotations."""
import platform
import subprocess
import sys


def escape(text):
    return text.replace('%', '%25').replace('\r', '%0D').replace('\n', '%0A')


def main():
    if len(sys.argv) < 2:
        return 2
    print('::notice title=Native host::'+escape(
        f'{platform.system()}/{platform.machine()} macOS={platform.mac_ver()[0]}'), flush=True)
    result = subprocess.run([sys.executable, *sys.argv[1:]],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    print(result.stdout, end='', flush=True)
    if result.returncode:
        print('::error title=Native check failed::'+escape(result.stdout[-15000:]), flush=True)
    return result.returncode


if __name__ == '__main__':
    sys.exit(main())
