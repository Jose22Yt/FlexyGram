import io
import struct
import unittest
import zipfile
from verify_apk import (binary_boolean_is_false, has_launcher_alias, inspect_archive,
                        inspect_elf, launcher_diagnostic, provider_authorities,
                        security_attribute_diagnostic)


PACKAGED_MANIFEST = '''
E: manifest (line=2)
  E: application (line=10)
    A: android:enabled(0x0101000e)=(type 0x12)0xffffffff
    E: activity (line=15)
      A: android:name(0x01010003)="org.telegram.ui.LaunchActivity" (Raw: "org.telegram.ui.LaunchActivity")
    E: activity-alias (line=35)
      A: android:name(0x01010003)="org.telegram.messenger.ExteralessIcon" (Raw: "org.telegram.messenger.ExteralessIcon")
      A: android:targetActivity(0x01010202)="org.telegram.ui.LaunchActivity" (Raw: "org.telegram.ui.LaunchActivity")
      A: android:enabled(0x0101000e)=(type 0x12)0xffffffff
      A: android:exported(0x01010010)=(type 0x12)0xffffffff
      E: intent-filter (line=40)
        E: action (line=41)
          A: android:name(0x01010003)="android.intent.action.MAIN" (Raw: "android.intent.action.MAIN")
        E: category (line=42)
          A: android:name(0x01010003)="android.intent.category.LAUNCHER" (Raw: "android.intent.category.LAUNCHER")
'''


class PackagedLauncherVerification(unittest.TestCase):
    def test_binary_backup_flags_reject_true_missing_or_duplicates(self):
        for prefix in ('android:', 'http://schemas.android.com/apk/res/android:'):
            with self.subTest(prefix=prefix):
                line = f'A: {prefix}allowBackup(0x01010280)=(type 0x12)0x00000000'
                self.assertTrue(binary_boolean_is_false(line, 'allowBackup'))
                self.assertTrue(binary_boolean_is_false(line.replace('0x00000000', '0x0'), 'allowBackup'))
                self.assertFalse(binary_boolean_is_false(line.replace('0x00000000', '0xffffffff'), 'allowBackup'))
                self.assertFalse(binary_boolean_is_false(line + '\n' + line, 'allowBackup'))
                self.assertFalse(binary_boolean_is_false('', 'allowBackup'))

    def test_packaged_provider_authorities_accepts_both_namespace_spellings(self):
        self.assertEqual(provider_authorities('''
            A: http://schemas.android.com/apk/res/android:authorities(0x01010018)="io.github.jose22yt.flexygram.alpha.provider" (Raw: "io.github.jose22yt.flexygram.alpha.provider")
            A: android:authorities(0x01010018)="io.github.jose22yt.flexygram.alpha.streaming"
        '''), ['io.github.jose22yt.flexygram.alpha.provider',
               'io.github.jose22yt.flexygram.alpha.streaming'])

    def test_security_diagnostic_excludes_other_metadata(self):
        manifest = ('A: http://schemas.android.com/apk/res/android:allowBackup(0x01010280)=(type 0x12)0x0\n'
                    'A: android:value="sensitive-other-metadata"\n')
        self.assertEqual(len(security_attribute_diagnostic(manifest)), 1)
        self.assertNotIn('sensitive-other-metadata', str(security_attribute_diagnostic(manifest)))

    def test_failure_diagnostic_limits_output_to_public_launcher_structure(self):
        diagnostic = launcher_diagnostic(PACKAGED_MANIFEST +
            '    A: android:value="sensitive-other-metadata"\n')
        self.assertIn('activity-alias', str(diagnostic))
        self.assertIn('ExteralessIcon', str(diagnostic))
        self.assertNotIn('sensitive-other-metadata', str(diagnostic))

    def test_accepts_launcher_alias_even_without_badging_launchable_activity(self):
        self.assertTrue(has_launcher_alias(PACKAGED_MANIFEST))

    def test_accepts_actual_aapt2_namespace_and_indentation(self):
        real_shape = PACKAGED_MANIFEST.replace('android:',
            'http://schemas.android.com/apk/res/android:')
        real_shape = '\n'.join('  ' + line for line in real_shape.splitlines())
        self.assertTrue(has_launcher_alias(real_shape))

    def test_rejects_disabled_or_unexported_alias(self):
        for attribute in ('enabled', 'exported'):
            with self.subTest(attribute=attribute):
                hex_id = '0e' if attribute == 'enabled' else '10'
                original = f'      A: android:{attribute}(0x010100{hex_id})=(type 0x12)0xffffffff'
                manifest = PACKAGED_MANIFEST.replace(original, original.replace('0xffffffff', '0x0'))
                self.assertFalse(has_launcher_alias(manifest))

    def test_rejects_missing_target_wrong_category_and_alias_before_target(self):
        self.assertFalse(has_launcher_alias(PACKAGED_MANIFEST.replace('android.intent.category.LAUNCHER', 'android.intent.category.DEFAULT')))
        self.assertFalse(has_launcher_alias(PACKAGED_MANIFEST.replace('android:targetActivity(0x01010202)="org.telegram.ui.LaunchActivity"', 'android:targetActivity(0x01010202)="org.telegram.ui.MissingActivity"')))
        start = PACKAGED_MANIFEST.index('    E: activity (line=15)')
        end = PACKAGED_MANIFEST.index('    E: activity-alias (line=35)')
        self.assertFalse(has_launcher_alias(PACKAGED_MANIFEST[:start]+PACKAGED_MANIFEST[end:]+PACKAGED_MANIFEST[start:end]))


def elf(machine=183, alignment=16384, address=0, kind=1):
    data = bytearray(128)
    data[:6] = b'\x7fELF\x02\x01'
    struct.pack_into('<H', data, 18, machine)
    struct.pack_into('<Q', data, 32, 64)
    struct.pack_into('<HH', data, 54, 56, 1)
    struct.pack_into('<IIQQQQQQ', data, 64, kind, 5, 0, address, 0, len(data), len(data), alignment)
    return data


class ElfVerification(unittest.TestCase):
    def test_arm64_16k(self):
        self.assertEqual(inspect_elf(elf(), 'runtime.so')['name'], 'runtime.so')

    def test_arm64_64k(self):
        self.assertIn('sha256', inspect_elf(elf(alignment=65536), 'runtime.so'))

    def test_reject_x86(self):
        with self.assertRaisesRegex(ValueError, 'not AArch64'):
            inspect_elf(elf(machine=62), 'runtime.so')

    def test_reject_4k_only(self):
        with self.assertRaisesRegex(ValueError, '16 KB'):
            inspect_elf(elf(alignment=4096), 'runtime.so')

    def test_reject_bad_segment_congruence(self):
        with self.assertRaisesRegex(ValueError, '16 KB'):
            inspect_elf(elf(address=4096), 'runtime.so')

    def test_reject_no_loads(self):
        with self.assertRaisesRegex(ValueError, 'missing PT_LOAD'):
            inspect_elf(elf(kind=0), 'runtime.so')

    def test_reject_truncated_segment(self):
        with self.assertRaisesRegex(ValueError, 'truncated PT_LOAD'):
            inspect_elf(elf()[:-1], 'runtime.so')

    def test_inspect_nested_chaquopy(self):
        nested = io.BytesIO()
        with zipfile.ZipFile(nested, 'w') as z:
            z.writestr('java/chaquopy.so', elf())
        outer = io.BytesIO()
        with zipfile.ZipFile(outer, 'w') as z:
            z.writestr('assets/chaquopy/bootstrap-native.imy', nested.getvalue())
        with zipfile.ZipFile(outer) as z:
            result = inspect_archive(z)
        self.assertEqual(len(result), 1)
        self.assertIn('imy!/java/chaquopy.so', result[0]['name'])


if __name__ == '__main__':
    unittest.main()
