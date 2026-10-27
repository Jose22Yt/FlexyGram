"""Alpha1275 changes must reverse exactly onto the physically accepted Alpha1274."""
import subprocess
import unittest

from alpha1275_contract import BASE, ROOT, paths, restore as restore_alpha1275
from performance.universal_contract import restore as restore_performance3

def restore(path, data):
    return restore_alpha1275(path, restore_performance3(path, data))


class Alpha1275Integration(unittest.TestCase):
    def test_reviewed_delta_and_tamper_rejection(self):
        changed = paths()
        self.assertGreater(len(changed), 15)
        self.assertIn('TMessagesProj/src/main/java/org/telegram/ui/Components/FilterTabsView.java', changed)
        self.assertIn('TMessagesProj/src/main/java/app/flexygram/bubbles/BubbleSkinPickerView.java', changed)
        for path in changed:
            with self.subTest(path=path):
                current = (ROOT / path).read_bytes()
                baseline = subprocess.run(['git', 'show', BASE + ':' + path], cwd=ROOT, capture_output=True)
                self.assertEqual(restore(path, current), baseline.stdout if baseline.returncode == 0 else b'')
                with self.assertRaises(ValueError):
                    restore(path, current + b'\nUNREVIEWED\n')

    def test_native_engine_and_approved_studio_are_untouched(self):
        for path in ('TMessagesProj/src/main/java/org/telegram/messenger/MediaController.java',
                     'TMessagesProj/src/main/java/org/telegram/ui/ActionBar/ActionBarLayout.java',
                     'TMessagesProj/src/main/java/app/flexygram/studio/core/StudioCodec.java'):
            with self.subTest(path=path):
                baseline = subprocess.check_output(['git', 'show', BASE + ':' + path], cwd=ROOT)
                self.assertEqual((ROOT / path).read_bytes(), baseline)

    def test_direct_signed_apk_remains_private(self):
        import re
        import yaml
        from startup_contract import restore as restore_current
        gradle = restore_current('TMessagesProj/build.gradle', (ROOT / 'TMessagesProj/build.gradle').read_bytes()).decode()
        self.assertEqual(re.search(r'def verCode = (\d+)', gradle)[1], '1275')
        workflow = yaml.safe_load(restore_current('.github/workflows/connected-alpha-arm64.yml', (ROOT / '.github/workflows/connected-alpha-arm64.yml').read_bytes()).decode())
        steps = workflow['jobs']['build-arm64']['steps']
        verifier = next(step['run'] for step in steps if step.get('name') == 'Verify APK against independently authorized certificate')
        self.assertIn('tools/connected_alpha/signature_verifier.py', verifier)
        self.assertIn('--expected-version-code 1275', verifier)
        self.assertIn("data['elf_count'] != 96", verifier)
        self.assertFalse(any('upload-artifact' in step.get('uses', '') for step in steps))
        pr = yaml.safe_load((ROOT / '.github/workflows/pr.yml').read_text())
        self.assertNotIn("secrets.LOCAL_PROPERTIES",str(pr["jobs"]["build"]))
        self.assertIn(":TMessagesProj:assembleConnectedAlpha --dry-run",str(pr["jobs"]["build"]))
