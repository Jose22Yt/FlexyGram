#!/usr/bin/env python3
"""One-command, offline, fail-closed reproduction of the P0.4c native experiment.

Runs existing approved native builders twice, compares the outputs with the
historical reviewed hashes, and writes a private local receipt. Never signs,
installs, downloads, publishes, changes Gradle/locks or claims Android support.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile

REPO = Path(__file__).resolve().parents[2]
NAMES = ('libexslt.so', 'libfreetype.so', 'libxml2.so', 'libxslt.so')
EVIDENCE = REPO / 'docs/security-p04c/evidence-16k-experimental'
NATIVE = REPO / 'tools/native_compatibility'


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as src:
        for data in iter(lambda: src.read(1024 * 1024), b''):
            digest.update(data)
    return digest.hexdigest()


def load(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def expected() -> tuple[dict, dict]:
    abi = load(EVIDENCE / 'abi-report-final.json')
    wheels = load(EVIDENCE / 'wheel-reproducibility.json')['rebuilt']
    libraries = {row['library']: row['contract']['after_sha256'] for row in abi
                 if row['static_abi_pass'] is True and row['independent_build_identical'] is True}
    replacements = {row['filename']: row['sha256'] for row in wheels if row['rebuilt'] is True}
    if set(libraries) != set(NAMES) or len(replacements) != 3:
        raise ValueError('Reviewed ELF or wheel evidence is incomplete')
    return libraries, replacements


def check_inputs(sources: Path, wheelhouse: Path, ndk: Path, cmake: Path) -> int:
    # The preflight performs no builds, network access or filesystem mutation.
    from rebuild_candidates import verify_archive
    from wheelhouse import select, verified
    from experiment_recipe import BINUTILS

    for name, root in [('sources', sources), ('wheelhouse', wheelhouse), ('ndk', ndk)]:
        if root.is_symlink() or not root.is_dir():
            raise ValueError('Missing or unsafe ' + name + ' directory')
    if cmake.is_symlink() or not cmake.is_file():
        raise ValueError('Pinned CMake executable is missing or unsafe')
    version = (ndk / 'source.properties').read_text()
    if '27.2.12479018' not in version:
        raise ValueError('Expected NDK 27.2.12479018')
    clang = ndk / 'toolchains/llvm/prebuilt/linux-x86_64/bin/aarch64-linux-android24-clang'
    if not clang.is_file():
        raise ValueError('Pinned Android ARM64 compiler is missing')
    source_manifest = load(NATIVE / 'rebuild-sources.json')
    for row in source_manifest['archives'] + [BINUTILS]:
        verify_archive(sources / row['file'], row['sha256'])
    freetype = sources / 'freetype-git'
    if freetype.is_symlink() or not (freetype / '.git').exists():
        raise ValueError('Pinned FreeType Git checkout is missing')
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=freetype,
                                     text=True, timeout=10).strip()
    if commit != source_manifest['freetype_commit']:
        raise ValueError('Pinned FreeType revision differs')
    approved = select(load(REPO / 'TMessagesProj/python/wheels.lock.json'), ['arm64-v8a'])
    if len(approved) != 18:
        raise ValueError('Expected 18 locked ARM64 wheels')
    allowed = {row['filename'] for row in approved}
    if {p.name for p in wheelhouse.iterdir()} != allowed:
        raise ValueError('Original ARM64 wheelhouse has missing or extra files')
    for row in approved:
        if not verified(wheelhouse / row['filename'], row):
            raise ValueError('Missing original locked wheel: ' + row['filename'])
    return len(approved)


def check_outputs(folder: Path, approved: list[dict], library_pins: dict,
                  wheel_pins: dict) -> dict:
    libs = {}
    for name in NAMES:
        candidate = folder / ('freetype-build' if name == 'libfreetype.so' else 'prefix/lib') / name
        if candidate.is_symlink() or not candidate.is_file():
            raise ValueError('Missing source-rebuilt ELF ' + name)
        digest = sha(candidate)
        if digest != library_pins[name]:
            raise ValueError('Reviewed ELF SHA-256 mismatch: ' + name)
        libs[name] = digest
    manifest = load(folder / 'wheels-manifest.json')
    rows = manifest['wheels']
    names = {row['filename'] for row in rows}
    if len(rows) != 18 or len(names) != 18:
        raise ValueError('Wheel manifest must contain exactly 18 unique wheels')
    expected_names = set(wheel_pins) | {row['filename'] for row in approved if row['filename'] not in
                    {r['original_filename'] for r in rows if r['rebuilt']}}
    if names != expected_names:
        raise ValueError('Output wheel inventory differs from the pinned overlay')
    observed = {}
    for row in rows:
        path = folder / 'wheels' / row['filename']
        if path.is_symlink() or not path.is_file():
            raise ValueError('Missing wheel file')
        digest = sha(path)
        if digest != row['sha256']:
            raise ValueError('Wheel manifest checksum mismatch')
        if row['filename'] in wheel_pins:
            if row['rebuilt'] is not True or digest != wheel_pins[row['filename']]:
                raise ValueError('Reviewed rebuilt wheel SHA-256 mismatch')
        else:
            original = next((r for r in approved if r['filename'] == row['filename']), None)
            if original is None or row['rebuilt'] is not False or digest != original['sha256']:
                raise ValueError('Original wheel was modified')
        with zipfile.ZipFile(path) as archive:
            if archive.testzip() is not None:
                raise ValueError('Wheel CRC failure')
        observed[row['filename']] = digest
    if {p.name for p in (folder / 'wheels').iterdir()} != names:
        raise ValueError('Extra files in rebuilt wheelhouse')
    if manifest.get('android_runtime_validated') is not False:
        raise ValueError('Unsupported Android runtime assertion in manifest')
    return {'elf_sha256': libs, 'wheel_sha256': observed}


def execute(args) -> dict:
    sources, wheelhouse, ndk = [Path(getattr(args, name)).absolute() for name in
                                ('sources', 'wheelhouse', 'ndk')]
    cmake = Path(args.cmake).absolute()
    output = Path(args.output).absolute()
    if output.is_symlink() or output.exists():
        raise ValueError('Use a previously nonexistent private output directory')
    # Canonicalize ancestors too: a parent symlink must not redirect a fresh
    # output directory into the checkout, sources, wheelhouse or NDK.
    canonical_output = output.resolve()
    canonical_repo = REPO.resolve()
    input_roots = tuple(p.resolve() for p in (sources, wheelhouse, ndk))
    if (canonical_output == canonical_repo or canonical_repo in canonical_output.parents
            or any(canonical_output == p or canonical_output in p.parents
                   for p in input_roots)):
        raise ValueError('Output must be isolated from all inputs and repository')
    library_pins, wheel_pins = expected()
    check_inputs(sources, wheelhouse, ndk, cmake)
    approved = __import__('wheelhouse').select(
        load(REPO / 'TMessagesProj/python/wheels.lock.json'), ['arm64-v8a'])
    output.mkdir(parents=True)

    def run(stage: str, argv: list[str]) -> None:
        with (output / (stage + '.log')).open('w', encoding='utf-8') as log:
            subprocess.run(argv, cwd=REPO, stdout=log, stderr=subprocess.STDOUT, check=True)

    cmd = str(sys.executable)
    linker_dir = output / 'gnu'
    run('linker', [cmd, str(NATIVE / 'experiment_recipe.py'), '--build-linker',
                   '--sources', str(sources), '--output', str(linker_dir)])
    linker = linker_dir / 'build/ld/ld-new'
    if not linker.is_file():
        raise ValueError('GNU linker build did not create ld-new')
    reports = []
    for letter in ('a', 'b'):
        target = output / letter
        common = ['--sources', str(sources), '--output', str(target), '--ndk', str(ndk),
                  '--cmake', str(cmake), '--wheelhouse', str(wheelhouse)]
        run(letter + '-candidates', [cmd, str(NATIVE / 'rebuild_candidates.py'), *common])
        run(letter + '-final', [cmd, str(NATIVE / 'experiment_recipe.py'), *common,
                                '--linker', str(linker)])
        reports.append(check_outputs(target, approved, library_pins, wheel_pins))
    if reports[0] != reports[1]:
        raise ValueError('Independent A/B native outputs differ')
    receipt = {'status': 'REPRODUCIBLE_STATIC_OUTPUTS_ONLY',
               'experimental_only': True, 'android_runtime_validated': False,
               'apk_built': False, 'apk_signed': False, 'merged': False,
               'runs': 2, 'input_original_wheels': 18, **reports[0]}
    (output / 'reproduction-receipt.json').write_text(json.dumps(receipt, indent=2,
                                                          sort_keys=True) + '\n')
    return receipt


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--sources', required=True)
    p.add_argument('--wheelhouse', required=True)
    p.add_argument('--ndk', required=True)
    p.add_argument('--cmake', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--verify-inputs-only', action='store_true')
    args = p.parse_args(argv)
    try:
        if args.verify_inputs_only:
            count = check_inputs(Path(args.sources), Path(args.wheelhouse),
                                 Path(args.ndk), Path(args.cmake))
            report = {'status': 'INPUTS_VERIFIED_ONLY', 'original_wheels': count,
                      'android_runtime_validated': False}
        else:
            report = execute(args)
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    except (OSError, ValueError, subprocess.CalledProcessError, KeyError, zipfile.BadZipFile) as exc:
        print(json.dumps({'status': 'BLOCKED', 'error_class': type(exc).__name__,
                          'android_runtime_validated': False}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
