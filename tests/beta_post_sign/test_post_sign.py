"""Synthetic ZIPs and tool doubles only. No certificates, signing, APK or Android."""
from pathlib import Path
import json
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/beta_handoff'))
import post_sign as subject


class BetaPostSignTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.args = SimpleNamespace(
            unsigned_apk=self.root/'unsigned.apk', signed_apk=self.root/'signed.apk',
            recovered_apk=self.root/'recovered.apk', approval=self.root/'approval.json',
            build_receipt=self.root/'build.json', unsigned_review=self.root/'review.json',
            classes=self.root/'classes', build_tools=self.root/'tools', ndk=self.root/'ndk',
            javap=self.root/'javap', output=self.root/'result.json',
            commit='a'*40, version_code='1261', version_name='13.0.2')
        self.payload = {'AndroidManifest.xml': b'synthetic binary manifest',
                        'classes.dex': b'synthetic dex',
                        'resources.arsc': b'synthetic resources',
                        'lib/arm64-v8a/libtest.so': b'synthetic native bytes',
                        'assets/chaquopy/requirements-common.imy': b'synthetic Python'}
        self.write_zip(self.args.unsigned_apk, self.payload)
        self.write_zip(self.args.signed_apk, dict(self.payload, **{'META-INF/BETA.SF': b'synthetic'}))
        self.args.unsigned_sha256 = subject.gate.sha256(self.args.unsigned_apk)
        self.refresh_signed()
        class_file = self.args.classes/'org/telegram/messenger/BuildConfig.class'
        class_file.parent.mkdir(parents=True)
        class_file.write_bytes(b'synthetic constants')
        self.args.build_tools.mkdir()
        for name in ('apksigner', 'zipalign', 'aapt2'):
            (self.args.build_tools/name).write_text('inert tool fixture', encoding='utf-8')
        self.manifest = {'package': subject.PACKAGE, 'permissions': []}
        self.baseline = dict(status='BETA_UNSIGNED_STATIC_REVIEW_ONLY_PENDING_ANDROID',
                             apk_sha256=self.args.unsigned_sha256,
                             version_code='1261', version_name='13.0.2',
                             input_bytes_checked=True, compiled_buildconfig_closed=True,
                             zipalign_16k=True, native_acceptance={'blockers': []},
                             manifest=self.manifest)
        self.write_json(self.args.unsigned_review, self.baseline)
        self.receipt = dict(schema=1, package=subject.PACKAGE, source_commit='a'*40,
                            version_code='1261', version_name='13.0.2',
                            unsigned_apk_sha256=self.args.unsigned_sha256,
                            unsigned_review_sha256=subject.gate.sha256(self.args.unsigned_review),
                            classes=subject.class_inventory(self.args.classes))
        self.identity = dict(schema=1, status='CUSTODY_VERIFIED_BETA_SIGNING_AUTHORIZED',
                             approval_scope=subject.SCOPE, package=subject.PACKAGE,
                             apk_signing_authorized=True, production_use_allowed=False,
                             private_key_backed_up=True, custody_recovery_verified=True,
                             approval_reference='synthetic approval only',
                             approved_unsigned_apk_sha256=self.args.unsigned_sha256,
                             certificate_sha256='b'*64)
        self.refresh_receipt()
        self.cert_output = ('Verified using v2 scheme (APK Signature Scheme v2): true\n'
                            'Signer #1 certificate SHA-256 digest: ' + 'b'*64 + '\n')
        self.sign_result = 0
        self.align_result = 0
        self.signature_runner = lambda *a, **k: subprocess.CompletedProcess(
            a[0], self.sign_result, self.cert_output, '')
        self.alignment_runner = lambda *a, **k: subprocess.CompletedProcess(
            a[0], self.align_result, '', '')
        real_signature = subject.signature.check_signature
        real_alignment = subject.signature.check_alignment
        self.gate_mock = self.enterContext(patch.object(subject.gate, 'run', return_value=self.baseline))
        self.enterContext(patch.object(subject.signature, 'check_signature',
            side_effect=lambda *a: real_signature(*a, runner=self.signature_runner)))
        self.enterContext(patch.object(subject.signature, 'check_alignment',
            side_effect=lambda *a: real_alignment(*a, runner=self.alignment_runner)))
        self.manifest_mock = Mock(return_value=self.manifest)
        self.enterContext(patch.dict(sys.modules, {'review_apk':
            SimpleNamespace(binary_manifest=self.manifest_mock)}))

    def write_json(self, path, data):
        path.write_text(json.dumps(data), encoding='utf-8')

    def write_zip(self, path, members):
        with zipfile.ZipFile(path, 'w') as archive:
            for name, value in members.items():
                archive.writestr(name, value)

    def refresh_signed(self):
        self.args.signed_sha256 = subject.gate.sha256(self.args.signed_apk)
        self.args.recovered_apk.write_bytes(self.args.signed_apk.read_bytes())

    def refresh_receipt(self):
        self.write_json(self.args.build_receipt, self.receipt)
        self.identity['build_receipt_sha256'] = subject.gate.sha256(self.args.build_receipt)
        self.write_json(self.args.approval, self.identity)

    def blocked(self):
        with self.assertRaises((ValueError, OSError, subprocess.SubprocessError)):
            subject.verify(self.args)

    def test_synthetic_success_requires_real_primitive_calls_and_gate(self):
        result = subject.verify(self.args)
        self.assertTrue(result['payload_identical'])
        self.assertTrue(result['apk_v2_min_sdk_24_verified'])
        self.assertFalse(result['android_runtime_validated'])
        self.assertFalse(result['installation_authorized'])
        self.assertFalse(result['remote_recovery_independently_observed'])
        self.gate_mock.assert_called_once()
        self.manifest_mock.assert_called_once()

    def test_wrong_certificate_blocks(self):
        self.cert_output = self.cert_output.replace('b'*64, 'c'*64)
        self.blocked()

    def test_invalid_v2_and_multiple_signers_block(self):
        original = self.cert_output
        for output in (original.replace(': true', ': false'),
                       original + 'Signer #2 certificate SHA-256 digest: ' + 'b'*64 + '\n'):
            with self.subTest(output=output[:24]):
                self.cert_output = output
                self.blocked()

    def test_post_sign_tamper_blocks_even_with_updated_expected_hash(self):
        # Simulates invalid cryptographic verification after a byte modification.
        with self.args.signed_apk.open('ab') as stream:
            stream.write(b'tampered')
        self.refresh_signed()
        self.sign_result = 1
        self.blocked()

    def test_payload_changes_and_added_removed_entries_block(self):
        for name in self.payload:
            with self.subTest(member=name, action='changed'):
                changed = dict(self.payload)
                changed[name] += b'changed'
                self.write_zip(self.args.signed_apk, changed)
                self.refresh_signed()
                self.blocked()
        for changed in (dict(self.payload, injected=b'new'), {k:v for k,v in self.payload.items() if k!='classes.dex'}):
            self.write_zip(self.args.signed_apk, changed)
            self.refresh_signed()
            self.blocked()

    def test_hash_mismatches_block(self):
        for name in ('unsigned_sha256', 'signed_sha256'):
            original = getattr(self.args, name)
            setattr(self.args, name, 'c'*64)
            self.blocked()
            setattr(self.args, name, original)

    def test_alignment_failure_blocks(self):
        self.align_result = 1
        self.blocked()

    def test_missing_and_diagnostic_authorization_block_before_tools(self):
        for change in ({'apk_signing_authorized':False},
                       {'approval_scope':'Diagnostic_lab_only'},
                       {'status':'DRAFT_NOT_AUTHORIZED'},
                       {'private_key_backed_up':False},
                       {'custody_recovery_verified':False},
                       {'production_use_allowed':True}):
            original = dict(self.identity)
            self.identity.update(change)
            self.refresh_receipt()
            self.blocked()
            self.identity = original
        self.gate_mock.assert_not_called()

    def test_tool_errors_and_timeouts_block(self):
        for error in (FileNotFoundError(), subprocess.TimeoutExpired('synthetic', 120)):
            self.signature_runner = Mock(side_effect=error)
            self.blocked()

    def test_gate_blocker_or_changed_manifest_blocks(self):
        self.gate_mock.side_effect = ValueError('SYNTHETIC_GATE_BLOCKER')
        self.blocked()
        self.gate_mock.side_effect = None
        self.manifest_mock.return_value = {'package': subject.PACKAGE, 'permissions':['android.permission.INTERNET']}
        self.blocked()

    def test_commit_version_classes_and_review_binding_block(self):
        for field in ('source_commit', 'version_code', 'version_name'):
            original = self.receipt[field]
            self.receipt[field] = 'invalid'
            self.refresh_receipt()
            self.blocked()
            self.receipt[field] = original
        self.refresh_receipt()
        self.args.unsigned_review.write_text('{}', encoding='utf-8')
        self.blocked()
        self.write_json(self.args.unsigned_review, self.baseline)
        (self.args.classes/'org/telegram/messenger/BuildConfig.class').write_bytes(b'changed')
        self.blocked()

    def test_recovered_copy_and_input_mutation_block(self):
        self.args.recovered_apk.write_bytes(b'wrong backup')
        self.blocked()
        self.refresh_signed()
        def mutate(*args):
            self.args.signed_apk.write_bytes(b'changed during tools')
            return self.manifest
        self.manifest_mock.side_effect = mutate
        self.blocked()

    def test_duplicate_approval_json_is_rejected(self):
        self.args.approval.write_text('{"schema":1,"schema":1}', encoding='utf-8')
        self.blocked()
        self.gate_mock.assert_not_called()

    def test_zip_path_and_duplicate_member_rejected(self):
        for changed in (dict(self.payload, **{'../escape': b'bad'}),
                        dict(self.payload, **{'/absolute': b'bad'})):
            self.write_zip(self.args.signed_apk, changed)
            self.refresh_signed()
            self.blocked()
        self.write_zip(self.args.signed_apk, self.payload)
        with zipfile.ZipFile(self.args.signed_apk, 'a') as archive:
            archive.writestr('classes.dex', b'duplicate')
        self.refresh_signed()
        self.blocked()

    def test_cli_blocks_without_exposing_tool_output_or_overwriting_report(self):
        argv = []
        for name, value in vars(self.args).items():
            argv.extend(['--' + name.replace('_', '-'), str(value)])
        with patch.object(subject, 'verify', side_effect=RuntimeError('SYNTHETIC_PRIVATE_VALUE')), patch('builtins.print') as printed:
            self.assertEqual(subject.main(argv), 1)
            result = self.args.output.read_text()
            self.assertNotIn('SYNTHETIC_PRIVATE_VALUE', result)
            self.assertEqual(json.loads(result)['status'], 'BLOCKED')
            self.assertNotIn('SYNTHETIC_PRIVATE_VALUE', str(printed.call_args_list))
        previous = self.args.output.read_bytes()
        with patch('builtins.print'):
            self.assertEqual(subject.main(argv), 1)
        self.assertEqual(self.args.output.read_bytes(), previous)


if __name__ == '__main__':
    unittest.main()
