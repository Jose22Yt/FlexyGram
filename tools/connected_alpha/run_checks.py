#!/usr/bin/env python3
"""Single entry point for source parity and every Connected Alpha host test."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    commands = [
        [sys.executable, 'tools/connected_alpha/check_source.py'],
        [sys.executable, 'tools/connected_alpha/stability/audit_sources.py'],
        [sys.executable, '-m', 'unittest', 'discover', '-s', 'tools/connected_alpha', '-p', 'test_*.py', '-v'],
        [sys.executable, '-m', 'pytest', 'tests/', '-q', '-rs'],
    ]
    for command in commands:
        result = subprocess.run(command, cwd=ROOT)
        if result.returncode:
            return result.returncode
    print('PASS: source and host checks only; Android runtime NOT_TESTED.', flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
