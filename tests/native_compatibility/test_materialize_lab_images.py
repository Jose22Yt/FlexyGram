"""Synthetic sparse-copy and traversal checks; never uses Android image data."""
from pathlib import Path
from io import BytesIO
import hashlib
import tempfile
import unittest
import materialize_lab_images as images


class MaterializationTests(unittest.TestCase):
    def test_sparse_zero_and_nonzero_bytes_preserved(self):
        payload = bytes(65536*2)+b'SYNTHETIC'+bytes(65536*2)
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory)/'image'
            row = images.sparse_copy(BytesIO(payload), p, len(payload))
            self.assertEqual(p.read_bytes(), payload)
            self.assertEqual(row['sha256'], hashlib.sha256(payload).hexdigest())
            self.assertTrue(row['readback_verified'])

    def test_length_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError): images.sparse_copy(BytesIO(b'SYNTHETIC'), Path(directory)/'image', 999)

    def test_existing_file_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory)/'image';p.write_bytes(b'SYNTHETIC_EXISTING')
            with self.assertRaises(FileExistsError): images.sparse_copy(BytesIO(b''), p, 0)
            self.assertEqual(p.read_bytes(), b'SYNTHETIC_EXISTING')

    def test_traversal_and_foreign_root_rejected(self):
        for name in ('../escape', '/arm64-v8a/file', 'arm64-v8a/../../escape', 'x86_64/file', 'arm64-v8a\\escape'):
            with self.subTest(name=name), self.assertRaises(ValueError): images.safe_relative(name)
        self.assertEqual(images.safe_relative('arm64-v8a/system.img'), Path('system.img'))
