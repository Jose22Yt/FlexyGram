"""No network or Android environment required. Tests inspect only local wheels."""
import hashlib
import io
import tempfile
import unittest
import zipfile
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/native_compatibility'))
from wheelhouse import prepare


def fixture():
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, 'w') as z:
        z.writestr('synthetic-1.dist-info/METADATA', 'Name: synthetic\nVersion: 1\n')
    data = archive.getvalue()
    filename = 'synthetic-1-py3-none-any.whl'
    row = {'filename': filename, 'url': 'https://files.pythonhosted.org/synthetic.whl',
           'sha256': hashlib.sha256(data).hexdigest()}
    lock = {'schema': 1, 'python': '3.11', 'abis': ['arm64-v8a'],
            'packages': [{'name': 'synthetic', 'version': '1', 'files': [row]}]}
    return data, filename, lock


class WheelhouseHardeningTests(unittest.TestCase):
    def test_verified_offline_cache_remains_usable(self):
        with tempfile.TemporaryDirectory() as d:
            data, filename, lock = fixture()
            root = Path(d); cache = root/'cache'; cache.mkdir()
            (cache/filename).write_bytes(data)
            out = root/'out'
            self.assertEqual(prepare(lock, out, ['arm64-v8a'], True, cache), 1)
            self.assertEqual((out/filename).read_bytes(), data)
            self.assertEqual(prepare(lock, out, ['arm64-v8a'], True, cache), 1)

    def test_unlisted_non_wheel_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            _, _, lock = fixture(); root = Path(d)
            out = root/'out'; out.mkdir()
            (out/'unlisted.zip').write_bytes(b'not a permitted wheel')
            with self.assertRaisesRegex(ValueError, 'unlisted or unsafe'):
                prepare(lock, out, ['arm64-v8a'], True, root/'cache')

    def test_unlisted_directory_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            _, _, lock = fixture(); root = Path(d)
            out = root/'out'; out.mkdir(); (out/'unlisted').mkdir()
            with self.assertRaisesRegex(ValueError, 'unlisted or unsafe'):
                prepare(lock, out, ['arm64-v8a'], True, root/'cache')

    def test_symlink_to_approved_filename_in_output_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            data, filename, lock = fixture(); root = Path(d)
            out = root/'out'; out.mkdir()
            target = root/'outside.whl'; target.write_bytes(data)
            (out/filename).symlink_to(target)
            with self.assertRaisesRegex(ValueError, 'unlisted or unsafe'):
                prepare(lock, out, ['arm64-v8a'], True, root/'cache')

    def test_symlink_in_cache_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            data, filename, lock = fixture(); root = Path(d)
            cache = root/'cache'; cache.mkdir()
            target = root/'outside.whl'; target.write_bytes(data)
            (cache/filename).symlink_to(target)
            with self.assertRaisesRegex(ValueError, 'Symlink is not allowed'):
                prepare(lock, root/'out', ['arm64-v8a'], True, cache)

    def test_symlink_destination_directory_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            data, filename, lock = fixture(); root = Path(d)
            target = root/'elsewhere'; target.mkdir()
            alias = root/'out'; alias.symlink_to(target, target_is_directory=True)
            cache = root/'cache'; cache.mkdir(); (cache/filename).write_bytes(data)
            with self.assertRaisesRegex(ValueError, 'destination cannot be a symlink'):
                prepare(lock, alias, ['arm64-v8a'], True, cache)
            self.assertEqual(list(target.iterdir()), [])

    def test_symlink_cache_directory_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            data, filename, lock = fixture(); root = Path(d)
            target = root/'elsewhere'; target.mkdir()
            (target/filename).write_bytes(data)
            alias = root/'cache'; alias.symlink_to(target, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, 'cache cannot be a symlink'):
                prepare(lock, root/'out', ['arm64-v8a'], True, alias)

    def test_modified_locked_wheel_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            _, filename, lock = fixture(); root = Path(d)
            out = root/'out'; out.mkdir()
            (out/filename).write_bytes(b'tampered')
            with self.assertRaisesRegex(ValueError, 'digest mismatch'):
                prepare(lock, out, ['arm64-v8a'], True, root/'cache')

if __name__ == '__main__':
    unittest.main()
