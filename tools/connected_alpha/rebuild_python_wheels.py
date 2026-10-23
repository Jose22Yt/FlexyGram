#!/usr/bin/env python3
"""Rebuild only legacy third-party wheels using the pinned Chaquopy recipes."""
import argparse
import base64
import csv
import hashlib
import io
import json
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import zipfile
from pathlib import Path

import yaml
from verify_apk import inspect_archive

CHAQUOPY = 'd47b4a1e1817b4590b9c56dfd4ee5fcfdd6f0cbd'
SOURCES = {
    'chaquopy-libxml2': ('2.9.8',
        'https://download.gnome.org/sources/libxml2/2.9/libxml2-2.9.8.tar.xz',
        'dcca21d624bbbe094fcc104e1f15f2eacfb65aecd0e38ed220aeca56b62c81e2'),
    'chaquopy-libxslt': ('1.1.32',
        'https://download.gnome.org/sources/libxslt/1.1/libxslt-1.1.32.tar.xz',
        'b7da90eaa6b0dae9e9a3769e29a757342eef0edb9a7b431424814375414422af'),
    'chaquopy-freetype': ('2.9.1',
        'https://download.savannah.gnu.org/releases/freetype/freetype-2.9.1.tar.gz',
        'ec391504e55498adceb30baceebd147a6e963f636eb617424bcfc47a169898ce'),
}
DEBUGPY_SHA256 = 'a9e9d3550e15ca479c59333e90845029190531f0cacfedab3b815a57bd913947'
ATTACH = 'debugpy/_vendored/pydevd/pydevd_attach_to_process/'
HOST_HELPERS = {ATTACH + name for name in (
    'attach.dylib', 'attach_amd64.dll', 'attach_linux_amd64.so', 'attach_x86.dll',
    'inject_dll_amd64.exe', 'inject_dll_x86.exe',
    'run_code_on_dllmain_amd64.dll', 'run_code_on_dllmain_x86.dll')}


def checked_bytes(data, expected):
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError('Source SHA-256 mismatch')
    return data


def android_debugpy(source, destination):
    """Keep Python network debugging; remove only fixed desktop PID-attach binaries."""
    checked_bytes(source.read_bytes(), DEBUGPY_SHA256)
    with zipfile.ZipFile(source) as wheel:
        files = {name: wheel.read(name) for name in wheel.namelist() if not name.endswith('/')}
    if not HOST_HELPERS <= files.keys() or 'debugpy/server/api.py' not in files:
        raise ValueError('Unexpected debugpy wheel layout')
    for name in HOST_HELPERS:
        del files[name]
    info = 'debugpy-1.8.22.dist-info/'
    wheel_metadata = files[info+'WHEEL'].decode()
    files[info+'WHEEL'] = (wheel_metadata.rstrip() + '\nBuild: 100\n').encode()
    del files[info+'RECORD']
    record = io.StringIO(newline='')
    writer = csv.writer(record, lineterminator='\n')
    for name, data in sorted(files.items()):
        digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b'=').decode()
        writer.writerow((name, 'sha256='+digest, len(data)))
    writer.writerow((info+'RECORD', '', ''))
    files[info+'RECORD'] = record.getvalue().encode()
    with zipfile.ZipFile(destination, 'w', zipfile.ZIP_DEFLATED) as wheel:
        for name, data in sorted(files.items()):
            wheel.writestr(name, data)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--chaquopy', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root, output = args.chaquopy.resolve(), args.output.resolve()
    actual = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
    if actual != CHAQUOPY or 'max-page-size=16384' not in (root/'target/android-env.sh').read_text():
        raise ValueError('Pinned Chaquopy recipes or 16 KB linker policy changed')
    output.mkdir(parents=True, exist_ok=False)
    pypi = root/'server/pypi'
    evidence = {}
    # The original compiler wrapper deliberately rejects include/library paths
    # outside its checkout. Keep temporary recipes inside that trusted tree.
    with tempfile.TemporaryDirectory(prefix='alpha-wheel-sources-', dir=root) as tmp:
        work = Path(tmp)
        # libxml2 must be built before libxslt, whose recipe consumes its wheel.
        for name, (version, url, digest) in SOURCES.items():
            recipe = work/name
            shutil.copytree(pypi/'packages'/name, recipe, ignore=shutil.ignore_patterns('build'))
            metadata = yaml.safe_load((recipe/'meta.yaml').read_text())
            if metadata['package'] != {'name': name, 'version': version}:
                raise ValueError('Unexpected upstream package identity')
            data = checked_bytes(urllib.request.urlopen(url, timeout=60).read(), digest)
            source = work/(name+'-source')
            source.mkdir()
            with tarfile.open(fileobj=io.BytesIO(data), mode='r:*') as archive:
                archive.extractall(source, filter='data')
            directories = list(source.iterdir())
            if len(directories) != 1 or not directories[0].is_dir():
                raise ValueError('Unexpected source archive layout')
            metadata['source'] = {'path': str(directories[0])}
            metadata.setdefault('build', {})['number'] = 100
            (recipe/'meta.yaml').write_text(yaml.safe_dump(metadata, sort_keys=False))
            subprocess.run([sys.executable, str(pypi/'build-wheel.py'), '--abi', 'arm64-v8a',
                            '--api-level', '24', str(recipe)], cwd=pypi, check=True)
            candidates = list((pypi/'dist'/name).glob('*-100-py3-none-android_24_arm64_v8a.whl'))
            if len(candidates) != 1:
                raise ValueError('Expected exactly one rebuilt ARM64 wheel')
            with zipfile.ZipFile(candidates[0]) as wheel:
                if not inspect_archive(wheel):
                    raise ValueError('Rebuilt wheel contains no native library')
            shutil.copy2(candidates[0], output/candidates[0].name)
            evidence[name] = {'source_sha256': digest, 'version': version}
        subprocess.run([sys.executable, '-m', 'pip', 'download', '--index-url',
                        'https://pypi.org/simple', '--no-deps', '--only-binary=:all:',
                        '--dest', str(work), 'debugpy==1.8.22'], check=True)
        android_debugpy(work/'debugpy-1.8.22-py2.py3-none-any.whl',
                        output/'debugpy-1.8.22-100-py2.py3-none-any.whl')
    evidence['debugpy_removed_desktop_helpers'] = sorted(HOST_HELPERS)
    evidence['wheel_sha256'] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in output.glob('*.whl')}
    (output/'provenance.json').write_text(json.dumps(evidence, indent=2)+'\n')


if __name__ == '__main__':
    main()
