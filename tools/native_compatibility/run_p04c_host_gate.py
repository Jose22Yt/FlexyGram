#!/usr/bin/env python3
"""Strict offline P0.4c host-only gate, to run with Python 3.11 and -O.

No Android, downloads, original binaries, wheel rebuild or signing is attempted.
Both invocations are required; do not treat a single success as a complete gate.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import unittest

REPO = Path(__file__).resolve().parents[2]
TESTS = REPO / 'tests/native_compatibility'
PATTERNS = (
    'test_stage_recovered_inputs.py',
    'test_pinned_freetype.py',
    'test_reproduce_locked_16k.py',
)
SCRIPTS = (
    'tools/native_compatibility/stage_recovered_inputs.py',
    'tools/native_compatibility/pinned_freetype.py',
    'tools/native_compatibility/reproduce_locked_16k.py',
)
MINIMUM_TESTS = 52


def main() -> int:
    mode = 'optimized' if sys.flags.optimize else 'normal'
    # Disallow implicit fallback to Python 3.13, even if the synthetic tests pass.
    if sys.version_info[:2] != (3, 11):
        print(json.dumps({'status': 'BLOCKED_PYTHON_VERSION',
                          'required': '3.11', 'actual': sys.version.split()[0],
                          'mode': mode}))
        return 1

    # Do not persist interpreter caches in the source checkout.
    sys.dont_write_bytecode = True
    hashes = {}
    try:
        for filename in SCRIPTS:
            target = REPO / filename
            source = target.read_bytes()
            compile(source, str(target), 'exec')
            hashes[filename] = hashlib.sha256(source).hexdigest()

        loader = unittest.TestLoader()
        suites = []
        for pattern in PATTERNS:
            suite = loader.discover(str(TESTS), pattern=pattern)
            suites.append(suite)
        tests = unittest.TestSuite(suites)
        count = tests.countTestCases()
        if loader.errors or count < MINIMUM_TESTS:
            raise ValueError('Test discovery incomplete or below reviewed minimum: '
                             + str(count) + '; ' + repr(loader.errors))
        result = unittest.TextTestRunner(verbosity=2, stream=sys.stderr).run(tests)
        approved = (result.wasSuccessful() and result.testsRun == count and
                    not result.skipped and not result.expectedFailures and
                    not result.unexpectedSuccesses)
        report = {'status': 'P04C_HOST_PASS' if approved else 'P04C_HOST_BLOCKED',
                  'python': sys.version.split()[0], 'mode': mode,
                  'tests': result.testsRun, 'skipped': len(result.skipped),
                  'failures': len(result.failures), 'errors': len(result.errors),
                  'file_sha256': hashes, 'android_runtime_validated': False,
                  'apk_built': False, 'apk_signed': False}
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if approved else 1
    except (OSError, ValueError, SyntaxError) as exc:
        print(json.dumps({'status': 'P04C_HOST_BLOCKED',
                          'error_class': type(exc).__name__,
                          'mode': mode, 'android_runtime_validated': False}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
