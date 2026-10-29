"""Exercise the current packaged alias and all inherited negative cases."""
import unittest
from test_verify_apk import PACKAGED_MANIFEST, PackagedLauncherVerification
from signature_verifier import has_signature_launcher
import test_verify_apk as inherited

BLUE = PACKAGED_MANIFEST.replace('ExteralessIcon', 'FlexyBlueIcon')

class SignatureLauncherPolicy(unittest.TestCase):
    def test_blue_default_and_original_negative_cases(self):
        previous = inherited.has_launcher_alias
        fixture = inherited.PACKAGED_MANIFEST
        try:
            inherited.has_launcher_alias = has_signature_launcher
            inherited.PACKAGED_MANIFEST = BLUE
            # Every original packaged-launcher positive/negative assertion applies.
            suite = unittest.TestSuite(PackagedLauncherVerification(name)
                for name in unittest.defaultTestLoader.getTestCaseNames(PackagedLauncherVerification)
                if name.startswith(('test_accepts_', 'test_rejects_')))
            result = unittest.TestResult()
            suite.run(result)
            self.assertEqual(result.errors, [])
            self.assertEqual(result.failures, [])
            self.assertTrue(result.wasSuccessful())
        finally:
            inherited.has_launcher_alias = previous
            inherited.PACKAGED_MANIFEST = fixture

    def test_old_unknown_disabled_and_duplicate_defaults_rejected(self):
        self.assertTrue(has_signature_launcher(BLUE))
        self.assertFalse(has_signature_launcher(PACKAGED_MANIFEST))
        self.assertFalse(has_signature_launcher(BLUE.replace('FlexyBlueIcon', 'UnknownIcon')))
        alias = BLUE[BLUE.index('    E: activity-alias'):]
        self.assertFalse(has_signature_launcher(BLUE + alias))
        self.assertFalse(has_signature_launcher(BLUE + alias.replace('FlexyBlueIcon', 'ExteralessIcon')))
        self.assertTrue(has_signature_launcher(BLUE + alias.replace('FlexyBlueIcon', 'ExteralessIcon').replace(
            'android:enabled(0x0101000e)=(type 0x12)0xffffffff',
            'android:enabled(0x0101000e)=(type 0x12)0x0')))
