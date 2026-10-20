"""Offline combined gate: retains the native gate and actually runs lab_readiness.

Run under Python 3.11, optionally -O. No SDK, APK, ADB, boot or network operations.
Pinned PR20/PR21 paths and JDK21 must already be prepared outside the checkout.
"""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
SUITES = {'native': (ROOT / 'tests/native_compatibility', 318),
          'readiness': (ROOT / 'tests/lab_readiness', 49)}
COUNTERS = ('failures', 'errors', 'skipped', 'expected_failures', 'unexpected_successes')


def ids(suite):
    result = []
    for item in suite:
        result.extend(ids(item) if isinstance(item, unittest.TestSuite) else [item.id()])
    return result


def discover(name):
    directory, _ = SUITES[name]
    return unittest.TestLoader().discover(str(directory), top_level_dir=str(directory))


def worker(name, inventory_only):
    suite = discover(name)
    names = ids(suite)
    if inventory_only:
        return {'ids': names}
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    counters = {key: len(getattr(result, key if key != 'expected_failures' else 'expectedFailures'))
                for key in ('failures', 'errors', 'skipped', 'expected_failures')}
    counters['unexpected_successes'] = len(result.unexpectedSuccesses)
    passed = result.testsRun - sum(counters.values())
    accepted = result.wasSuccessful() and not any(counters.values()) and result.testsRun >= SUITES[name][1]
    return dict(status='PASS' if accepted else 'BLOCKED', tests_run=result.testsRun,
                passed=passed, **counters)


def evaluate(reports, inventories, exits):
    reasons, all_ids = [], []
    for name, (_, minimum) in SUITES.items():
        row, names = reports.get(name, {}), inventories.get(name, {}).get('ids', [])
        if not isinstance(row, dict):
            row = {}
        if not isinstance(names, list) or not all(type(x) is str for x in names):
            reasons.append(name + ':invalid_inventory')
            names = []
        all_ids.extend(names)
        if type(exits.get(name)) is not int or exits[name] != 0:
            reasons.append(name + ':exit')
        if row.get('status') != 'PASS':
            reasons.append(name + ':status')
        count = row.get('tests_run')
        if type(count) is not int or count < minimum or count != len(names):
            reasons.append(name + ':discovery_count')
        if type(row.get('passed')) is not int or row.get('passed') != count:
            reasons.append(name + ':passed_count')
        for field in COUNTERS:
            if type(row.get(field)) is not int or row[field] != 0:
                reasons.append(name + ':' + field)
    if len(all_ids) != len(set(all_ids)):
        reasons.append('duplicate_test_ids')
    return {'status': 'BLOCKED' if reasons else 'PASS', 'blocking_reasons': reasons,
            'distinct_tests': len(set(all_ids)), 'tests_run': sum(
                r['tests_run'] for r in reports.values() if isinstance(r, dict) and type(r.get('tests_run')) is int),
            'suite_reports': reports, 'android_executed': False,
            'limits': 'Host Python/Java synthetic regressions only; not Android certification'}


def snapshot():
    # Detect source changes between inventory and execution. No environment values retained.
    files = []
    for folder in ['tests/native_compatibility', 'tests/lab_readiness',
                   'tools/native_compatibility', 'tools/lab_readiness']:
        files.extend(sorted((ROOT / folder).rglob('*.py')))
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}


def run(output):
    if sys.version_info[:2] != (3, 11):
        raise ValueError('Python 3.11 required')
    output = output.absolute()
    if output.exists() or output == ROOT or ROOT in output.resolve().parents or any(p.is_symlink() for p in output.parents):
        raise ValueError('New evidence directory outside checkout required')
    output.mkdir(parents=True, mode=0o700)
    start = snapshot()
    flags = ['-B'] + (['-O'] if sys.flags.optimize else [])
    reports, inventories, exits = {}, {}, {}
    for name in SUITES:
        # Separate interpreters avoid module-name collisions between discovery roots.
        inv_command = [sys.executable, *flags, str(Path(__file__).resolve()), '--inventory', name]
        try:
            inv = subprocess.run(inv_command, cwd=ROOT, capture_output=True, text=True, timeout=180)
            (output / (name + '-inventory.log')).write_text(inv.stderr)
            inventories[name] = json.loads(inv.stdout) if inv.returncode == 0 else {}
        except (OSError, ValueError, subprocess.SubprocessError):
            inventories[name] = {}
        if not isinstance(inventories[name], dict):
            inventories[name] = {}
        result_path = output / (name + '.json')
        command = ([sys.executable, *flags, str(ROOT / 'tests/native_compatibility/run_gate.py'), '--output', str(result_path)]
                   if name == 'native' else
                   [sys.executable, *flags, str(Path(__file__).resolve()), '--readiness-worker'])
        try:
            process = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=900)
            exits[name] = process.returncode
            (output / (name + '.log')).write_text(process.stderr)
            (output / (name + '.stdout')).write_text(process.stdout)
            reports[name] = json.loads(result_path.read_text() if name == 'native' and result_path.exists() else process.stdout)
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            exits[name] = -1
            reports[name] = {'status': 'BLOCKED', 'error_type': type(error).__name__}
    result = evaluate(reports, inventories, exits)
    result.update(python=sys.version.split()[0], optimized=bool(sys.flags.optimize), source_sha256=start,
                  test_ids=inventories)
    if snapshot() != start:
        result['blocking_reasons'].append('sources_changed_during_execution')
        result['status'] = 'BLOCKED'
    (output / 'combined.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument('--output', type=Path)
    modes.add_argument('--inventory', choices=SUITES)
    modes.add_argument('--readiness-worker', action='store_true')
    args = parser.parse_args()
    if args.inventory:
        result = worker(args.inventory, True)
    elif args.readiness_worker:
        result = worker('readiness', False)
    else:
        result = run(args.output)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get('status', 'PASS') == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
