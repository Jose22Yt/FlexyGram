#!/usr/bin/env python3
"""Validate and privately stage Work's pinned recovered-original-inputs ZIP.

Fully offline. Does not build software, fetch sources, handle signing keys,
install APKs, or write to the source checkout. Only originally verified inputs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import tempfile
import zipfile

REPO = Path(__file__).resolve().parents[2]
MANIFEST_PATH = REPO / 'docs/security-p04c/evidence-lab-integration/recovery-bundle-manifest.json'
EXPECTED_BUNDLE_SHA256 = '17325285036532db37a4ed09600f5a62a61056de6a2c59bec1d17da550ea0d82'
CHUNK = 1024 * 1024


def digest(path: Path) -> str:
    d = hashlib.sha256()
    with path.open('rb') as file:
        for block in iter(lambda: file.read(CHUNK), b''):
            d.update(block)
    return d.hexdigest()


def validate_manifest(data: object) -> dict:
    if not isinstance(data, dict) or not isinstance(data.get('files'), dict):
        raise ValueError('Invalid recovery manifest')
    files = data['files']
    if not files or len(files) != len(set(files)):
        raise ValueError('No unique manifest entries')
    for name, row in files.items():
        if not isinstance(name, str) or not name or '\\x00' in name:
            raise ValueError('Unsafe manifest entry')
        path = Path(name)
        if (path.is_absolute() or '..' in path.parts or name in ('.', '..') or
                any(part in ('', '.') for part in name.split('/')) or
                '\\' in name or len(path.parts) < 1 or path.as_posix() != name or
                not isinstance(row, dict) or not isinstance(row.get('bytes'), int) or
                isinstance(row['bytes'], bool) or row['bytes'] < 0 or
                not isinstance(row.get('sha256'), str) or len(row['sha256']) != 64 or
                any(c not in '0123456789abcdef' for c in row['sha256'])):
            raise ValueError('Unsafe manifest entry')
        if not name.startswith(('sources/', 'original-wheels/')) and name not in (
                'wheel-recovery.json', 'source-recovery.json'):
            raise ValueError('Unexpected manifest member type')
    return files


def inspect_archive(path: Path, manifest: dict, expected_sha: str) -> dict:
    if path.is_symlink() or not path.is_file() or digest(path) != expected_sha:
        raise ValueError('Recovered ZIP is absent, unsafe or has unexpected SHA-256')
    entries = validate_manifest(manifest)
    with zipfile.ZipFile(path) as archive:
        file_info = {}
        seen = set()
        for member in archive.infolist():
            name = member.filename
            if not name or '\\x00' in name or any(part in ('', '.') for part in name.rstrip('/').split('/')):
                raise ValueError('Unsafe ZIP member path')
            if name in seen:
                raise ValueError('Duplicate ZIP member')
            seen.add(name)
            if name.startswith('/') or '\\' in name or '..' in Path(name).parts:
                raise ValueError('Unsafe ZIP member path')
            mode = stat.S_IFMT(member.external_attr >> 16)
            if mode not in (0, stat.S_IFREG, stat.S_IFDIR):
                raise ValueError('ZIP contains a nonregular member')
            if member.flag_bits & 1:
                raise ValueError('Encrypted ZIP members are unsupported')
            if member.is_dir():
                if mode not in (0, stat.S_IFDIR) or not any(
                        key.startswith(name) for key in entries):
                    raise ValueError('Unexpected ZIP directory')
                continue
            if mode == stat.S_IFDIR or member.compress_type not in (
                    zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
                raise ValueError('ZIP contains an unsupported file')
            if name not in entries or member.file_size != entries[name]['bytes']:
                raise ValueError('Unexpected file or size in recovered ZIP')
            file_info[name] = member
        if set(file_info) != set(entries):
            raise ValueError('Recovered ZIP has missing manifest members')
        # A file cannot also serve as an ancestor directory for another member.
        # Reject before extraction, even if a separately pinned manifest requested it.
        for name in file_info:
            if any('/'.join(Path(name).parts[:n]) in file_info
                   for n in range(1, len(Path(name).parts))):
                raise ValueError('ZIP file and directory path collision')
        # Stream the *uncompressed* bytes with an upper bound fixed by the manifest.
        for name, info in sorted(file_info.items()):
            total = 0
            check = hashlib.sha256()
            with archive.open(info, 'r') as source:
                while data := source.read(CHUNK):
                    total += len(data)
                    if total > entries[name]['bytes']:
                        raise ValueError('ZIP member exceeded approved size')
                    check.update(data)
            if total != entries[name]['bytes'] or check.hexdigest() != entries[name]['sha256']:
                raise ValueError('Recovered ZIP member digest mismatch')
    return {'status': 'VERIFIED_ORIGINAL_INPUTS_ONLY', 'bundle_sha256': expected_sha,
            'verified_files': len(entries), 'original_wheels': sum(
                name.startswith('original-wheels/') for name in entries),
            'source_archives': sum(name.startswith('sources/') for name in entries),
            'experimental_wheels_present': False, 'signing_key_present': False}


def stage(archive: Path, destination: Path, manifest: dict,
          expected_sha: str = EXPECTED_BUNDLE_SHA256) -> dict:
    # Verify before *any* output is created. Never alter checkout or originals.
    report = inspect_archive(archive, manifest, expected_sha)
    root = destination.absolute()
    checked = root.resolve()
    source_root = REPO.resolve()
    if (root.exists() or root.is_symlink() or checked == source_root or
            source_root in checked.parents):
        raise ValueError('Destination must be new and outside checkout')
    root.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix='.flexygram-stage-', dir=root.parent))
    try:
        with zipfile.ZipFile(archive) as zip_input:
            for name in sorted(manifest['files']):
                target = temporary / name
                target.parent.mkdir(parents=True, exist_ok=True)
                with zip_input.open(name) as inp, target.open('xb') as out:
                    shutil.copyfileobj(inp, out, CHUNK)
                os.chmod(target, 0o600)
                if digest(target) != manifest['files'][name]['sha256']:
                    raise ValueError('Extracted private member changed')
        report['freetype_git_checkout_prepared'] = False
        report['note'] = ('FreeType tar is a verified source export, not a Git checkout. '
                          'The experimental recipe accepts its pinned TAR without '
                          'fabricating Git history; no private signing keys are included.')
        (temporary / 'stage-receipt.json').write_text(json.dumps(report, indent=2) + '\n')
        os.chmod(temporary / 'stage-receipt.json', 0o600)
        if root.exists():
            raise ValueError('Destination was created concurrently')
        temporary.rename(root)
    except Exception:
        shutil.rmtree(temporary)
        raise
    return report


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bundle', required=True, type=Path)
    p.add_argument('--output', type=Path)
    p.add_argument('--verify-only', action='store_true')
    args = p.parse_args(argv)
    if (not args.verify_only and args.output is None) or (
            args.verify_only and args.output is not None):
        p.error('--output is required to stage; omit --output with --verify-only')
    try:
        manifest = json.loads(MANIFEST_PATH.read_text())
        result = (inspect_archive(args.bundle, manifest, EXPECTED_BUNDLE_SHA256)
                  if args.verify_only else stage(args.bundle, args.output, manifest))
        print(json.dumps(result, sort_keys=True))
        return 0
    except (OSError, ValueError, zipfile.BadZipFile, RuntimeError) as exc:
        print(json.dumps({'status': 'BLOCKED', 'error_class': type(exc).__name__,
                          'inputs_staged': False}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
