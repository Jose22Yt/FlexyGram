"""The new checkpoint preserves prior contracts and rejects arbitrary mutations."""
from motion_contract import restore_navigation
import subprocess
import unittest
from signature_refinement_contract import ROOT, BASE, REVIEWED, restore


class SignatureRefinement(unittest.TestCase):
    def test_every_reviewed_change_restores_exact_alpha1275(self):
        for path in REVIEWED:
            with self.subTest(path=path):
                data = (ROOT / path).read_bytes()
                baseline = subprocess.run(['git', 'show', BASE + ':' + path], cwd=ROOT, capture_output=True)
                before = baseline.stdout if baseline.returncode == 0 else b''
                self.assertEqual(restore(path, data), before)
                self.assertEqual(restore(path, before), before)
                with self.assertRaises(ValueError):
                    restore(path, data + b'\nUNREVIEWED\n')

    def test_native_navigation_audio_and_studio_are_byte_exact(self):
        for path in (
            'org/telegram/ui/ActionBar/ActionBarLayout.java',
            'org/telegram/messenger/MediaController.java',
            'app/flexygram/studio/core/StudioCodec.java',
        ):
            path = 'TMessagesProj/src/main/java/' + path
            with self.subTest(path=path):
                before = subprocess.check_output(['git', 'show', BASE + ':' + path], cwd=ROOT)
                self.assertEqual(restore_navigation(path, (ROOT / path).read_bytes()), before)
