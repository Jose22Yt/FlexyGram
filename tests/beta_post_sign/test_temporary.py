"""Disposable policy: synthetic ZIPs/tool doubles, no secrets/certificates/signing."""
from pathlib import Path
import json
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools/beta_handoff'))
import temporary_post_sign as subject
import post_sign as permanent
import test_post_sign as fixtures


class TemporaryPolicyTests(unittest.TestCase):
    def setUp(self):
        # Reuse PR30's fixtures without inheriting/recounting its 15 methods.
        self.f = fixtures.BetaPostSignTests('test_synthetic_success_requires_real_primitive_calls_and_gate')
        self.addCleanup(self.f.doCleanups)
        self.f.setUp()
        f = self.f
        f.args.recovery_receipt = f.root/'recovery.json'
        self.recovery = dict(schema=1, trial_id=subject.TRIAL,
            status='PRIVATE_SIGNED_APK_RECOVERY_VERIFIED', provider='Dropbox',
            independently_downloaded=True, signed_apk_sha256=f.args.signed_sha256,
            bytes=f.args.recovered_apk.stat().st_size,
            file_id='synthetic Dropbox file id', revision='synthetic revision',
            verification_reference='synthetic independent recovery')
        f.write_json(f.args.recovery_receipt, self.recovery)
        f.args.commit = subject.COMMIT
        f.args.unsigned_sha256 = subject.UNSIGNED
        f.receipt.update(source_commit=subject.COMMIT, unsigned_apk_sha256=subject.UNSIGNED)
        f.baseline['apk_sha256'] = subject.UNSIGNED
        f.write_json(f.args.unsigned_review, f.baseline)
        f.receipt['unsigned_review_sha256'] = permanent.gate.sha256(f.args.unsigned_review)
        self.identity = dict(
            schema=1, status='DISPOSABLE_BETA_TRIAL_SIGNING_AUTHORIZED',
            approval_scope=subject.SCOPE, trial_id=subject.TRIAL,
            package=permanent.PACKAGE, source_commit=subject.COMMIT,
            approved_unsigned_apk_sha256=subject.UNSIGNED,
            build_receipt_sha256='', certificate_sha256='b'*64,
            approval_reference='synthetic signing decision',
            ephemeral_key_generation_approval_reference='synthetic generation decision',
            protected_input_review_reference='synthetic protected channel review',
            apk_signing_authorized=True, production_use_allowed=False,
            permanent_identity=False, discard_key_after_trial=True,
            future_updates_guaranteed=False, installation_authorized=False,
            distribution_allowed=False)
        self.save()
        # Explicit hash oracle ONLY for the synthetic unsigned fixture: test ZIP
        # bytes cannot possess the real production candidate's pinned digest.
        # All other digests and all ZIP/CRC/payload/class checks remain real.
        real_sha = permanent.gate.sha256
        self.actual_sha = real_sha
        self.enterContext(patch.object(permanent.gate, 'sha256', side_effect=lambda p:
            subject.UNSIGNED if p == f.args.unsigned_apk else real_sha(p)))

    def save(self):
        f = self.f
        f.write_json(f.args.build_receipt, f.receipt)
        self.identity['build_receipt_sha256'] = permanent.gate.sha256(f.args.build_receipt)
        f.write_json(f.args.approval, self.identity)

    def blocked(self):
        with self.assertRaises((ValueError, OSError)):
            subject.verify(self.f.args)

    def sync_recovery_fixture(self):
        self.recovery.update(signed_apk_sha256=self.f.args.signed_sha256,
                             bytes=self.f.args.recovered_apk.stat().st_size)
        self.f.write_json(self.f.args.recovery_receipt, self.recovery)

    def test_synthetic_full_shared_pipeline_and_explicit_temporary_result(self):
        r = subject.verify(self.f.args)
        self.assertEqual(r['status'], subject.STATUS)
        self.assertEqual(r['trial_id'], subject.TRIAL)
        for k in ('permanent_identity', 'future_updates_guaranteed',
                  'key_custody_recovery_claimed', 'key_discard_observed',
                  'installation_authorized', 'distribution_allowed',
                  'android_runtime_validated', 'remote_recovery_independently_observed'):
            self.assertIs(r[k], False, k)
        self.assertTrue(r['payload_identical'])
        self.assertTrue(r['apk_v2_min_sdk_24_verified'])
        self.f.gate_mock.assert_called_once()
        self.f.manifest_mock.assert_called_once()

    def test_wrong_cli_pin_blocks_before_gate(self):
        for k in ('commit', 'unsigned_sha256', 'version_code', 'version_name'):
            old = getattr(self.f.args, k)
            setattr(self.f.args, k, 'invalid')
            self.blocked()
            setattr(self.f.args, k, old)
        self.f.gate_mock.assert_not_called()

    def test_wrong_contract_fields_missing_fields_and_custody_claims_block(self):
        old = dict(self.identity)
        for k, v in (('approval_scope', permanent.SCOPE), ('trial_id', 'other'),
                     ('package', 'com.exteraless.app'), ('source_commit', 'a'*40),
                     ('approved_unsigned_apk_sha256', 'a'*64),
                     ('status', 'DRAFT_NOT_AUTHORIZED'), ('schema', True)):
            with self.subTest(field=k):
                self.identity = dict(old, **{k: v}); self.save(); self.blocked()
        for k in old:
            self.identity = dict(old); del self.identity[k]
            # save() derives the receipt hash, so write the malformed JSON directly.
            self.f.write_json(self.f.args.approval, self.identity); self.blocked()
        for k in ('private_key_backed_up', 'custody_recovery_verified', 'password'):
            for v in (False, True):
                self.identity = dict(old, **{k: v}); self.save(); self.blocked()
        self.f.gate_mock.assert_not_called()

    def test_false_permissions_and_discard_requirements_are_strict(self):
        old = dict(self.identity)
        fields = ('apk_signing_authorized', 'production_use_allowed', 'permanent_identity',
                  'discard_key_after_trial', 'future_updates_guaranteed',
                  'installation_authorized', 'distribution_allowed')
        for k in fields:
            for v in (not old[k], int(old[k])):
                self.identity = dict(old, **{k: v}); self.save(); self.blocked()

    def test_references_and_certificate_must_be_explicit(self):
        old = dict(self.identity)
        for k in ('approval_reference', 'ephemeral_key_generation_approval_reference',
                  'protected_input_review_reference', 'certificate_sha256'):
            for v in ('', None, '0'*64 if k == 'certificate_sha256' else 'short'):
                self.identity = dict(old, **{k: v}); self.save(); self.blocked()

    def test_wrong_receipt_hash_and_build_pin_block(self):
        self.identity['build_receipt_sha256'] = 'a'*64
        self.f.write_json(self.f.args.approval, self.identity); self.blocked()
        self.save()
        original = dict(self.f.receipt)
        for k in ('source_commit', 'unsigned_apk_sha256', 'version_name', 'version_code', 'package'):
            self.f.receipt = dict(original, **{k: 'wrong'}); self.save(); self.blocked()

    def test_permanent_and_diagnostic_contracts_cannot_cross_modes(self):
        self.save()
        with self.assertRaises(ValueError):
            permanent.verify(self.f.args)
        self.f.identity.update(approved_unsigned_apk_sha256=subject.UNSIGNED)
        self.f.refresh_receipt()
        # Permanent approval still works for its own policy with the shared engine.
        self.assertEqual(permanent.verify(self.f.args)['status'],
                         'BETA_SIGNED_STATIC_REVIEW_ONLY_PENDING_ANDROID')
        self.blocked()
        self.f.identity['approval_scope'] = 'Diagnostic_lab_only'
        self.f.refresh_receipt(); self.blocked()

    def test_payload_manifest_and_missing_recovery_still_block(self):
        f = self.f
        f.args.recovered_apk.write_bytes(b'wrong recovery'); self.blocked()
        f.refresh_signed()
        changed = dict(f.payload); changed['classes.dex'] += b'changed'
        f.write_zip(f.args.signed_apk, changed); f.refresh_signed()
        self.sync_recovery_fixture(); self.blocked()
        f.write_zip(f.args.signed_apk, f.payload); f.refresh_signed()
        self.sync_recovery_fixture()
        f.manifest_mock.return_value = {'package': permanent.PACKAGE, 'permissions':['android.permission.INTERNET']}
        self.blocked()

    def test_certificate_v2_and_alignment_still_block(self):
        f = self.f
        original = f.cert_output
        for output in (original.replace('b'*64, 'c'*64), original.replace(': true', ': false'),
                       original + 'Signer #2 certificate SHA-256 digest: ' + 'b'*64 + '\n'):
            f.cert_output = output; self.blocked()
        f.cert_output = original
        f.sign_result = 1; self.blocked()
        f.sign_result = 0; f.align_result = 1; self.blocked()

    def test_native_gate_and_classes_still_block(self):
        self.f.baseline['native_acceptance'] = {'blockers':['synthetic native blocker']}
        self.blocked()
        self.f.baseline['native_acceptance'] = {'blockers':[]}
        (self.f.args.classes/'org/telegram/messenger/BuildConfig.class').write_bytes(b'changed')
        self.blocked()

    def test_cli_status_and_exclusive_report(self):
        argv = [v for k, value in vars(self.f.args).items()
                for v in ('--'+k.replace('_','-'), str(value))]
        with patch('builtins.print'):
            self.assertEqual(subject.main(argv), 0)
            before = self.f.args.output.read_bytes()
            self.assertEqual(subject.main(argv), 1)
        self.assertEqual(before, self.f.args.output.read_bytes())
        self.assertEqual(json.loads(before)['status'], subject.STATUS)

    def test_recovery_receipt_is_required_bound_and_not_remote_proof(self):
        original = dict(self.recovery)
        for k, v in (('trial_id', 'other'), ('signed_apk_sha256', 'c'*64),
                     ('independently_downloaded', False), ('bytes', 0),
                     ('provider', 'local'), ('revision', ''), ('schema', True)):
            self.f.write_json(self.f.args.recovery_receipt, dict(original, **{k:v}))
            self.blocked()
        self.f.args.recovery_receipt.unlink(); self.blocked()
        self.sync_recovery_fixture()
        r = subject.verify(self.f.args)
        self.assertTrue(r['signed_recovery_receipt_checked'])
        self.assertFalse(r['remote_recovery_independently_observed'])

    def test_without_synthetic_hash_oracle_wrong_unsigned_bytes_block(self):
        with patch.object(permanent.gate, 'sha256', side_effect=self.actual_sha):
            self.blocked()
        self.f.gate_mock.assert_not_called()

    def test_recovery_receipt_mutation_and_output_overlap_block(self):
        def mutate(*args):
            self.f.args.recovery_receipt.write_text('{}')
            return self.f.manifest
        self.f.manifest_mock.side_effect = mutate; self.blocked()
        self.f.manifest_mock.side_effect = None
        self.sync_recovery_fixture()
        self.f.args.output = self.f.args.recovery_receipt
        argv = [v for k, value in vars(self.f.args).items()
                for v in ('--'+k.replace('_','-'), str(value))]
        before = self.f.args.recovery_receipt.read_bytes()
        with patch('builtins.print'):
            self.assertEqual(subject.main(argv), 1)
        self.assertEqual(before, self.f.args.recovery_receipt.read_bytes())


if __name__ == '__main__':
    unittest.main()
