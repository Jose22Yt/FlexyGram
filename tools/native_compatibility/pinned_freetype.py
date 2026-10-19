"""Accept Work's pinned FreeType Git commit *or* its byte-verified git-archive TAR.

The tar was exported from the fixed FreeType commit during Work's authorized
recovery. It contains sources, not .git; never synthesize a revision or history.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess

EXPORT_NAME = 'freetype-source-86bc8a9.tar'
EXPORT_SHA256 = 'fdf98f8fc19df83d2640d7b6e40c5195f4a56b280c38582b04a5e84efd30add3'
PINNED_COMMIT = '86bc8a95056c97a810986434a3f268cbe67f2902'


def read_pinned_freetype(sources: Path, expected_commit: str) -> bytes:
    if expected_commit != PINNED_COMMIT:
        raise ValueError('FreeType commit has changed from the reviewed version')
    source_checkout = sources / 'freetype-git'
    if source_checkout.exists() or source_checkout.is_symlink():
        if source_checkout.is_symlink() or not source_checkout.is_dir() or not (source_checkout / '.git').exists():
            raise ValueError('Unsafe or incomplete FreeType checkout')
        actual = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=source_checkout,
                                         text=True, timeout=15).strip()
        if actual != expected_commit:
            raise ValueError('FreeType Git revision mismatch')
        return subprocess.check_output(['git', 'archive', '--format=tar', actual],
                                       cwd=source_checkout, timeout=120)
    export = sources / EXPORT_NAME
    if export.is_symlink() or not export.is_file():
        raise ValueError('Neither verified FreeType Git checkout nor pinned TAR is available')
    payload = export.read_bytes()
    if hashlib.sha256(payload).hexdigest() != EXPORT_SHA256:
        raise ValueError('FreeType source export SHA-256 mismatch')
    return payload
