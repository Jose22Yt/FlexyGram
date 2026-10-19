#!/usr/bin/env python3
"""Read-only FlexyGram Diagnostic ARM64 emulator and APK preflight.

Never installs/starts an APK, changes settings, connects to a service, or pulls
logs from a device. Successful checks are NOT Android runtime certification or final lab acceptance.
Python standard library only; designed to run offline in an authorized lab.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import zipfile

PACKAGE = 'io.github.jose22yt.flexygram.diagnostic'
MODES = {'api24': (24, 4096), '16k': (35, 16384)}
SHA256 = re.compile(r'^[a-fA-F0-9]{64}$')
EMULATOR = re.compile(r'^emulator-[0-9]+$')
MAX_LOG_BYTES = 16 * 1024 * 1024
LOG_PATTERNS = {
    'native_loader_error': re.compile(r'dlopen failed|cannot locate symbol|UnsatisfiedLinkError|linker.*error', re.I),
    'python_import_error': re.compile(r'ImportError|ModuleNotFoundError|No module named|chaquopy.*(?:error|exception)', re.I),
    'crash_or_anr': re.compile(r'FATAL EXCEPTION|\bANR in\b|SIGSEGV|SIGABRT|Fatal signal', re.I),
    'memory_failure': re.compile(r'OutOfMemoryError|bad_alloc|Cannot allocate memory', re.I),
}


class Blocked(ValueError):
    """Expected fail-closed outcome with no sensitive command output."""


def command(argv: list[str]) -> str:
    """Run only an explicitly assembled read-only command; no shell.

    The caller does not include subprocess stdout/stderr in errors or reports.
    """
    try:
        result = subprocess.run(argv, capture_output=True, text=True, errors='replace',
                                timeout=12, check=False, shell=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise Blocked('Command unavailable or timed out') from exc
    if result.returncode != 0:
        raise Blocked('Required read-only command failed')
    return result.stdout.strip()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def read_log_counts(path: Path) -> dict:
    """Categorize an existing *local* log. Never emit log text or user data."""
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_LOG_BYTES:
        raise Blocked('Log file must be a regular local file of at most 16 MiB')
    counts = {k: 0 for k in LOG_PATTERNS}
    lines = 0
    with path.open('r', encoding='utf-8', errors='replace') as fh:
        for line in fh:
            lines += 1
            for category, pattern in LOG_PATTERNS.items():
                if pattern.search(line):
                    counts[category] += 1
    return {'lines_examined': lines, 'category_counts': counts,
            'raw_log_included': False, 'note': 'Only indicators, not a diagnosis or evidence of no crashes'}


def emulator_probe(serial: str, profile: str, run=command) -> dict:
    if profile not in MODES:
        raise Blocked('Unsupported laboratory profile')
    # Avoid ever issuing a command to a physical/personal phone from this tool.
    if not EMULATOR.fullmatch(serial):
        raise Blocked('Only explicit emulator-NNNN serials are accepted')
    out = run(['adb', 'devices', '-l'])
    states: dict[str, str] = {}
    for line in out.splitlines():
        fields = line.split()
        if len(fields) >= 2 and fields[0] != 'List':
            states[fields[0]] = fields[1]
    if states.get(serial) != 'device':
        raise Blocked('Selected emulator is missing, offline, or unauthorized')

    def getprop(prop: str) -> str:
        return run(['adb', '-s', serial, 'shell', 'getprop', prop]).strip()

    # Emulator-* alone does not prove this is an emulator: inspect its QEMU properties.
    if getprop('ro.kernel.qemu') != '1' and getprop('ro.boot.qemu') != '1':
        raise Blocked('Emulator identity could not be verified')
    # A reported arm64-v8a *secondary* ABI is not proof of an ARM64 kernel.
    # Never accept an x86 guest using native bridge or a translated ABI.
    kernel_arch = run(['adb', '-s', serial, 'shell', 'uname', '-m']).strip()
    primary_abi = getprop('ro.product.cpu.abi')
    native_bridge = getprop('ro.dalvik.vm.native.bridge').strip().lower()
    native_bridge_exec = getprop('ro.enable.native.bridge.exec').strip().lower()
    sdk = getprop('ro.build.version.sdk')
    abilist = getprop('ro.product.cpu.abilist')
    page = run(['adb', '-s', serial, 'shell', 'getconf', 'PAGE_SIZE']).strip()
    if kernel_arch not in ('aarch64', 'arm64'):
        raise Blocked('Guest kernel is not ARM64')
    if primary_abi != 'arm64-v8a' or abilist.split(',')[0] != 'arm64-v8a':
        raise Blocked('Primary Android ABI is not arm64-v8a')
    if native_bridge not in ('', '0', 'false') or native_bridge_exec not in ('', '0', 'false'):
        raise Blocked('Native bridge must be disabled for the ARM64 laboratory')
    if not sdk.isdecimal() or not page.isdecimal():
        raise Blocked('Android API or page-size probe was not numeric')
    api = int(sdk)
    page_bytes = int(page)
    expected_min_api, expected_page = MODES[profile]
    if (profile == 'api24' and api != 24) or (profile == '16k' and api < expected_min_api):
        raise Blocked('Android API does not match selected lab profile')
    if 'arm64-v8a' not in abilist.split(','):
        raise Blocked('Target is not advertising arm64-v8a')
    if page_bytes != expected_page:
        raise Blocked('Device page size does not match lab profile')

    # Detect an existing Diagnostic package before any later separate install procedure.
    # This utility NEVER calls install. A non-empty pm path requires human review.
    prior = run(['adb', '-s', serial, 'shell', 'pm', 'path', PACKAGE]).strip()
    if prior:
        raise Blocked('Diagnostic package already exists on this emulator; stop and review')
    return {
        'target_id_sha256_prefix': hashlib.sha256(serial.encode()).hexdigest()[:12],
        'emulator_property_verified': True, 'android_api': api,
        'kernel_arm64_verified': True, 'primary_arm64_v8a_verified': True,
        'native_bridge_disabled': True,
        'advertises_arm64_v8a': True, 'page_size_bytes': page_bytes,
        'diagnostic_preinstalled': False, 'profile': profile,
    }


def apk_probe(path: Path, expected_digest: str, expected_cert: str, run=command) -> dict:
    if not SHA256.fullmatch(expected_digest) or not SHA256.fullmatch(expected_cert):
        raise Blocked('APK and signer certificate SHA-256 pins must contain 64 hex characters')
    if path.is_symlink() or path.suffix.lower() != '.apk' or not path.is_file():
        raise Blocked('An existing regular .apk (not a symlink) is required')
    if sha256_file(path).lower() != expected_digest.lower():
        raise Blocked('APK SHA-256 does not match reviewed evidence')
    if not zipfile.is_zipfile(path):
        raise Blocked('APK is not a valid ZIP container')
    with zipfile.ZipFile(path, 'r') as archive:
        if 'AndroidManifest.xml' not in archive.namelist():
            raise Blocked('APK AndroidManifest.xml is missing')
        if archive.testzip() is not None:
            raise Blocked('APK has a corrupt ZIP entry')

    badging = run(['aapt2', 'dump', 'badging', str(path)])
    match = re.search(r"(?m)^package:\s+name='([^']+)'", badging)
    if match is None or match.group(1) != PACKAGE:
        raise Blocked('APK applicationId is not the approved Diagnostic package')
    # Check the binary manifest's permissions independently from its badging.
    perms = run(['aapt2', 'dump', 'permissions', str(path)])
    if re.search(r'\bandroid\.permission\.INTERNET\b', badging + '\n' + perms):
        raise Blocked('Diagnostic APK unexpectedly requests INTERNET')
    signer = run(['apksigner', 'verify', '--verbose', '--print-certs', str(path)])
    match = re.search(r'(?im)^Signer #1 certificate SHA-256 digest:\s*([0-9a-f]{64})\s*$', signer)
    if match is None or match.group(1).lower() != expected_cert.lower():
        raise Blocked('APK signer certificate does not match the laboratory pin')
    if not re.search(r'(?im)^Verified using v2 scheme \(APK Signature Scheme v2\): true\s*$', signer):
        raise Blocked('APK v2 signature has not been confirmed')
    return {'apk_sha256': expected_digest.lower(), 'apk_zip_integrity_checked': True,
            'package': PACKAGE, 'internet_permission_absent_in_dump': True,
            'lab_certificate_sha256': expected_cert.lower(), 'apk_v2_signature_verified': True,
            'limitations': 'No API ID, runtime, JNI, Chaquopy or ELF compatibility verification'}


def main(argv=None, run=command) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--serial', required=True, help='Explicit local emulator-NNNN ADB serial')
    parser.add_argument('--profile', required=True, choices=sorted(MODES))
    parser.add_argument('--apk', type=Path, help='Optional reviewed Diagnostic APK, never installed')
    parser.add_argument('--expected-apk-sha256')
    parser.add_argument('--expected-cert-sha256')
    parser.add_argument('--log-file', type=Path, help='Optional existing local log; only event counts emitted')
    args = parser.parse_args(argv)
    report = {'schema': 1, 'type': 'diagnostic_android_lab_preflight',
              'status': 'BLOCKED', 'profile': args.profile, 'target': None, 'apk': None,
              'log_indicators': None, 'reasons': [],
              'never_performed': ['adb install', 'am start', 'logcat capture', 'external service requests'],
              'not_certified': ['Android startup', 'JNI/Python loading', '16 KB runtime',
                                'API credentials and translation policies', 'APK distribution']}
    try:
        if (args.apk is None) != (args.expected_apk_sha256 is None) or \
           (args.apk is None) != (args.expected_cert_sha256 is None):
            raise Blocked('APK path and both SHA-256 pins must be provided together')
        if args.log_file is not None:
            report['log_indicators'] = read_log_counts(args.log_file)
            if any(report['log_indicators']['category_counts'].values()):
                raise Blocked('Critical indicators detected in the supplied local log')
        report['target'] = emulator_probe(args.serial, args.profile, run)
        if args.apk is not None:
            report['apk'] = apk_probe(args.apk, args.expected_apk_sha256,
                                      args.expected_cert_sha256, run)
            report['status'] = 'READY_FOR_HUMAN_REVIEW_NOT_RUNTIME_VALIDATED'
        else:
            report['status'] = 'EMULATOR_CHECKS_ONLY_APK_NOT_VERIFIED'
    except (Blocked, OSError, zipfile.BadZipFile) as exc:
        # Never print the subprocess output, serial, file contents or paths.
        report['reasons'].append(str(exc) if isinstance(exc, Blocked)
                                 else 'Required local file or ZIP check failed')
    print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
    return 1 if report['status'] == 'BLOCKED' else 0


if __name__ == '__main__':
    raise SystemExit(main())
