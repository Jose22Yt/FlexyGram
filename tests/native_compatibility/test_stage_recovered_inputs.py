"""All cases synthetic, no external original wheels required or downloaded."""
import io
import importlib.util
import hashlib
import json
from pathlib import Path
import stat
import tempfile
import unittest
import zipfile
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[2] / 'tools/native_compatibility/stage_recovered_inputs.py'
spec = importlib.util.spec_from_file_location('p04c_stage_private_inputs', SOURCE)
s = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s)


class StageTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.base = Path(tmp.name)
        self.bundle = self.base / 'original.zip'
        self.parts = {'original-wheels/example.whl': b'example-wheel-data',
                      'sources/example.tar.xz': b'example-source-data',
                      'source-recovery.json': b'{}'}
        self.manifest = {'files': {name: {'sha256': hashlib.sha256(value).hexdigest(),
                                        'bytes': len(value)} for name, value in self.parts.items()}}
        self.make_zip(self.parts)

    def make_zip(self, parts, **opts):
        with zipfile.ZipFile(self.bundle, 'w') as z:
            for name, data in parts.items():
                z.writestr(name, data)
        self.pin = s.digest(self.bundle)

    def verify(self, manifest=None):
        return s.inspect_archive(self.bundle, manifest or self.manifest, self.pin)

    def test_valid_archives_verified_without_staging(self):
        report = self.verify()
        self.assertEqual(report['verified_files'], 3)
        self.assertEqual(report['original_wheels'], 1)
        self.assertFalse(report['signing_key_present'])

    def test_private_staging_verified_and_receipted(self):
        output = self.base / 'private' / 'stage'
        report = s.stage(self.bundle, output, self.manifest, self.pin)
        self.assertTrue(output.is_dir())
        self.assertEqual((output / 'original-wheels/example.whl').read_bytes(), self.parts['original-wheels/example.whl'])
        self.assertFalse(report['freetype_git_checkout_prepared'])
        self.assertEqual(json.loads((output / 'stage-receipt.json').read_text())['bundle_sha256'], self.pin)

    def test_wrong_bundle_sha_rejected_without_writing(self):
        out = self.base / 'never'
        with self.assertRaisesRegex(ValueError, 'unexpected SHA'):
            s.stage(self.bundle, out, self.manifest, 'f' * 64)
        self.assertFalse(out.exists())

    def test_corrupted_member_rejected_even_if_bundle_pin_updated(self):
        self.make_zip({**self.parts, 'sources/example.tar.xz': b'CHANGED'})
        with self.assertRaisesRegex(ValueError, 'file or size|digest mismatch'):
            self.verify()

    def test_extra_file_rejected(self):
        self.make_zip({**self.parts, 'private/password.txt': b'bad'})
        with self.assertRaisesRegex(ValueError, 'Unexpected file'):
            self.verify()

    def test_missing_file_rejected(self):
        self.make_zip({k:v for k,v in self.parts.items() if k!='source-recovery.json'})
        with self.assertRaisesRegex(ValueError, 'missing manifest'):
            self.verify()

    def test_duplicate_member_rejected(self):
        with zipfile.ZipFile(self.bundle, 'w') as z:
            z.writestr('original-wheels/example.whl', b'example-wheel-data')
            z.writestr('original-wheels/example.whl', b'example-wheel-data')
        self.pin = s.digest(self.bundle)
        with self.assertRaisesRegex(ValueError, 'Duplicate ZIP'):
            self.verify()

    def test_path_traversal_rejected(self):
        self.make_zip({**self.parts, '../evil': b'evil'})
        with self.assertRaisesRegex(ValueError, 'Unsafe ZIP'):
            self.verify()

    def test_symlink_member_rejected(self):
        with zipfile.ZipFile(self.bundle, 'w') as z:
            for name, data in self.parts.items():
                m = zipfile.ZipInfo(name)
                m.create_system = 3
                m.external_attr = (stat.S_IFLNK | 0o777) << 16 if name.endswith('.whl') else (stat.S_IFREG | 0o600) << 16
                z.writestr(m, data)
        self.pin = s.digest(self.bundle)
        with self.assertRaisesRegex(ValueError, 'nonregular'):
            self.verify()

    def test_manifest_with_parent_traversal_rejected(self):
        data = {'files': {'sources/../../escape': {'sha256': '0'*64, 'bytes': 0}}}
        with self.assertRaisesRegex(ValueError, 'Unsafe manifest'):
            s.validate_manifest(data)

    def test_source_checkout_as_stage_directory_rejected(self):
        with patch.object(s, 'REPO', self.base):
            with self.assertRaisesRegex(ValueError, 'outside checkout'):
                s.stage(self.bundle, self.base / 'repo-folder', self.manifest, self.pin)

    def test_destination_already_exists_rejected(self):
        dest = self.base / 'exists'
        dest.mkdir()
        with self.assertRaisesRegex(ValueError, 'Destination must be new'):
            s.stage(self.bundle, dest, self.manifest, self.pin)

    def test_archive_symlink_rejected(self):
        link = self.base / 'link.zip'
        link.symlink_to(self.bundle)
        with self.assertRaisesRegex(ValueError, 'absent, unsafe'):
            s.inspect_archive(link, self.manifest, self.pin)

    def test_bad_manifest_digest_rejected(self):
        other = json.loads(json.dumps(self.manifest))
        other['files']['sources/example.tar.xz']['sha256'] = 'a' * 64
        with self.assertRaisesRegex(ValueError, 'digest mismatch'):
            self.verify(other)


if __name__ == '__main__':
    unittest.main()
