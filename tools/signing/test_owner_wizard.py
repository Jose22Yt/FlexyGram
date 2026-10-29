"""Lifecycle/recovery tests using fake bytes and mocked tools. Never generates a key."""
import contextlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import owner_wizard as wizard

FAKE_KEY = b'NOT_A_KEY: synthetic test bytes'
FINGERPRINT = 'a' * 64
PASSWORD = 'SYNTHETIC_NON_SECRET_TEST_INPUT_123456'
REPORT = dict(status='PASS', sha256=FINGERPRINT, private_key='POSSESSION_VERIFIED',
              public_key='RSA-3072', signature='SHA256withRSA', not_before='TEST', not_after='TEST')


class OwnerWizardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.vault = self.root / 'vault'
        self.vault.mkdir(mode=0o700)
        self.state = dict(package=wizard.PACKAGE, alias=wizard.ALIAS, status='PENDING', backups=[])
        self.guard = patch('owner_wizard.subprocess.run', side_effect=AssertionError('No real tool execution permitted in wizard tests'))
        self.guard.start()
        self.addCleanup(self.guard.stop)

    def existing_original(self):
        store = self.vault / 'flexygram-release.p12'
        store.write_bytes(FAKE_KEY)
        (self.vault / 'flexygram-release.cer').write_bytes(b'FAKE_PUBLIC_CERT')
        return store

    def targets(self):
        result = []
        for name in ['support-A', 'support-B']:
            directory = self.root / name
            directory.mkdir()
            path = directory / 'backup.age'
            path.write_bytes(b'FAKE_ENCRYPTED_BACKUP')
            result.append(path)
        return result

    def test_hosted_environment_cannot_generate(self):
        with patch('owner_wizard.sys.stdin.isatty', return_value=True), patch('owner_wizard.sys.stderr.isatty', return_value=True), patch.dict('owner_wizard.os.environ', {'CI': 'true'}, clear=True):
            with self.assertRaises(wizard.CustodyError):
                wizard.runtime_preflight()

    def test_pinned_identity_is_never_replaced_when_original_is_missing(self):
        self.state.update(sha256=FINGERPRINT, status='KEY_VERIFIED_BACKUPS_PENDING')
        with patch('owner_wizard.private_command') as command, patch('builtins.input') as prompt:
            with self.assertRaises(wizard.CustodyError):
                wizard.create_or_resume(self.vault, PASSWORD, self.state)
            command.assert_not_called()
            prompt.assert_not_called()

    def test_interrupted_generation_without_original_does_not_generate_again(self):
        self.state['status'] = 'GENERATION_STARTED_NOT_CUSTODIED'
        with patch('owner_wizard.private_command') as command:
            with self.assertRaises(wizard.CustodyError):
                wizard.create_or_resume(self.vault, PASSWORD, self.state)
            command.assert_not_called()

    def test_existing_original_is_inspected_without_regeneration(self):
        store = self.existing_original()
        with patch('owner_wizard.inspect', return_value=REPORT), patch('owner_wizard.private_command') as private, patch('owner_wizard.subprocess.run', return_value=subprocess.CompletedProcess([], 0)), patch('builtins.input') as prompt:
            wizard.create_or_resume(self.vault, PASSWORD, self.state)
            private.assert_not_called()
            prompt.assert_not_called()
        self.assertEqual(store.read_bytes(), FAKE_KEY)
        self.assertEqual(wizard.load_state(self.vault)['sha256'], FINGERPRINT)

    def test_new_generation_uses_password_env_names_without_password_arguments(self):
        def simulated(command, password):
            self.assertNotIn(password, command)
            if '-genkeypair' in command:
                self.assertIn('-storepass:env', command)
                self.assertIn('-keypass:env', command)
                (self.vault / 'flexygram-release.p12').write_bytes(FAKE_KEY)
            else:
                self.assertIn('-exportcert', command)
                (self.vault / 'flexygram-release.cer').write_bytes(b'FAKE_CERT')
            return ''
        with patch('builtins.input', return_value='GENERAR'), patch('owner_wizard.private_command', side_effect=simulated), patch('owner_wizard.inspect', return_value=REPORT), patch('owner_wizard.subprocess.run', return_value=subprocess.CompletedProcess([], 0)):
            wizard.create_or_resume(self.vault, PASSWORD, self.state)
        self.assertNotIn(PASSWORD, (self.vault / 'custody-state.json').read_text())

    def test_child_password_never_enters_command_arguments_or_parent_environment(self):
        def simulated(command, **kwargs):
            self.assertNotIn(PASSWORD, command)
            self.assertEqual(kwargs['env'][wizard.PASSWORD_ENV], PASSWORD)
            return subprocess.CompletedProcess(command, 0, stdout='PUBLIC_ONLY', stderr='')
        with patch('owner_wizard.subprocess.run', side_effect=simulated), patch.dict('owner_wizard.os.environ', {}, clear=True):
            self.assertEqual(wizard.private_command(['fake-tool'], PASSWORD), 'PUBLIC_ONLY')
            self.assertNotIn(wizard.PASSWORD_ENV, wizard.os.environ)

    def test_existing_encrypted_backup_is_never_overwritten(self):
        store = self.existing_original()
        target = self.targets()[0]
        with self.assertRaises(FileExistsError):
            wizard.encrypt_new(store, target)
        self.assertEqual(target.read_bytes(), b'FAKE_ENCRYPTED_BACKUP')

    def test_failed_encryption_removes_only_its_partial_backup(self):
        store = self.existing_original()
        target = self.root / 'new.age'
        with patch('owner_wizard.subprocess.run', return_value=subprocess.CompletedProcess([], 1)):
            with self.assertRaises(wizard.CustodyError):
                wizard.encrypt_new(store, target)
        self.assertFalse(target.exists())
        self.assertEqual(store.read_bytes(), FAKE_KEY)

    def test_mismatching_recovery_is_rejected_and_plaintext_temp_removed(self):
        store = self.existing_original()
        def simulated(command, **kwargs):
            kwargs['stdout'].write(b'WRONG_RECOVERY')
            return subprocess.CompletedProcess(command, 0)
        with patch('owner_wizard.subprocess.run', side_effect=simulated), patch('owner_wizard.inspect') as inspect:
            with self.assertRaises(wizard.CustodyError):
                wizard.restore_and_verify(store, self.targets()[0], PASSWORD, FINGERPRINT, self.vault)
            inspect.assert_not_called()
        self.assertEqual(list(self.vault.glob('.recovery-*')), [])
        self.assertEqual(store.read_bytes(), FAKE_KEY)

    def test_successful_recovery_checks_same_pinned_identity_and_cleans_temp(self):
        store = self.existing_original()
        def simulated(command, **kwargs):
            kwargs['stdout'].write(FAKE_KEY)
            return subprocess.CompletedProcess(command, 0)
        with patch('owner_wizard.subprocess.run', side_effect=simulated), patch('owner_wizard.inspect', return_value=REPORT) as inspect:
            wizard.restore_and_verify(store, self.targets()[0], PASSWORD, FINGERPRINT, self.vault)
            self.assertEqual(inspect.call_args.args[2], FINGERPRINT)
        self.assertEqual(list(self.vault.glob('.recovery-*')), [])

    def test_symlink_and_same_directory_are_not_two_backup_destinations(self):
        a, b = self.targets()
        link = self.root / 'link.age'
        link.symlink_to(a)
        with self.assertRaises(wizard.CustodyError):
            wizard.backup_target(str(link), self.vault, [])
        with self.assertRaises(wizard.CustodyError):
            wizard.backup_target(str(a.parent / 'other.age'), self.vault, [a])
        self.assertEqual(wizard.backup_target(str(b), self.vault, [a]), b)

    def run_simulated_setup(self, confirmation, fail_second=False):
        store = self.existing_original()
        a, b = self.targets()
        calls = [None, wizard.CustodyError('Simulated restore failure')] if fail_second else [None, None]
        with patch('builtins.input', side_effect=[str(a), str(b), confirmation]), patch('owner_wizard.ask_password', return_value=PASSWORD), patch('owner_wizard.create_or_resume', return_value=(store, REPORT)), patch('owner_wizard.restore_and_verify', side_effect=calls), contextlib.redirect_stdout(io.StringIO()):
            return wizard.run_setup(self.vault)

    def test_two_restores_without_owner_confirmation_cannot_complete(self):
        self.assertEqual(self.run_simulated_setup('NO'), 2)
        self.assertEqual(wizard.load_state(self.vault)['status'], 'TWO_RESTORES_VERIFIED_OWNER_CONFIRMATION_PENDING')
        self.assertFalse((self.vault / 'public-verification.json').exists())

    def test_failure_of_second_restore_cannot_complete(self):
        with self.assertRaises(wizard.CustodyError):
            self.run_simulated_setup('CONFIRMO', fail_second=True)
        self.assertEqual(len(wizard.load_state(self.vault)['backups']), 1)
        self.assertFalse((self.vault / 'public-verification.json').exists())

    def test_failed_revalidation_demotes_old_custody_without_replacing_original(self):
        store = self.existing_original()
        self.state.update(sha256=FINGERPRINT, status='OWNER_ATTESTED_AFTER_TWO_RESTORES')
        wizard.write_state(self.vault, self.state)
        a, b = self.targets()
        with patch('builtins.input', side_effect=[str(a), str(b)]), patch('owner_wizard.ask_password', return_value=PASSWORD), patch('owner_wizard.inspect', side_effect=wizard.CustodyError('Fingerprint mismatch')), patch('owner_wizard.private_command') as command, contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(wizard.CustodyError):
                wizard.run_setup(self.vault)
            command.assert_not_called()
        self.assertEqual(wizard.load_state(self.vault)['status'], 'REVALIDATION_PENDING')
        self.assertEqual(store.read_bytes(), FAKE_KEY)

    def test_public_report_cannot_follow_a_symlink_to_destroy_the_original(self):
        store = self.existing_original()
        report = self.vault / 'public-verification.json'
        report.symlink_to(store)
        self.assertEqual(self.run_simulated_setup('CONFIRMO'), 0)
        self.assertFalse(report.is_symlink())
        self.assertEqual(store.read_bytes(), FAKE_KEY)

    def test_confirmed_local_result_contains_no_private_paths_password_or_key(self):
        self.assertEqual(self.run_simulated_setup('CONFIRMO'), 0)
        text = (self.vault / 'public-verification.json').read_text()
        report = json.loads(text)
        self.assertEqual(report['custody'], 'OWNER_ATTESTED_AFTER_TWO_RESTORES')
        for sensitive in [PASSWORD, str(self.root), FAKE_KEY.decode()]:
            self.assertNotIn(sensitive, text)
        self.assertEqual(report['android_apk'], 'NOT_TESTED')
        self.assertEqual((self.vault / 'flexygram-release.p12').read_bytes(), FAKE_KEY)


if __name__ == '__main__':
    unittest.main()
