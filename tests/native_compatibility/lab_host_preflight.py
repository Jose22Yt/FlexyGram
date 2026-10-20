"""Linux host/image preflight only. Never boots Android, installs, signs or calls ADB devices.

Reuses the existing Android instrumentation runner after future authorization.
"""
from pathlib import Path
import argparse
import gzip
import hashlib
import json
import os
import platform
import shutil
import subprocess
import zipfile

IMAGES = {
    'api24-4k': {'api': '24', 'filename': 'arm64-v8a-24_r09.zip',
                 'sha256': '3c3a70dcffe8c162984ec190fc3388bf237b241b3ba80bf7aa5c86e130d8f59b',
                 'url': 'https://dl.google.com/android/repository/sys-img/android/arm64-v8a-24_r09.zip'},
    'arm64-16k': {'api': '35', 'filename': 'arm64-v8a-ps16k-35_r05.zip',
                  'sha256': '991c7c08258a0a32d7851ae8f9fb7dcd62f5b3907f1a91a2514cd94e75005cb3',
                  'url': 'https://dl.google.com/android/repository/sys-img/google_apis/arm64-v8a-ps16k-35_r05.zip'}}


def require(value, message):
    if not value:
        raise ValueError(message)


def properties(text, profile):
    rows = {}
    for line in text.splitlines():
        if '=' in line:
            key, value = line.split('=', 1)
            require(key not in rows, 'Duplicate image property')
            rows[key] = value
    require(rows.get('SystemImage.Abi') == 'arm64-v8a', 'Not a native ARM64 image')
    require(rows.get('AndroidVersion.ApiLevel') == IMAGES[profile]['api'], 'Wrong API image')
    if profile == 'arm64-16k':
        require('page_size_16kb' in rows.get('SystemImage.TagId', '').split(','), '16KB image tag missing')
    return rows


def verify_image(path, profile):
    require(path.is_file() and not path.is_symlink() and
            not any(p.is_symlink() for p in path.parents), 'Regular image archive required')
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''): h.update(block)
    require(h.hexdigest() == IMAGES[profile]['sha256'], 'Image archive hash mismatch')
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        require(len(names) == len(set(names)) and archive.testzip() is None, 'Image CRC/duplicates invalid')
        props = [n for n in names if n.endswith('/source.properties')]
        require(len(props) == 1, 'Image properties missing/ambiguous')
        metadata = properties(archive.read(props[0]).decode(), profile)
        kernels = [n for n in names if n.endswith('/kernel-ranchu')]
        require(len(kernels) == 1, 'Ranchu kernel missing/ambiguous')
        with archive.open(kernels[0]) as stream:
            prefix = stream.read(64)
        compressed = prefix.startswith(b'\x1f\x8b')
        if compressed:
            with archive.open(kernels[0]) as stream, gzip.GzipFile(fileobj=stream) as inner:
                prefix = inner.read(64)
        require(prefix[56:60] == b'ARMd', 'ARM64 kernel header missing')
    return {'profile': profile, 'sha256': h.hexdigest(), 'bytes': path.stat().st_size,
            'crc_valid': True, 'properties': metadata, 'kernel_gzip': compressed,
            'arm64_kernel_header_verified': True, 'actual_guest_api': None,
            'actual_guest_page_size': None, 'strict_16k_runtime_verified': False, 'booted': False}


def command(args, env=None):
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=20, env=env)
        return {'exit_code': result.returncode, 'output': (result.stdout+result.stderr)[:4000]}
    except (OSError, subprocess.TimeoutExpired) as error:
        return {'exit_code': None, 'error': type(error).__name__}


def probe(sdk, archives):
    blockers = []
    images = []
    for profile, spec in IMAGES.items():
        try: images.append(verify_image(archives/spec['filename'], profile))
        except (OSError, ValueError, zipfile.BadZipFile) as error:
            blockers.append(profile+': '+str(error))
    env = os.environ.copy()
    env['LD_LIBRARY_PATH'] = str(sdk/'emulator/lib64')+':'+str(sdk/'emulator/lib64/qt/lib')
    version = command([str(sdk/'emulator/emulator'), '-no-window', '-version'], env)
    engine = command([str(sdk/'emulator/qemu/linux-x86_64/qemu-system-aarch64-headless'), '-version'], env)
    adb = command([str(sdk/'platform-tools/adb'), 'version'], env)
    network = command(['unshare', '--user', '--map-root-user', '--net', 'true'])
    for name, row in [('emulator', version), ('ARM64 engine', engine), ('adb executable', adb), ('isolated network namespace', network)]:
        if row['exit_code'] != 0: blockers.append(name+' unavailable')
    if not shutil.which('ip'): blockers.append('iproute2 missing for isolated loopback setup')
    if platform.system() != 'Linux': blockers.append('This preflight recipe requires Linux')
    return {'status': 'HOST_BLOCKED_BEFORE_ANDROID_BOOT' if blockers else 'HOST_READY_FOR_MANUAL_OFFLINE_BOOT_CHECK_ONLY',
            'blockers': blockers, 'images': images, 'emulator': version, 'arm64_engine': engine,
            'adb_version_only': adb, 'network_namespace': network,
            'kvm_present': Path('/dev/kvm').exists(), 'host_arch': platform.machine(),
            'host_page_size': os.sysconf('SC_PAGE_SIZE'), 'android_executed': False,
            'installation_authorized': False, 'runtime_validated': False,
            'limits': 'Tool versions, image bytes and namespace availability only. A READY result is not an ARM64 boot, actual page-size observation or a runtime/signing authorization.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sdk', type=Path, required=True)
    parser.add_argument('--archives', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = probe(args.sdk.resolve(), args.archives.resolve())
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'status': result['status'], 'blockers': result['blockers'], 'images_verified': len(result['images'])}))
    return int(bool(result['blockers']))


if __name__ == '__main__':
    raise SystemExit(main())
