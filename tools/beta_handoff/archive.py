#!/usr/bin/env python3
"""Create/verify private APK transport bundles; never upload, sign or extract blindly."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile
import stat
import os
from gate import precheck, require, sha256


def create(apk, expected, output):
    identity = precheck(apk, expected)
    receipt = dict(schema=1, kind='unsigned-beta-private-transport', **identity,
                   members={'payload.apk': expected}, signing_authorized=False)
    # Exclusive destination: cannot clobber a historical backup.
    with os.fdopen(os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'wb') as file:
        with zipfile.ZipFile(file, 'w', compression=zipfile.ZIP_STORED) as archive:
            archive.write(apk, 'payload.apk')
            archive.writestr('receipt.json', json.dumps(receipt, sort_keys=True) + '\n')
    return verify(output, sha256(output), expected)


def verify(bundle, expected_bundle, expected_apk):
    require(re.fullmatch('[0-9a-f]{64}', expected_bundle or ''), 'INVALID_BUNDLE_DIGEST')
    require(bundle.is_file() and not bundle.is_symlink(), 'BUNDLE_UNAVAILABLE_OR_UNSAFE')
    require(sha256(bundle) == expected_bundle, 'BUNDLE_SHA256_MISMATCH')
    with zipfile.ZipFile(bundle) as archive:
        require(sorted(archive.namelist()) == ['payload.apk', 'receipt.json'], 'BUNDLE_INVENTORY_MISMATCH')
        require(archive.getinfo('receipt.json').file_size <= 4096, 'RECEIPT_TOO_LARGE')
        receipt = json.loads(archive.read('receipt.json'))
        require(receipt.get('schema') == 1 and receipt.get('kind') == 'unsigned-beta-private-transport' and
                receipt.get('apk_sha256') == expected_apk and
                receipt.get('members') == {'payload.apk': expected_apk} and
                receipt.get('signing_authorized') is False, 'BUNDLE_RECEIPT_MISMATCH')
        with archive.open('payload.apk') as file:
            actual = hashlib.file_digest(file, 'sha256').hexdigest()
        require(actual == expected_apk and archive.getinfo('payload.apk').file_size == receipt.get('bytes'),
                'BUNDLE_APK_MISMATCH')
        require(archive.testzip() is None, 'BUNDLE_CRC_FAILED')
    return dict(bundle_sha256=expected_bundle, apk_sha256=actual,
                private_persistence_confirmed=False, remote_recovery_verified=False)


def inspect_existing(bundle, expected_bundle, expected_apk):
    """Read an existing Work2 archive without assuming its private receipt layout."""
    require(re.fullmatch('[0-9a-f]{64}', expected_bundle or ''), 'INVALID_BUNDLE_DIGEST')
    require(bundle.is_file() and not bundle.is_symlink() and sha256(bundle) == expected_bundle,
            'BUNDLE_SHA256_MISMATCH')
    require(re.fullmatch('[0-9a-f]{64}', expected_apk or ''), 'INVALID_APK_DIGEST')
    apks = []
    inventory = []
    with zipfile.ZipFile(bundle) as archive:
        names = archive.namelist()
        require(len(names) == len(set(names)) and len(names) <= 10000, 'BUNDLE_INVENTORY_MISMATCH')
        require(sum(x.file_size for x in archive.infolist()) <= 4 * 2**30, 'BUNDLE_EXPANSION_LIMIT')
        for info in archive.infolist():
            name = info.filename
            require(not name.startswith('/') and '\\' not in name and '..' not in name.split('/'),
                    'UNSAFE_BUNDLE_MEMBER')
            require(stat.S_IFMT(info.external_attr >> 16) not in
                    (stat.S_IFLNK, stat.S_IFCHR, stat.S_IFBLK), 'UNSAFE_BUNDLE_MEMBER_TYPE')
            if info.is_dir():
                continue
            with archive.open(info) as file:
                digest = hashlib.file_digest(file, 'sha256').hexdigest()
            inventory.append(dict(sha256=digest, bytes=info.file_size))
            if name.lower().endswith('.apk'):
                apks.append(digest)
    require(apks == [expected_apk], 'BUNDLE_APK_INVENTORY_OR_HASH_MISMATCH')
    return dict(bundle_sha256=expected_bundle, apk_sha256=expected_apk,
                members=len(names), file_inventory=inventory, all_member_bytes_read=True,
                remote_recovery_verified=False, private_persistence_confirmed=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['create', 'verify', 'inspect'])
    parser.add_argument('--apk', type=Path)
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--apk-sha256', required=True)
    parser.add_argument('--bundle-sha256')
    args = parser.parse_args()
    if args.mode == 'create':
        require(args.apk is not None, 'APK_REQUIRED')
        result = create(args.apk, args.apk_sha256, args.bundle)
    elif args.mode == 'verify':
        result = verify(args.bundle, args.bundle_sha256, args.apk_sha256)
    else:
        result = inspect_existing(args.bundle, args.bundle_sha256, args.apk_sha256)
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
