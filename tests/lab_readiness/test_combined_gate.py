"""Synthetic gate receipts. These tests do not recursively run the real suites."""
from pathlib import Path
import copy
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools/lab_readiness'))
import run_combined_gate as gate


class CombinedGate(unittest.TestCase):
    def setUp(self):
        self.rows, self.inventories = {}, {}
        self.exits = {name: 0 for name in gate.SUITES}
        for name, (_, minimum) in gate.SUITES.items():
            self.rows[name] = dict(status='PASS', tests_run=minimum, passed=minimum,
                                   **{key: 0 for key in gate.COUNTERS})
            self.inventories[name] = {'ids': [name + '.synthetic_' + str(i) for i in range(minimum)]}

    def report(self): return gate.evaluate(self.rows, self.inventories, self.exits)

    def test_complete_separate_suites_pass(self):
        self.assertEqual(self.report()['status'], 'PASS')
        self.assertEqual(self.report()['distinct_tests'], sum(x[1] for x in gate.SUITES.values()))
        self.assertIs(self.report()['android_executed'], False)

    def test_skip_is_not_a_pass(self):
        self.rows['readiness']['skipped'] = 1
        self.assertEqual(self.report()['status'], 'BLOCKED')

    def test_expected_failure_is_not_a_pass(self):
        self.rows['native']['expected_failures'] = 1
        self.assertEqual(self.report()['status'], 'BLOCKED')

    def test_nonzero_exit_overrides_pass_receipt(self):
        self.exits['native'] = 1
        self.assertEqual(self.report()['status'], 'BLOCKED')

    def test_boolean_is_not_a_test_count(self):
        self.rows['readiness']['tests_run'] = True
        self.assertEqual(self.report()['status'], 'BLOCKED')

    def test_missing_counter_is_not_assumed_zero(self):
        del self.rows['native']['errors']
        self.assertEqual(self.report()['status'], 'BLOCKED')

    def test_missing_inventory_blocks_count_claim(self):
        self.inventories.pop('readiness')
        self.assertEqual(self.report()['status'], 'BLOCKED')

    def test_duplicate_ids_cannot_inflate_coverage(self):
        self.inventories['readiness']['ids'][0] = self.inventories['native']['ids'][0]
        self.assertIn('duplicate_test_ids', self.report()['blocking_reasons'])

    def test_partial_discovery_cannot_pass(self):
        self.inventories['readiness']['ids'].pop()
        self.rows['readiness']['tests_run'] -= 1
        self.rows['readiness']['passed'] -= 1
        self.assertEqual(self.report()['status'], 'BLOCKED')

    def test_claimed_passed_count_must_match_execution(self):
        self.rows['readiness']['passed'] -= 1
        self.assertEqual(self.report()['status'], 'BLOCKED')
