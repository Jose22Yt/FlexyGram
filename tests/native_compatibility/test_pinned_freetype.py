"""Offline tests of the signed-off FreeType source export fallback."""
import hashlib
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[2] / 'tools/native_compatibility/pinned_freetype.py'
spec = importlib.util.spec_from_file_location('flexygram_free_freetype_source', SCRIPT)
f = importlib.util.module_from_spec(spec)
spec.loader.exec_module(f)


class PinnedFreetypeTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.original = b'illustrative-git-archive-payload'
        self.export = self.root / f.EXPORT_NAME
        self.export.write_bytes(self.original)

    def read(self):
        with patch.object(f, 'EXPORT_SHA256', hashlib.sha256(self.original).hexdigest()):
            return f.read_pinned_freetype(self.root, f.PINNED_COMMIT)

    def test_exact_pinned_source_tar_is_accepted(self):
        self.assertEqual(self.read(), self.original)

    def test_unrecognized_commit_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'commit has changed'):
            f.read_pinned_freetype(self.root, '0'*40)

    def test_missing_export_is_rejected(self):
        self.export.unlink()
        with self.assertRaisesRegex(ValueError, 'Neither verified'):
            self.read()

    def test_export_contents_changed_is_rejected(self):
        self.export.write_bytes(b'tampered')
        with self.assertRaisesRegex(ValueError, 'SHA-256 mismatch'):
            self.read()

    def test_export_symlink_is_rejected(self):
        real = self.root / 'real-export.tar'
        self.export.rename(real)
        self.export.symlink_to(real)
        with self.assertRaisesRegex(ValueError, 'Neither verified'):
            self.read()

    def test_invalid_checkout_does_not_silently_fallback_to_export(self):
        (self.root / 'freetype-git').mkdir()
        with self.assertRaisesRegex(ValueError, 'incomplete FreeType checkout'):
            self.read()

    def test_symlinked_checkout_is_rejected(self):
        actual = self.root / 'checkout'
        actual.mkdir()
        (self.root / 'freetype-git').symlink_to(actual, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'Unsafe'):
            self.read()

    def test_pinned_checkout_uses_git_archive_not_untracked_files(self):
        repo = self.root / 'freetype-git'
        repo.mkdir()
        subprocess.run(['git','init','-q',str(repo)], check=True)
        subprocess.run(['git','-C',str(repo),'config','user.email','test@example.invalid'], check=True)
        subprocess.run(['git','-C',str(repo),'config','user.name','Lab fixture'], check=True)
        (repo / 'a.c').write_text('int safe;')
        subprocess.run(['git','-C',str(repo),'add','a.c'], check=True)
        subprocess.run(['git','-C',str(repo),'commit','-qm','fixture'], check=True)
        head = subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
        (repo / 'untracked-secret.txt').write_text('must_not_be_exported')
        with patch.object(f, 'PINNED_COMMIT', head):
            archive = f.read_pinned_freetype(self.root, head)
        self.assertNotIn(b'untracked-secret.txt', archive)
        self.assertIn(b'a.c', archive)


if __name__ == '__main__':
    unittest.main()
