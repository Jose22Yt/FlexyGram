"""Fail-closed contract tests for run_gate.py; no Android or network dependencies."""
import io
from pathlib import Path
import tempfile
import unittest
from run_gate import run_suite


class OfflineGateTests(unittest.TestCase):
    def run_fixture(self, name, source):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path / ('test_gate_' + name + '.py')).write_text(source, encoding='utf-8')
            return run_suite(path, stream=io.StringIO())

    def test_success_reports_pass(self):
        summary = self.run_fixture('success', '''import unittest
class TestFixture(unittest.TestCase):
    def test_success(self): self.assertEqual(1, 1)
''')
        self.assertEqual((summary['status'], summary['passed'], summary['tests_run']), ('PASS', 1, 1))

    def test_skip_blocks_gate(self):
        summary = self.run_fixture('skip', '''import unittest
class TestFixture(unittest.TestCase):
    @unittest.skip('Required hardware not available')
    def test_skip(self): pass
''')
        self.assertEqual((summary['status'], summary['skipped']), ('BLOCKED', 1))

    def test_failure_blocks_gate(self):
        summary = self.run_fixture('failure', '''import unittest
class TestFixture(unittest.TestCase):
    def test_failure(self): self.fail('expected')
''')
        self.assertEqual((summary['status'], summary['failures']), ('BLOCKED', 1))

    def test_import_error_blocks_gate(self):
        summary = self.run_fixture('import', 'import intentionally_nonexistent_p04c_dependency\n')
        self.assertEqual((summary['status'], summary['errors']), ('BLOCKED', 1))

    def test_expected_failure_blocks_gate(self):
        summary = self.run_fixture('xfail', '''import unittest
class TestFixture(unittest.TestCase):
    @unittest.expectedFailure
    def test_known_problem(self): self.fail('still failing')
''')
        self.assertEqual((summary['status'], summary['expected_failures']), ('BLOCKED', 1))

    def test_zero_tests_blocks_gate(self):
        summary = self.run_fixture('empty', '"""No tests."""\n')
        self.assertEqual((summary['status'], summary['tests_run']), ('BLOCKED', 0))


if __name__ == '__main__':
    unittest.main()
