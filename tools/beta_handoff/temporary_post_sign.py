#!/usr/bin/env python3
"""Review one disposable offline beta trial. Never generates keys or signs."""
from __future__ import annotations
import re
from pathlib import Path
import post_sign as shared

TRIAL = 'flexygram-personal-offline-9513d497-v1'
SCOPE = 'FlexyGram_Beta_disposable_single_trial_v1'
UNSIGNED = '9513d49706a714d496b45aab1992c0cc250e8c2e4df8bb1a1be00d8451e60ede'
COMMIT = '97dfb08e58159b31d322dd8435080fb039abdeb9'
STATUS = 'BETA_TEMPORARY_SIGNED_STATIC_REVIEW_ONLY_PENDING_ANDROID'
require = shared.require


def approval(path, receipt_hash, receipt):
    data = shared.signature.strict_json(path)
    required = {
        'schema', 'status', 'approval_scope', 'trial_id', 'package',
        'source_commit', 'approved_unsigned_apk_sha256', 'build_receipt_sha256',
        'certificate_sha256', 'approval_reference', 'apk_signing_authorized',
        'ephemeral_key_generation_approval_reference', 'protected_input_review_reference',
        'production_use_allowed', 'permanent_identity', 'discard_key_after_trial',
        'future_updates_guaranteed', 'installation_authorized', 'distribution_allowed',
    }
    require(isinstance(data, dict) and set(data) == required,
            'TEMPORARY_AUTHORIZATION_FIELDS_INVALID')
    expected = dict(
        schema=1, status='DISPOSABLE_BETA_TRIAL_SIGNING_AUTHORIZED',
        approval_scope=SCOPE, trial_id=TRIAL, package=shared.PACKAGE,
        source_commit=COMMIT, approved_unsigned_apk_sha256=UNSIGNED,
        build_receipt_sha256=receipt_hash,
        apk_signing_authorized=True, production_use_allowed=False,
        permanent_identity=False, discard_key_after_trial=True,
        future_updates_guaranteed=False, installation_authorized=False,
        distribution_allowed=False)
    require(all(type(data[k]) is type(v) and data[k] == v for k, v in expected.items()),
            'TEMPORARY_SIGNING_AUTHORIZATION_REQUIRED')
    require(receipt.get('source_commit') == COMMIT and
            receipt.get('unsigned_apk_sha256') == UNSIGNED and
            receipt.get('package') == shared.PACKAGE and
            receipt.get('version_code') == '1261' and
            receipt.get('version_name') == '13.0.2', 'TEMPORARY_BUILD_NOT_PINNED')
    for name in ('approval_reference', 'ephemeral_key_generation_approval_reference',
                 'protected_input_review_reference'):
        require(isinstance(data[name], str) and len(data[name].strip()) >= 8,
                'TEMPORARY_APPROVAL_REFERENCE_REQUIRED')
    cert = data['certificate_sha256']
    require(isinstance(cert, str) and re.fullmatch('[0-9a-f]{64}', cert) and
            cert != '0'*64, 'CERTIFICATE_NOT_APPROVED')
    return cert


def verify(args):
    # Pin this trial before delegating all byte/tool checks to the shared engine.
    require(args.commit == COMMIT and args.unsigned_sha256 == UNSIGNED and
            args.version_code == '1261' and args.version_name == '13.0.2',
            'TEMPORARY_TRIAL_INPUT_NOT_PINNED')
    # This is a reviewed recovery assertion, not proof of a network transfer.
    # The signing operator must independently download and observe that transfer.
    path = args.recovery_receipt
    shared.signature.regular(path)
    inputs = (args.unsigned_apk, args.signed_apk, args.recovered_apk, args.approval,
              args.build_receipt, args.unsigned_review, args.output)
    require(all(path.resolve() != p.resolve() for p in inputs),
            'TEMPORARY_RECOVERY_RECEIPT_OVERLAPS_INPUT')
    recovery_hash = shared.gate.sha256(path)
    recovery = shared.signature.strict_json(path)
    require(isinstance(recovery, dict) and type(recovery.get('schema')) is int and
            recovery['schema'] == 1 and recovery.get('trial_id') == TRIAL and
            recovery.get('status') == 'PRIVATE_SIGNED_APK_RECOVERY_VERIFIED' and
            recovery.get('provider') == 'Dropbox' and
            recovery.get('independently_downloaded') is True and
            recovery.get('signed_apk_sha256') == args.signed_sha256 and
            type(recovery.get('bytes')) is int and
            recovery['bytes'] == args.recovered_apk.stat().st_size,
            'TEMPORARY_PRIVATE_RECOVERY_RECEIPT_REQUIRED')
    for field in ('file_id', 'revision', 'verification_reference'):
        require(isinstance(recovery.get(field), str) and
                len(recovery[field].strip()) >= 8,
                'TEMPORARY_PRIVATE_RECOVERY_REFERENCE_REQUIRED')
    result = shared.verify(args, authorize=approval)
    require(shared.gate.sha256(path) == recovery_hash,
            'TEMPORARY_RECOVERY_RECEIPT_CHANGED')
    require(result['status'] == 'BETA_SIGNED_STATIC_REVIEW_ONLY_PENDING_ANDROID',
            'TEMPORARY_SHARED_REVIEW_FAILED')
    result.update(status=STATUS, approval_scope=SCOPE, trial_id=TRIAL,
                  permanent_identity=False, future_updates_guaranteed=False,
                  key_discard_required=True, key_discard_observed=False,
                  key_custody_recovery_claimed=False,
                  signed_recovery_receipt_sha256=recovery_hash,
                  signed_recovery_receipt_checked=True)
    return result


def main(argv=None):
    return shared.run_cli(argv, verifier=verify, success_status=STATUS,
                          add_arguments=lambda p: p.add_argument(
                              '--recovery-receipt', type=Path, required=True))


if __name__ == '__main__':
    raise SystemExit(main())
