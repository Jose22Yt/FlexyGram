#!/usr/bin/env python3
"""Read-only post-signing verifier for an explicitly authorised Diagnostic APK.

Requires independent custody/authorization review and real apksigner verification.
NEVER creates certificates, signs APKs, installs Android, or changes repo contracts.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import subprocess
import zipfile

import verify_private_unsigned_apk as unsigned

HEX = re.compile(r'^[0-9a-f]{64}$')
CERT = re.compile(r'^Signer #(\\d+) certificate SHA-256 digest:\\s*([0-9a-f:]{64,95})\\s*$', re.I | re.M)
V2 = re.compile(r'^Verified using v2 scheme \\(APK Signature Scheme v2\\):\\s*true\\s*$', re.I | re.M)
SIGNATURE = re.compile(r'(?i)^META-INF/[^/]+\\.(?:RSA|DSA|EC|SF)$')


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def regular(file):
    require(file.is_file() and not file.is_symlink() and
            not any(p.is_symlink() for p in file.parents), 'Missing/unsafe local file')


def strict_json(path):
    regular(path)
    def pairs(items):
        result = {}
        for name, value in items:
            require(name not in result, 'Duplicate signing approval key')
            result[name] = value
        return result
    def reject_constant(value):
        raise ValueError('Nonfinite approval JSON')
    return json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=pairs,
                      parse_constant=reject_constant)


def approved_identity(path, source_sha):
    identity = strict_json(path)
    require(isinstance(identity, dict) and
            identity.get('status') == 'CUSTODY_VERIFIED_SIGNING_AUTHORIZED' and
            identity.get('apk_signing_authorized') is True and
            identity.get('production_use_allowed') is False and
            identity.get('private_key_backed_up') is True and
            identity.get('custody_recovery_verified') is True and
            identity.get('approval_scope') == 'Diagnostic_lab_only' and
            identity.get('approved_unsigned_apk_sha256') == source_sha and
            isinstance(identity.get('approval_reference'), str) and
            len(identity['approval_reference'].strip()) >= 8,
            'Custody/signing authorization record incomplete')
    cert = identity.get('certificate_sha256')
    require(isinstance(cert, str) and HEX.fullmatch(cert) is not None and
            cert != '0'*64, 'Reviewed certificate SHA-256 absent')
    return cert


def members(path):
    regular(path)
    with zipfile.ZipFile(path) as zip_file:
        names = zip_file.namelist()
        require(len(names) == len(set(names)) and zip_file.testzip() is None,
                'APK duplicate ZIP entries or CRC failure')
        result = {}
        for name in names:
            require(not name.startswith('/') and '\\' not in name and
                    all(part not in ('', '.', '..') for part in name.rstrip('/').split('/')),
                    'Unsafe APK ZIP path')
            if SIGNATURE.fullmatch(name) or name.upper() == 'META-INF/MANIFEST.MF':
                continue
            if name.endswith('/'):
                continue
            info = zip_file.getinfo(name)
            require(info.file_size <= 512*1024*1024, 'Unexpected oversized APK member')
            data = zip_file.read(name)
            result[name] = (len(data), hashlib.sha256(data).hexdigest())
        return result


def check_signature(signed, apksigner, expected_cert, runner=subprocess.run):
    regular(signed)
    regular(apksigner)
    completed = runner([str(apksigner), 'verify', '--verbose', '--print-certs',
                        '--min-sdk-version', '24', str(signed)],
                       capture_output=True, text=True, timeout=120, check=False)
    require(completed.returncode == 0, 'Signed APK verification failed')
    result = completed.stdout + '\n' + completed.stderr
    require(V2.search(result) is not None, 'APK signature scheme v2 is not valid')
    signers = CERT.findall(result)
    require(len(signers) == 1 and signers[0][0] == '1',
            'Signing certificate count ambiguous')
    cert = signers[0][1].replace(':', '').lower()
    require(cert == expected_cert, 'Signing certificate does not match reviewed identity')
    return cert


def verify(unsigned_apk, signed_apk, identity, apksigner,
           evidence=unsigned.review.EVIDENCE, signature_runner=subprocess.run):
    unsigned_receipt = unsigned.verify(unsigned_apk, evidence)
    source_sha = unsigned_receipt['sha256']
    cert = approved_identity(identity, source_sha)
    unsigned_entries = members(unsigned_apk)
    signed_entries = members(signed_apk)
    require(unsigned_entries == signed_entries,
            'Signing changed APK entry set or uncompressed payloads')
    signed_sha = unsigned.review.sha256(signed_apk)
    require(signed_sha != source_sha, 'Signed APK identical to unsigned baseline')
    check_signature(signed_apk, apksigner, cert, runner=signature_runner)
    return {
        'status': 'SIGNED_STATIC_REVIEW_ONLY_PENDING_ANDROID',
        'signed_apk_sha256': signed_sha,
        'signed_apk_bytes': signed_apk.stat().st_size,
        'source_unsigned_apk_sha256': source_sha,
        'certificate_sha256': cert,
        'apk_v2_verified': True,
        'apk_payload_identical_to_reviewed_unsigned': True,
        'installable': None,
        'android_runtime_validated': False,
        'distribution_allowed': False,
        'production_allowed': False,
        'historical_lab_contract_updated': False,
    }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('unsigned-apk', 'signed-apk', 'identity', 'apksigner'):
        p.add_argument('--'+name, type=Path, required=True)
    p.add_argument('--evidence', type=Path, default=unsigned.review.EVIDENCE)
    a = p.parse_args(argv)
    try:
        result = verify(a.unsigned_apk, a.signed_apk, a.identity, a.apksigner, a.evidence)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (OSError, ValueError, TypeError, KeyError, zipfile.BadZipFile,
            subprocess.SubprocessError) as exc:
        print(json.dumps({'status':'BLOCKED','error_class':type(exc).__name__,
                          'android_runtime_validated':False,'distribution_allowed':False}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
