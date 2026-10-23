"""Regressions for concrete CI/verification failures; does not build a Telegram client."""
import base64
import json
from pathlib import Path
import unittest
import yaml
from ci_inputs import decode_input, fingerprint, validate_api, validate_firebase
from verify_apk import require_telegram_payload

ROOT = Path(__file__).resolve().parents[2]
APP = 'io.github.jose22yt.flexygram.alpha'


class CloudBuildRegression(unittest.TestCase):
    def test_accept_actual_versioned_telegram_library(self):
        require_telegram_payload(['classes.dex', 'lib/arm64-v8a/libtmessages.49.so'])

    def test_reject_unversioned_substitute(self):
        with self.assertRaises(ValueError):
            require_telegram_payload(['classes.dex', 'lib/arm64-v8a/libtmessages.so'])

    def test_reject_missing_dex(self):
        with self.assertRaises(ValueError):
            require_telegram_payload(['lib/arm64-v8a/libtmessages.49.so'])

    def test_verifier_matches_both_native_producers(self):
        cmake = (ROOT/'TMessagesProj/jni/CMakeLists.txt').read_text()
        loader = (ROOT/'TMessagesProj/src/main/java/org/telegram/messenger/NativeLoader.java').read_text()
        self.assertIn('set(NATIVE_LIB "tmessages.49")', cmake)
        self.assertIn('LIB_VERSION = 49;', loader)

    def test_certificate_colons_supported(self):
        self.assertEqual(fingerprint(':'.join(['AB']*32)), 'ab'*32)

    def test_certificate_junk_not_silently_discarded(self):
        for value in ['x'+'ab'*32, '', 'ab'*31]:
            with self.subTest(value_length=len(value)), self.assertRaises(ValueError):
                fingerprint(value)

    def test_reject_inherited_api_identifiers(self):
        for value in ['4','6','2040','0','2147483648','x']:
            with self.subTest(identifier=value), self.assertRaises(ValueError):
                validate_api({'TELEGRAM_APP_ID':value, 'TELEGRAM_APP_HASH':'0'*32})

    def test_reject_malformed_api_hash(self):
        with self.assertRaises(ValueError):
            validate_api({'TELEGRAM_APP_ID':'123456', 'TELEGRAM_APP_HASH':'not-a-hash'})

    def test_base64_wrapping_supported(self):
        self.assertEqual(decode_input({'INPUT':base64.b64encode(b'unit-test').decode()+'\n'}, 'INPUT'), b'unit-test')

    def test_base64_errors_hide_values(self):
        with self.assertRaisesRegex(ValueError, '^INPUT is not valid base64$'):
            decode_input({'INPUT':'private-invalid-value!!!'}, 'INPUT')

    def test_firebase_other_client_rejected(self):
        fixture = {'project_info':{'project_id':'unit','project_number':'123'}, 'client':[
            {'client_info':{'android_client_info':{'package_name':'com.exteraless.app'}}}]}
        with self.assertRaisesRegex(ValueError, 'Alpha package'):
            validate_firebase(json.dumps(fixture))

    def test_firebase_truncated_configuration_rejected(self):
        with self.assertRaisesRegex(ValueError, 'complete Firebase'):
            validate_firebase(json.dumps({'client':[{'client_info':{'android_client_info':{'package_name':APP}}}]}))

    def test_support_push_enters_registered_workflow(self):
        workflow = yaml.safe_load((ROOT/'.github/workflows/pr.yml').read_text())
        events = workflow.get('on', workflow.get(True))
        self.assertIn('support/connected-alpha-ci-20261022', events['push']['branches'])
        native = workflow['jobs']['connected-alpha-native']
        self.assertEqual(native['uses'], './.github/workflows/connected-alpha-arm64.yml')
        self.assertIn("github.event_name == 'push'", native['if'])
        self.assertIn('ALPHA_CERTIFICATE_SHA256', native['secrets'])

    def test_native_support_route_is_not_duplicated(self):
        workflow = yaml.safe_load((ROOT/'.github/workflows/connected-alpha-arm64.yml').read_text())
        events = workflow.get('on', workflow.get(True))
        self.assertNotIn('support/connected-alpha-ci-20261022', events['push']['branches'])
        self.assertIn('workflow_call', events)
        self.assertEqual(len(events['workflow_call']['secrets']), 8)

    def test_legacy_debug_build_never_runs_for_push(self):
        workflow = yaml.safe_load((ROOT/'.github/workflows/pr.yml').read_text())
        self.assertIn("github.event_name == 'pull_request'", workflow['jobs']['build']['if'])

    def test_workflow_contract(self):
        workflow = yaml.safe_load((ROOT/'.github/workflows/connected-alpha-arm64.yml').read_text())
        jobs = workflow['jobs']
        self.assertIn('source-checks', jobs)
        self.assertNotIn('env', jobs['source-checks'])
        self.assertEqual(jobs['build-arm64']['needs'], ['source-checks','credentials-present'])
        self.assertEqual(jobs['build-arm64']['env']['NATIVE_TARGET'], 'arm64-v8a')
        runs = '\n'.join(s.get('run','') for s in jobs['build-arm64']['steps'])
        self.assertIn(':TMessagesProj:assembleConnectedAlpha', runs)
        self.assertNotIn('NATIVE_TARGET=SKIP', runs)
        self.assertNotRegex(runs, r'\./gradlew[^\n]*\s(?:-x|--exclude-task)\b')
        self.assertIn('toolchainVendor=ADOPTIUM', runs)
        self.assertIn('CMAKE=$ANDROID_HOME/cmake/3.31.6/bin/cmake', runs)
        gradle_setup = next(s for s in jobs['build-arm64']['steps'] if s.get('uses','').startswith('gradle/actions/setup-gradle'))
        self.assertIs(gradle_setup['with']['cache-disabled'], True)

    def test_no_plaintext_apk_upload(self):
        workflow = yaml.safe_load((ROOT/'.github/workflows/connected-alpha-arm64.yml').read_text())
        upload = [s for s in workflow['jobs']['build-arm64']['steps'] if s.get('uses','').startswith('actions/upload-artifact')]
        self.assertEqual(len(upload), 1)
        self.assertTrue(upload[0]['with']['path'].endswith('.tar.age'))
        self.assertIn('ALPHA_AGE_RECIPIENT', upload[0]['if'])
        self.assertNotIn('*.apk', upload[0]['with']['path'])


if __name__ == '__main__':
    unittest.main()
