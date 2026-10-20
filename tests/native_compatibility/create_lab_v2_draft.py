#!/usr/bin/env python3
"""Produce a non-runnable v2 lab draft from reviewed unsigned evidence.

No signing, secrets, device operations or changes to historical v1 contract.
"""
import argparse
import json
from pathlib import Path
import os
import review_unsigned_contract as review

SCHEMA = 2
STATUS = 'BLOCKED_UNSIGNED_V2_DRAFT_NOT_LAB_CONTRACT'


def require(ok, message):
    if not ok:
        raise ValueError(message)


def make_draft(evidence, previous, audit, wheel_manifest, apk):
    require(evidence['status'] == 'UNSIGNED_EVIDENCE_REVIEWED_SIGNING_BLOCKED' and
            evidence['signing_authorized'] is False and
            evidence['android_runtime_validated'] is False and
            evidence['distribution_allowed'] is False,
            'Only reviewed unsigned, blocked evidence can seed the lab v2 draft')
    require(previous['schema'] == 1 and
            len(previous['case_ids']) == 12 and
            len(set(previous['case_ids'])) == 12, 'Historical lab v1 invalid')
    require(len(wheel_manifest['wheels']) == 18 and
            sum(x['rebuilt'] is True for x in wheel_manifest['wheels']) == 3,
            'Reviewed wheel overlay incomplete')
    expected_apk = evidence['unsigned_apk_sha256']
    require(apk['apk_sha256'] == expected_apk and
            apk['signature'] == 'absent', 'Unsigned source receipt disagreement')
    name = previous['jni_library']
    matches = [x for x in audit['libraries']
               if x['path'].endswith('!lib/arm64-v8a/' + name) and
                  x['machine'] == 'EM_AARCH64']
    require(len(matches) == 1 and matches[0]['load_4k'] is True and
            matches[0]['load_16k'] is True,
            'Exactly one verified packaged JNI library required')
    require(previous['target_package'] == 'io.github.jose22yt.flexygram.diagnostic',
            'Diagnostic package changed')
    return {
        'schema': SCHEMA, 'status': STATUS,
        'purpose': 'public_metadata_review_only_do_not_feed_to_lab_runner',
        'derived_from_historical_v1_head': previous['reviewed_head'],
        'target_package': previous['target_package'],
        'runner_package': previous['runner_package'],
        'runner_class': previous['runner_class'],
        'source_unsigned_apk_sha256': expected_apk,
        'source_unsigned_apk_bytes': evidence['unsigned_apk_bytes'],
        'reviewed_unsigned_apk_source_head': evidence['source_head'],
        'jni_library': name,
        'jni_sha256_from_unsigned_apk_audit': matches[0]['sha256'],
        'native_elf_sha256_from_rebuild': evidence['native_elf_sha256'],
        'wheel_sha256': {r['filename']: r['sha256'] for r in wheel_manifest['wheels']},
        'cases': previous['case_ids'],
        'runtime_cases_sha256': previous['runtime_cases_sha256'],
        'font_sha256': previous['font_sha256'],
        'font_license_sha256': previous['font_license_sha256'],
        'policy_scope': previous['policy_scope'],
        'lab_profiles_required': ['api24-4k', 'arm64-16k'],
        'signing_custody_verified': False,
        'apk_signing_authorized': False,
        'signed_apk_sha256': None, 'signed_apk_bytes': None,
        'certificate_sha256': None, 'signed_runner_sha256': None,
        'lab_api24_receipt_sha256': None, 'lab_16k_receipt_sha256': None,
        'android_runtime_validated': False, 'distribution_allowed': False,
        'merge_authorized': False,
        'runtime_contract_activated': False,
        'missing_review_gates': [
            'Recoverable signing-key custody confirmed by owner',
            'Separate owner authorization for Diagnostic signing',
            'Measured signed APK and reviewed certificate',
            'Signed, rebuilt and inspected instrumentation runner',
            'Android ARM64 API24/4K 12/12 functional cases',
            'Android ARM64 16KB strict 12/12 functional cases',
        ],
    }


def prepare(evidence_dir=review.EVIDENCE):
    report = review.verify(evidence_dir)
    return make_draft(report,
                      review.read_json(review.LAB_V1),
                      review.read_json(evidence_dir/'apk-native-audit.json'),
                      review.read_json(evidence_dir/'experimental-wheels-manifest.json'),
                      review.read_json(evidence_dir/'unsigned-apk-receipt.json'))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', type=Path, default=review.EVIDENCE)
    parser.add_argument('--output', type=Path,
                        help='New private JSON destination; never existing or under repository')
    args = parser.parse_args(argv)
    try:
        result = prepare(args.evidence)
        if args.output is not None:
            path = args.output.absolute()
            repo = review.ROOT.resolve()
            require(not path.exists() and not path.is_symlink() and
                    repo not in path.resolve().parents and path.resolve() != repo and
                    not any(p.is_symlink() for p in path.parents),
                    'Output must be new/private outside checkout')
            require(path.parent.is_dir(), 'Private output parent must already exist')
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            try:
                with os.fdopen(fd, 'w', encoding='utf-8') as file:
                    json.dump(result, file, indent=2, sort_keys=True)
                    file.write('\n')
            except BaseException:
                path.unlink(missing_ok=True)
                raise
        print(json.dumps({'status': STATUS,
                          'signed': False, 'android_runtime_validated': False,
                          'output_written': args.output is not None}))
        return 0
    except (OSError, KeyError, TypeError, ValueError) as exc:
        print(json.dumps({'status':'BLOCKED', 'error_class':type(exc).__name__,
                          'signed':False, 'android_runtime_validated':False}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
