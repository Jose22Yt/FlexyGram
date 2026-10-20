"""Read-only supplement to the reviewed image gate. Never contacts ADB or boots Android."""
from pathlib import Path
import argparse
import json
import os
import re
import shutil
import subprocess

PROFILES = {
    'api24-4k': (24, 'default', 'flexygram-api24-offline-v2'),
    'arm64-16k': (35, 'google_apis_ps16k', 'flexygram-api35-offline-v2'),
}
GIB = 1024 ** 3
HOST_OVERRIDES = ['ADB_SERVER_SOCKET', 'ANDROID_ADB_SERVER_ADDRESS',
                  'ANDROID_ADB_SERVER_PORT', 'ANDROID_SERIAL', 'LD_PRELOAD',
                  'LD_AUDIT', 'JAVA_TOOL_OPTIONS', 'JDK_JAVA_OPTIONS', '_JAVA_OPTIONS']


def properties(path):
    values = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith(('#', ';')):
            continue
        key, sep, value = line.partition('=')
        key, value = key.strip(), value.strip()
        if not sep or not key or key in values:
            raise ValueError('Malformed or duplicate property')
        values[key] = value
    return values


def below(path, root):
    resolved = path.resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise ValueError('Path escapes explicit laboratory root')
    return resolved


def inspect(sdk, avd_home, java_home, env=None, runner=subprocess.run, usage=shutil.disk_usage):
    """Only version subprocesses; structured issue codes never include environment values."""
    env = dict(os.environ if env is None else env)
    sdk, avd_home, java_home = map(lambda p: Path(p).absolute(), (sdk, avd_home, java_home))
    issues, checks = [], []

    def check(code, operation):
        try:
            operation()
            checks.append(code)
        except (OSError, ValueError, subprocess.SubprocessError):
            issues.append(code)

    def require(value):
        if not value:
            raise ValueError('Requirement unmet')

    # Check both output locations, without creating them or counting shared free space twice.
    volumes = {}
    for label, path in [('sdk', sdk), ('avd', avd_home)]:
        def storage(path=path, label=label):
            require(path.is_dir() and not path.is_symlink())
            device = path.stat().st_dev
            volumes.setdefault(device, {'path': path, 'budget': 0})['budget'] += (2 if label == 'sdk' else 10) * GIB
            require(os.access(path, os.W_OK | os.X_OK))
        check('storage_' + label, storage)
    for index, volume in enumerate(volumes.values()):
        check('free_space_volume_' + str(index), lambda v=volume: require(usage(v['path']).free >= v['budget']))

    # A subsequent authorized offline session must explicitly clear inherited routing defaults.
    for key in HOST_OVERRIDES + ['HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY',
                                'http_proxy', 'https_proxy', 'all_proxy']:
        check('environment_' + key, lambda key=key: require(not env.get(key)))

    for label, relative, expected in [
        ('sdk_cli_metadata', 'cmdline-tools/19.0/source.properties', '19.0'),
        ('build_tools_metadata', 'build-tools/36.0.0/source.properties', '36.0.0'),
    ]:
        check(label, lambda relative=relative, expected=expected: require(
            properties(below(sdk / relative, sdk)).get('Pkg.Revision') == expected))

    commands = [
        ('adb_version', [str(sdk / 'platform-tools/adb'), 'version'], r'Version 37\.0\.1(?:[-\s]|$)'),
        ('emulator_version', [str(sdk / 'emulator/emulator'), '-no-window', '-version'], r'Android emulator version 37\.2\.12(?:[.\s(]|$)'),
        ('java_version', [str(java_home / 'bin/java'), '-version'], r'version "21(?:[.\"]|$)'),
    ]
    for code, command, expected in commands:
        def version(command=command, expected=expected):
            require(Path(command[0]).is_file())
            # No personal SDK/ADB defaults and no proxy values passed to child tools.
            child = {k: v for k, v in env.items() if k not in HOST_OVERRIDES and 'proxy' not in k.lower()}
            child['ANDROID_AVD_HOME'] = str(avd_home)
            child['ANDROID_USER_HOME'] = str(avd_home)
            child['ANDROID_HOME'] = str(sdk)
            child['ANDROID_SDK_ROOT'] = str(sdk)
            child['LD_LIBRARY_PATH'] = str(sdk / 'emulator/lib64') + ':' + str(sdk / 'emulator/lib64/qt/lib')
            result = runner(command, capture_output=True, text=True, timeout=20, env=child)
            require(result.returncode == 0 and re.search(expected, result.stdout + result.stderr))
        check(code, version)

    for profile, (api, tag, name) in PROFILES.items():
        def image(api=api, tag=tag, name=name):
            locator_path = avd_home / (name + '.ini')
            require(not locator_path.is_symlink())
            locator = properties(below(locator_path, avd_home))
            directory = below(Path(locator.get('path', '')), avd_home)
            require(directory.is_dir() and locator.get('target') == 'android-' + str(api))
            require(directory == (avd_home / (name + '.avd')).resolve())
            for item in (Path(locator.get('path', '')), directory / 'config.ini'):
                require(not item.is_symlink() and not any(parent.is_symlink() for parent in item.parents))
            require(not any(directory.glob('userdata-qemu*')) and not any(
                (directory / item).exists() for item in ('snapshots', 'cache.img', 'hardware-qemu.ini')))
            config = properties(below(directory / 'config.ini', avd_home))
            # Match empty_avd_boot: only the reviewed ephemeral marker is accepted.
            # Explicit paths (even private ones) need a separate launcher review.
            for key in ('disk.dataPartition.path', 'disk.cachePartition.path', 'sdcard.path'):
                require(config.get(key, '') in ('', '<temp>'))
            require(config.get('abi.type') == 'arm64-v8a' and config.get('hw.cpu.arch') == 'arm64')
            image_dir = below(sdk / config.get('image.sysdir.1', ''), sdk)
            require(image_dir == (sdk / f'system-images/android-{api}/{tag}/arm64-v8a').resolve())
            source = properties(below(image_dir / 'source.properties', sdk))
            require(source.get('AndroidVersion.ApiLevel') == str(api) and source.get('SystemImage.Abi') == 'arm64-v8a')
            require(source.get('Pkg.Revision') in (('9', '9.0.0') if api == 24 else ('5', '5.0.0')))
            if api == 35:
                require('page_size_16kb' in source.get('SystemImage.TagId', '').split(','))
            for filename in ['kernel-ranchu', 'system.img', 'userdata.img']:
                item = below(image_dir / filename, sdk)
                require(item.is_file() and item.stat().st_size > 0)
            require(config.get('PlayStore.enabled', '').lower() == 'false')
        check('avd_' + profile, image)

    return {
        'schema': 'flexygram-readiness-supplement-v1',
        'status': 'PREBOOT_CONFIGURATION_CHECKED' if not issues else 'PREBOOT_BLOCKED',
        'passed_checks': checks, 'blocking_checks': issues,
        'android_executed': False, 'apk_installed': False, 'apk_signed': False,
        'image_bytes_verified': False, 'network_isolation_verified': False,
        'required_next': ['reviewed image/archive gate', 'authorized offline namespace verification',
                          'explicit -no-snapshot boot plan', 'authorized Android runtime validation'],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['sdk', 'avd-home', 'java-home']:
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    result = inspect(args.sdk, args.avd_home, args.java_home)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not result['blocking_checks'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
