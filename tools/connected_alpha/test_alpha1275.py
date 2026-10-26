"""Alpha1275 changes must reverse exactly onto the physically accepted Alpha1274."""
import subprocess
import unittest

from alpha1275_contract import BASE, ROOT, paths, restore


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
        gradle = (ROOT / 'TMessagesProj/build.gradle').read_text()
        self.assertEqual(re.search(r'def verCode = (\d+)', gradle)[1], '1275')
        workflow = yaml.safe_load((ROOT / '.github/workflows/connected-alpha-arm64.yml').read_text())
        steps = workflow['jobs']['build-arm64']['steps']
        verifier = next(step['run'] for step in steps if step.get('name') == 'Verify APK against independently authorized certificate')
        self.assertIn('tools/connected_alpha/signature_verifier.py', verifier)
        self.assertIn('--expected-version-code 1275', verifier)
        self.assertIn("data['elf_count'] != 96", verifier)
        self.assertFalse(any('upload-artifact' in step.get('uses', '') for step in steps))
        pr = yaml.safe_load((ROOT / '.github/workflows/pr.yml').read_text())
        self.assertIn("github.head_ref != 'integration/alpha1275-signature-performance-ui'", pr['jobs']['build']['if'])
