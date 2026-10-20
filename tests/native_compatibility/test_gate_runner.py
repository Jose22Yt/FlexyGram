"""Fail-closed contract tests for run_gate.py; no Android or network dependencies."""
import io
import json
from contextlib import redirect_stdout
from unittest.mock import patch
from pathlib import Path
import tempfile
import unittest
from run_gate import run_suite, main


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

    def test_main_blocks_incomplete_test_discovery(self):
        fake = {'status': 'PASS', 'passed': 199, 'tests_run': 199,
                'errors': 0, 'failures': 0, 'skipped': 0}
        with patch('run_gate.run_suite', return_value=fake), redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main([]), 1)
        report = json.loads(output.getvalue())
        self.assertEqual(report['status'], 'BLOCKED')
        self.assertTrue(report['discovery_incomplete'])
        self.assertEqual(report['minimum_required'], 200)

    def test_main_accepts_complete_reviewed_discovery(self):
        fake = {'status': 'PASS', 'passed': 200, 'tests_run': 200,
                'errors': 0, 'failures': 0, 'skipped': 0}
        with patch('run_gate.run_suite', return_value=fake), redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main([]), 0)
        report = json.loads(output.getvalue())
        self.assertEqual(report['status'], 'PASS')
        self.assertFalse(report['discovery_incomplete'])

    def test_zero_tests_blocks_gate(self):
        summary = self.run_fixture('empty', '"""No tests."""\n')
        self.assertEqual((summary['status'], summary['tests_run']), ('BLOCKED', 0))


if __name__ == '__main__':
    unittest.main()
