"""Host configuration/collector tests, not Android instrumentation."""
import subprocess
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

try:
    from .physical_preflight import APP, SCENARIOS, collect
except ImportError:  # Direct discovery with -s .../stability remains supported.
    from physical_preflight import APP, SCENARIOS, collect

ROOT = Path(__file__).resolve().parents[3]
BASE = '4b0bf291284ff64c3cac89ccdf2b76bb00041e39'
XML = 'TMessagesProj/src/connectedAlpha/res/xml/provider_paths.xml'
MAIN = 'TMessagesProj/src/main/res/xml/provider_paths.xml'
FILES = Path('/data/user/0/' + APP + '/files')
ROOTS = {'files-path': FILES, 'cache-path': FILES.parent / 'cache',
         'external-path': Path('/storage/emulated/0'), 'root-path': Path('/')}


def configured_paths(data):
    """Model FileProvider's canonical directory containment, not its Android runtime."""
    return [(ROOTS[e.tag] / e.attrib['path'].lstrip('/')).resolve()
            for e in ET.fromstring(data)]


def covered(data, file):
    return any(file.resolve().is_relative_to(root) for root in configured_paths(data))


class AttachmentConfiguration(unittest.TestCase):
    def test_baseline_cannot_expose_relocated_attachment(self):
        original = subprocess.check_output(['git', 'show', f'{BASE}:{MAIN}'], cwd=ROOT)
        self.assertFalse(covered(original, FILES / 'Saved Attachments/test.pdf'))

    def test_overlay_exposes_saved_attachment_and_nested_media(self):
        xml = (ROOT / XML).read_bytes()
        for name in ('test.pdf', 'subfolder/video.mp4'):
            with self.subTest(name=name):
                self.assertTrue(covered(xml, FILES / 'Saved Attachments' / name))

    def test_other_private_files_remain_outside_roots(self):
        xml = (ROOT / XML).read_bytes()
        for file in (FILES / 'Saved Attachments/../secret.txt',
                     FILES / 'Saved Attachments-other/file.pdf',
                     FILES / 'account1/session.dat', FILES.parent / 'shared_prefs/userconf.xml',
                     FILES.parent / 'databases/cache4.db'):
            with self.subTest(file=file):
                self.assertFalse(covered(xml, file))

    def test_all_original_paths_preserved_with_only_narrow_addition(self):
        def entries(path):
            return {(e.tag, tuple(sorted(e.attrib.items()))) for e in ET.parse(ROOT / path).getroot()}
        addition = ('files-path', (('name', 'saved-attachments'), ('path', 'Saved Attachments/')))
        self.assertEqual(entries(XML), entries(MAIN) | {addition})

    def test_provider_requires_explicit_grant_and_is_not_exported(self):
        a = '{http://schemas.android.com/apk/res/android}'
        app = ET.parse(ROOT / 'TMessagesProj/src/main/AndroidManifest.xml').getroot().find('application')
        provider = next(e for e in app.findall('provider') if e.get(a+'authorities') == '${applicationId}.provider')
        self.assertEqual(provider.get(a+'exported'), 'false')
        self.assertEqual(provider.get(a+'grantUriPermissions'), 'true')
        self.assertTrue(any(e.get(a+'resource') == '@xml/provider_paths' for e in provider.findall('meta-data')))


class DeviceCollector(unittest.TestCase):
    def fake(self, api='37', abi='arm64-v8a', qemu='', pages='4096', installed=()):
        values = {'ro.build.version.sdk': api, 'ro.product.cpu.abi': abi, 'ro.kernel.qemu': qemu}
        def shell(*args):
            if args[0] == 'getprop':
                return values[args[1]] + '\n'
            if args[0] == 'getconf':
                return pages + '\n'
            # Simulate pm substring filtering: only exact package matches count.
            return '\n'.join('package:' + p for p in installed if args[-1] in p)
        return shell

    def test_both_page_sizes_leave_every_acceptance_pending(self):
        for pages in ('4096', '16384'):
            result = collect(self.fake(pages=pages, installed=(APP, 'com.exteraless.app')))
            self.assertEqual(result['page_size'], int(pages))
            self.assertEqual(result['acceptance'], dict.fromkeys(SCENARIOS, 'PENDING'))
            self.assertTrue(result['installed'][APP])
            self.assertTrue(result['installed']['com.exteraless.app'])

    def test_substring_package_does_not_count_as_alpha(self):
        self.assertFalse(collect(self.fake(installed=(APP+'.old',)))['installed'][APP])

    def test_reject_wrong_api_abi_emulator_or_unknown_pages(self):
        for kwargs in ({'api': '36'}, {'api': ''}, {'abi': 'x86_64'}, {'qemu': '1'},
                       {'qemu': 'unknown'}, {'pages': '65536'}, {'pages': 'error'}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                collect(self.fake(**kwargs))

    def test_package_manager_error_cannot_be_treated_as_not_installed(self):
        fake = self.fake()
        with self.assertRaisesRegex(ValueError, 'package-manager'):
            collect(lambda *args: 'Error: user locked' if args[0] == 'pm' else fake(*args))


if __name__ == '__main__':
    unittest.main()
