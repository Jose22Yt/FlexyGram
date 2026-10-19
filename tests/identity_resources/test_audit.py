"""Fixture-based, network-free regression tests for the identity audit."""
import contextlib
import io
from pathlib import Path
import tempfile
import unittest

from audit import audit, main


MANIFEST = '''<manifest xmlns:android="http://schemas.android.com/apk/res/android">
<application android:label="FlexyGram Diagnostic" android:icon="@mipmap/ic_launcher_exteraless"
 android:roundIcon="@mipmap/ic_launcher_exteraless_round">
 <activity-alias android:name="org.telegram.messenger.ExteralessIcon" android:enabled="true">
  <intent-filter>
   <action android:name="android.intent.action.MAIN"/>
   <category android:name="android.intent.category.LAUNCHER"/>
  </intent-filter>
 </activity-alias>
</application></manifest>'''
POLICY = '''{"variants": {"diagnostic": {"applicationId": "io.github.jose22yt.flexygram.diagnostic", "buildEnabled": true}, "production": {"applicationId": "io.github.jose22yt.flexygram.app", "buildEnabled": false}}}'''


class IdentityAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.write('gradle/variant-policy.json', POLICY)
        self.write('TMessagesProj/src/diagnostic/AndroidManifest.xml', MANIFEST)
        self.write('TMessagesProj/src/main/res/values/strings.xml',
                   '<resources><string name="AppName">exteraless</string><string name="AppNameBeta">Telegram Beta</string></resources>')
        self.write('TMessagesProj/src/main/res/xml/auth.xml',
                   '<account-authenticator xmlns:android="http://schemas.android.com/apk/res/android" android:label="@string/AppName" android:icon="@mipmap/ic_launcher_exteraless" android:smallIcon="@mipmap/ic_launcher_exteraless_round"/>')
        self.write('settings.gradle', 'rootProject.name = "exteraless"\n')
        for name in ('ic_launcher_exteraless', 'ic_launcher_exteraless_round'):
            self.write('TMessagesProj/src/main/res/mipmap-anydpi-v26/' + name + '.xml', '<adaptive-icon/>')

    def tearDown(self):
        self.temp.cleanup()

    def write(self, path, data):
        p = self.root / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(data, encoding='utf-8')

    def codes(self):
        return {f['code'] for f in audit(self.root)['findings']}

    def test_legacy_user_visible_names_flagged_without_failing_safe_baseline(self):
        result = audit(self.root)
        self.assertEqual(result['errors'], 0)
        self.assertGreaterEqual(result['review_items'], 6)
        self.assertIn('LEGACY_VISIBLE_STRING', self.codes())
        self.assertIn('LEGACY_ACCOUNT_LABEL', self.codes())
        self.assertIn('LEGACY_PRIMARY_ICON', self.codes())
        self.assertIn('LEGACY_BUILD_NAME', self.codes())

    def test_launcher_component_identifier_is_not_a_user_visible_brand_failure(self):
        self.assertNotIn('INTERNAL_PACKAGE_NAME', self.codes())
        self.assertEqual(audit(self.root)['errors'], 0)

    def test_changed_diagnostic_identity_fails_closed(self):
        p = 'TMessagesProj/src/diagnostic/AndroidManifest.xml'
        self.write(p, MANIFEST.replace('FlexyGram Diagnostic', 'Exteraless'))
        self.assertIn('DIAGNOSTIC_LABEL', self.codes())

    def test_missing_launcher_is_error(self):
        p = 'TMessagesProj/src/diagnostic/AndroidManifest.xml'
        self.write(p, MANIFEST.replace('android.intent.category.LAUNCHER', 'android.intent.category.DEFAULT'))
        self.assertIn('DIAGNOSTIC_LAUNCHER_COUNT', self.codes())

    def test_missing_icon_resource_is_error(self):
        p = self.root / 'TMessagesProj/src/main/res/mipmap-anydpi-v26/ic_launcher_exteraless.xml'
        p.unlink()
        self.assertIn('RESOURCE_MISSING', self.codes())

    def test_policy_identity_mismatch_is_error(self):
        self.write('gradle/variant-policy.json', POLICY.replace('io.github.jose22yt.flexygram.app', 'com.example.imposter'))
        self.assertIn('IDENTITY_ID_MISMATCH', self.codes())

    def test_strict_only_fails_on_errors_not_review_items(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(['--repo', str(self.root), '--strict']), 0)
            self.write('gradle/variant-policy.json', '{}')
            self.assertEqual(main(['--repo', str(self.root), '--strict']), 1)

    def test_rebranding_visible_strings_does_not_require_renaming_internal_alias(self):
        self.write('TMessagesProj/src/main/res/values/strings.xml',
                   '<resources><string name="AppName">FlexyGram</string><string name="AppNameBeta">FlexyGram Beta</string></resources>')
        self.write('settings.gradle', 'rootProject.name = "FlexyGram"\n')
        result = audit(self.root)
        self.assertEqual(result['errors'], 0)
        self.assertNotIn('LEGACY_VISIBLE_STRING', self.codes())
        self.assertNotIn('LEGACY_ACCOUNT_LABEL', self.codes())
        self.assertNotIn('LEGACY_BUILD_NAME', self.codes())


if __name__ == '__main__':
    unittest.main()
