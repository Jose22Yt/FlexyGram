"""Synthetic, strictly offline regression tests for Android evidence validation."""
from __future__ import annotations

import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

AUDIT = Path(__file__).resolve().parents[2] / 'tools/android_lab_evidence/check.py'
spec = importlib.util.spec_from_file_location('flexygram_lab_evidence_gate', AUDIT)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def fixture():
    def run(api, page):
        return {
            'api': api, 'abi': 'arm64-v8a', 'page_size_bytes': page,
            'package': gate.PACKAGE, 'permission_internet': False,
            'startup': 'pass', 'jni': 'pass', 'chaquopy': 'pass', 'python': 'pass',
            'native_loader_errors': 0, 'fatal_exceptions': 0, 'anrs': 0,
            'network_attempts': 0, 'libraries': dict(gate.LIBRARIES),
            'cases': {x: 'pass' for x in gate.CASE_NAMES},
        }
    return {'schema': 1, 'apk_sha256': gate.APK_SHA256,
            'cert_sha256': gate.CERT_SHA256,
            'profiles': {'api24': run(24, 4096), '16k': run(35, 16384)}}


class EvidenceContractTests(unittest.TestCase):
    def setUp(self):
        self.report = fixture()

    def assert_blocked(self, edit, reason):
        state = copy.deepcopy(self.report)
        edit(state)
        actual = gate.validate(state)
        self.assertEqual(actual['status'], 'BLOCKED')
        self.assertIn(reason, actual['reasons'])
        self.assertFalse(actual['runtime_certified'])

    def test_valid_fixture_is_never_claimed_as_android_certification(self):
        r = gate.validate(self.report)
        self.assertEqual(r['status'], 'CONSISTENT_SELF_REPORTED_EVIDENCE_REQUIRES_HUMAN_REVIEW')
        self.assertFalse(r['runtime_certified'])
        self.assertEqual(r['profiles_checked'], ['api24', '16k'])
        self.assertEqual(r['case_count_per_profile'], 12)
        self.assertEqual(r['library_count_per_profile'], 4)

    def test_missing_profile_is_blocked(self):
        self.assert_blocked(lambda x: x['profiles'].pop('16k'), 'missing_or_extra_lab_profile')

    def test_extra_profile_is_blocked(self):
        self.assert_blocked(lambda x: x['profiles'].update({'fake': {}}), 'missing_or_extra_lab_profile')

    def test_wrong_apk_hash_is_blocked(self):
        self.assert_blocked(lambda x: x.update(apk_sha256='0' * 64), 'apk_digest_mismatch')

    def test_wrong_cert_is_blocked(self):
        self.assert_blocked(lambda x: x.update(cert_sha256='a' * 64), 'lab_signer_mismatch')

    def test_wrong_arm_abi_is_blocked(self):
        self.assert_blocked(lambda x: x['profiles']['api24'].update(abi='x86_64'), 'api24:wrong_abi')

    def test_16k_profile_wrong_pages_is_blocked(self):
        self.assert_blocked(lambda x: x['profiles']['16k'].update(page_size_bytes=4096), '16k:wrong_page_size')

    def test_api24_requires_exact_api(self):
        self.assert_blocked(lambda x: x['profiles']['api24'].update(api=27), 'api24:wrong_android_api')

    def test_16k_requires_modern_api(self):
        self.assert_blocked(lambda x: x['profiles']['16k'].update(api=34), '16k:wrong_android_api')

    def test_bool_cannot_pass_as_numeric_zero(self):
        self.assert_blocked(lambda x: x['profiles']['api24'].update(anrs=False), 'api24:anrs_not_zero')

    def test_jni_failure_is_blocked(self):
        self.assert_blocked(lambda x: x['profiles']['16k'].update(jni='error'), '16k:jni_not_pass')

    def test_chaquopy_failure_is_blocked(self):
        self.assert_blocked(lambda x: x['profiles']['api24'].update(chaquopy='skip'), 'api24:chaquopy_not_pass')

    def test_unexpected_network_activity_is_blocked(self):
        self.assert_blocked(lambda x: x['profiles']['16k'].update(network_attempts=1), '16k:network_attempts_not_zero')

    def test_internet_permission_is_blocked(self):
        self.assert_blocked(lambda x: x['profiles']['api24'].update(permission_internet=True), 'api24:internet_not_denied')

    def test_missing_native_library_is_blocked(self):
        self.assert_blocked(lambda x: x['profiles']['16k']['libraries'].pop('libxml2.so'),
                            '16k:library_inventory_incomplete')

    def test_changed_library_hash_is_blocked(self):
        self.assert_blocked(lambda x: x['profiles']['api24']['libraries'].update({'libxslt.so': '0'*64}),
                            'api24:library_digest_mismatch:libxslt.so')

    def test_missing_runtime_case_is_blocked(self):
        name = sorted(gate.CASE_NAMES)[0]
        self.assert_blocked(lambda x: x['profiles']['api24']['cases'].pop(name),
                            'api24:runtime_cases_incomplete')

    def test_skipped_runtime_case_is_blocked(self):
        name = sorted(gate.CASE_NAMES)[0]
        self.assert_blocked(lambda x: x['profiles']['16k']['cases'].update({name: 'skip'}),
                            '16k:case_not_pass:' + name)

    def test_extra_unknown_case_is_blocked(self):
        self.assert_blocked(lambda x: x['profiles']['16k']['cases'].update({'fake_test': 'pass'}),
                            '16k:runtime_cases_incomplete')

    def test_unexpected_private_fields_are_blocked(self):
        self.assert_blocked(lambda x: x.update(api_token='PRIVATE_TEST_VALUE'), 'invalid_schema_or_fields')
        self.assertNotIn('PRIVATE_TEST_VALUE', json.dumps(gate.validate(self.report)))

    def test_duplicate_json_key_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'dup.json'
            path.write_text('{"schema":1,"schema":2}', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'duplicate_json_key'):
                gate.load(path)

    def test_symlink_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            actual = Path(td) / 'actual.json'
            actual.write_text('{}')
            link = Path(td) / 'link.json'
            link.symlink_to(actual)
            with self.assertRaisesRegex(ValueError, 'unapproved_evidence_file'):
                gate.load(link)

    def test_cli_synthetic_evidence_emits_no_private_data(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'evidence.json'
            path.write_text(json.dumps(self.report))
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                rc = gate.main(['--evidence', str(path)])
            self.assertEqual(rc, 0)
            data = json.loads(out.getvalue())
            self.assertFalse(data['runtime_certified'])
            self.assertNotIn(str(path), out.getvalue())

    def test_cli_missing_evidence_is_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                rc = gate.main(['--evidence', str(Path(td) / 'missing.json')])
            self.assertEqual(rc, 1)
            self.assertEqual(json.loads(out.getvalue())['status'], 'BLOCKED')


if __name__ == '__main__':
    unittest.main()
