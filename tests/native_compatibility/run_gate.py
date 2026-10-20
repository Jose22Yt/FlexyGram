"""Fail-closed, offline unittest gate for the P0.4c native-compatibility suite.

Usage (from any directory): python tests/native_compatibility/run_gate.py
Zero skips are required. This does not build/install an APK or test Android.
"""
import argparse
import io
import json
from pathlib import Path
import sys
import unittest


def run_suite(directory, pattern='test_*.py', stream=None):
    """Return a machine-readable result; skipped tests and zero tests are failures."""
    loader = unittest.TestLoader()
    suite = loader.discover(str(directory), pattern=pattern, top_level_dir=str(directory))
    runner = unittest.TextTestRunner(stream=stream if stream is not None else sys.stderr,
                                     verbosity=2)
    result = runner.run(suite)
    passed = result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped)
    passed -= len(result.unexpectedSuccesses) + len(result.expectedFailures)
    accepted = bool(result.testsRun and result.wasSuccessful() and not result.skipped
                    and not result.expectedFailures)
    return {
        'gate': 'P0.4c Python offline native-compatibility',
        'status': 'PASS' if accepted else 'BLOCKED',
        'tests_run': result.testsRun,
        'passed': passed,
        'failures': len(result.failures),
        'errors': len(result.errors),
        'skipped': len(result.skipped),
        'unexpected_successes': len(result.unexpectedSuccesses),
        'expected_failures': len(result.expectedFailures),
        'limits': 'Python unittest only; not an Android build, runtime, API24, or 16KB certification'
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path,
                        help='Optional JSON evidence path; never include environment variables')
    args = parser.parse_args(argv)
    suite_dir = Path(__file__).resolve().parent
    summary = run_suite(suite_dir)
    # Includes unsigned evidence, raw APK, post-signing and v2 draft tests.
    # No partial discovery may pass.
    minimum_tests = 249
    summary['minimum_required'] = minimum_tests
    if summary['tests_run'] < minimum_tests:
        summary['status'] = 'BLOCKED'
        summary['discovery_incomplete'] = True
    else:
        summary['discovery_incomplete'] = False
    payload = json.dumps(summary, indent=2, sort_keys=True) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding='utf-8')
    print(payload, end='')
    return 0 if summary['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
