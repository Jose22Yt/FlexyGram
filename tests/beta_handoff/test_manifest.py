"""Execute the real PR23 binary-manifest validator with synthetic aapt2 output."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/beta_development'))
import review_apk

PACKAGE = review_apk.PACKAGE


def dump(category=True, application='org.telegram.messenger.ApplicationLoader'):
    text = f'''E: manifest
  A: package="{PACKAGE}"
  E: uses-sdk
    A: android:minSdkVersion=0x18
    A: android:targetSdkVersion=0x24
  E: uses-permission
    A: android:name="android.permission.ACCESS_NETWORK_STATE"
  E: uses-permission
    A: android:name="{PACKAGE}.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION"
  E: permission
    A: android:name="{PACKAGE}.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION"
    A: android:protectionLevel=0x2
  E: application
    A: android:name="{application}"
    A: android:debuggable=(type 0x12)0xffffffff
    A: android:allowBackup=(type 0x12)0x0
    A: android:usesCleartextTraffic=(type 0x12)0x0
    E: activity
      A: android:name="{review_apk.ENTRY}"
      A: android:exported=(type 0x12)0x0
    E: activity-alias
      A: android:name="{review_apk.LAUNCHER}"
      A: android:targetActivity="{review_apk.ENTRY}"
      A: android:exported=(type 0x12)0xffffffff
      E: intent-filter
        E: action
          A: android:name="android.intent.action.MAIN"
'''
    if category:
        text += '        E: category\n          A: android:name="android.intent.category.LAUNCHER"\n'
    return text


class ManifestRegressionTests(unittest.TestCase):
    def check(self, text):
        with patch.object(review_apk, 'command', return_value=text):
            return review_apk.binary_manifest(Path('synthetic.apk'), Path('not-executed-aapt2'))

    def test_valid_beta_launcher_contract(self):
        self.assertEqual(self.check(dump())['package'], PACKAGE)

    def test_missing_launcher_category_must_fail(self):
        with self.assertRaisesRegex(ValueError, 'launcher intent'):
            self.check(dump(category=False))

    def test_current_optional_multiwindow_category_remains_compatible(self):
        text = dump() + '        E: category\n          A: android:name="android.intent.category.MULTIWINDOW_LAUNCHER"\n'
        self.assertEqual(self.check(text)['package'], PACKAGE)

    def test_arbitrary_launcher_category_is_rejected(self):
        text = dump() + '        E: category\n          A: android:name="synthetic.unapproved.category"\n'
        with self.assertRaisesRegex(ValueError, 'launcher intent'):
            self.check(text)

    def test_wrong_application_initializer_must_fail(self):
        with self.assertRaisesRegex(ValueError, 'initializer'):
            self.check(dump(application='synthetic.UnrelatedApplication'))


if __name__ == '__main__':
    unittest.main()
