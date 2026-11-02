import tempfile
import unittest
import zipfile
from pathlib import Path
from preflight_sdk import normalize_platform


def payload(root, level='37.0'):
    root.mkdir(parents=True, exist_ok=True)
    (root/'source.properties').write_text('AndroidVersion.ApiLevel='+level+'\n')
    (root/'build.prop').write_text('ro.build.version.sdk=37\n')
    (root/'framework.aidl').write_text('// SDK layout unit fixture\n')
    for name in ['android.jar', 'core-for-system-modules.jar']:
        with zipfile.ZipFile(root/name, 'w') as z:
            z.writestr('android/app/Activity.class', b'unit-fixture')


class SdkLayoutRegression(unittest.TestCase):
    def test_complete_platform_is_not_modified(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)/'android-37.0'; payload(root)
            before = (root/'android.jar').read_bytes()
            self.assertFalse(normalize_platform(root))
            self.assertEqual(before, (root/'android.jar').read_bytes())

    def test_lifts_original_payload_without_rewriting_metadata(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)/'android-37.0'; nested = root/root.name; payload(nested)
            original = {p.name:p.read_bytes() for p in nested.iterdir()}
            (root/'package.xml').write_text('unit package manager metadata')
            self.assertTrue(normalize_platform(root))
            self.assertFalse(nested.exists())
            for name, data in original.items():self.assertEqual((root/name).read_bytes(), data)
            self.assertTrue((root/'package.xml').exists())

    def test_wrong_api_rejected_before_any_moves(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)/'android-37.0'; nested = root/root.name; payload(nested, '35')
            with self.assertRaisesRegex(ValueError, 'API 37'):normalize_platform(root)
            self.assertTrue((nested/'android.jar').is_file())
            self.assertFalse((root/'android.jar').exists())

    def test_ambiguous_installation_never_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)/'android-37.0'; payload(root/root.name)
            (root/'android.jar').write_bytes(b'existing-file')
            with self.assertRaisesRegex(ValueError, 'Ambiguous'):normalize_platform(root)
            self.assertEqual((root/'android.jar').read_bytes(), b'existing-file')

    def test_missing_payload_is_not_synthesized(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)/'android-37.0'; payload(root/root.name)
            (root/root.name/'build.prop').unlink()
            with self.assertRaisesRegex(ValueError, 'build.prop'):normalize_platform(root)
            self.assertFalse((root/'build.prop').exists())
