#!/usr/bin/env python3
"""Validate real SDK payloads; lift a known nested platform layout without synthesizing files."""
import argparse
from decimal import Decimal, InvalidOperation
from pathlib import Path
import zipfile

REQUIRED = ('android.jar', 'core-for-system-modules.jar', 'build.prop', 'source.properties', 'framework.aidl')


def properties(path):
    result = {}
    for line in path.read_text().splitlines():
        if '=' in line and not line.lstrip().startswith('#'):
            key, value = line.split('=', 1)
            result[key.strip()] = value.strip()
    return result


def validate_platform(path):
    for name in REQUIRED:
        if not (path/name).is_file():
            raise ValueError('Incomplete SDK 37 platform: missing ' + name)
    source = properties(path/'source.properties')
    build = properties(path/'build.prop')
    try:
        if Decimal(source.get('AndroidVersion.ApiLevel', '0')) != 37 or Decimal(build.get('ro.build.version.sdk', '0')) != 37:
            raise ValueError('SDK platform metadata does not describe API 37')
    except InvalidOperation:
        raise ValueError('Invalid API level in SDK platform metadata') from None
    for name in ['android.jar', 'core-for-system-modules.jar']:
        with zipfile.ZipFile(path/name) as archive:
            if archive.testzip() is not None:
                raise ValueError('Corrupt SDK platform JAR: ' + name)
            if name == 'android.jar' and 'android/app/Activity.class' not in archive.namelist():
                raise ValueError('SDK android.jar lacks platform classes')


def normalize_platform(root):
    # Never replace an already valid installation, or fabricate build.prop/stubs.
    if all((root/name).is_file() for name in REQUIRED):
        validate_platform(root)
        return False
    nested = root/root.name
    validate_platform(nested)
    planned = list(nested.iterdir())
    if any((root/p.name).exists() for p in planned):
        raise ValueError('Ambiguous nested SDK layout; refusing to overwrite existing files')
    for p in planned:
        p.rename(root/p.name)
    nested.rmdir()
    validate_platform(root)
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--sdk-root', type=Path, required=True)
    args = parser.parse_args()
    sdk = args.sdk_root
    changed = normalize_platform(sdk/'platforms/android-37.0')
    expected = [('build-tools/36.0.0', '36.0.0'), ('ndk/27.2.12479018', '27.2.12479018'), ('cmake/3.31.6', '3.31.6')]
    for path, version in expected:
        if properties(sdk/path/'source.properties').get('Pkg.Revision') != version:
            raise ValueError('Unexpected installed SDK tool version: ' + path)
    if not (sdk/'ndk/27.2.12479018/build/cmake/android.toolchain.cmake').is_file():
        raise ValueError('Incomplete NDK CMake toolchain')
    print('SDK 37 real payload verified; nested layout lifted.' if changed else 'SDK 37 real payload verified; layout already correct.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
