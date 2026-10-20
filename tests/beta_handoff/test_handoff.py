"""Synthetic files only. No Android, private APK, network, credentials or signing."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/beta_handoff'))
import gate
import archive as bundle_tool

REQUIRED = ['AndroidManifest.xml', 'resources.arsc', 'classes.dex',
            'lib/arm64-v8a/libtmessages.49.so',
            'assets/chaquopy/requirements-common.imy',
            'assets/chaquopy/stdlib-arm64-v8a.imy']


class HandoffTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.apk = self.root / 'synthetic.apk'
        self.write_apk()

    def write_apk(self, omit=None, extra=None):
        with zipfile.ZipFile(self.apk, 'w') as z:
            for name in REQUIRED:
                if name != omit:
                    z.writestr(name, b'SYNTHETIC_ONLY_NOT_AN_ANDROID_BINARY')
            if extra:
                z.writestr(extra, 'synthetic')

    def test_digest_and_inventory_precheck_only(self):
        actual = gate.precheck(self.apk, gate.sha256(self.apk))
        self.assertEqual(actual['bytes'], self.apk.stat().st_size)
        self.assertNotIn('android_executed', actual)

    def test_wrong_hash_blocks_before_importing_review_tools(self):
        with self.assertRaisesRegex(ValueError, 'APK_SHA256_MISMATCH'):
            gate.run(SimpleNamespace(apk=self.apk, sha256='0' * 64))

    def test_missing_file_is_never_a_success(self):
        with self.assertRaisesRegex(ValueError, 'APK_UNAVAILABLE'):
            gate.precheck(self.root / 'absent.apk', '0' * 64)

    def test_missing_or_empty_required_resources(self):
        for name in REQUIRED:
            self.write_apk(omit=name)
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'MISSING_REQUIRED'):
                gate.precheck(self.apk, gate.sha256(self.apk))
        self.write_apk()
        with zipfile.ZipFile(self.apk, 'a') as z:
            z.writestr('extra-empty-resource', '')
        # Empty required entries have their own fail-closed condition.
        with zipfile.ZipFile(self.apk, 'w') as z:
            for name in REQUIRED:
                z.writestr(name, b'' if name == 'resources.arsc' else b'x')
        with self.assertRaisesRegex(ValueError, 'EMPTY_REQUIRED'):
            gate.precheck(self.apk, gate.sha256(self.apk))

    def test_path_traversal_and_duplicate_members_blocked(self):
        self.write_apk(extra='../private')
        with self.assertRaisesRegex(ValueError, 'UNSAFE_APK_MEMBER'):
            gate.precheck(self.apk, gate.sha256(self.apk))
        self.write_apk()
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', UserWarning)
            with zipfile.ZipFile(self.apk, 'a') as z:
                z.writestr('classes.dex', b'duplicate')
        with self.assertRaisesRegex(ValueError, 'DUPLICATE_APK'):
            gate.precheck(self.apk, gate.sha256(self.apk))

    def test_roundtrip_bundle_after_independent_copy(self):
        bundle = self.root / 'bundle.zip'
        receipt = bundle_tool.create(self.apk, gate.sha256(self.apk), bundle)
        restored = self.root / 'recovered.zip'
        restored.write_bytes(bundle.read_bytes())
        result = bundle_tool.verify(restored, receipt['bundle_sha256'], gate.sha256(self.apk))
        self.assertFalse(result['remote_recovery_verified'])
        self.assertFalse(result['private_persistence_confirmed'])
        self.assertEqual(bundle.stat().st_mode & 0o777, 0o600)
        with self.assertRaises(FileExistsError):
            bundle_tool.create(self.apk, gate.sha256(self.apk), bundle)

    def test_corrupt_restored_bytes_fail(self):
        bundle = self.root / 'bundle.zip'
        receipt = bundle_tool.create(self.apk, gate.sha256(self.apk), bundle)
        with bundle.open('ab') as file:
            file.write(b'corruption')
        with self.assertRaisesRegex(ValueError, 'BUNDLE_SHA256_MISMATCH'):
            bundle_tool.verify(bundle, receipt['bundle_sha256'], gate.sha256(self.apk))

    def test_archive_inventory_cannot_smuggle_private_members(self):
        bundle = self.root / 'bundle.zip'
        bundle_tool.create(self.apk, gate.sha256(self.apk), bundle)
        with zipfile.ZipFile(bundle, 'a') as z:
            z.writestr('../unwanted', 'synthetic')
        with self.assertRaisesRegex(ValueError, 'BUNDLE_INVENTORY_MISMATCH'):
            bundle_tool.verify(bundle, gate.sha256(bundle), gate.sha256(self.apk))

    def test_receipt_cannot_substitute_other_apk(self):
        bundle = self.root / 'bundle.zip'
        bundle_tool.create(self.apk, gate.sha256(self.apk), bundle)
        with self.assertRaisesRegex(ValueError, 'BUNDLE_RECEIPT_MISMATCH'):
            bundle_tool.verify(bundle, gate.sha256(bundle), '0' * 64)

    def test_existing_work_archive_inventory_without_extracting(self):
        bundle = self.root / 'existing.zip'
        with zipfile.ZipFile(bundle, 'w') as z:
            z.write(self.apk, 'private/build-original.apk')
            z.writestr('logs/synthetic.log', 'synthetic')
        result = bundle_tool.inspect_existing(bundle, gate.sha256(bundle), gate.sha256(self.apk))
        self.assertEqual(result['members'], 2)
        self.assertTrue(result['all_member_bytes_read'])
        self.assertFalse(result['remote_recovery_verified'])
        self.assertEqual(set(self.root.iterdir()), {self.apk, bundle})

    def test_existing_archive_wrong_payload_or_unsafe_path_blocks(self):
        bundle = self.root / 'existing.zip'
        with zipfile.ZipFile(bundle, 'w') as z:
            z.write(self.apk, 'payload.apk')
        with self.assertRaisesRegex(ValueError, 'BUNDLE_APK_INVENTORY_OR_HASH_MISMATCH'):
            bundle_tool.inspect_existing(bundle, gate.sha256(bundle), '0' * 64)
        with zipfile.ZipFile(bundle, 'a') as z:
            z.writestr('../unwanted', 'synthetic')
        with self.assertRaisesRegex(ValueError, 'UNSAFE_BUNDLE_MEMBER'):
            bundle_tool.inspect_existing(bundle, gate.sha256(bundle), gate.sha256(self.apk))

    def test_signed_jar_is_not_accepted_for_unsigned_handoff(self):
        with zipfile.ZipFile(self.apk, 'a') as z:
            z.writestr('META-INF/SYNTHETIC.RSA', b'SYNTHETIC_NOT_A_KEY')
        with self.assertRaisesRegex(ValueError, 'APK_JAR_SIGNATURE_NOT_AUTHORIZED'):
            gate.precheck(self.apk, gate.sha256(self.apk))

    def test_gate_delegates_full_review_and_checks_version(self):
        sys.path.insert(0, str(ROOT / 'tools/beta_development'))
        import review_apk
        args = SimpleNamespace(apk=self.apk, sha256=gate.sha256(self.apk),
                               build_tools=self.root, version_code='1261', version_name='13.0.2')
        badging = "package: name='" + review_apk.PACKAGE + "' versionCode='1261' versionName='13.0.2'"
        with patch.object(review_apk, 'command', return_value=badging), patch.object(review_apk, 'review', return_value={'status': 'SYNTHETIC_DELEGATE'}) as call:
            result = gate.run(args)
            call.assert_called_once_with(args)
            self.assertFalse(result['signing_authorized'])
        with patch.object(review_apk, 'command', return_value=badging.replace('1261', '1262')), patch.object(review_apk, 'review') as call:
            with self.assertRaisesRegex(ValueError, 'BETA_PACKAGE_OR_VERSION_MISMATCH'):
                gate.run(args)
            call.assert_not_called()

    def test_subprocess_failure_cannot_leave_old_pass_or_print_private_output(self):
        import contextlib
        import io
        import subprocess
        output = self.root / 'result.json'
        output.write_text('{"status":"OLD_PASS"}')
        args = ['gate.py', '--apk', str(self.apk), '--sha256', gate.sha256(self.apk),
                '--build-tools', str(self.root), '--ndk', str(self.root), '--classes', str(self.root / 'classes'),
                '--javap', str(self.root / 'javap'), '--output', str(output), '--version-code', '1261', '--version-name', '13.0.2']
        stream = io.StringIO()
        private = 'SYNTHETIC_PRIVATE_SUBPROCESS_OUTPUT'
        for error in (subprocess.CalledProcessError(1, 'tool', output=private, stderr=private), ImportError(private), RuntimeError(private)):
            output.write_text('{"status":"OLD_PASS"}')
            with self.subTest(error=type(error).__name__), patch.object(sys, 'argv', args), patch.object(gate, 'run', side_effect=error), contextlib.redirect_stdout(stream):
                self.assertEqual(gate.main(), 1)
            self.assertEqual(json.loads(output.read_text())['status'], 'BLOCKED')
            self.assertNotIn(private, output.read_text() + stream.getvalue())



if __name__ == '__main__':
    unittest.main()
