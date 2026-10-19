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
    if (len(abi) != len(libraries) or len(wheels) != len(replacements) or
            set(libraries) != set(NAMES) or len(replacements) != 3):
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
    # Work's private recovery bundle contains the SHA-pinned git-archive TAR.
    # That TAR and the real fixed Git commit are equivalent approved inputs.
    from pinned_freetype import read_pinned_freetype
    read_pinned_freetype(sources, source_manifest['freetype_commit'])
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
                  wheel_pins: dict, replacement_sources: dict | None = None) -> dict:
    # Every approved input must map to precisely one output. A hash match alone
    # is insufficient if the manifest misidentifies which package was replaced.
    approved_map = {row['filename']: row['sha256'] for row in approved}
    if len(approved) != 18 or len(approved_map) != 18 or len(wheel_pins) != 3:
        raise ValueError('Invalid original or replacement wheel inventory')
    if replacement_sources is not None and set(replacement_sources) != set(wheel_pins):
        raise ValueError('Reviewed replacement mapping is incomplete')

    def safe_file(path: Path) -> bool:
        # Reject symlinks in ancestors too: a regular ELF reached through
        # prefix/lib -> /external is still outside the requested build.
        try:
            relative = path.relative_to(folder)
        except ValueError:
            return False
        current = folder
        if current.is_symlink():
            return False
        for part in relative.parts:
            current = current / part
            if current.is_symlink():
                return False
        return path.is_file()

    libs = {}
    for name in NAMES:
        candidate = folder / ('freetype-build' if name == 'libfreetype.so' else 'prefix/lib') / name
        if not safe_file(candidate):
            raise ValueError('Missing source-rebuilt ELF ' + name)
        digest = sha(candidate)
        if digest != library_pins[name]:
            raise ValueError('Reviewed ELF SHA-256 mismatch: ' + name)
        libs[name] = digest
    wheels_dir = folder / 'wheels'
    if wheels_dir.is_symlink() or not wheels_dir.is_dir():
        raise ValueError('Unsafe rebuilt wheel directory')
    if not safe_file(folder / 'wheels-manifest.json'):
        raise ValueError('Unsafe wheel manifest')
    manifest = load(folder / 'wheels-manifest.json')
    rows = manifest['wheels']
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ValueError('Malformed wheel manifest')
    try:
        names = {row['filename'] for row in rows}
        original_names = [row['original_filename'] for row in rows]
        rebuilt = [row for row in rows if row['rebuilt'] is True]
        copied = [row for row in rows if row['rebuilt'] is False]
    except (KeyError, TypeError):
        raise ValueError('Malformed wheel manifest') from None
    if len(rows) != 18 or len(names) != 18 or len(set(original_names)) != 18:
        raise ValueError('Wheel manifest must contain exactly 18 unique wheels and origins')
    if (set(original_names) != set(approved_map) or len(rebuilt) != 3 or
            {row['filename'] for row in rebuilt} != set(wheel_pins) or
            len(copied) != 15):
        raise ValueError('Original-to-rebuilt wheel mapping is incomplete')
    for row in rows:
        name = row['filename']
        source = row['original_filename']
        if (not isinstance(name, str) or '/' in name or '\\' in name or
                not isinstance(source, str) or source not in approved_map):
            raise ValueError('Unsafe wheel manifest name or origin')
        if row['rebuilt'] is True:
            if name not in wheel_pins or source == name:
                raise ValueError('Invalid rebuilt wheel origin')
            if (replacement_sources is not None and
                    replacement_sources[name] != source):
                raise ValueError('Reviewed rebuilt wheel origin mismatch')
        elif row['rebuilt'] is False:
            if name != source or name in wheel_pins:
                raise ValueError('Unmodified wheel origin mismatch')
        else:
            raise ValueError('Wheel rebuilt flag must be boolean')
    expected_names = (set(approved_map) -
                      {row['original_filename'] for row in rebuilt}) | set(wheel_pins)
    if names != expected_names:
        raise ValueError('Output wheel inventory differs from the pinned overlay')
    observed = {}
    for row in rows:
        path = folder / 'wheels' / row['filename']
        if not safe_file(path):
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
            or any(canonical_output == p or p in canonical_output.parents
                   for p in input_roots)):
        raise ValueError('Output must be isolated from all inputs and repository')
    library_pins, wheel_pins = expected()
    check_inputs(sources, wheelhouse, ndk, cmake)
    approved = __import__('wheelhouse').select(
        load(REPO / 'TMessagesProj/python/wheels.lock.json'), ['arm64-v8a'])
    reviewed = load(EVIDENCE / 'wheel-reproducibility.json')['rebuilt']
    if len(reviewed) != 3 or {row['filename'] for row in reviewed} != set(wheel_pins):
        raise ValueError('Reviewed replacement wheel origins are incomplete')
    replacement_sources = {row['filename']: row['original_filename'] for row in reviewed}
    approved_pins = {row['filename']: row['sha256'] for row in approved}
    if any(approved_pins.get(row['original_filename']) != row['original_sha256']
           for row in reviewed):
        raise ValueError('Reviewed original wheel SHA-256 mismatch')
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
        reports.append(check_outputs(target, approved, library_pins, wheel_pins,
                                     replacement_sources))
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
