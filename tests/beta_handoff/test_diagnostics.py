"""Optional pinned-source compatibility is an explicit command, not a skipped test."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/beta_handoff'))
import diagnostics


class DiagnosticsAdapterTests(unittest.TestCase):
    def test_modified_or_missing_pr24_source_is_not_executed(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            with self.assertRaisesRegex(ValueError, 'PR24_SOURCE_PIN_MISMATCH'):
                diagnostics.load_reviewed(folder)
            for name in diagnostics.PINS:
                (folder / name).write_text('raise AssertionError("must never execute")')
            with self.assertRaisesRegex(ValueError, 'PR24_SOURCE_PIN_MISMATCH'):
                diagnostics.load_reviewed(folder)

    def test_beta_package_is_independent(self):
        self.assertEqual(diagnostics.PACKAGE, 'io.github.jose22yt.flexygram.beta.development')
        self.assertNotIn('diagnostic', diagnostics.PACKAGE)


if __name__ == '__main__':
    unittest.main()
