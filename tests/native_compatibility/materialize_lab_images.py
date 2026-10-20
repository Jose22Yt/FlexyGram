"""Materialize pinned official image bytes sparsely; no boot, ADB or APK operations."""
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import json
import os
import stat
import zipfile
from lab_host_preflight import IMAGES, require, verify_image

ROOT = Path(__file__).resolve().parents[2]


def safe_relative(name):
    path = PurePosixPath(name)
    require(not path.is_absolute() and '\\' not in name and '..' not in path.parts and
            len(path.parts) >= 2 and path.parts[0] == 'arm64-v8a', 'Unsafe image path')
    return Path(*path.parts[1:])


def sparse_copy(source, destination, expected_size):
    digest = hashlib.sha256()
    size = 0
    with destination.open('xb') as output:
        for block in iter(lambda: source.read(65536), b''):
            digest.update(block)
            size += len(block)
            if block.count(0) == len(block): output.seek(len(block), os.SEEK_CUR)
            else: output.write(block)
        output.truncate(size)
    require(size == expected_size, 'Image length mismatch')
    readback = hashlib.sha256()
    with destination.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''): readback.update(block)
    require(readback.hexdigest() == digest.hexdigest(), 'Sparse copy changed bytes')
    return {'bytes': size, 'allocated_bytes': destination.stat().st_blocks*512,
            'sha256': digest.hexdigest(), 'readback_verified': True}


def materialize(archive, profile, destination):
    verify_image(archive, profile)
    destination = destination.absolute()
    require(not destination.exists() and not destination.is_symlink() and
            ROOT not in destination.resolve().parents and
            not any(p.is_symlink() for p in destination.parents), 'New private SDK image directory required')
    destination.mkdir(parents=True, mode=0o700)
    rows = {}
    with zipfile.ZipFile(archive) as source:
        for member in source.infolist():
            if member.is_dir(): continue
            relative = safe_relative(member.filename)
            require(not stat.S_ISLNK(member.external_attr >> 16), 'Symlink image rejected')
            target = destination/relative
            target.parent.mkdir(parents=True, exist_ok=True)
            with source.open(member) as stream: rows[str(relative)] = sparse_copy(stream, target, member.file_size)
    return {'profile': profile, 'archive_sha256': IMAGES[profile]['sha256'],
            'files': rows, 'booted': False, 'apk_installed': False,
            'status': 'IMAGE_BYTES_MATERIALIZED_NOT_ANDROID_VALIDATED'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--profile', choices=IMAGES, required=True)
    parser.add_argument('--destination', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = materialize(args.archive, args.profile, args.destination)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'status': result['status'], 'files': len(result['files']), 'booted': False}))


if __name__ == '__main__':
    main()
