#!/usr/bin/env python3
"""Read-only beta post-sign review. No signing, keys, installation or network."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import zipfile
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'tools/beta_handoff'),
               str(ROOT / 'tests/native_compatibility')]
import gate
# Only generic primitives: never call historical verify()/approved_identity().
import verify_post_sign_diagnostic as signature

PACKAGE = 'io.github.jose22yt.flexygram.beta.development'
SCOPE = 'FlexyGram_Beta_personal_offline_only'
require = gate.require


def class_inventory(folder):
    require(folder.is_dir() and not folder.is_symlink() and
            not any(p.is_symlink() for p in folder.parents), 'UNSAFE_CLASSES_DIRECTORY')
    inventory = {}
    for path in sorted(folder.rglob('*')):
        require(not path.is_symlink(), 'UNSAFE_CLASSES_MEMBER')
        if path.is_file():
            signature.regular(path)
            inventory[path.relative_to(folder).as_posix()] = gate.sha256(path)
        else:
            require(path.is_dir(), 'UNSAFE_CLASSES_MEMBER')
    require(any(n.endswith('/BuildConfig.class') for n in inventory), 'CLASSES_MISSING_BUILDCONFIG')
    return inventory


def bounded_members(apk):
    signature.regular(apk)
    with zipfile.ZipFile(apk) as archive:
        require(sum(i.file_size for i in archive.infolist()) <= 2**31, 'APK_EXPANSION_LIMIT')
        for item in archive.infolist():
            require(stat.S_IFMT(item.external_attr >> 16) in
                    (0, stat.S_IFREG, stat.S_IFDIR), 'UNSAFE_APK_MEMBER_TYPE')
    return signature.members(apk)


def approval(path, receipt_hash, receipt):
    data = signature.strict_json(path)
    require(isinstance(data, dict) and data.get('schema') == 1 and
            data.get('status') == 'CUSTODY_VERIFIED_BETA_SIGNING_AUTHORIZED' and
            data.get('approval_scope') == SCOPE and data.get('package') == PACKAGE and
            data.get('apk_signing_authorized') is True and
            data.get('production_use_allowed') is False and
            data.get('private_key_backed_up') is True and
            data.get('custody_recovery_verified') is True and
            data.get('build_receipt_sha256') == receipt_hash and
            data.get('approved_unsigned_apk_sha256') == receipt['unsigned_apk_sha256'] and
            isinstance(data.get('approval_reference'), str) and
            len(data['approval_reference'].strip()) >= 8,
            'BETA_SIGNING_AUTHORIZATION_REQUIRED')
    cert = data.get('certificate_sha256')
    require(isinstance(cert, str) and re.fullmatch('[0-9a-f]{64}', cert) and
            cert != '0'*64, 'CERTIFICATE_NOT_APPROVED')
    return cert


def verify(args, *, authorize=None):
    # Everything is local input; receipts are reviewed assertions, not a PKI or
    # proof that a compiler actually built a declared Git commit.
    files = (args.unsigned_apk, args.signed_apk, args.recovered_apk,
             args.approval, args.build_receipt, args.unsigned_review)
    for path in files:
        signature.regular(path)
    require(len({p.resolve() for p in files}) == len(files), 'INPUT_PATHS_MUST_DIFFER')
    initial = {p: gate.sha256(p) for p in files}
    receipt = signature.strict_json(args.build_receipt)
    require(isinstance(receipt, dict) and receipt.get('schema') == 1 and
            receipt.get('package') == PACKAGE and
            re.fullmatch('[0-9a-f]{40}', receipt.get('source_commit', '')) and
            receipt.get('source_commit') == args.commit and
            receipt.get('version_code') == args.version_code and
            receipt.get('version_name') == args.version_name and
            receipt.get('unsigned_apk_sha256') == args.unsigned_sha256 and
            receipt.get('unsigned_review_sha256') == initial[args.unsigned_review],
            'BUILD_RECEIPT_MISMATCH')
    cert = (approval if authorize is None else authorize)(
        args.approval, initial[args.build_receipt], receipt)
    require(initial[args.unsigned_apk] == args.unsigned_sha256, 'UNSIGNED_SHA256_MISMATCH')
    require(re.fullmatch('[0-9a-f]{64}', args.signed_sha256 or '') and
            initial[args.signed_apk] == args.signed_sha256, 'SIGNED_SHA256_MISMATCH')
    require(initial[args.recovered_apk] == args.signed_sha256, 'RECOVERED_SHA256_MISMATCH')
    require(args.signed_sha256 != args.unsigned_sha256, 'SIGNED_EQUALS_UNSIGNED')
    inventory = class_inventory(args.classes)
    require(receipt.get('classes') == inventory, 'BUILD_CLASSES_MISMATCH')
    previous = signature.strict_json(args.unsigned_review)
    require(isinstance(previous, dict) and
            previous.get('status') == 'BETA_UNSIGNED_STATIC_REVIEW_ONLY_PENDING_ANDROID' and
            previous.get('apk_sha256') == args.unsigned_sha256 and
            previous.get('version_code') == args.version_code and
            previous.get('version_name') == args.version_name and
            previous.get('input_bytes_checked') is True and
            previous.get('compiled_buildconfig_closed') is True,
            'UNSIGNED_REVIEW_INCOMPLETE')
    # Re-run the existing beta gate on actual unsigned bytes; no report-only PASS.
    baseline = gate.run(SimpleNamespace(
        apk=args.unsigned_apk, sha256=args.unsigned_sha256, classes=args.classes,
        build_tools=args.build_tools, ndk=args.ndk, javap=args.javap,
        version_code=args.version_code, version_name=args.version_name))
    require(baseline.get('status') == previous['status'] and
            baseline.get('apk_sha256') == args.unsigned_sha256 and
            baseline.get('manifest') == previous.get('manifest') and
            baseline.get('compiled_buildconfig_closed') is True and
            baseline.get('zipalign_16k') is True and
            baseline.get('native_acceptance', {}).get('blockers') == [],
            'UNSIGNED_REVIEW_NOT_REPRODUCED')
    require(bounded_members(args.unsigned_apk) == bounded_members(args.signed_apk),
            'SIGNED_PAYLOAD_CHANGED')
    # Historical helper excludes JAR metadata. An existing manifest is still
    # immutable; only newly introduced v1 signature metadata may be excluded.
    with zipfile.ZipFile(args.unsigned_apk) as before, zipfile.ZipFile(args.signed_apk) as after:
        for name in before.namelist():
            if name.upper() == 'META-INF/MANIFEST.MF':
                require(name in after.namelist() and before.read(name) == after.read(name),
                        'EXISTING_JAR_MANIFEST_CHANGED')
    signature.check_signature(args.signed_apk, args.build_tools / 'apksigner', cert)
    signature.check_alignment(args.signed_apk, args.build_tools / 'zipalign')
    # Imported by gate.run only after its unsigned checks.
    import review_apk
    require(review_apk.binary_manifest(args.signed_apk, args.build_tools / 'aapt2') ==
            baseline['manifest'], 'SIGNED_MANIFEST_POLICY_CHANGED')
    require(class_inventory(args.classes) == inventory, 'CLASSES_CHANGED_DURING_REVIEW')
    require(all(gate.sha256(p) == digest for p, digest in initial.items()),
            'INPUT_CHANGED_DURING_REVIEW')
    return dict(
        status='BETA_SIGNED_STATIC_REVIEW_ONLY_PENDING_ANDROID',
        source_commit_declared=args.commit, version_code=args.version_code,
        version_name=args.version_name, package=PACKAGE,
        unsigned_apk_sha256=args.unsigned_sha256, signed_apk_sha256=args.signed_sha256,
        certificate_sha256=cert, apk_v2_min_sdk_24_verified=True,
        zipalign_4k_16k_verified=True, payload_identical=True,
        native_static_acceptance=baseline['native_acceptance'],
        recovered_local_copy_sha256_verified=True, remote_recovery_independently_observed=False,
        build_receipt_sha256=initial[args.build_receipt],
        approval_sha256=initial[args.approval],
        unsigned_review_sha256=initial[args.unsigned_review],
        source_provenance='Reviewed receipt assertion; not derivable from APK bytes.',
        android_runtime_validated=False, installable=None,
        installation_authorized=False, distribution_allowed=False, production_allowed=False)


def run_cli(argv=None, *, verifier, success_status, add_arguments=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('unsigned-apk', 'signed-apk', 'recovered-apk', 'approval',
                 'build-receipt', 'unsigned-review', 'classes', 'build-tools',
                 'ndk', 'javap', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    for name in ('unsigned-sha256', 'signed-sha256', 'commit', 'version-code', 'version-name'):
        parser.add_argument('--' + name, required=True)
    if add_arguments is not None:
        add_arguments(parser)
    args = parser.parse_args(argv)
    try:
        # Reserve a NEW private report outside repository and all input trees.
        output = args.output.absolute()
        require(not output.is_symlink() and not any(p.is_symlink() for p in output.parents),
                'UNSAFE_OUTPUT')
        output = output.resolve()
        for path in (ROOT, args.classes, args.build_tools, args.ndk):
            require(not output.is_relative_to(path.resolve()), 'OUTPUT_OVERLAPS_INPUT')
        for name in ('unsigned_apk', 'signed_apk', 'recovered_apk', 'approval',
                     'build_receipt', 'unsigned_review', 'javap'):
            require(output != getattr(args, name).resolve(), 'OUTPUT_OVERLAPS_INPUT')
        descriptor = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, 'w', encoding='utf-8') as report:
            # A prewritten block survives interruption; no stale PASS.
            report.write('{"status":"BLOCKED","code":"REVIEW_INCOMPLETE"}\n')
            report.flush()
            try:
                result = verifier(args)
            except Exception as error:
                result = dict(status='BLOCKED', error_type=type(error).__name__,
                              android_runtime_validated=False, distribution_allowed=False)
            report.seek(0)
            report.write(json.dumps(result, indent=2, sort_keys=True) + '\n')
            report.truncate()
        print(json.dumps({'status': result['status']}))
        return 0 if result['status'] == success_status else 1
    except Exception:
        print('{"status":"BLOCKED","code":"REPORT_OR_INPUT_UNAVAILABLE"}')
        return 1


def main(argv=None):
    # Permanent CLI has no temporary-policy switch; its defaults stay closed.
    return run_cli(argv, verifier=verify,
                   success_status='BETA_SIGNED_STATIC_REVIEW_ONLY_PENDING_ANDROID')


if __name__ == '__main__':
    raise SystemExit(main())
