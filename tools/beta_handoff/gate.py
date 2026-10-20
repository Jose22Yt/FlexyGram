#!/usr/bin/env python3
"""One unsigned beta check; delegates ELF/policy/scanner checks to PR23. No ADB."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import shutil
from pathlib import Path
import re
import stat
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]


def require(condition, code):
    if not condition:
        raise ValueError(code)


def sha256(path):
    with path.open('rb') as file:
        return hashlib.file_digest(file, 'sha256').hexdigest()


def precheck(apk, expected_sha256):
    require(re.fullmatch('[0-9a-f]{64}', expected_sha256 or ''), 'INVALID_EXPECTED_SHA256')
    require(apk.is_file() and not apk.is_symlink(), 'APK_UNAVAILABLE_OR_UNSAFE')
    digest = sha256(apk)
    require(digest == expected_sha256, 'APK_SHA256_MISMATCH')
    required = {'AndroidManifest.xml', 'resources.arsc', 'classes.dex',
                'lib/arm64-v8a/libtmessages.49.so',
                'assets/chaquopy/requirements-common.imy',
                'assets/chaquopy/stdlib-arm64-v8a.imy'}
    with zipfile.ZipFile(apk) as archive:
        names = archive.namelist()
        require(len(names) == len(set(names)), 'DUPLICATE_APK_MEMBER')
        require(sum(x.file_size for x in archive.infolist()) <= 2**31, 'APK_EXPANSION_LIMIT')
        for item in archive.infolist():
            require(not item.filename.startswith('/') and '\\' not in item.filename and
                    '..' not in item.filename.split('/'), 'UNSAFE_APK_MEMBER')
            require(stat.S_IFMT(item.external_attr >> 16) not in
                    (stat.S_IFLNK, stat.S_IFCHR, stat.S_IFBLK), 'UNSAFE_APK_MEMBER_TYPE')
        require(required <= set(names), 'MISSING_REQUIRED_APK_RESOURCE')
        require(all(archive.getinfo(n).file_size > 0 for n in required), 'EMPTY_REQUIRED_APK_RESOURCE')
        require(not any(re.fullmatch(r'META-INF/[^/]+\.(RSA|DSA|EC|SF)', n, re.I) for n in names), 'APK_JAR_SIGNATURE_NOT_AUTHORIZED')
        with apk.open('rb') as file:
            file.seek(max(0, archive.start_dir - 16))
            require(file.read(16) != b'APK Sig Block 42', 'APK_SIGNATURE_BLOCK_NOT_AUTHORIZED')
        require(archive.testzip() is None, 'APK_CRC_FAILED')
    return {'apk_sha256': digest, 'bytes': apk.stat().st_size}


def run(args):
    # Hash/ZIP precede tools: never waste a full native review on the wrong build.
    identity = precheck(args.apk, args.sha256)
    sys.path.insert(0, str(ROOT / 'tools/beta_development'))
    import review_apk
    badging = review_apk.command([args.build_tools / 'aapt2', 'dump', 'badging', args.apk])
    match = re.search(r"(?m)^package: name='([^']+)' versionCode='([^']+)' versionName='([^']+)'", badging)
    require(match is not None and match.groups() ==
            (review_apk.PACKAGE, args.version_code, args.version_name), 'BETA_PACKAGE_OR_VERSION_MISMATCH')
    result = review_apk.review(args)
    require(sha256(args.apk) == identity['apk_sha256'], 'APK_CHANGED_DURING_REVIEW')
    result.update(identity, version_code=args.version_code, version_name=args.version_name,
                  input_bytes_checked=True, signing_authorized=False, installation_authorized=False,
                  limits='Host static checks only. BuildConfig classes are separate build inputs; Android loading and runtime policy remain untested.')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('apk', 'classes', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    sdk = Path(os.environ.get('ANDROID_SDK_ROOT', os.environ.get('ANDROID_HOME', '/unavailable-sdk')))
    parser.add_argument('--build-tools', type=Path, default=sdk / 'build-tools/36.0.0')
    parser.add_argument('--ndk', type=Path, default=sdk / 'ndk/27.2.12479018')
    java = Path(os.environ['JAVA_HOME']) / 'bin/javap' if os.environ.get('JAVA_HOME') else Path(shutil.which('javap') or '/unavailable-javap')
    parser.add_argument('--javap', type=Path, default=java)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--version-code', default='1261')
    parser.add_argument('--version-name', default='13.0.2')
    args = parser.parse_args()
    if args.output.resolve() in {p.resolve() for p in (args.apk, args.classes, args.javap)}:
        print(json.dumps({'status': 'BLOCKED', 'code': 'OUTPUT_OVERLAPS_INPUT'}))
        return 1
    try:
        result = run(args)
    except Exception as error:
        # Includes missing optional parsers and malformed ELF; every failed review closes the gate.
        # No traceback or subprocess outputs in public reports.
        blocked = {'status': 'BLOCKED', 'error_type': type(error).__name__,
                   'code': str(error) if type(error) is ValueError and re.fullmatch('[A-Z][A-Z0-9_]{1,100}', str(error)) else 'STATIC_REVIEW_FAILED',
                   'android_executed': False, 'distribution_allowed': False}
        args.output.write_text(json.dumps(blocked, indent=2) + '\n')
        print(json.dumps(blocked))
        return 1
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'status': result['status'], 'apk_sha256': result['apk_sha256'],
                      'android_executed': False, 'distribution_allowed': False}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
