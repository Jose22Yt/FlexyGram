"""Synthetic post-signature contract regressions; no key, APK signing or Android."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import verify_post_sign_diagnostic as post

CERT = 'a' * 64
SOURCE = 'b' * 64


class PostSignTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        self.unsigned = root / 'unsigned.apk'
        self.signed = root / 'signed.apk'
        self.identity = root / 'identity.json'
        self.signer = root / 'apksigner'
        self.signer.write_text('synthetic, never executed')
        with zipfile.ZipFile(self.unsigned, 'w') as z:
            z.writestr('AndroidManifest.xml', b'<manifest diagnostic="true" />')
        with zipfile.ZipFile(self.signed, 'w') as z:
            z.writestr('AndroidManifest.xml', b'<manifest diagnostic="true" />')
            z.writestr('META-INF/SIGNER.RSA', b'fake synthetic signature')
        self.record = {
            'status': 'CUSTODY_VERIFIED_SIGNING_AUTHORIZED',
            'apk_signing_authorized': True,
            'production_use_allowed': False,
            'private_key_backed_up': True,
            'custody_recovery_verified': True,
            'approval_scope': 'Diagnostic_lab_only',
            'approved_unsigned_apk_sha256': SOURCE,
            'approval_reference': 'test-authorized-only',
            'certificate_sha256': CERT,
        }
        self.save()

    def save(self):
        self.identity.write_text(json.dumps(self.record))

    @staticmethod
    def runner(output=None, returncode=0):
        text = output if output is not None else (
            'Verified using v2 scheme (APK Signature Scheme v2): true\n'
            'Signer #1 certificate SHA-256 digest: ' + CERT + '\n'
        )
        def fake(*args, **kwargs):
            return subprocess.CompletedProcess(args[0], returncode, text, '')
        return fake

    def check(self, runner=None):
        with patch.object(post.unsigned, 'verify', return_value={'sha256': SOURCE}):
            return post.verify(self.unsigned, self.signed, self.identity, self.signer,
                               signature_runner=runner or self.runner())

    def test_synthetic_authorized_metadata_produces_static_only_result(self):
        result = self.check()
        self.assertEqual(result['status'], 'SIGNED_STATIC_REVIEW_ONLY_PENDING_ANDROID')
        self.assertEqual(result['certificate_sha256'], CERT)
        self.assertTrue(result['apk_v2_verified'])
        self.assertFalse(result['android_runtime_validated'])
        self.assertFalse(result['distribution_allowed'])
        self.assertIsNone(result['installable'])

    def test_missing_custody_or_approval_blocks(self):
        originals = self.record.copy()
        for key, value in [
            ('apk_signing_authorized', False), ('private_key_backed_up', False),
            ('custody_recovery_verified', False), ('production_use_allowed', True),
            ('approval_scope', 'Production'),
            ('approved_unsigned_apk_sha256', '0' * 64),
        ]:
            self.record[key] = value
            self.save()
            with self.assertRaisesRegex(ValueError, 'Custody/signing authorization'):
                self.check()
            self.record = originals.copy()
        self.save()

    def test_modified_manifest_blocks(self):
        with zipfile.ZipFile(self.signed, 'w') as z:
            z.writestr('AndroidManifest.xml', b'changed')
        with self.assertRaisesRegex(ValueError, 'Signing changed APK entry'):
            self.check()

    def test_added_resource_blocks(self):
        with zipfile.ZipFile(self.signed, 'a') as z:
            z.writestr('assets/extra.bin', b'unreviewed')
        with self.assertRaisesRegex(ValueError, 'Signing changed APK entry'):
            self.check()

    def test_apk_v2_mandatory(self):
        fake = self.runner(
            'Verified using v2 scheme (APK Signature Scheme v2): false\n'
            'Signer #1 certificate SHA-256 digest: ' + CERT
        )
        with self.assertRaisesRegex(ValueError, 'scheme v2'):
            self.check(fake)

    def test_certificate_mismatch_blocks(self):
        fake = self.runner(
            'Verified using v2 scheme (APK Signature Scheme v2): true\n'
            'Signer #1 certificate SHA-256 digest: ' + 'c' * 64
        )
        with self.assertRaisesRegex(ValueError, 'certificate does not match'):
            self.check(fake)

    def test_multiple_signers_block(self):
        fake = self.runner(
            'Verified using v2 scheme (APK Signature Scheme v2): true\n'
            'Signer #1 certificate SHA-256 digest: ' + CERT + '\n'
            'Signer #2 certificate SHA-256 digest: ' + CERT
        )
        with self.assertRaisesRegex(ValueError, 'count ambiguous'):
            self.check(fake)

    def test_signer_nonzero_exit_blocks(self):
        with self.assertRaisesRegex(ValueError, 'verification failed'):
            self.check(self.runner(returncode=1))

    def test_missing_identity_file_blocks(self):
        self.identity.unlink()
        with self.assertRaisesRegex(ValueError, 'Missing/unsafe'):
            self.check()

    def test_duplicate_identity_fields_block(self):
        self.identity.write_text('{"status":"safe","status":"unsafe"}')
        with self.assertRaisesRegex(ValueError, 'Duplicate signing approval key'):
            self.check()

    def test_missing_signed_apk_blocks(self):
        self.signed.unlink()
        with self.assertRaisesRegex(ValueError, 'Missing/unsafe'):
            self.check()


if __name__ == '__main__':
    unittest.main()
