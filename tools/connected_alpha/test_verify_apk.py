import io
import struct
import unittest
import zipfile
from verify_apk import inspect_archive, inspect_elf


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
