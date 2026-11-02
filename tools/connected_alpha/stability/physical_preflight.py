#!/usr/bin/env python3
"""Read-only device preflight. Never marks functional acceptance as passed."""
import argparse
import json
import subprocess

APP = 'io.github.jose22yt.flexygram.alpha'
SCENARIOS = ['independent_install', 'startup', 'native_login', 'real_dialogs',
             'chat_navigation', 'send_receive', 'multimedia', 'background_push',
             'android_17', 'upstream_performance']


def collect(shell):
    api = shell('getprop', 'ro.build.version.sdk').strip()
    abi = shell('getprop', 'ro.product.cpu.abi').strip()
    emulator = shell('getprop', 'ro.kernel.qemu').strip()
    pages = shell('getconf', 'PAGE_SIZE').strip()
    # Reject unknown values; ARM64 and page size are observations, not assumptions.
    if api != '37' or abi != 'arm64-v8a' or emulator not in ('', '0') or pages not in ('4096', '16384'):
        raise ValueError('Expected physical ARM64 Android 17 (API 37), known 4/16 KiB page size')
    packages = {}
    for package in (APP, 'com.exteraless.app', 'org.telegram.messenger'):
        lines = shell('pm', 'list', 'packages', package).splitlines()
        if any(line and not line.startswith('package:') for line in lines):
            raise ValueError('Unexpected package-manager response')
        packages[package] = 'package:' + package in lines
    return {'status': 'DEVICE_METADATA_ONLY', 'api': int(api), 'abi': abi,
            'page_size': int(pages), 'installed': packages,
            'acceptance': {case: 'PENDING' for case in SCENARIOS}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--serial', required=True, help='Explicitly selected adb device; not included in output')
    args = parser.parse_args()

    def shell(*command):
        try:
            return subprocess.check_output(['adb', '-s', args.serial, 'shell', *command],
                                           text=True, stderr=subprocess.DEVNULL, timeout=15)
        except (OSError, subprocess.SubprocessError):
            raise ValueError('ADB unavailable, unauthorized, timed out or command failed') from None

    try:
        result = collect(shell)
    except ValueError as error:
        print(json.dumps({'status': 'BLOCKED', 'reason': str(error),
                          'acceptance': {case: 'PENDING' for case in SCENARIOS}}, indent=2))
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
