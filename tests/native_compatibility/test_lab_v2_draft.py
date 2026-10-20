"""Host-only tests of the non-executable draft for a future lab v2 contract."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import create_lab_v2_draft as lab


class V2DraftTests(unittest.TestCase):
    def setUp(self):
        self.summary = {
            'status': 'UNSIGNED_EVIDENCE_REVIEWED_SIGNING_BLOCKED',
            'signing_authorized': False, 'android_runtime_validated': False,
            'distribution_allowed': False, 'unsigned_apk_sha256': 'a'*64,
            'unsigned_apk_bytes': 113080783, 'source_head': 'b'*40,
            'native_elf_sha256': {'libxml2.so': 'c'*64},
        }
        self.previous = {
            'schema': 1, 'reviewed_head': 'e'*40,
            'case_ids': ['test' + str(i) for i in range(12)],
            'target_package': 'io.github.jose22yt.flexygram.diagnostic',
            'runner_package': 'runner', 'runner_class': 'LabInstrumentation',
            'jni_library': 'libtmessages.49.so', 'runtime_cases_sha256': 'f'*64,
            'font_sha256': '1'*64, 'font_license_sha256': '2'*64,
            'policy_scope': 'diagnostic-fixture',
        }
        self.audit = {'libraries': [{
            'path': 'app.apk!lib/arm64-v8a/libtmessages.49.so',
            'machine': 'EM_AARCH64', 'load_4k': True, 'load_16k': True,
            'sha256': 'd'*64,
        }]}
        self.wheels = {'wheels': [
            {'filename': 'wheel'+str(i), 'sha256': str(i%10)*64, 'rebuilt': i<3}
            for i in range(18)
        ]}
        self.apk = {'apk_sha256': 'a'*64, 'signature': 'absent'}

    def build(self):
        return lab.make_draft(self.summary, self.previous,
                              self.audit, self.wheels, self.apk)

    def test_unsigned_draft_pins_data_but_cannot_activate_signing(self):
        result = self.build()
        self.assertEqual(result['status'], lab.STATUS)
        self.assertEqual(result['jni_sha256_from_unsigned_apk_audit'], 'd'*64)
        self.assertEqual(len(result['wheel_sha256']), 18)
        self.assertEqual(len(result['cases']), 12)
        self.assertFalse(result['apk_signing_authorized'])
        self.assertFalse(result['runtime_contract_activated'])
        self.assertIsNone(result['signed_apk_sha256'])
        self.assertIsNone(result['certificate_sha256'])

    def test_duplicate_jni_blocks(self):
        self.audit['libraries'].append(copy.deepcopy(self.audit['libraries'][0]))
        with self.assertRaisesRegex(ValueError, 'Exactly one verified'):
            self.build()

    def test_missing_functional_case_blocks(self):
        self.previous['case_ids'].pop()
        with self.assertRaisesRegex(ValueError, 'Historical lab v1 invalid'):
            self.build()

    def test_signed_source_receipt_blocks(self):
        self.apk['signature'] = 'signed'
        with self.assertRaisesRegex(ValueError, 'Unsigned source receipt'):
            self.build()

    def test_forged_runtime_success_blocks(self):
        self.summary['android_runtime_validated'] = True
        with self.assertRaisesRegex(ValueError, 'reviewed unsigned'):
            self.build()

    def test_no_output_inside_checkout(self):
        with tempfile.TemporaryDirectory() as root:
            with patch.object(lab, 'prepare', return_value=self.build()):
                with patch.object(lab.review, 'ROOT', Path(root)):
                    self.assertEqual(lab.main(['--output', str(Path(root)/'draft.json')]), 1)
            self.assertFalse((Path(root)/'draft.json').exists())

    def test_private_new_draft_file_created_and_overwrite_blocked(self):
        with tempfile.TemporaryDirectory() as root:
            with patch.object(lab, 'prepare', return_value=self.build()):
                path = Path(root)/'draft.json'
                self.assertEqual(lab.main(['--output', str(path)]), 0)
                self.assertEqual(json.loads(path.read_text())['status'], lab.STATUS)
                self.assertEqual(lab.main(['--output', str(path)]), 1)


if __name__ == '__main__':
    unittest.main()
